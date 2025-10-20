"""
Main entry point for Cortex Analytics Orchestrator
"""

import logging
from orchestrators.conversational import ConversationalOrchestrator

# Configure logging
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main interactive loop"""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    
    print("\n" + "="*80)
    print("🚀 CORTEX ANALYTICS ORCHESTRATOR")
    print("="*80 + "\n")
    
    orchestrator = ConversationalOrchestrator()
    status = orchestrator.get_status()
    print(f"✅ Status: {status}")
    
    print("\n💬 Commands:")
    print("  - Type your question")
    print("  - Add 'viz' or 'chart' to visualize")
    print("  - Type 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            # Check if user wants visualization
            with_viz = any(kw in user_input.lower() for kw in ['viz', 'chart', 'graph', 'visualize', 'show me'])
            
            # Process query
            response = orchestrator.process_query(user_input, with_viz=with_viz)
            
            # Display results
            if response.get('success'):
                print(f"\n✅ Success! {len(response.get('data', []))} rows returned")
                print(f"📝 SQL: {response.get('sql', 'N/A')[:100]}...")
                
                # Show sample data
                data = response.get('data', [])
                for i, row in enumerate(data[:3]):
                    print(f"   Row {i+1}: {row}")
                if len(data) > 3:
                    print(f"   ... and {len(data) - 3} more rows")
                
                # Show visualization if present
                if 'visualization' in response:
                    print("\n📊 Opening visualization in browser...")
                    response['visualization'].show()
            else:
                print(f"\n❌ Error: {response.get('error', 'Unknown error')}")
                if response.get('sql'):
                    print(f"📝 SQL: {response['sql']}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()