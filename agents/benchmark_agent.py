"""
Benchmark Agent - Retrieves industry benchmarks for comparison
Uses tiered approach: Snowflake tables → LLM → Hardcoded fallbacks
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BenchmarkAgent:
    """Agent for fetching industry benchmarks and comparisons"""
    
    def __init__(self, cortex_tool):
        """
        Initialize BenchmarkAgent
        
        Args:
            cortex_tool: CortexAnalystTool for database access
        """
        self.cortex_tool = cortex_tool
        logger.info("✅ BenchmarkAgent initialized")
    
    def process(self, query: str, data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch industry benchmarks relevant to the query"""
        
        logger.info(f"🔍 BenchmarkAgent processing: {query}")
        
        # Initialize ALL variables at the start
        source = 'unknown'
        metric = 'email_open_rate'
        benchmarks = None
        
        try:
            # Step 1: Identify metric
            metric = self._identify_metric(query, data)
            logger.info(f"📊 Identified metric: {metric}")
            
            # Step 2: Try database
            try:
                benchmarks = self._fetch_from_database(metric)
                if benchmarks:
                    source = 'database'
                    logger.info("✅ Benchmarks from database")
            except Exception as e:
                logger.warning(f"⚠️ Database fetch failed: {e}")
                benchmarks = None
            
            # Step 3: Try LLM if database failed
            if not benchmarks:
                try:
                    logger.info("⚠️ Trying LLM")
                    benchmarks = self._fetch_from_llm(metric)
                    if benchmarks:
                        source = 'llm'
                        logger.info("✅ Benchmarks from LLM")
                except Exception as e:
                    logger.warning(f"⚠️ LLM fetch failed: {e}")
                    benchmarks = None
            
            # Step 4: Use hardcoded if both failed
            if not benchmarks:
                logger.info("⚠️ Using hardcoded benchmarks")
                benchmarks = self._get_hardcoded_benchmarks(metric)
                source = 'hardcoded'
            
            # Build successful response
            return {
                'success': True,
                'metric': metric,
                'benchmarks': benchmarks,
                'source': source,
                'source_description': self._get_source_description(source),
                'context': self._build_context(metric, benchmarks)
            }
            
        except Exception as e:
            # Complete failure - return safe defaults
            logger.error(f"❌ Complete benchmark failure: {e}")
            return {
                'success': False,
                'error': str(e),
                'metric': metric,
                'source': 'error',
                'source_description': 'Error occurred, using defaults',
                'benchmarks': self._get_default_benchmarks(),
                'context': 'Default benchmark values'
            }
    
    def _identify_metric(self, query: str, data: List[Dict[str, Any]] = None) -> str:
        """Identify which metric the query is asking about"""
        
        query_lower = query.lower()
        
        # Check query text for metric keywords
        if 'open rate' in query_lower or 'opens' in query_lower:
            return 'email_open_rate'
        elif 'click rate' in query_lower or 'clicks' in query_lower or 'ctr' in query_lower:
            return 'email_click_rate'
        elif 'conversion' in query_lower or 'convert' in query_lower:
            return 'conversion_rate'
        elif 'bounce' in query_lower:
            return 'bounce_rate'
        elif 'unsubscribe' in query_lower:
            return 'unsubscribe_rate'
        
        # Check data columns if available
        if data and len(data) > 0:
            columns = list(data[0].keys())
            for col in columns:
                col_lower = col.lower()
                if 'open' in col_lower:
                    return 'email_open_rate'
                elif 'click' in col_lower:
                    return 'email_click_rate'
                elif 'conversion' in col_lower:
                    return 'conversion_rate'
        
        # Default
        return 'email_open_rate'
    
    def _fetch_from_database(self, metric: str) -> Optional[Dict[str, Any]]:
        """Try to fetch benchmarks from Snowflake database"""
        
        try:
            # Query benchmark table
            query = f"""
            SELECT 
                INDUSTRY_AVERAGE,
                TOP_QUARTILE,
                BOTTOM_QUARTILE,
                EXCELLENT_THRESHOLD,
                SOURCE,
                UPDATED_DATE
            FROM BENCHMARKS
            WHERE METRIC_NAME = '{metric}'
                AND IS_CURRENT = TRUE
            LIMIT 1
            """
            
            result = self.cortex_tool.session.sql(query).collect()
            
            if result and len(result) > 0:
                row = result[0]
                
                # Calculate age
                updated_date = row['UPDATED_DATE']
                age_days = (datetime.now() - updated_date).days if updated_date else 0
                
                return {
                    'industry_average': float(row['INDUSTRY_AVERAGE']),
                    'top_quartile': float(row['TOP_QUARTILE']),
                    'bottom_quartile': float(row['BOTTOM_QUARTILE']),
                    'excellent_threshold': float(row['EXCELLENT_THRESHOLD']),
                    'source_name': row['SOURCE'],
                    'updated_date': str(updated_date),
                    'age_days': age_days
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Database fetch failed: {e}")
            return None
    
    def _fetch_from_llm(self, metric: str) -> Optional[Dict[str, Any]]:
        """Generate benchmarks using LLM knowledge"""
        
        try:
            prompt = f"""What are the typical industry benchmarks for {metric} in email marketing?

Please provide:
1. Industry average (as percentage)
2. Top quartile performance (as percentage)
3. Bottom quartile performance (as percentage)
4. Threshold for excellent performance (as percentage)

Format your response as:
Industry Average: [number]%
Top Quartile: [number]%
Bottom Quartile: [number]%
Excellent Threshold: [number]%"""

            response = self.cortex_tool.session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'mistral-large',
                    '{prompt.replace("'", "''")}'
                ) AS benchmark_data
            """).collect()
            
            if response:
                text = response[0]['BENCHMARK_DATA']
                # Parse the response
                benchmarks = self._parse_llm_response(text)
                if benchmarks:
                    return benchmarks
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ LLM fetch failed: {e}")
            return None
    
    def _parse_llm_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response to extract benchmark numbers"""
        
        import re
        
        try:
            numbers = re.findall(r'(\d+\.?\d*)\s*%', text)
            
            if len(numbers) >= 4:
                return {
                    'industry_average': float(numbers[0]),
                    'top_quartile': float(numbers[1]),
                    'bottom_quartile': float(numbers[2]),
                    'excellent_threshold': float(numbers[3]),
                    'source_name': 'LLM Knowledge',
                    'updated_date': str(datetime.now().date()),
                    'age_days': 0
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None
    
    def _get_hardcoded_benchmarks(self, metric: str) -> Dict[str, Any]:
        """Return hardcoded benchmark values as fallback"""
        
        # Hardcoded benchmarks from industry research (2024)
        benchmarks = {
            'email_open_rate': {
                'industry_average': 21.5,
                'top_quartile': 28.0,
                'bottom_quartile': 15.0,
                'excellent_threshold': 30.0
            },
            'email_click_rate': {
                'industry_average': 2.3,
                'top_quartile': 3.5,
                'bottom_quartile': 1.2,
                'excellent_threshold': 4.0
            },
            'conversion_rate': {
                'industry_average': 2.5,
                'top_quartile': 5.0,
                'bottom_quartile': 1.0,
                'excellent_threshold': 7.0
            },
            'bounce_rate': {
                'industry_average': 2.0,
                'top_quartile': 0.5,
                'bottom_quartile': 4.0,
                'excellent_threshold': 0.3
            },
            'unsubscribe_rate': {
                'industry_average': 0.25,
                'top_quartile': 0.1,
                'bottom_quartile': 0.5,
                'excellent_threshold': 0.1
            }
        }
        
        data = benchmarks.get(metric, benchmarks['email_open_rate'])
        data['source_name'] = 'Industry Research 2024'
        data['updated_date'] = '2024-01-01'
        data['age_days'] = (datetime.now() - datetime(2024, 1, 1)).days
        
        return data
    
    def _get_default_benchmarks(self) -> Dict[str, Any]:
        """Return safe default benchmarks on error"""
        return {
            'industry_average': 20.0,
            'top_quartile': 25.0,
            'bottom_quartile': 15.0,
            'excellent_threshold': 28.0,
            'source_name': 'Default Values',
            'updated_date': str(datetime.now().date()),
            'age_days': 0
        }
    
    def _get_source_description(self, source: str) -> str:
        """Get human-readable source description"""
        
        descriptions = {
            'database': 'Retrieved from internal benchmark database',
            'llm': 'Generated using AI knowledge base',
            'hardcoded': 'Industry research benchmarks (2024)',
            'error': 'Default fallback values',
            'unknown': 'Source unavailable'
        }
        
        return descriptions.get(source, 'Unknown source')
    
    def _build_context(self, metric: str, benchmarks: Dict[str, Any]) -> str:
        """Build contextual information about the benchmarks"""
        
        avg = benchmarks.get('industry_average', 0)
        top = benchmarks.get('top_quartile', 0)
        
        metric_names = {
            'email_open_rate': 'Email Open Rate',
            'email_click_rate': 'Email Click Rate',
            'conversion_rate': 'Conversion Rate',
            'bounce_rate': 'Bounce Rate',
            'unsubscribe_rate': 'Unsubscribe Rate'
        }
        
        metric_name = metric_names.get(metric, metric.replace('_', ' ').title())
        
        return f"""
Industry benchmarks for {metric_name}:
- The average across the industry is {avg}%
- Top performers achieve {top}% or higher
- These benchmarks help evaluate performance relative to peers
"""

logger.info("✅ BenchmarkAgent class defined")