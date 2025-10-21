"""Conversational Orchestrator - Interactive Q&A mode"""

from typing import Dict, Any
import logging
from orchestrators.base import BaseOrchestrator

logger = logging.getLogger(__name__)

class ConversationalOrchestrator(BaseOrchestrator):
    """Conversational orchestrator for interactive Q&A with multi-agent coordination"""
    
    def __init__(self):
        """Initialize conversational orchestrator with all agents"""
        super().__init__()
        
        # Initialize agents
        from agents.data_agent import DataAgent
        from agents.visualization_agent import VisualizationAgent
        from agents.insight_agent import InsightAgent
        from agents.benchmark_agent import BenchmarkAgent
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
        
        # Initialize all agents
        self.data_agent = DataAgent(cortex_tool)
        self.viz_agent = VisualizationAgent()
        self.insight_agent = InsightAgent(cortex_tool)
        self.benchmark_agent = BenchmarkAgent(cortex_tool)
        
        logger.info("✅ ConversationalOrchestrator initialized with all agents")
    
    def process_query(
        self, 
        query: str, 
        with_viz: bool = False,
        with_benchmarks: bool = True,
        with_insights: bool = True
    ) -> Dict[str, Any]:
        """
        Process query with multi-agent coordination
        
        Args:
            query: Natural language question
            with_viz: Whether to create visualization
            with_benchmarks: Whether to fetch industry benchmarks
            with_insights: Whether to generate AI insights
            
        Returns:
            Dict with success, data, sql, metadata, benchmarks, insights, visualization
        """
        logger.info(f"❓ Processing query: {query}")
        
        try:
            # STEP 1: Get actual data from DataAgent
            data_result = self.data_agent.process(query)
            
            if not data_result.get('success'):
                logger.error(f"❌ Query failed: {data_result.get('error')}")
                return {
                    'success': False,
                    'error': data_result.get('error', 'Unknown error'),
                    'sql': data_result.get('sql'),
                    'data': []
                }
            
            logger.info(f"✅ Query successful, {len(data_result['data'])} rows")
            
            response = {
                'success': True,
                'data': data_result['data'],
                'sql': data_result.get('sql'),
                'metadata': data_result.get('metadata', {})
            }
            
            # STEP 2: Get benchmarks (if requested)
            benchmarks = None
            if with_benchmarks:
                try:
                    logger.info("📊 Fetching industry benchmarks...")
                    benchmarks = self.benchmark_agent.process(
                        query=query,
                        data=data_result['data']
                    )
                    response['benchmarks'] = benchmarks
                    logger.info("✅ Benchmarks retrieved")
                except Exception as e:
                    logger.warning(f"⚠️ Benchmark fetch failed: {e}")
            
            # STEP 3: Generate insights with benchmark comparison
            if with_insights and len(data_result['data']) > 0:
                try:
                    logger.info("🤔 Generating insights...")
                    insights = self.insight_agent.process(
                        data=data_result['data'],
                        query=query,
                        sql=data_result.get('sql'),
                        benchmarks=benchmarks
                    )
                    response['insights'] = insights
                    logger.info("✅ Insights generated")
                except Exception as e:
                    logger.error(f"❌ Insight generation failed: {e}")
                    # Don't fail the whole query if insights fail
            
            # STEP 4: Create visualization (if requested)
            if with_viz and len(data_result['data']) > 0:
                try:
                    logger.info("📊 Creating visualization...")
                    fig = self.viz_agent.create_visualization(
                        data=data_result['data'],
                        question=query
                    )
                    if fig:
                        response['visualization'] = fig
                        logger.info("✅ Visualization created")
                    else:
                        logger.warning("⚠️ Visualization returned None")
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
            'agents_loaded': ['data', 'visualization', 'insight', 'benchmark'],
            'config_valid': self.config.validate()
        }