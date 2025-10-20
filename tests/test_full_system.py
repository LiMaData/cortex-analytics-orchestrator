"""Comprehensive system test"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrators.conversational import ConversationalOrchestrator
import logging

logging.basicConfig(level=logging.INFO)

def test_full_workflow():
    """Test complete workflow: query → data → viz → insights"""
    
    orchestrator = ConversationalOrchestrator()
    
    print("\n" + "="*80)
    print("FULL SYSTEM TEST")
    print("="*80)
    
    # Test 1: Simple query
    print("\n🧪 TEST 1: Simple Aggregation")
    result = orchestrator.process_query("What was the total number of emails sent?")
    assert result['success'], "Simple query failed"
    assert len(result['data']) == 1, "Should return 1 row"
    print("✅ PASS")
    
    # Test 2: Query with visualization
    print("\n🧪 TEST 2: Query with Visualization")
    result = orchestrator.process_query("Show me open rates by market", with_viz=True)
    assert result['success'], "Viz query failed"
    assert 'visualization' in result, "Should have visualization"
    print("✅ PASS")
    
    # Test 3: Error handling
    print("\n🧪 TEST 3: Invalid Query Handling")
    result = orchestrator.process_query("Show me data from nonexistent_table")
    assert not result['success'], "Should fail for invalid query"
    assert 'error' in result, "Should have error message"
    print("✅ PASS")
    
    print("\n" + "="*80)
    print("ALL TESTS PASSED! ✅")
    print("="*80)

if __name__ == "__main__":
    test_full_workflow()