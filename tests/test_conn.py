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
        # Allow database/schema to be set via environment variables so tests work across environments
        db = os.getenv('SNOWFLAKE_DATABASE', 'CAMPAIGN_ANALYTICS')
        schema = os.getenv('SNOWFLAKE_SCHEMA', 'GENERATED_DATA')

        session = Session.builder.configs({
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
            "role": os.getenv("SNOWFLAKE_ROLE"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "database": db,
            "schema": schema
        }).create()
        logger.info("Session created")
        logger.info(f"Current DB: {session.get_current_database()}, Schema: {session.get_current_schema()}")

        # Ensure session has an explicit current database/schema in case the connection does not set it
        try:
            session.sql(f'USE DATABASE "{db}"').collect()
            session.sql(f'USE SCHEMA "{db}"."{schema}"').collect()
            logger.info(f"Set current database/schema to: {db}/{schema}")
        except Exception as e:
            logger.warning(f"Could not explicitly set database/schema: {e}")

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
            # r may be a PutResult object; try attribute access first, then dict-like fallback
            try:
                status = getattr(r, 'status', None)
                source = getattr(r, 'source', None)
                target = getattr(r, 'target', None)
            except Exception:
                status = None
                source = None
                target = None

            # dict-like fallback
            if status is None:
                try:
                    status = r.get('status')
                    source = r.get('source', '')
                    target = r.get('target', '')
                except Exception:
                    # last resort: stringify the result
                    status = str(r)
                    source = ''
                    target = ''

            logger.info(f"PUT: {status} {source} -> {target}")

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