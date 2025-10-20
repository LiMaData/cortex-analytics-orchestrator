"""Conversational Orchestrator - Interactive Q&A mode"""

from typing import Dict, Any
import logging
from orchestrators.base import BaseOrchestrator

logger = logging.getLogger(__name__)

class ConversationalOrchestrator(BaseOrchestrator):
    """Conversational orchestrator for interactive Q&A"""
    
    def __init__(self):
        """Initialize conversational orchestrator"""
        super().__init__()
        
        # Initialize agents
        from agents.data_agent import DataAgent
        from agents.visualization_agent import VisualizationAgent
        from agents.insight_agent import InsightAgent
        from tools.cortex_analyst import CortexAnalystTool
        from snowflake.snowpark import Session
        
        # Create Snowflake session
        session = Session.builder.configs(self.config.snowflake).create()
        logger.info("✅ Connected to Snowflake")
        
        # Initialize Cortex Analyst Tool
        cortex_tool = CortexAnalystTool(
            session=session,
            semantic_model_stage=self.config.semantic_model_stage
        )
        
        # Initialize agents
        self.data_agent = DataAgent(cortex_tool)
        self.viz_agent = VisualizationAgent()
        self.insight_agent = InsightAgent(cortex_tool)
        
        logger.info("✅ ConversationalOrchestrator initialized")
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process user query and return results
        
        Args:
            query: Natural language question
            
        Returns:
            Dict with success, data, sql, metadata, error
        """
        logger.info(f"❓ Processing query: {query}")
        
        try:
            # Get data from DataAgent
            data_result = self.data_agent.process(query)
            
            if not data_result.get('success'):
                logger.error(f"❌ Query failed: {data_result.get('error')}")
                return {
                    'success': False,
                    'error': data_result.get('error', 'Unknown error'),
                    'sql': data_result.get('sql'),
                    'data': []
                }
            
            # Success - return data
            logger.info(f"✅ Query successful, {len(data_result['data'])} rows")
        
            response = {
                'success': True,
                'data': data_result['data'],
                'sql': data_result.get('sql'),
                'metadata': data_result.get('metadata', {})
            }
            
            # Add visualization if requested
            if with_viz and len(data_result['data']) > 0:
                viz_keywords = ['show', 'visualize', 'chart', 'graph', 'by market', 'by country']
                should_viz = with_viz or any(kw in query.lower() for kw in viz_keywords)
                
                if should_viz:
                    try:
                        fig = self.viz_agent.create_visualization(
                            data=data_result['data'],
                            question=query
                        )
                        if fig:
                            response['visualization'] = fig
                            logger.info("📊 Visualization created")
                    except Exception as e:
                        logger.warning(f"⚠️ Visualization failed: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'data': []
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'name': 'ConversationalOrchestrator',
            'mode': 'conversational',
            'agents_loaded': ['data', 'visualization', 'insight'],
            'config_valid': self.config.validate()
        }