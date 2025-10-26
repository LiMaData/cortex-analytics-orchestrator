"""Data Agent - Handles data retrieval using CortexAnalyst with date serialization"""

from typing import Dict, Any
import logging
from tools.cortex_analyst import CortexAnalystTool
from datetime import date, datetime

logger = logging.getLogger(__name__)

class DataAgent:
    """
    Agent that uses CortexAnalystTool to run NL → SQL → Data
    
    FIXED: Now serializes date objects to prevent JSON errors downstream
    """
    
    def __init__(self, cortex_tool: CortexAnalystTool):
        """
        Initialize DataAgent with a pre-created CortexAnalystTool
        
        Args:
            cortex_tool: Pre-initialized CortexAnalystTool instance
        """
        self.analyst = cortex_tool
        logger.info("✅ DataAgent initialized")
    
    def _serialize_for_json(self, obj: Any) -> Any:
        """
        🔧 CRITICAL FIX: Convert non-JSON-serializable objects to strings
        This prevents "Object of type date is not JSON serializable" errors
        downstream when data is passed to other agents
        """
        if isinstance(obj, dict):
            return {key: self._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]
        elif isinstance(obj, (date, datetime)):
            return obj.isoformat()  # Convert to ISO format string
        else:
            return obj
    
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
                # 🔧 CRITICAL: Serialize all data to prevent JSON errors
                serialized_data = self._serialize_for_json(result['results'])
                
                return {
                    'success': True,
                    'data': serialized_data,  # ← Now JSON-safe!
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