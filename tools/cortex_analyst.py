from snowflake.snowpark import Session
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CortexAnalystTool:
    """Cortex Analyst wrapper using CORTEX.COMPLETE with improved SQL validation"""
    
    def __init__(self, session: Session, semantic_model_stage: str):
        self.session = session
        self.semantic_model_stage = semantic_model_stage
        self.semantic_model = self._load_semantic_model()
        self.schema_context = self._build_context()
        
        logger.info(f"✅ Loaded semantic model ({len(self.semantic_model)} chars)")
        logger.info(f"✅ Context built ({len(self.schema_context)} chars)")
    
    def _load_semantic_model(self) -> str:
        """Load semantic model from Snowflake stage"""
        self.session.sql("""
            CREATE FILE FORMAT IF NOT EXISTS yaml_format
            TYPE = 'CSV'
            FIELD_DELIMITER = NONE
            RECORD_DELIMITER = NONE
        """).collect()
        
        result = self.session.sql(f"""
            SELECT t.$1 AS content
            FROM {self.semantic_model_stage} (FILE_FORMAT => yaml_format) t
        """).collect()
        
        return "\n".join([row['CONTENT'] for row in result])
    
    def _build_context(self) -> str:
        """Build strategic context for better generalization"""
        header = self.semantic_model[:800]
        
        verified_start = self.semantic_model.find('verified_queries:')
        verified_end = self.semantic_model.find('tables:', verified_start)
        verified = self.semantic_model[verified_start:verified_end] if verified_start != -1 else ""
        
        tables_start = self.semantic_model.find('tables:')
        first_table = self.semantic_model[tables_start:tables_start+2000] if tables_start != -1 else ""
        
        context = f"{header}\n\n{verified}\n\n{first_table}"
        return context
    
    def _clean_sql(self, text: str) -> str:
        """
        🔧 IMPROVED: Clean SQL with better validation
        Fixes malformed SQL like unexpected closing parentheses
        """
        # Remove markdown code blocks
        text = re.sub(r'```sql\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        # Check if response starts with explanation
        explanation_keywords = ['to answer', 'this query', 'here is', 'the following', 
                               'we need', 'first', 'let me', 'i will']
        
        if any(text.lower().startswith(keyword) for keyword in explanation_keywords):
            match = re.search(r'((?:WITH|SELECT).*?)(?:;|\Z)', text, re.IGNORECASE | re.DOTALL)
            if match:
                text = match.group(1)
            else:
                raise ValueError(f"LLM returned explanation without SQL: {text[:100]}...")
        
        # Extract SQL if multiple statements
        if 'SELECT' in text.upper():
            match = re.search(r'(SELECT.*?;?)\s*$', text, re.IGNORECASE | re.DOTALL)
            if match:
                text = match.group(1)
        
        # Remove trailing semicolon
        text = text.rstrip(';').strip()
        
        # 🔧 NEW: Remove trailing closing parentheses that cause syntax errors
        text = re.sub(r'\s*\)\s*$', '', text)
        
        # 🔧 NEW: Remove empty FROM clauses like "FROM )"
        text = re.sub(r'\bFROM\s*\)', '', text, flags=re.IGNORECASE)
        
        # 🔧 NEW: Remove empty WHERE clauses like "WHERE )"
        text = re.sub(r'\bWHERE\s*\)', '', text, flags=re.IGNORECASE)
        
        # 🔧 NEW: Remove stray closing parens at line 7
        lines = text.split('\n')
        cleaned_lines = []
        for i, line in enumerate(lines):
            # Skip lines that are just closing parentheses
            if line.strip() == ')':
                continue
            cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)
        
        # Final validation - make sure parentheses are balanced
        open_count = text.count('(')
        close_count = text.count(')')
        if close_count > open_count:
            # Remove excess closing parens
            extra_closes = close_count - open_count
            for _ in range(extra_closes):
                text = text.rstrip(')')
        
        return text.strip()
    
    def _fix_date_columns(self, data: list) -> list:
        """Convert month numbers (1-12) to proper dates"""
        if not data:
            return data
        
        for row in data:
            for col_name, value in row.items():
                if isinstance(value, int) and 1 <= value <= 12:
                    year = 2024
                    if col_name.upper() in ['MONTH', 'DATE']:
                        try:
                            row[col_name] = f"{year}-{value:02d}-01"
                            logger.debug(f"✅ Converted {col_name} {value} → {row[col_name]}")
                        except Exception as e:
                            logger.warning(f"⚠️ Could not convert {col_name}: {e}")
        
        return data
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query using semantic model with improved SQL validation
        
        Returns:
            Dict with keys: success, sql, results, row_count, error
        """
        clean_sql_text = None
        
        try:
            # Improved prompt with better SQL generation instructions
            prompt = f"""You are a SQL generator. Learn from the VERIFIED QUERIES examples and apply the SAME PATTERNS to new questions.

{self.schema_context}

PATTERN LEARNING RULES:
1. For "X by market" → Use GROUP BY BUSINESSUNIT (email table) or COUNTRY_CODE (conversion table)
2. For "X this week" → WHERE date >= DATE_TRUNC('week', CURRENT_DATE())
3. For "X last month" → WHERE date >= DATEADD(month, -1, CURRENT_DATE())
4. For "rate" calculations → (SUM(numerator) / NULLIF(SUM(denominator), 0)) * 100
5. For specific market (VCUS, VCUK, etc.) → WHERE BUSINESSUNIT = 'X' or COUNTRY_CODE = 'X'
6. FOR TIME-SERIES QUERIES: ALWAYS use DATE_TRUNC('MONTH', date_column) AS DATE, NEVER EXTRACT(MONTH)
7. Apply patterns from verified queries to similar questions
8. For year-month queries: Use YEAR(date_col), MONTH(date_col) with proper formatting
9. CRITICAL: Always close all parentheses - do NOT have unexpected closing parens

CRITICAL SQL RULES:
- Return ONLY executable SQL
- NO explanations, NO comments, NO text
- Start directly with SELECT or WITH
- Use physical column names (BUSINESSUNIT not market, SENDDATE not send_date)
- For any trend/time-series query: DATE_TRUNC('MONTH', SENDDATE) AS DATE (not EXTRACT!)
- Ensure ALL parentheses are properly closed
- Do NOT add extra closing parentheses at the end
- Do NOT have FROM ) or WHERE ) - these are invalid
- Test mentally: Does the query have balanced parentheses?

USER QUESTION: {question}

SQL CODE (ONLY SQL, nothing else):"""

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
            
            # 🔧 NEW: Validate SQL structure before executing
            if '()' in clean_sql_text or clean_sql_text.endswith(')'):
                logger.warning(f"⚠️ Potential SQL syntax issue detected, attempting fix...")
                # Remove trailing parens
                clean_sql_text = re.sub(r'\)\s*$', '', clean_sql_text)
            
            logger.info(f"📝 Generated SQL: {clean_sql_text[:150]}...")
            
            # Execute the SQL
            data = self.session.sql(clean_sql_text).collect()
            results = [dict(row.asDict()) for row in data]
            
            # Fix date columns
            results = self._fix_date_columns(results)
            
            return {
                'success': True,
                'sql': clean_sql_text,
                'results': results,
                'row_count': len(results),
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
        """Execute raw SQL directly"""
        try:
            data = self.session.sql(sql).collect()
            results = [dict(row.asDict()) for row in data]
            results = self._fix_date_columns(results)
            
            return {
                'success': True,
                'results': results,
                'row_count': len(results),
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'results': [],
                'row_count': 0,
                'error': str(e)
            }