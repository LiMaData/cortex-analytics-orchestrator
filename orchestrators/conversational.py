"""
Conversational Orchestrator
Handles interactive Q&A with intelligent routing
"""
import logging
from orchestrators.base import BaseOrchestrator
from agents.data_agent import DataAgent
from agents.visualization_agent import VisualizationAgent
from agents.insight_agent import InsightAgent
from agents.benchmark_agent import BenchmarkAgent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ConversationalOrchestrator(BaseOrchestrator):
 def __init__(self):
     super().__init__()
     self.mode = "conversational"
     self._init_agents()

 def _init_agents(self):
     data_agent = DataAgent()
     self.register_agent('data', data_agent)
     self.register_agent('visualization', VisualizationAgent())
     self.register_agent('insight', InsightAgent(data_agent.session))
     # self.register_agent('benchmark', BenchmarkAgent())

 def process_query(self, query: str):
     logger.info(f"❓ Processing query: {query}")

     # Step 1: Get data from DataAgent
     data_result = self.get_agent('data').process(query)
     if not data_result['success']:
         return {
             'success': False,
             'error': data_result['error'],
             'sql': data_result['sql']
         }

     data = data_result['results']

     # Step 2: Create chart
     chart = None
     if data:
         chart = self.get_agent('visualization').process(data, chart_type="bar")

     # Step 3: Generate insights
     insights = self.get_agent('insight').process(data)

     # Step 4: Benchmark example (if data has these columns)
     # benchmark = None
     # if data and 'SENDS' in data[0] and 'MARKET' in data[0]:
     #     benchmark = self.get_agent('benchmark').process(data, metric='SENDS', group_by='MARKET')

     return {
         'success': True,
         'sql': data_result['sql'],
         'data': data,
         'chart': chart,
         'insights': insights,
         # 'benchmark': benchmark
     }

# ---------------------------
# Example usage (TOP LEVEL)
# ---------------------------
if __name__ == "__main__":
 orch = ConversationalOrchestrator()
 test_query = "What were the sends by market last month?"
 result = orch.process_query(test_query)

 print("\n=== SQL ===")
 print(result['sql'])

 print("\n=== Data ===")
 print(result['data'])

 print("\n=== Insights ===")
 print(result['insights'])

 # print("\n=== Benchmark ===")
 # print(result['benchmark'])

 if result['chart']:
     result['chart'].show()