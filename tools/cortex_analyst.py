from snowflake.snowpark import Session
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CortexAnalystTool:
    """Cortex Analyst wrapper using CORTEX.COMPLETE"""
    
    def __init__(self, session: Session, semantic_model_stage: str):
        self.session = session
        self.semantic_model_stage = semantic_model_stage
        self.semantic_model = self._load_semantic_model()
        
        # CHANGED: Use _build_context() instead of [:2500]
        self.schema_context = self._build_context()
        
        logger.info(f"✅ Loaded semantic model ({len(self.semantic_model)} chars)")
        logger.info(f"✅ Context built ({len(self.schema_context)} chars)")
    
    def _load_semantic_model(self) -> str:
        """Load semantic model from Snowflake stage"""
        # Create file format
        self.session.sql("""
            CREATE FILE FORMAT IF NOT EXISTS yaml_format
            TYPE = 'CSV'
            FIELD_DELIMITER = NONE
            RECORD_DELIMITER = NONE
        """).collect()
        
        # Read file
        result = self.session.sql(f"""
            SELECT t.$1 AS content
            FROM {self.semantic_model_stage} (FILE_FORMAT => yaml_format) t
        """).collect()
        
        return "\n".join([row['CONTENT'] for row in result])
    
    def _build_context(self) -> str:
        """
        NEW METHOD: Build strategic context for better generalization
        Instead of just taking first 2500 chars, extract key sections
        """
        
        # Get critical sections
        header = self.semantic_model[:800]  # Name, physical columns, market codes
        
        # Extract verified queries (they're now at top of your semantic model)
        verified_start = self.semantic_model.find('verified_queries:')
        verified_end = self.semantic_model.find('tables:', verified_start)
        verified = self.semantic_model[verified_start:verified_end] if verified_start != -1 else ""
        
        # Get first table definition (email table)
        tables_start = self.semantic_model.find('tables:')
        first_table = self.semantic_model[tables_start:tables_start+2000] if tables_start != -1 else ""
        
        # Combine sections
        context = f"{header}\n\n{verified}\n\n{first_table}"
        
        return context
    
    def _clean_sql(self, text: str) -> str:
        """Clean SQL from LLM response"""
        # Remove markdown code blocks
        text = re.sub(r'```sql\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        
        # Remove any leading/trailing whitespace
        text = text.strip()
        
        # Check if response starts with explanation instead of SQL
        explanation_keywords = ['to answer', 'this query', 'here is', 'the following', 
                               'we need', 'first', 'let me', 'i will']
        
        if any(text.lower().startswith(keyword) for keyword in explanation_keywords):
            # Try to extract SQL from explanation
            match = re.search(r'((?:WITH|SELECT).*?)(?:;|\Z)', text, re.IGNORECASE | re.DOTALL)
            if match:
                text = match.group(1)
            else:
                raise ValueError(f"LLM returned explanation without SQL: {text[:100]}...")
        
        # If multiple statements, take the first SELECT
        if 'SELECT' in text.upper():
            match = re.search(r'(SELECT.*?;?)\s*$', text, re.IGNORECASE | re.DOTALL)
            if match:
                text = match.group(1)
        
        # Remove trailing semicolon
        text = text.rstrip(';').strip()
        
        return text
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query using semantic model with pattern-based generalization
        
        Returns:
            Dict with keys: success, sql, results, row_count, error
        """
        clean_sql_text = None
        
        try:
            # Build prompt with pattern learning instructions
            prompt = f"""You are a SQL generator. Learn from the VERIFIED QUERIES examples and apply the SAME PATTERNS to new questions.

{self.schema_context}

PATTERN LEARNING RULES:
1. For "X by market" → Use GROUP BY BUSINESSUNIT (email table) or COUNTRY_CODE (conversion table)
2. For "X this week" → WHERE date >= DATE_TRUNC('week', CURRENT_DATE())
3. For "X last month" → WHERE date >= DATEADD(month, -1, CURRENT_DATE())
4. For "rate" calculations → (SUM(numerator) / NULLIF(SUM(denominator), 0)) * 100
5. For specific market (VCUS, VCUK, etc.) → WHERE BUSINESSUNIT = 'X' or COUNTRY_CODE = 'X'
6. Apply patterns from verified queries to similar questions

CRITICAL:
- Return ONLY executable SQL
- NO explanations, NO comments, NO text
- Start directly with SELECT or WITH
- Use physical column names (BUSINESSUNIT not market, SENDDATE not send_date)

USER QUESTION: {question}

SQL CODE:"""

            # Generate SQL with CORTEX.COMPLETE
            result = self.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'mistral-large',
                    '{prompt.replace("'", "''")}'
                ) AS sql_text
            """).collect()
            
            raw_sql = result[0]['SQL_TEXT']
            clean_sql_text = self._clean_sql(raw_sql)
            
            # Validation: Must start with SQL keyword
            if not clean_sql_text.strip().upper().startswith(('SELECT', 'WITH')):
                raise ValueError(f"Invalid SQL generated: {clean_sql_text[:100]}")
            
            logger.info(f"📝 Generated SQL: {clean_sql_text[:150]}...")
            
            # Execute the SQL
            data = self.session.sql(clean_sql_text).collect()
            
            return {
                'success': True,
                'sql': clean_sql_text,
                'results': [dict(row.asDict()) for row in data],
                'row_count': len(data),
                'error': None
            }
            
        except Exception as e:
            logger.error(f"❌ Query failed: {str(e)}")
            return {
                'success': False,
                'sql': clean_sql_text,
                'results': [],
                'row_count': 0,
                'error': str(e)
            }
    
    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """
        Execute raw SQL directly (for visualization agent, etc.)
        """
        try:
            data = self.session.sql(sql).collect()
            return {
                'success': True,
                'results': [dict(row.asDict()) for row in data],
                'row_count': len(data),
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'results': [],
                'row_count': 0,
                'error': str(e)
            }