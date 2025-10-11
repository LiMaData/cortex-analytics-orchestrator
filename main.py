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
  """Main function"""
  print("=" * 60)
  print("Cortex Analytics Orchestrator")
  print("=" * 60)
  
  # Initialize conversational orchestrator
  print("\n🤖 Initializing Conversational Orchestrator...")
  orchestrator = ConversationalOrchestrator()
  
  # Check status
  status = orchestrator.get_status()
  print(f"✅ Status: {status}")
  
  # Interactive loop
  print("\n💬 Ready for queries! (type 'exit' to quit)\n")
  
  while True:
      try:
          query = input("You: ").strip()
          
          if not query:
              continue
          
          if query.lower() in ['exit', 'quit', 'q']:
              print("\n👋 Goodbye!")
              break
          
          # Process query
          response = orchestrator.process_query(query)
          
          # Display response
          print(f"\n🤖 Assistant:\n{response.text}\n")
          
          if response.data and len(response.data) > 0:
              print(f"📊 Data Preview (showing {min(3, len(response.data))} of {len(response.data)} rows):")
              for row in response.data[:3]:
                  print(f"   {row}")
              print()
          
      except KeyboardInterrupt:
          print("\n\n👋 Goodbye!")
          break
      except Exception as e:
          logger.error(f"Error: {e}", exc_info=True)
          print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
  main()
