"""Test BenchmarkAgent with all three sources"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.benchmark_agent import BenchmarkAgent
from tools.cortex_analyst import CortexAnalystTool
from snowflake.snowpark import Session
from config.shared_config import SharedConfig
import logging

logging.basicConfig(level=logging.INFO)

def test_benchmark_sources():
    """Test all three benchmark sources"""
    
    print("\n" + "="*80)
    print("TESTING BENCHMARK AGENT - HYBRID SOURCES")
    print("="*80)
    
    # Setup
    config = SharedConfig()
    session = Session.builder.configs(config.snowflake).create()
    
    from tools.cortex_analyst import CortexAnalystTool
    cortex_tool = CortexAnalystTool(session, config.semantic_model_stage)
    
    # Initialize agent
    agent = BenchmarkAgent(cortex_tool, use_database=True, use_llm_fallback=True)
    
    # Test queries
    test_cases = [
        "What is the industry open rate benchmark?",
        "Show me click rate standards",
        "What's a good conversion rate?",
    ]
    
    for query in test_cases:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print('='*80)
        
        result = agent.process(query)
        
        print(f"\n✅ Source: {result['source_description']}")
        print(f"📊 Metric: {result['metric']}")
        print(f"\n{result['context']}")
        
        # Test comparison
        test_value = 18.5
        comparison = agent.compare_performance(
            test_value, 
            result['metric'],
            result['benchmarks']
        )
        
        print(f"\n🔍 Performance Analysis (for {test_value}%):")
        print(f"   Level: {comparison['performance_level']}")
        print(f"   Description: {comparison['description']}")
        print(f"   Gap from average: {comparison['gap']:+.1f}% ({comparison['gap_percentage']:+.1f}%)")
    
    # Show agent status
    status = agent.get_status()
    print(f"\n{'='*80}")
    print("AGENT STATUS")
    print('='*80)
    print(f"Capabilities: {', '.join(status['capabilities'])}")
    print(f"Available Metrics: {', '.join(status['available_metrics'])}")
    
    session.close()
    print("\n✅ All tests complete!")

if __name__ == "__main__":
    test_benchmark_sources()