"""
Benchmark Agent - Multi-source industry benchmarks with intelligent fallback
Sources: Database (web-sourced) → LLM Knowledge → Hardcoded Standards
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BenchmarkAgent:
    """
    Fetches industry benchmarks from multiple sources with intelligent fallback
    
    Source Priority:
    1. Database table (web-sourced, updated monthly)
    2. LLM knowledge (training data)
    3. Hardcoded standards (last resort)
    """
    
    def __init__(
        self, 
        cortex_tool=None, 
        use_database: bool = True,
        use_llm_fallback: bool = True,
        freshness_days: int = 90
    ):
        """
        Initialize BenchmarkAgent with multi-source capabilities
        
        Args:
            cortex_tool: CortexAnalystTool for session and LLM access
            use_database: Whether to try database benchmarks first
            use_llm_fallback: Whether to use LLM if database fails
            freshness_days: Max age of database benchmarks (default 90 days)
        """
        self.session = cortex_tool.session if cortex_tool else None
        self.use_database = use_database
        self.use_llm_fallback = use_llm_fallback
        self.freshness_days = freshness_days
        self.model = 'mistral-large'
        
        # Industry standard benchmarks (hardcoded fallback)
        # Sources: Mailchimp 2024, Campaign Monitor 2024, Litmus 2024
        self.hardcoded_benchmarks = {
            'open_rate': {
                'industry_average': 21.5,
                'top_quartile': 28.0,
                'bottom_quartile': 15.0,
                'excellent_threshold': 25.0,
                'metric_name': 'Open Rate',
                'unit': 'percentage',
                'source': 'Industry Standards 2024'
            },
            'click_rate': {
                'industry_average': 2.6,
                'top_quartile': 5.0,
                'bottom_quartile': 2.0,
                'excellent_threshold': 4.0,
                'metric_name': 'Click Rate',
                'unit': 'percentage',
                'source': 'Industry Standards 2024'
            },
            'click_to_open_rate': {
                'industry_average': 14.3,
                'top_quartile': 20.0,
                'bottom_quartile': 10.0,
                'excellent_threshold': 18.0,
                'metric_name': 'Click-to-Open Rate',
                'unit': 'percentage',
                'source': 'Industry Standards 2024'
            },
            'bounce_rate': {
                'industry_average': 0.7,
                'top_quartile': 0.5,  # Lower is better
                'bottom_quartile': 2.0,
                'excellent_threshold': 0.5,
                'metric_name': 'Bounce Rate',
                'unit': 'percentage',
                'source': 'Industry Standards 2024',
                'inverse': True  # Lower is better
            },
            'unsubscribe_rate': {
                'industry_average': 0.2,
                'top_quartile': 0.1,  # Lower is better
                'bottom_quartile': 0.5,
                'excellent_threshold': 0.1,
                'metric_name': 'Unsubscribe Rate',
                'unit': 'percentage',
                'source': 'Industry Standards 2024',
                'inverse': True
            },
            'conversion_rate': {
                'industry_average': 2.5,
                'top_quartile': 5.0,
                'bottom_quartile': 1.0,
                'excellent_threshold': 4.0,
                'metric_name': 'Conversion Rate',
                'unit': 'percentage',
                'source': 'Industry Standards 2024'
            }
        }
        
        # Industry-specific benchmarks
        self.industry_benchmarks = {
            'retail': {'open_rate': 18.5, 'click_rate': 2.3},
            'financial_services': {'open_rate': 21.0, 'click_rate': 2.8},
            'healthcare': {'open_rate': 22.5, 'click_rate': 3.0},
            'technology': {'open_rate': 20.0, 'click_rate': 2.5},
            'media_entertainment': {'open_rate': 23.0, 'click_rate': 3.2},
            'nonprofit': {'open_rate': 25.5, 'click_rate': 2.8}
        }
        
        logger.info("✅ BenchmarkAgent initialized (multi-source hybrid)")
    
    def process(
        self, 
        query: str, 
        data: List[Dict] = None, 
        metric: str = None,
        industry: str = None
    ) -> Dict[str, Any]:
        """
        Get benchmarks with intelligent source selection
        
        Args:
            query: Original user question
            data: Actual performance data (for context)
            metric: Specific metric (auto-detected if None)
            industry: Industry vertical (optional)
            
        Returns:
            Dict with benchmarks, source, and context
        """
        logger.info(f"📊 Fetching benchmarks for query: {query[:60]}...")
        
        # Infer metric if not provided
        if not metric:
            metric = self._infer_metric_from_query(query)
        
        logger.info(f"   Detected metric: {metric}")
        
        # Try sources in priority order
        benchmark_result = None
        source_used = None
        
        # Priority 1: Database (web-sourced, fresh)
        if self.use_database and self.session:
            benchmark_result = self._try_database_benchmarks(metric)
            if benchmark_result:
                source_used = 'database'
                logger.info(f"✅ Using database benchmarks (fresh)")
        
        # Priority 2: LLM Knowledge
        if not benchmark_result and self.use_llm_fallback and self.session:
            benchmark_result = self._try_llm_benchmarks(metric)
            if benchmark_result:
                source_used = 'llm'
                logger.info(f"✅ Using LLM knowledge benchmarks")
        
        # Priority 3: Hardcoded (always works)
        if not benchmark_result:
            benchmark_result = self._get_hardcoded_benchmarks(metric)
            source_used = 'hardcoded'
            logger.info(f"✅ Using hardcoded benchmarks (fallback)")
        
        # Add industry-specific adjustments if available
        if industry and industry.lower() in self.industry_benchmarks:
            industry_data = self.industry_benchmarks[industry.lower()]
            if metric in industry_data:
                benchmark_result['industry_specific'] = industry_data[metric]
                benchmark_result['industry_name'] = industry.title()
        
        # Build response
        return {
            'success': True,
            'metric': metric,
            'benchmarks': benchmark_result,
            'source': source_used,
            'source_description': self._get_source_description(source_used, benchmark_result),
            'context': self._build_context(metric, benchmark_result),
            'comparison_ready': True
        }
    
    def _try_database_benchmarks(self, metric: str) -> Optional[Dict[str, Any]]:
        """
        Try to get benchmarks from Snowflake table
        Returns None if table doesn't exist or data is stale
        """
        try:
            # Check if table exists
            table_exists = self.session.sql("""
                SELECT COUNT(*) as cnt 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'BENCHMARK_DATA'
                AND TABLE_SCHEMA = CURRENT_SCHEMA()
            """).collect()
            
            if not table_exists or table_exists[0]['CNT'] == 0:
                logger.info("   Database benchmark table not found")
                return None
            
            # Query for fresh benchmarks
            cutoff_date = (datetime.now() - timedelta(days=self.freshness_days)).strftime('%Y-%m-%d')
            
            result = self.session.sql(f"""
                SELECT 
                    metric,
                    industry_average,
                    top_quartile,
                    bottom_quartile,
                    excellent_threshold,
                    source,
                    updated_date,
                    DATEDIFF(day, updated_date, CURRENT_DATE()) as age_days
                FROM BENCHMARK_DATA
                WHERE LOWER(metric) = LOWER('{metric}')
                AND updated_date >= '{cutoff_date}'
                ORDER BY updated_date DESC
                LIMIT 1
            """).collect()
            
            if not result:
                logger.info(f"   No fresh database benchmarks for {metric}")
                return None
            
            row = result[0].asDict()
            
            return {
                'industry_average': float(row['INDUSTRY_AVERAGE']),
                'top_quartile': float(row['TOP_QUARTILE']),
                'bottom_quartile': float(row['BOTTOM_QUARTILE']),
                'excellent_threshold': float(row.get('EXCELLENT_THRESHOLD', row['TOP_QUARTILE'])),
                'metric_name': metric.replace('_', ' ').title(),
                'unit': 'percentage',
                'source': row['SOURCE'],
                'updated_date': str(row['UPDATED_DATE']),
                'age_days': int(row['AGE_DAYS']),
                'is_fresh': True
            }
            
        except Exception as e:
            logger.warning(f"   Database benchmark fetch failed: {e}")
            return None
    
    def _try_llm_benchmarks(self, metric: str) -> Optional[Dict[str, Any]]:
        """
        Use LLM to provide benchmarks from training knowledge
        Returns None if LLM call fails
        """
        try:
            metric_display = metric.replace('_', ' ').title()
            
            prompt = f"""You are an email marketing analytics expert. Provide the current industry benchmark for {metric_display}.

