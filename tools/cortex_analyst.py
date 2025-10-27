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
        🔧 ENHANCED: Clean SQL with parentheses balancing and GROUP BY validation
        Fixes: Missing closing parens, incomplete clauses, EOF errors
        """
        import re
        
        # Remove markdown
        text = re.sub(r'```sql\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        if not text:
            raise ValueError("LLM returned empty response")
        
        # Remove explanatory text before SQL
        explanation_words = ['to answer', 'this query', 'here is', 'the following', 
                            'we need', 'first', 'let me', 'i will', 'i would']
        
        first_line_lower = text.split('\n')[0].lower()
        if any(word in first_line_lower for word in explanation_words):
            match = re.search(r'((?:WITH|SELECT).*?)(?:;|\Z)', text, re.IGNORECASE | re.DOTALL)
            if match:
                text = match.group(1)
            else:
                raise ValueError(f"LLM added explanation, couldn't extract SQL: {text[:100]}")
        
        # Extract SQL if mixed with other content
        if 'SELECT' in text.upper():
            match = re.search(r'((?:WITH\s+.*?\s+)?SELECT.*?)(?:;|\Z)', text, re.IGNORECASE | re.DOTALL)
            if match:
                text = match.group(1)
        
        # Clean up
        text = text.rstrip(';').strip()
        
        # Remove lines that are ONLY closing parentheses
        lines = [line for line in text.split('\n') 
                if line.strip() and not re.match(r'^\)+$', line.strip())]
        text = '\n'.join(lines)
        
        # ✅ NEW: Detect incomplete function calls at end of lines
        # This catches: GROUP BY DATE_TRUNC('MONTH', SENDDATE  <- missing )
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Check if line has unclosed function call
            if re.search(r'\w+\([^)]*$', line.strip()):
                # Count parens in this line
                open_parens = line.count('(')
                close_parens = line.count(')')
                if open_parens > close_parens:
                    logger.warning(f"⚠️ Line {i+1} has unclosed parentheses: {line.strip()}")
                    # Add missing closing parens
                    missing = open_parens - close_parens
                    lines[i] = line + ')' * missing
                    logger.info(f"✅ Fixed by adding {missing} closing paren(s)")
        
        text = '\n'.join(lines)
        
        # ✅ ENHANCED: Balance ALL parentheses in the entire query
        open_parens = text.count('(')
        close_parens = text.count(')')
        
        if close_parens > open_parens:
            # Too many closing parens - remove excess from end
            excess = close_parens - open_parens
            logger.warning(f"⚠️ Removing {excess} excess closing parentheses")
            for _ in range(excess):
                pos = text.rfind(')')
                if pos != -1:
                    text = text[:pos] + text[pos + 1:]
        
        elif open_parens > close_parens:
            # Too many opening parens - add missing closing parens
            missing = open_parens - close_parens
            logger.warning(f"⚠️ Adding {missing} missing closing parentheses")
            text = text + ')' * missing
        
        # Remove empty clauses
        text = re.sub(r'\bFROM\s*\)', 'FROM', text, flags=re.IGNORECASE)
        text = re.sub(r'\bWHERE\s*\)', 'WHERE', text, flags=re.IGNORECASE)
        
        # Remove trailing closing parens that create syntax errors
        text = re.sub(r'\)\s*$', '', text)
        
        # Re-balance after cleanup (sometimes removing trailing ) creates imbalance)
        open_parens = text.count('(')
        close_parens = text.count(')')
        if open_parens > close_parens:
            missing = open_parens - close_parens
            text = text + ')' * missing
            logger.info(f"✅ Re-balanced: added {missing} closing paren(s)")
        
        text = text.strip()
        
        # Validate: Must start with SELECT or WITH
        if not text.upper().startswith(('SELECT', 'WITH')):
            raise ValueError(f"SQL must start with SELECT or WITH: {text[:100]}")
        
        # ✅ ENHANCED: Detect specific incomplete patterns
        incomplete_patterns = [
            (r'GROUP\s+BY\s+\w+\([^)]*$', 'GROUP BY with unclosed function'),
            (r'ORDER\s+BY\s+\w+\([^)]*$', 'ORDER BY with unclosed function'),
            (r'FROM\s*$', 'FROM without table'),
            (r'WHERE\s*$', 'WHERE without condition'),
            (r'JOIN\s*$', 'JOIN without table'),
            (r'ON\s*$', 'ON without condition'),
        ]
        
        for pattern, error_msg in incomplete_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValueError(f"Incomplete SQL - {error_msg}: ...{text[-100:]}")
        
        # ✅ NEW: Specific validation for GROUP BY and ORDER BY clauses
        # Check if GROUP BY or ORDER BY exists but looks incomplete
        group_by_match = re.search(r'GROUP\s+BY\s+(.+?)(?:ORDER|LIMIT|$)', text, re.IGNORECASE | re.DOTALL)
        if group_by_match:
            group_clause = group_by_match.group(1).strip()
            # Check if parentheses are balanced in GROUP BY
            if group_clause.count('(') != group_clause.count(')'):
                raise ValueError(f"Unbalanced parentheses in GROUP BY clause: {group_clause}")
        
        order_by_match = re.search(r'ORDER\s+BY\s+(.+?)(?:LIMIT|$)', text, re.IGNORECASE | re.DOTALL)
        if order_by_match:
            order_clause = order_by_match.group(1).strip()
            # Check if parentheses are balanced in ORDER BY
            if order_clause.count('(') != order_clause.count(')'):
                raise ValueError(f"Unbalanced parentheses in ORDER BY clause: {order_clause}")
        
        logger.info(f"✅ SQL validated and balanced: {len(text)} chars, {text.count('(')} parens")
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
            # ✅ ENHANCED PROMPT: Emphasizes parentheses and completeness
            prompt = f"""You are a SQL code generator. Return ONLY complete, executable SQL.

    {self.schema_context}

    🚨 CRITICAL RULES:
    1. Return ONLY SQL code - NO explanations, NO comments, NO text
    2. SQL MUST be 100% COMPLETE - every clause must be finished
    3. Start with SELECT or WITH - nothing else
    4. CLOSE ALL PARENTHESES - count them before returning!
    5. GROUP BY and ORDER BY must have complete function calls
    6. For time-series: DATE_TRUNC('MONTH', date_column) AS month
    7. Double-check: Every opening ( has a matching closing )

    ❌ INVALID (causes EOF error):
    GROUP BY DATE_TRUNC('MONTH', SENDDATE     ← Missing )
    ORDER BY DATE_TRUNC('MONTH', date         ← Missing )

    ✅ VALID:
    GROUP BY DATE_TRUNC('MONTH', SENDDATE)    ← Complete!
    ORDER BY DATE_TRUNC('MONTH', date)        ← Complete!

    PARENTHESES CHECK:
    - SUM(OPENS) ✅ balanced: 1 open, 1 close
    - DATE_TRUNC('MONTH', date) ✅ balanced: 1 open, 1 close
    - DATE_TRUNC('MONTH', date ❌ INVALID: 1 open, 0 close

    USER QUESTION: {question}

    Generate ONLY complete SQL with all parentheses closed:"""

            # Generate SQL
            result = self.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'mistral-large',
                    '{prompt.replace("'", "''")}'
                ) AS sql_text
            """).collect()
            
            raw_sql = result[0]['SQL_TEXT']
            logger.info(f"🔍 Raw LLM output ({len(raw_sql)} chars): {raw_sql[:200]}...")
            
            # Clean and validate the SQL
            clean_sql_text = self._clean_sql(raw_sql)
            
            # Final validation
            if not clean_sql_text.strip().upper().startswith(('SELECT', 'WITH')):
                raise ValueError(f"Invalid SQL (doesn't start with SELECT/WITH): {clean_sql_text[:100]}")
            
            # Check parentheses are balanced
            if clean_sql_text.count('(') != clean_sql_text.count(')'):
                raise ValueError(
                    f"Unbalanced parentheses: "
                    f"{clean_sql_text.count('(')} open, {clean_sql_text.count(')')} close"
                )
            
            logger.info(f"✅ Validated SQL ({len(clean_sql_text)} chars): {clean_sql_text[:150]}...")
            
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
            error_msg = str(e)
            logger.error(f"❌ Query failed: {error_msg}")
            
            # Provide helpful error message
            if 'unexpected <EOF>' in error_msg or 'syntax error' in error_msg:
                logger.error(f"💡 SQL appears incomplete. Raw SQL was: {clean_sql_text}")
            
            return {
                'success': False,
                'sql': clean_sql_text,
                'results': [],
                'row_count': 0,
                'error': error_msg
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