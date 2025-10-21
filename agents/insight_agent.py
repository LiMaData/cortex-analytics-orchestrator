"""Insight Agent - Generates insights using LLM (CORTEX.COMPLETE)"""

import logging
from typing import Dict, List, Any
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

class InsightAgent:
    """Generates textual insights using CORTEX.COMPLETE with smart prompting"""
    
    def __init__(self, cortex_tool):
        """
        Initialize InsightAgent
        
        Args:
            cortex_tool: CortexAnalystTool instance (for session access)
        """
        self.session = cortex_tool.session
        self.model = 'mistral-large'
        logger.info("✅ InsightAgent initialized")
    
    def _convert_decimals(self, obj):
        """
        Convert Decimal objects to float for JSON serialization
        
        Args:
            obj: Object that may contain Decimals
            
        Returns:
            Object with Decimals converted to floats
        """
        if isinstance(obj, list):
            return [self._convert_decimals(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_decimals(value) for key, value in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj
    
    def process(
        self, 
        data: List[Dict], 
        query: str = None, 
        sql: str = None,
        benchmarks: Dict[str, Any] = None
    ) -> str:
        """
        Generate insights from data using LLM with benchmark comparison
        
        Args:
            data: Query results
            query: Original user question
            sql: SQL query that generated the data
            benchmarks: Industry benchmarks from BenchmarkAgent
            
        Returns:
            String with AI-generated insights
        """
        if not data:
            return "No data available to analyze."
        
        logger.info(f"🤔 Processing {len(data)} rows for insights...")
        
        # Convert Decimals to floats for JSON serialization
        data = self._convert_decimals(data)
        
        # Build smart prompt
        prompt = self._build_insight_prompt(data, query, sql, benchmarks)
        
        try:
            logger.info("📝 Calling LLM for insights...")
            
            result = self.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{self.model}',
                    '{prompt.replace("'", "''")}'
                ) AS insight
            """).collect()
            
            insight = result[0]['INSIGHT']
            logger.info(f"✅ Insights generated ({len(insight)} chars)")
            return insight
            
        except Exception as e:
            logger.error(f"❌ Insight generation failed: {e}")
            return f"Unable to generate insights: {str(e)}"
    
    def _build_insight_prompt(
        self, 
        data: List[Dict], 
        query: str = None, 
        sql: str = None,
        benchmarks: Dict[str, Any] = None
    ) -> str:
        """
        Build structured prompt for better insights
        
        Args:
            data: Converted data (Decimals already converted)
            query: User's question
            sql: Generated SQL
            benchmarks: Benchmark data
            
        Returns:
            Formatted prompt string
        """
        
        # Summarize data
        data_summary = self._summarize_data(data)
        
        # Add benchmark context if available
        benchmark_context = ""
        if benchmarks and benchmarks.get('success'):
            bm = benchmarks.get('benchmarks', {})
            benchmark_context = f"""
INDUSTRY BENCHMARKS:
Metric: {benchmarks.get('metric', 'N/A').replace('_', ' ').title()}
Industry Average: {bm.get('industry_average', 0):.1f}%
Top Quartile (Best 25%): {bm.get('top_quartile', 0):.1f}%
Bottom Quartile (Lowest 25%): {bm.get('bottom_quartile', 0):.1f}%
Excellence Threshold: {bm.get('excellent_threshold', 0):.1f}%
Source: {benchmarks.get('source_description', 'Industry Standards')}

CRITICAL: Compare actual performance against these benchmarks in your analysis.
"""
        
        prompt = f"""You are a marketing analytics expert. Analyze this data and provide actionable insights WITH BENCHMARK COMPARISON.

CONTEXT:
User Question: {query or 'N/A'}
SQL Query: {sql[:200] if sql else 'N/A'}...

{benchmark_context}

DATA SUMMARY:
- Total Rows: {len(data)}
- Columns: {list(data[0].keys()) if data else []}

SAMPLE DATA (first 5 rows):
{json.dumps(data[:5], indent=2)}

{data_summary}

INSTRUCTIONS:
1. Compare actual performance to industry benchmarks (if provided)
2. Identify TOP 3 key insights focusing on performance gaps
3. Highlight markets/segments above/below industry standards
4. Provide 2-3 actionable recommendations to close performance gaps
5. Be specific with numbers and percentages

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

📊 PERFORMANCE vs INDUSTRY:
- [How does overall performance compare to benchmarks - be specific with numbers]

🔍 KEY INSIGHTS:
- [Insight 1 - with benchmark comparison and specific values]
- [Insight 2 - with benchmark comparison and specific values]
- [Insight 3 - with benchmark comparison and specific values]

💡 RECOMMENDATIONS:
- [Action 1 - specific and actionable to reach benchmark levels]
- [Action 2 - specific and actionable]
- [Action 3 - specific and actionable]

INSIGHTS:"""

        return prompt
    
    def _summarize_data(self, data: List[Dict]) -> str:
        """
        Create statistical summary of data
        
        Args:
            data: Converted data (no Decimals)
            
        Returns:
            Formatted statistical summary
        """
        
        if not data:
            return ""
        
        summary = []
        
        # Get numeric columns
        numeric_cols = []
        for key, value in data[0].items():
            if isinstance(value, (int, float)):
                numeric_cols.append(key)
        
        # Calculate statistics for numeric columns
        for col in numeric_cols:
            values = [row[col] for row in data if row.get(col) is not None]
            
            if values:
                total = sum(values)
                avg = total / len(values)
                max_val = max(values)
                min_val = min(values)
                
                summary.append(f"""
{col}:
  - Total: {total:,.0f}
  - Average: {avg:,.2f}
  - Max: {max_val:,.0f}
  - Min: {min_val:,.0f}
  - Range: {max_val - min_val:,.0f}
""")
        
        if summary:
            return "STATISTICAL SUMMARY:\n" + "\n".join(summary)
        return ""

logger.info("✅ InsightAgent class defined")