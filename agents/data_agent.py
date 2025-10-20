"""Data Agent - Handles data retrieval using CortexAnalyst"""

from typing import Dict, Any
import logging
from tools.cortex_analyst import CortexAnalystTool

logger = logging.getLogger(__name__)

class DataAgent:
    """
    Agent that uses CortexAnalystTool to run NL → SQL → Data
    """
    
    def __init__(self, cortex_tool: CortexAnalystTool):
        """
        Initialize DataAgent with a pre-created CortexAnalystTool
        
        Args:
            cortex_tool: Pre-initialized CortexAnalystTool instance
        """
        self.analyst = cortex_tool
        logger.info("✅ DataAgent initialized")
    
    def process(self, query: str) -> Dict[str, Any]:
        """
        Process a query and return results
        
        Args:
            query: Natural language question
            
        Returns:
            Dict with success, data, sql, metadata
        """
        try:
            # Use CortexAnalystTool.query() method
            result = self.analyst.query(query)
            
            if result['success']:
                return {
                    'success': True,
                    'data': result['results'],
                    'sql': result['sql'],
                    'metadata': {
                        'row_count': result['row_count'],
                        'source': 'Cortex Analyst'
                    }
                }
            else:
                return {
                    'success': False,
                    'data': [],
                    'error': result['error'],
                    'sql': result.get('sql')
                }
                
        except Exception as e:
            logger.error(f"❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'data': [],
                'error': str(e)
            }