"""Test environment variables loading"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.shared_config import SharedConfig

config = SharedConfig()

print("🔍 Checking environment variables:")
print(f"Account: {config.snowflake.get('account')}")      # ← Changed from snowflake_config
print(f"User: {config.snowflake.get('user')}")            # ← Changed from snowflake_config
print(f"Database: {config.snowflake.get('database')}")    # ← Changed from snowflake_config
print(f"Semantic Model: {config.semantic_model_stage}")

# Check if any are None
missing = [k for k, v in config.snowflake.items() if v is None]  # ← Changed from snowflake_config
if missing:
    print(f"\n❌ Missing env vars: {missing}")
    print("   Make sure .env file exists and has all required values")
else:
    print("\n✅ All environment variables loaded successfully!")

# Bonus: validate config
print("\n🔍 Validating configuration...")
if config.validate():
    print("✅ Configuration is valid!")
else:
    print("❌ Configuration validation failed")