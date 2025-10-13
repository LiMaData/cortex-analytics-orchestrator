from snowflake.snowpark import Session

connection_parameters = {
    "account": "wkswaox-lt08934",
    "user": "Lima717",
    "password": "Easy2snowflake!",
    "role": "ACCOUNTADMIN",
    "warehouse": "COMPUTE_WH",
    "database": "CAMPAIGN_ANALYTICS",
    "schema": "GENERATED_DATA"
}

session = Session.builder.configs(connection_parameters).create()
print("✅ Connected to Snowflake\n")

# Upload the semantic model
print("📤 Uploading semantic model...")
session.file.put(
    local_file_name="marketing_semantic_model.yaml",  # File in current directory
    stage_location="@semantic_models/",
    auto_compress=False,
    overwrite=True
)

print("✅ Upload complete!\n")

# Verify it's there
print("📋 Files in stage:")
result = session.sql("LIST @semantic_models/").collect()
for row in result:
    print(f"  {row['name']} - {row['size']} bytes")

# Preview first 10 lines
print("\n📄 File preview (first 10 lines):")
session.sql("""
    CREATE FILE FORMAT IF NOT EXISTS yaml_format
    TYPE = 'CSV'
    FIELD_DELIMITER = NONE
    RECORD_DELIMITER = NONE
""").collect()

preview = session.sql("""
    SELECT $1 AS line
    FROM @semantic_models/marketing_semantic_model.yaml 
    (FILE_FORMAT => yaml_format)
    LIMIT 10
""").collect()

for row in preview:
    print(row['LINE'])

session.close()
print("\n✅ Done!")