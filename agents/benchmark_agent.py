"""
Benchmark Agent - Retrieves industry benchmarks for comparison
Uses tiered approach: Snowflake tables → LLM → Hardcoded fallbacks
FIXED: Date type handling to prevent datetime/date mismatch errors
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import re

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
        
        # ========== CRITICAL: Initialize ALL variables at the start ==========
        source = 'unknown'
        metric = 'email_open_rate'
        benchmarks = None
        error = None
        # ======================================================================
        
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
                else:
                    logger.debug("⚠️ No benchmarks from database")
            except Exception as db_error:
                logger.warning(f"⚠️ Database fetch failed: {db_error}")
                benchmarks = None
            
            # Step 3: Try LLM if database failed
            if not benchmarks:
                try:
                    logger.info("⚠️ Trying LLM...")
                    benchmarks = self._fetch_from_llm(metric)
                    if benchmarks:
                        source = 'llm'
                        logger.info("✅ Benchmarks from LLM")
                    else:
                        logger.debug("⚠️ No benchmarks from LLM")
                except Exception as llm_error:
                    logger.warning(f"⚠️ LLM fetch failed: {llm_error}")
                    benchmarks = None
            
            # Step 4: Use hardcoded if both failed
            if not benchmarks:
                logger.info("⚠️ Using hardcoded benchmarks (fallback)")
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
            error = str(e)
            logger.error(f"❌ Complete benchmark failure: {error}")
            
            return {
                'success': False,
                'error': error,
                'metric': metric,
                'source': 'error',
                'source_description': 'Error occurred, using defaults',
                'benchmarks': self._get_default_benchmarks(),
                'context': 'Default benchmark values'
            }
    
    def _identify_metric(self, query: str, data: List[Dict[str, Any]] = None) -> str:
        """Identify which metric the query is asking about"""
        
        if not query:
            return 'email_open_rate'
        
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
            try:
                columns = list(data[0].keys())
                for col in columns:
                    col_lower = col.lower()
                    if 'open' in col_lower:
                        return 'email_open_rate'
                    elif 'click' in col_lower:
                        return 'email_click_rate'
                    elif 'conversion' in col_lower:
                        return 'conversion_rate'
            except (TypeError, KeyError, AttributeError) as e:
                logger.debug(f"Could not inspect data columns: {e}")
        
        # Default
        return 'email_open_rate'
    
    def _fetch_from_database(self, metric: str) -> Optional[Dict[str, Any]]:
        """Try to fetch benchmarks from Snowflake database (FIXED for actual schema)"""
        
        if not metric:
            return None
        
        try:
            # Escape metric name for SQL safety
            safe_metric = metric.replace("'", "''")
            
            # FIXED: Query now matches actual Snowflake table schema
            # Note: Removed IS_CURRENT filter (column doesn't exist)
            # Changed METRIC_NAME to METRIC
            query = f"""
            SELECT 
                INDUSTRY_AVERAGE,
                TOP_QUARTILE,
                BOTTOM_QUARTILE,
                EXCELLENT_THRESHOLD,
                SOURCE,
                UPDATED_DATE
            FROM BENCHMARK_DATA
            WHERE METRIC = '{safe_metric}'
            LIMIT 1
            """
            
            logger.debug(f"Executing benchmark query: {query}")
            result = self.cortex_tool.session.sql(query).collect()
            
            if result and len(result) > 0:
                row = result[0]
                
                # Extract fields with error handling
                try:
                    industry_avg = float(row['INDUSTRY_AVERAGE'])
                    top_quartile = float(row['TOP_QUARTILE'])
                    bottom_quartile = float(row['BOTTOM_QUARTILE'])
                    excellent = float(row['EXCELLENT_THRESHOLD'])
                    source_name = str(row['SOURCE'])
                    updated_date = row['UPDATED_DATE']
                    
                    # ✅ FIXED: Calculate age with proper date type handling
                    age_days = 0
                    if updated_date:
                        age_days = self._calculate_age_days(updated_date)
                    
                    logger.info(f"✅ Successfully fetched benchmarks from database for {metric}")
                    
                    return {
                        'industry_average': industry_avg,
                        'top_quartile': top_quartile,
                        'bottom_quartile': bottom_quartile,
                        'excellent_threshold': excellent,
                        'source_name': source_name,
                        'updated_date': str(updated_date),
                        'age_days': age_days
                    }
                except (ValueError, KeyError, TypeError) as parse_error:
                    logger.warning(f"⚠️ Failed to parse database row: {parse_error}")
                    return None
            else:
                logger.debug(f"No benchmarks found for metric: {metric}")
                return None
            
        except Exception as e:
            # Detect common "object does not exist" SQL compilation error from Snowflake
            err_text = str(e)
            if 'Object' in err_text and 'does not exist' in err_text:
                # Log at info level because this is an expected missing-table situation
                logger.info("Benchmarks table 'BENCHMARK_DATA' not found or not authorized. Using fallback benchmarks.")
            else:
                logger.warning(f"⚠️ Database fetch failed: {e}")

            return None
    
    def _calculate_age_days(self, updated_date) -> int:
        """
        ✅ NEW: Calculate days since last update
        Handles both datetime and date objects safely
        
        Args:
            updated_date: Either datetime.datetime or datetime.date from database
            
        Returns:
            Number of days since update
        """
        try:
            # Get today as a date object
            today = date.today()
            
            # Convert updated_date to date if it's a datetime
            if isinstance(updated_date, datetime):
                updated_date_as_date = updated_date.date()
            elif isinstance(updated_date, date):
                updated_date_as_date = updated_date
            else:
                # If it's neither, try to parse it
                logger.warning(f"Unexpected date type: {type(updated_date)}, attempting to parse")
                updated_date_as_date = datetime.fromisoformat(str(updated_date)).date()
            
            # Now both are date objects - safe to subtract
            age_days = (today - updated_date_as_date).days
            
            return age_days
            
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate age: {e}")
            return 0
    
    def _fetch_from_llm(self, metric: str) -> Optional[Dict[str, Any]]:
        """Generate benchmarks using LLM knowledge"""
        
        if not metric or not self.cortex_tool:
            return None
        
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

            # Escape single quotes for SQL
            safe_prompt = prompt.replace("'", "''")
            
            cortex_query = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'mistral-large',
                    '{safe_prompt}'
                ) AS benchmark_data
            """
            
            response = self.cortex_tool.session.sql(cortex_query).collect()
            
            if response and len(response) > 0:
                text = response[0]['BENCHMARK_DATA']
                
                # Parse the response
                benchmarks = self._parse_llm_response(text)
                if benchmarks:
                    logger.info(f"✅ Generated benchmarks from LLM for {metric}")
                    return benchmarks
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ LLM fetch failed: {e}")
            return None
    
    def _parse_llm_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response to extract benchmark numbers"""
        
        if not text:
            return None
        
        try:
            # Find all percentages in the response
            numbers = re.findall(r'(\d+\.?\d*)\s*%', text)
            
            if len(numbers) >= 4:
                return {
                    'industry_average': float(numbers[0]),
                    'top_quartile': float(numbers[1]),
                    'bottom_quartile': float(numbers[2]),
                    'excellent_threshold': float(numbers[3]),
                    'source_name': 'LLM Knowledge',
                    'updated_date': str(date.today()),
                    'age_days': 0
                }
            
            logger.debug(f"⚠️ Could not find 4+ percentages in LLM response")
            return None
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
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
        
        # Get data for this metric or use default
        if metric in benchmarks:
            data = benchmarks[metric].copy()
        else:
            data = benchmarks['email_open_rate'].copy()
        
        # Add metadata
        data['source_name'] = 'Industry Research 2024'
        data['updated_date'] = '2024-01-01'
        
        # ✅ FIXED: Calculate age with proper date handling
        data['age_days'] = self._calculate_age_days(datetime(2024, 1, 1))
        
        return data
    
    def _get_default_benchmarks(self) -> Dict[str, Any]:
        """Return safe default benchmarks on error"""
        return {
            'industry_average': 20.0,
            'top_quartile': 25.0,
            'bottom_quartile': 15.0,
            'excellent_threshold': 28.0,
            'source_name': 'Default Values',
            'updated_date': str(date.today()),
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
        
        if not benchmarks:
            benchmarks = self._get_default_benchmarks()
        
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


logger.info("✅ BenchmarkAgent class defined successfully")