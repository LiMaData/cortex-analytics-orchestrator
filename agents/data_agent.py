import logging
import os
from dotenv import load_dotenv
from snowflake.snowpark import Session
from tools.cortex_analyst import CortexAnalyst

logger = logging.getLogger(__name__)
load_dotenv()

class DataAgent:
    """
    Agent that uses CortexAnalyst to run NL → SQL → Data
    """
    def __init__(self, semantic_model_stage: str = None):
        self.session = self._create_session()
        self._log_connection_info()
        self._list_stages()
        self._check_semantic_models_stage()
        # Allow semantic_model_stage to be set via argument, env var, or default
        self.semantic_model_stage = (
            semantic_model_stage or
            os.getenv("SEMANTIC_MODEL_STAGE") or
            "@semantic_models/marketing_semantic_model.yaml"
        )
        self.analyst = self._load_analyst()

    def _create_session(self):
        connection_parameters = {
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
            "role": os.getenv("SNOWFLAKE_ROLE"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "database": "CAMPAIGN_ANALYTICS",
            "schema": "GENERATED_DATA"
        }
        session = Session.builder.configs(connection_parameters).create()
        logger.info("✅ Connected to Snowflake")
        return session

    def _log_connection_info(self):
        current_db = self.session.sql("SELECT CURRENT_DATABASE()").collect()[0][0]
        current_schema = self.session.sql("SELECT CURRENT_SCHEMA()").collect()[0][0]
        logger.info(f"✅ Connected to DB: {current_db}, Schema: {current_schema}")

    def _list_stages(self):
        logger.info("📂 Listing stages in current schema...")
        stages = self.session.sql("SHOW STAGES").collect()
        for stage in stages:
            logger.info(f"Stage found: {stage['name']}")

    def _check_semantic_models_stage(self):
        logger.info("📂 Checking if @semantic_models exists...")
        self.session.sql("LIST @semantic_models").show()

    def _load_analyst(self):
        return CortexAnalyst(
            session=self.session,
            semantic_model_stage=self.semantic_model_stage
        )

    def process(self, query: str) -> dict:
        """Process a natural language query and return results"""
        logger.info(f"❓ DataAgent received query: {query}")

        try:
            result = self.analyst.ask(query)
            if result.get('success'):
                return {
                    'success': True,
                    'sql': result.get('sql'),
                    'results': result.get('results', []),
                    'row_count': result.get('row_count', 0)
                }
            else:
                logger.error(f"DataAgent returned failure: {result.get('error')}")
                return {
                    'success': False,
                    'sql': result.get('sql'),
                    'results': [],
                    'row_count': 0,
                    'error': result.get('error')
                }
        except Exception as e:
            logger.error(f"❌ Error processing query: {e}", exc_info=True)
            return {
                'success': False,
                'sql': None,
                'results': [],
                'row_count': 0,
                'error': str(e)
            }
