"""Test different query patterns"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrators.conversational import ConversationalOrchestrator

def test_patterns():
    orchestrator = ConversationalOrchestrator()
    
    test_cases = [
        # Aggregations
        "What was the total number of emails sent?",
        "How many emails were delivered?",
        
        # Group by
        "Show me email open rates by market",
        "What are the sends by market?",
        
        # Filtering
        "What is the open rate for VCUS?",
        "Show me conversion rate for VCUK",
        
        # Time-based
        "What were sends last month?",
        "Show me open rates this week",
        
        # Complex
        "Which market has the highest click rate?",
        "Compare open rates across all markets",
    ]
    
    print("\n" + "="*80)
    print("TESTING DIFFERENT QUERY PATTERNS")
    print("="*80 + "\n")
    
    passed = 0
    failed = 0
    
    for query in test_cases:
        print(f"\n❓ {query}")
        result = orchestrator.process_query(query)
        
        if result['success']:
            print(f"✅ PASS - {len(result['data'])} rows")
            print(f"   SQL: {result['sql'][:80]}...")
            passed += 1
        else:
            print(f"❌ FAIL - {result.get('error', 'Unknown')}")
            failed += 1
    
    print(f"\n{'='*80}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)

if __name__ == "__main__":
    test_patterns()