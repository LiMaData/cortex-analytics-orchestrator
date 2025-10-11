import logging
import pandas as pd
import re
from tools.web_search import web_search

logger = logging.getLogger(__name__)

class BenchmarkAgent:
  """Compares internal metrics with external market benchmarks"""

  def __init__(self, session=None):
      self.session = session  # Snowflake session for LLM
      logger.info("✅ BenchmarkAgent initialized")

  def _extract_numbers(self, text: str):
      """Extract numbers from text snippet"""
      numbers = re.findall(r"\d[\d,]*\.?\d*", text)
      return [float(n.replace(",", "")) for n in numbers]

  def process(self, data: list[dict], metric: str, group_by: str, market_keyword: str):
      if not data:
          return {"error": "No internal data provided"}

      df = pd.DataFrame(data)
      if metric not in df.columns or group_by not in df.columns:
          return {"error": f"Metric '{metric}' or group_by '{group_by}' not found in data"}

      # Internal benchmark
      internal_summary = df.groupby(group_by)[metric].mean().reset_index()

      # External benchmark search
      search_query = f"{market_keyword} average {metric} benchmark"
      external_results = web_search(search_query, count=3)

      # Try to extract numeric benchmarks from snippets
      parsed_external = []
      for res in external_results:
          nums = self._extract_numbers(res["snippet"])
          parsed_external.append({
              "source": res["title"],
              "url": res["url"],
              "snippet": res["snippet"],
              "numbers": nums
          })

      # LLM comparison
      comparison_summary = None
      if self.session:
          prompt = f"""
          Compare the following internal benchmark data with the external market benchmarks:

          Internal Data:
          {internal_summary.to_dict(orient='records')}

          External Data:
          {parsed_external}

          Provide a concise analysis of how we perform vs the market.
          """
          result = self.session.sql(f"""
              SELECT SNOWFLAKE.CORTEX.COMPLETE(
                  'mistral-large',
                  '{prompt.replace("'", "''")}'
              ) AS insight
          """).collect()
          comparison_summary = result[0]['INSIGHT']

      return {
          "internal": internal_summary.to_dict(orient="records"),
          "external": parsed_external,
          "summary": comparison_summary
      }