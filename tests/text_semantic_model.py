from snowflake.snowpark import Session
from tools.cortex_analyst import CortexAnalystTool

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

# Initialize Cortex Analyst Tool
cortex = CortexAnalystTool(
    session=session,
    semantic_model_stage="@semantic_models/marketing_semantic_model.yaml"
)

print("📋 First 1000 chars of loaded semantic model:")
print(cortex.semantic_model[:1000])
print("\n" + "="*80 + "\n")

# Test the problematic query
print("🧪 TESTING: What were the sends by market last month?\n")

result = cortex.query("What were the sends by market last month?")

print(f"Success: {result['success']}")
print(f"\n📝 Generated SQL:\n{result['sql']}\n")

if result['success']:
    print(f"✅ Query worked! Returned {result['row_count']} rows")
    print(f"\nSample data:")
    for row in result['results'][:3]:
        print(f"  {row}")
else:
    print(f"❌ Error: {result['error']}")
    print("\n🔍 Check if SQL uses BUSINESSUNIT (correct) or market (wrong)")

session.close()