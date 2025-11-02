import os
from pathlib import Path
from dotenv import load_dotenv
from snowflake.snowpark import Session

load_dotenv()

connection_parameters = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE", "CAMPAIGN_ANALYTICS"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA", "GENERATED_DATA")
}

print("Connecting to Snowflake using environment variables...")
session = Session.builder.configs(connection_parameters).create()
print("✅ Connected to Snowflake\n")

# Determine local semantic model path (prefer config/, fallback to tools/)
local_candidates = [Path("config") / "marketing_semantic_model.yaml"]
local_path = None
for p in local_candidates:
    if p.exists():
        local_path = p
        break

if local_path is None:
    raise FileNotFoundError("Could not find marketing_semantic_model.yaml in config/, tools/ or repo root")

local_path = local_path.resolve()
print(f"📤 Uploading {local_path} -> @semantic_models (overwrite=True)")

# Force overwrite to ensure latest file is uploaded
put_results = session.file.put(f"file://{local_path}", "@semantic_models", auto_compress=False, overwrite=True)
for r in put_results:
    # r may be a PutResult object; print a safe representation
    try:
        status = getattr(r, 'status', None)
        source = getattr(r, 'source', None)
        target = getattr(r, 'target', None)
    except Exception:
        status = None
        source = None
        target = None

    if status is None:
        # fallback to str
        print("PUT:", str(r))
    else:
        print(f"PUT: {status} {source} -> {target}")

print("\n📋 Files in stage:")
result = session.sql("LIST @semantic_models/").collect()
for row in result:
    print(f"  {row['name']} - {row['size']} bytes")

session.close()
print("\n✅ Done!")