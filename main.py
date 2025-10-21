"""
Cortex Analytics Orchestrator - Main Entry Point
Interactive conversational mode for analytics queries
"""

import logging
from orchestrators.conversational import ConversationalOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def print_header():
    """Print application header"""
    print("\n" + "="*80)
    print("🚀 CORTEX ANALYTICS ORCHESTRATOR")
    print("   Multi-Agent Analytics with Benchmark Comparison")
    print("="*80 + "\n")

def print_status(status):
    """Print orchestrator status"""
    print("✅ System Status:")
    print(f"   Mode: {status.get('mode', 'N/A')}")
    print(f"   Agents: {', '.join(status.get('agents_loaded', []))}")
    print(f"   Config: {'Valid' if status.get('config_valid') else 'Invalid'}")

def print_commands():
    """Print available commands"""
    print("\n💬 Commands:")
    print("   • Type your analytics question")
    print("   • Add 'show me' or 'chart' to include visualization")
    print("   • Type 'help' for examples")
    print("   • Type 'exit' to quit")
    print()

def print_examples():
    """Print example queries"""
    print("\n📚 Example Queries:")
    print("   • What are the total email sends?")
    print("   • Show me open rates by market")
    print("   • What is the conversion rate for VCUS?")
    print("   • Compare click rates across all markets")
    print("   • Chart sends by country")
    print()

def print_data_summary(data):
    """Print formatted data summary"""
    if not data:
        return
    
    print("\n📊 DATA PREVIEW:")
    
    # Show up to 5 rows in a formatted way
    for i, row in enumerate(data[:5], 1):
        # Format row nicely
        formatted_row = []
        for key, value in row.items():
            if isinstance(value, float):
                formatted_row.append(f"{key}={value:,.2f}")
            elif isinstance(value, int):
                formatted_row.append(f"{key}={value:,}")
            else:
                formatted_row.append(f"{key}={value}")
        
        print(f"   [{i}] {', '.join(formatted_row)}")
    
    if len(data) > 5:
        print(f"   ... and {len(data) - 5} more rows")

def print_benchmarks(benchmark_data):
    """Print formatted benchmark information"""
    if not benchmark_data or not benchmark_data.get('success'):
        return
    
    benchmarks = benchmark_data.get('benchmarks', {})
    metric = benchmark_data.get('metric', 'metric').replace('_', ' ').title()
    source = benchmark_data.get('source_description', 'Industry Standards')
    
    print("\n" + "─"*80)
    print("📊 INDUSTRY BENCHMARKS")
    print("─"*80)
    
    print(f"   Metric: {metric}")
    print(f"   Source: {source}")
    
    if 'updated_date' in benchmarks:
        print(f"   Updated: {benchmarks['updated_date']} ({benchmarks.get('age_days', 0)} days ago)")
    
    print(f"\n   Benchmark Values:")
    
    # Format benchmark values
    unit = '%' if benchmarks.get('unit') == 'percentage' else ''
    
    avg = benchmarks.get('industry_average', 0)
    top = benchmarks.get('top_quartile', 0)
    bottom = benchmarks.get('bottom_quartile', 0)
    excellent = benchmarks.get('excellent_threshold', top)
    
    print(f"   • Industry Average:     {avg:6.2f}{unit}")
    print(f"   • Top Quartile:         {top:6.2f}{unit}  (best 25%)")
    print(f"   • Bottom Quartile:      {bottom:6.2f}{unit}  (lowest 25%)")
    print(f"   • Excellence Threshold: {excellent:6.2f}{unit}")
    
    # Show industry-specific if available
    if 'industry_specific' in benchmarks:
        print(f"\n   {benchmarks.get('industry_name', 'Industry')}-Specific: {benchmarks['industry_specific']:.2f}{unit}")
    
    print("─"*80)

def print_insights(insights_text):
    """Print formatted insights"""
    if not insights_text:
        return
    
    print("\n" + "─"*80)
    print("💡 AI-GENERATED INSIGHTS")
    print("─"*80)
    
    # Add some visual structure to insights
    lines = insights_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            print()
            continue
        
        # Add colored bullets for key sections
        if line.startswith('📊') or line.startswith('🔍') or line.startswith('💡'):
            print(f"\n{line}")
        elif line.startswith('•'):
            print(f"   {line}")
        else:
            print(f"   {line}")
    
    print("\n" + "─"*80)

def print_error(error_msg, sql=None):
    """Print formatted error message"""
    print("\n" + "="*80)
    print("❌ ERROR")
    print("="*80)
    print(f"   {error_msg}")
    
    if sql:
        print(f"\n   Generated SQL:")
        print(f"   {sql[:200]}...")
    
    print("="*80)

def main():
    """Main interactive loop"""
    
    try:
        # Print header
        print_header()
        
        # Initialize orchestrator
        print("⏳ Initializing orchestrator...")
        orchestrator = ConversationalOrchestrator()
        
        # Print status
        status = orchestrator.get_status()
        print_status(status)
        
        # Print commands
        print_commands()
        
        # Main loop
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                # Handle empty input
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Thank you for using Cortex Analytics Orchestrator!\n")
                    break
                
                if user_input.lower() == 'help':
                    print_examples()
                    continue
                
                # Detect visualization request
                viz_keywords = ['viz', 'chart', 'graph', 'visualize', 'show me', 'plot']
                with_viz = any(kw in user_input.lower() for kw in viz_keywords)
                
                # Process query
                print("\n⏳ Processing query...")
                response = orchestrator.process_query(
                    user_input, 
                    with_viz=with_viz,
                    with_benchmarks=True,
                    with_insights=True
                )
                
                # Display results
                if response.get('success'):
                    # Header
                    print("\n" + "="*80)
                    print("✅ QUERY RESULTS")
                    print("="*80)
                    
                    # Metadata
                    print(f"\n📈 Query Summary:")
                    print(f"   Rows returned: {len(response.get('data', []))}")
                    print(f"   SQL: {response.get('sql', 'N/A')[:80]}...")
                    
                    # Data preview
                    print_data_summary(response.get('data', []))
                    
                    # Benchmarks
                    if 'benchmarks' in response:
                        print_benchmarks(response['benchmarks'])
                    
                    # Insights
                    if 'insights' in response:
                        print_insights(response['insights'])
                    
                    # Visualization
                    if 'visualization' in response:
                        print("\n📊 Opening visualization in browser...")
                        response['visualization'].show()
                        print("✅ Visualization displayed")
                    
                    print("\n" + "="*80 + "\n")
                    
                else:
                    # Error handling
                    print_error(
                        response.get('error', 'Unknown error'),
                        response.get('sql')
                    )
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!\n")
                break
                
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                print(f"\n❌ Unexpected error: {e}")
                print("   Please try again or type 'exit' to quit.\n")
                
                # Debug mode - show traceback
                import traceback
                if logger.level == logging.DEBUG:
                    traceback.print_exc()
    
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        print(f"\n❌ Failed to start: {e}")
        print("   Please check your configuration and try again.\n")
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()