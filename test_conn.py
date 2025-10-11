from snowflake.snowpark import Session
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

connection_parameters = {
"account": os.getenv("SNOWFLAKE_ACCOUNT"),
"user": os.getenv("SNOWFLAKE_USER"),
"password": os.getenv("SNOWFLAKE_PASSWORD"),
"role": os.getenv("SNOWFLAKE_ROLE"),
"warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
"database": os.getenv("SNOWFLAKE_DATABASE"),
"schema": os.getenv("SNOWFLAKE_SCHEMA")
}

print("🔍 SNOWFLAKE_ACCOUNT =", connection_parameters["account"])

# Try connecting
session = Session.builder.configs(connection_parameters).create()
print("✅ Connected to Snowflake!")

session.close()