"""Test orchestrator with monitoring enabled"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrators.conversational import ConversationalOrchestrator
import logging

logging.basicConfig(level=logging.INFO)

def test_with_monitoring():
    """Test query processing with full monitoring"""
    
    print("\n" + "="*80)
    print("🧪 TESTING ORCHESTRATOR WITH MONITORING")
    print("="*80 + "\n")
    
    # Initialize with monitoring
    orchestrator = ConversationalOrchestrator(enable_monitoring=True)
    
    # Test queries
    queries = [
        "What are the total email sends?",
        "Show me open rates by market",
        "What is the conversion rate for VCUS?"
    ]
    
    for query in queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print('='*80)
        
        result = orchestrator.process_query(
            query,
            with_viz=True,
            with_benchmarks=True,
            with_insights=True
        )
        
        if result['success']:
            print(f"✅ SUCCESS")
            print(f"   Rows: {len(result['data'])}")
            print(f"   Has Viz: {'visualization' in result}")
            print(f"   Has Benchmarks: {'benchmarks' in result}")
            print(f"   Has Insights: {'insights' in result}")
        else:
            print(f"❌ FAILED: {result.get('error')}")
    
    # Get performance report
    print(f"\n{'='*80}")
    print("📊 PERFORMANCE REPORT")
    print('='*80)
    
    report = orchestrator.get_performance_report()
    
    print("\n🤖 AI Agents:")
    for agent, stats in report.get('ai_agents', {}).items():
        print(f"   {agent}:")
        print(f"      Calls: {stats.get('total_calls', 0)}")
        print(f"      Success Rate: {stats.get('success_rate', 0):.1f}%")
        print(f"      Avg Time: {stats.get('avg_execution_time', 0):.2f}s")
    
    print("\n⚙️ Internal Agents:")
    for agent, stats in report.get('internal_agents', {}).items():
        print(f"   {agent}:")
        print(f"      Executions: {stats.get('total_calls', 0)}")
        print(f"      Success Rate: {stats.get('success_rate', 0):.1f}%")
        print(f"      Avg Time: {stats.get('avg_execution_time', 0):.3f}s")
    
    print("\n📊 System Overview:")
    sys_stats = report.get('orchestrator', {})
    print(f"   Total Queries: {sys_stats.get('total_queries', 0)}")
    print(f"   Avg Query Time: {sys_stats.get('avg_query_time', 0):.2f}s")
    print(f"   Success Rate: {sys_stats.get('success_rate', 0):.1f}%")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    test_with_monitoring()