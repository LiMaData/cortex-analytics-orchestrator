from snowflake.snowpark import Session
from dotenv import load_dotenv
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

def main():
    session = None
    # quick env checks
    logger.info(f"Account={os.getenv('SNOWFLAKE_ACCOUNT')!r}, User={os.getenv('SNOWFLAKE_USER')!r}, Warehouse={os.getenv('SNOWFLAKE_WAREHOUSE')!r}")
    try:
        session = Session.builder.configs({
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
            "role": os.getenv("SNOWFLAKE_ROLE"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "database": "CAMPAIGN_ANALYTICS",
            "schema": "GENERATED_DATA"
        }).create()
        logger.info("Session created")
        logger.info(f"Current DB: {session.get_current_database()}, Schema: {session.get_current_schema()}")

        local_path = os.path.abspath("config/marketing_semantic_model.yaml")
        if not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            return

        # ensure stage exists (create if needed)
        try:
            session.sql("CREATE STAGE IF NOT EXISTS semantic_models").collect()
            logger.info("Ensured stage @semantic_models exists")
        except Exception as e:
            logger.warning(f"Could not ensure stage: {e}")

        logger.info(f"Uploading {local_path} -> @semantic_models")
        put_results = session.file.put(f"file://{local_path}", "@semantic_models", auto_compress=False)
        for r in put_results:
            # r is typically a dict-like object with status/source/target
            logger.info(f"PUT: {r.get('status')} {r.get('source', '')} -> {r.get('target', '')}")

    except Exception:
        logger.exception("Error during connection/upload")
        sys.exit(2)
    finally:
        if session is not None:
            try:
                session.close()
                logger.info("Session closed")
            except Exception:
                pass

if __name__ == "__main__":
    main()