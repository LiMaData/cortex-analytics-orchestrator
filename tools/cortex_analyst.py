import re
import logging
from snowflake.snowpark import Session

logger = logging.getLogger(__name__)

class CortexAnalyst:
    """Cortex Analyst using SNOWFLAKE.CORTEX.COMPLETE"""

    def __init__(self, session: Session, semantic_model_stage: str):
        self.session = session
        self.semantic_model = self._load_semantic_model(semantic_model_stage)
        self.schema_context = self.semantic_model[:2500]  # Limit prompt size
        logger.info(f"✅ Loaded semantic model ({len(self.semantic_model)} chars)")

    def _load_semantic_model(self, stage_path: str) -> str:
        """Load semantic model YAML from Snowflake stage"""
        self.session.sql("""
            CREATE FILE FORMAT IF NOT EXISTS yaml_format
            TYPE = 'CSV'
            FIELD_DELIMITER = NONE
            RECORD_DELIMITER = NONE
        """).collect()

        result = self.session.sql(f"""
            SELECT t.$1 AS content
            FROM {stage_path} (FILE_FORMAT => yaml_format) t
        """).collect()

        return "\n".join([row['CONTENT'] for row in result])

    def _clean_sql(self, text: str) -> str:
        """Remove markdown and formatting from SQL"""
        text = re.sub(r'```sql\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        return text.strip().rstrip(';').strip()

    def ask(self, question: str) -> dict:
        """Generate and execute SQL for a natural language question"""
        prompt = f"""Based on this database schema:

    {self.schema_context}

    Generate a SQL query to answer: {question}

    Return ONLY the raw SQL query. No markdown, no explanations."""

        result = self.session.sql(f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large',
                '{prompt.replace("'", "''")}'
            ) AS sql_text
        """).collect()

        raw_sql = result[0]['SQL_TEXT']
        clean_sql = self._clean_sql(raw_sql)

        try:
            data = self.session.sql(clean_sql).collect()
            return {
                'success': True,
                'sql': clean_sql,
                'results': [dict(row.asDict()) for row in data],
                'row_count': len(data)
            }
        except Exception as e:
            return {
                'success': False,
                'sql': clean_sql,
                'error': str(e)
            }