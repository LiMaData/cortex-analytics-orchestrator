"""
Quick test to check if Snowflake Cortex evaluation is available
Run this to see if you CAN enable Cortex evaluation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔍 Testing Cortex Evaluation Availability...")
print("=" * 60)

# Test 1: Check if cortex_evaluator.py exists
print("\n1️⃣ Checking if cortex_evaluator.py exists...")
cortex_file = project_root / "monitoring" / "cortex_evaluator.py"
if cortex_file.exists():
    print("   ✅ cortex_evaluator.py found!")
else:
    print("   ❌ cortex_evaluator.py NOT found!")
    print("   📍 Expected location:", cortex_file)
    print("   ⚠️ Cannot enable Cortex without this file")

# Test 2: Try importing CortexEvaluator
print("\n2️⃣ Trying to import CortexEvaluator...")
try:
    from monitoring.cortex_evaluator import CortexEvaluator
    print("   ✅ CortexEvaluator imported successfully!")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")
    print("   ⚠️ Cannot enable Cortex")

# Test 3: Check Snowflake connection
print("\n3️⃣ Checking Snowflake connection...")
try:
    from snowflake.snowpark import Session
    from config.snowflake_config import get_snowflake_connection
    
    session = get_snowflake_connection()
    print("   ✅ Snowflake connection successful!")
    
    # Test 4: Check if Cortex functions are available
    print("\n4️⃣ Testing Cortex function availability...")
    try:
        # Try a simple Cortex complete call
        test_query = "SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', 'test') as result"
        result = session.sql(test_query).collect()
        print("   ✅ Cortex functions available!")
        print("   🎉 Cortex evaluation CAN be enabled!")
        
    except Exception as e:
        print(f"   ❌ Cortex functions not available: {e}")
        print("   ⚠️ Your Snowflake account may not have Cortex enabled")
        
except Exception as e:
    print(f"   ❌ Snowflake connection failed: {e}")
    print("   ⚠️ Check your Snowflake credentials")

# Test 5: Try initializing CortexEvaluator
print("\n5️⃣ Trying to initialize CortexEvaluator...")
try:
    from monitoring.cortex_evaluator import CortexEvaluator
    from config.snowflake_config import get_snowflake_connection
    
    session = get_snowflake_connection()
    evaluator = CortexEvaluator(session)
    print("   ✅ CortexEvaluator initialized successfully!")
    print("   🎊 You're ready to enable Cortex evaluation!")
    
except Exception as e:
    print(f"   ❌ Failed to initialize: {e}")
    print("   ⚠️ Cannot enable Cortex yet")

print("\n" + "=" * 60)
print("🏁 Test Complete!")
print("\nSUMMARY:")
print("--------")
if cortex_file.exists():
    print("✅ Cortex evaluator file exists")
    print("📝 To enable Cortex evaluation:")
    print("   1. Edit streamlit_app.py line 66")
    print("   2. Change to: orchestrator = ConversationalOrchestrator(")
    print("                     enable_monitoring=True,")
    print("                     use_cortex_eval=True  # ← Add this!")
    print("                 )")
    print("   3. Restart app")
else:
    print("❌ Cortex evaluator not available")
    print("💡 You can continue using Fallback Mode (basic monitoring)")
    print("   This is perfectly fine for most use cases!")