Based on your knowledge of email marketing industry standards, return ONLY a valid JSON object with these exact keys:

{{
  "industry_average": <number as float>,
  "top_quartile": <number as float>,
  "bottom_quartile": <number as float>,
  "source": "<source name and year>",
  "confidence": "high|medium|low"
}}

Guidelines:
- Use your most recent knowledge
- Be precise with decimal numbers
- Top quartile = best performers
- Bottom quartile = poorest performers
- For metrics like bounce rate where lower is better, top_quartile should be the lower number
- Return ONLY the JSON, no explanation

JSON:"""

            result = self.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{self.model}',
                    '{prompt.replace("'", "''")}'
                ) AS benchmark_json
            """).collect()
            
            if not result:
                return None
            
            # Parse JSON from LLM response
            response_text = result[0]['BENCHMARK_JSON'].strip()
            
            # Extract JSON if wrapped in markdown
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            benchmark_data = json.loads(response_text)
            
            # Add metadata
            benchmark_data['metric_name'] = metric_display
            benchmark_data['unit'] = 'percentage'
            benchmark_data['excellent_threshold'] = benchmark_data.get('top_quartile')
            benchmark_data['is_llm'] = True
            
            logger.info(f"   LLM provided benchmarks (confidence: {benchmark_data.get('confidence', 'unknown')})")
            
            return benchmark_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"   LLM returned invalid JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"   LLM benchmark fetch failed: {e}")
            return None
    
    def _get_hardcoded_benchmarks(self, metric: str) -> Dict[str, Any]:
        """
        Get hardcoded benchmarks (always works)
        """
        benchmarks = self.hardcoded_benchmarks.get(
            metric,
            {
                'industry_average': 0,
                'top_quartile': 0,
                'bottom_quartile': 0,
                'excellent_threshold': 0,
                'metric_name': metric.replace('_', ' ').title(),
                'unit': 'percentage',
                'source': 'Default Standards',
                'is_fallback': True
            }
        )
        
        return benchmarks.copy()
    
    def _infer_metric_from_query(self, query: str) -> str:
        """Infer metric from natural language query"""
        
        query_lower = query.lower()
        
        # Check for specific metrics
        if 'open' in query_lower and 'click' in query_lower:
            return 'click_to_open_rate'
        elif 'open' in query_lower:
            return 'open_rate'
        elif 'click' in query_lower:
            return 'click_rate'
        elif 'bounce' in query_lower:
            return 'bounce_rate'
        elif 'unsubscribe' in query_lower:
            return 'unsubscribe_rate'
        elif 'conversion' in query_lower or 'convert' in query_lower:
            return 'conversion_rate'
        else:
            # Default to open rate
            return 'open_rate'
    
    def _build_context(self, metric: str, benchmarks: Dict[str, Any]) -> str:
        """Build human-readable context string"""
        
        metric_name = benchmarks.get('metric_name', metric.replace('_', ' ').title())
        unit = benchmarks.get('unit', 'percentage')
        unit_symbol = '%' if unit == 'percentage' else ''
        
        context = f"""Industry Benchmarks for {metric_name}:
- Industry Average: {benchmarks.get('industry_average', 0):.1f}{unit_symbol}
- Top Quartile (Best 25%): {benchmarks.get('top_quartile', 0):.1f}{unit_symbol}
- Bottom Quartile (Lowest 25%): {benchmarks.get('bottom_quartile', 0):.1f}{unit_symbol}
- Excellence Threshold: {benchmarks.get('excellent_threshold', 0):.1f}{unit_symbol}
"""
        
        # Add source info
        if 'source' in benchmarks:
            context += f"• Source: {benchmarks['source']}"
            if 'updated_date' in benchmarks:
                context += f" (Updated: {benchmarks['updated_date']})"
        
        # Add industry-specific if available
        if 'industry_specific' in benchmarks:
            context += f"\n• {benchmarks.get('industry_name', 'Industry')}-Specific Average: {benchmarks['industry_specific']:.1f}{unit_symbol}"
        
        return context
    
    def _get_source_description(self, source: str, benchmarks: Dict[str, Any]) -> str:
        """Get user-friendly source description"""
        
        descriptions = {
            'database': f"Web-sourced data ({benchmarks.get('source', 'recent research')})",
            'llm': f"AI knowledge base ({benchmarks.get('source', 'training data')})",
            'hardcoded': "Industry standard references (2024)"
        }
        
        return descriptions.get(source, 'Unknown source')
    
    def compare_performance(
        self, 
        actual_value: float, 
        metric: str,
        benchmarks: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Compare actual performance to benchmarks
        
        Args:
            actual_value: Actual metric value
            metric: Metric name
            benchmarks: Benchmark data (will fetch if not provided)
            
        Returns:
            Dict with detailed comparison analysis
        """
        # Get benchmarks if not provided
        if not benchmarks:
            result = self.process(query=f"benchmark for {metric}", metric=metric)
            benchmarks = result['benchmarks']
        
        avg = benchmarks.get('industry_average', 0)
        top = benchmarks.get('top_quartile', 0)
        bottom = benchmarks.get('bottom_quartile', 0)
        excellent = benchmarks.get('excellent_threshold', top)
        
        # Handle inverse metrics (lower is better)
        is_inverse = benchmarks.get('inverse', False)
        
        # Determine performance level
        if is_inverse:
            # For metrics like bounce rate, lower is better
            if actual_value <= excellent:
                level = "Excellent"
                description = "significantly better than industry average"
            elif actual_value <= avg:
                level = "Good"
                description = "better than industry average"
            elif actual_value <= top:  # top is actually the worst threshold
                level = "Fair"
                description = "below industry average"
            else:
                level = "Needs Improvement"
                description = "significantly below industry standards"
        else:
            # Normal metrics, higher is better
            if actual_value >= excellent:
                level = "Excellent"
                description = "significantly above industry average"
            elif actual_value >= avg:
                level = "Good"
                description = "above industry average"
            elif actual_value >= bottom:
                level = "Fair"
                description = "below industry average"
            else:
                level = "Needs Improvement"
                description = "significantly below industry standards"
        
        # Calculate gap
        gap = actual_value - avg
        gap_pct = (gap / avg) * 100 if avg > 0 else 0
        
        # Determine if above/below average
        if is_inverse:
            is_above_avg = actual_value <= avg
        else:
            is_above_avg = actual_value >= avg
        
        return {
            'actual': actual_value,
            'industry_avg': avg,
            'top_quartile': top,
            'bottom_quartile': bottom,
            'excellent_threshold': excellent,
            'gap': gap,
            'gap_percentage': gap_pct,
            'performance_level': level,
            'description': description,
            'is_above_avg': is_above_avg,
            'metric': metric
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and capabilities"""
        
        capabilities = []
        if self.use_database:
            capabilities.append('database_lookup')
        if self.use_llm_fallback:
            capabilities.append('llm_knowledge')
        capabilities.append('hardcoded_standards')
        
        return {
            'agent': 'BenchmarkAgent',
            'capabilities': capabilities,
            'freshness_threshold_days': self.freshness_days,
            'available_metrics': list(self.hardcoded_benchmarks.keys()),
            'available_industries': list(self.industry_benchmarks.keys())
        }

logger.info("✅ BenchmarkAgent class defined (hybrid multi-source)")