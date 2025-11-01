import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path so imports like `agents.*` resolve when run as a script
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from agents.benchmark_agent import BenchmarkAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

class FakeTool:
    def __init__(self):
        self.session = None

agent = BenchmarkAgent(FakeTool())
res = agent.process('What is the open rate benchmark?')
print('\nResult:')
print(res)
