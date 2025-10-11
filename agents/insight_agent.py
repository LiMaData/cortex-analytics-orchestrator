import logging

logger = logging.getLogger(__name__)

class InsightAgent:
    """Generates textual insights using CORTEX.COMPLETE"""

    def __init__(self, session):
        self.session = session
        logger.info("✅ InsightAgent initialized")

    def process(self, data: list[dict]):
        """Generate insights from data"""
        if not data:
            return "No data to analyze."

        prompt = f"Analyze the following data and provide key insights:\n{data}"

        result = self.session.sql(f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large',
                '{prompt.replace("'", "''")}'
            ) AS insight
        """).collect()

        return result[0]['INSIGHT']