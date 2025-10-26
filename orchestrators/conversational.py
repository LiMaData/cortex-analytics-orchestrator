"""
Conversational Orchestrator - Interactive Q&A mode with comprehensive monitoring
Tracks AI agents (TruLens), internal agents (traditional), and coordinates multi-agent workflows
"""

from typing import Dict, Any
import logging
import time
from datetime import date, datetime
from orchestrators.base import BaseOrchestrator

logger = logging.getLogger(__name__)

class ConversationalOrchestrator(BaseOrchestrator):
    """
    Conversational orchestrator for interactive Q&A with multi-agent coordination
    
    Agents:
    - DataAgent (AI): NL → SQL via LLM
    - InsightAgent (AI): Insight generation via LLM
    - BenchmarkAgent (Hybrid): Database → LLM fallback → Hardcoded
    - VisualizationAgent (Internal): Rule-based chart generation
    """
    
    def __init__(self, enable_monitoring: bool = True):
        """
        Initialize conversational orchestrator with all agents and monitoring
        
        Args:
            enable_monitoring: Whether to enable TruLens and performance monitoring
        """
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
        
        # Initialize monitoring
        self.enable_monitoring = enable_monitoring
        if enable_monitoring:
            try:
                from monitoring import get_agent_monitor
                self.monitor = get_agent_monitor(session=session)
                logger.info("✅ Monitoring enabled")
            except Exception as e:
                logger.warning(f"⚠️ Monitoring initialization failed: {e}")
                self.monitor = None
                self.enable_monitoring = False
        else:
            self.monitor = None
        
        logger.info("✅ ConversationalOrchestrator initialized with all agents")
    
    def _serialize_for_json(self, obj: Any) -> Any:
        """
        🔧 FIX: Convert non-JSON-serializable objects to strings
        Handles date, datetime, and other special types
        
        This prevents: "Object of type date is not JSON serializable" errors
        """
        if isinstance(obj, dict):
            return {key: self._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]
        elif isinstance(obj, (date, datetime)):
            return obj.isoformat()
        else:
            return obj
    
    def process_query(
        self, 
        query: str, 
        with_viz: bool = False,
        with_benchmarks: bool = True,
        with_insights: bool = True
    ) -> Dict[str, Any]:
        """
        Process query with multi-agent coordination and monitoring
        
        Args:
            query: Natural language question
            with_viz: Whether to create visualization
            with_benchmarks: Whether to fetch industry benchmarks
            with_insights: Whether to generate AI insights
            
        Returns:
            Dict with success, data, sql, metadata, benchmarks, insights, visualization
        """
        logger.info(f"❓ Processing query: {query}")
        
        orchestration_start = time.time()
        agents_used = []
        response = {}
        
        try:
            # ================================================================
            # STEP 1: DATA AGENT (AI - LLM for NL→SQL)
            # ================================================================
            logger.info("📊 Step 1: Querying data with DataAgent (AI)")
            data_start = time.time()
            
            try:
                data_result = self.data_agent.process(query)
                data_time = time.time() - data_start
                
                # Monitor AI agent with TruLens or Cortex
                # 🔧 FIX: Serialize data before passing to monitor (prevents JSON serialization errors)
                if self.enable_monitoring and self.monitor:
                    serialized_response = self._serialize_for_json(data_result)
                    self.monitor.track_ai_agent(
                        agent_name='DataAgent',
                        query=query,
                        response=serialized_response,
                        context=[data_result.get('sql', '')],
                        execution_time=data_time
                    )
                
                agents_used.append('DataAgent')
                
            except Exception as e:
                data_time = time.time() - data_start
                logger.error(f"❌ DataAgent failed: {e}")
                
                if self.enable_monitoring and self.monitor:
                    self.monitor.track_ai_agent(
                        agent_name='DataAgent',
                        query=query,
                        response={'success': False, 'error': str(e)},
                        execution_time=data_time
                    )
                
                raise
            
            # Check if data retrieval succeeded
            if not data_result.get('success'):
                logger.error(f"❌ Query failed: {data_result.get('error')}")
                
                # Track failed orchestration
                if self.enable_monitoring and self.monitor:
                    self.monitor.track_orchestrator(
                        query=query,
                        total_time=time.time() - orchestration_start,
                        agents_used=agents_used,
                        overall_success=False,
                        response={'error': data_result.get('error')}
                    )
                
                return {
                    'success': False,
                    'error': data_result.get('error', 'Unknown error'),
                    'sql': data_result.get('sql'),
                    'data': []
                }
            
            logger.info(f"✅ Query successful, {len(data_result['data'])} rows")
            
            # Build response
            response = {
                'success': True,
                'data': data_result['data'],
                'sql': data_result.get('sql'),
                'metadata': data_result.get('metadata', {})
            }
            
            # ================================================================
            # STEP 2: BENCHMARK AGENT (HYBRID - Database → LLM → Hardcoded)
            # ================================================================
            benchmarks = None
            if with_benchmarks:
                logger.info("📊 Step 2: Fetching benchmarks with BenchmarkAgent (Hybrid)")
                benchmark_start = time.time()
                
                try:
                    benchmarks = self.benchmark_agent.process(
                        query=query,
                        data=data_result['data']
                    )
                    benchmark_time = time.time() - benchmark_start
                    
                    # Monitor based on source used
                    if self.enable_monitoring and self.monitor:
                        source = benchmarks.get('source', 'unknown')
                        
                        # If LLM was used, track as AI agent
                        if source == 'llm':
                            # 🔧 FIX: Serialize benchmarks
                            serialized_benchmarks = self._serialize_for_json(benchmarks)
                            self.monitor.track_ai_agent(
                                agent_name='BenchmarkAgent',
                                query=query,
                                response=serialized_benchmarks,
                                context=[f"Metric: {benchmarks.get('metric')}"],
                                execution_time=benchmark_time
                            )
                        # If database was used, track as internal agent
                        else:
                            self.monitor.track_internal_agent(
                                agent_name='BenchmarkAgent',
                                operation='fetch_benchmark',
                                input_data={'query': query},
                                output_data=benchmarks,
                                execution_time=benchmark_time,
                                success=True
                            )
                    
                    response['benchmarks'] = benchmarks
                    agents_used.append('BenchmarkAgent')
                    logger.info(f"✅ Benchmarks fetched ({source})")
                    
                except Exception as e:
                    benchmark_time = time.time() - benchmark_start
                    logger.warning(f"⚠️ Benchmark generation failed: {e}")
                    
                    if self.enable_monitoring and self.monitor:
                        self.monitor.track_ai_agent(
                            agent_name='BenchmarkAgent',
                            query=query,
                            response={'success': False, 'error': str(e)},
                            execution_time=benchmark_time
                        )
                    
                    # Don't fail entire query if benchmarks fail
                    response['benchmark_error'] = str(e)
            
            # ================================================================
            # STEP 3: INSIGHT AGENT (AI - LLM for insights)
            # ================================================================
            if with_insights and len(data_result['data']) > 0:
                logger.info("💡 Step 3: Generating insights with InsightAgent (AI)")
                insight_start = time.time()
                
                try:
                    insights = self.insight_agent.process(
                        query=query,
                        data=data_result['data'],
                        benchmarks=benchmarks
                    )
                    insight_time = time.time() - insight_start
                    
                    # Monitor AI agent
                    # 🔧 FIX: Serialize data before passing to monitor
                    if self.enable_monitoring and self.monitor:
                        serialized_insight_response = self._serialize_for_json({
                            'success': True,
                            'insights': insights
                        })
                        self.monitor.track_ai_agent(
                            agent_name='InsightAgent',
                            query=query,
                            response=serialized_insight_response,
                            context=[
                                data_result.get('sql', ''),
                                benchmarks.get('context', '') if benchmarks else ''
                            ],
                            execution_time=insight_time
                        )
                    
                    response['insights'] = insights
                    agents_used.append('InsightAgent')
                    logger.info(f"✅ Insights generated ({len(insights)} chars)")
                    
                except Exception as e:
                    insight_time = time.time() - insight_start
                    logger.error(f"❌ Insight generation failed: {e}")
                    
                    if self.enable_monitoring and self.monitor:
                        self.monitor.track_ai_agent(
                            agent_name='InsightAgent',
                            query=query,
                            response={'success': False, 'error': str(e)},
                            execution_time=insight_time
                        )
                    
                    # Don't fail entire query if insights fail
                    response['insights_error'] = str(e)
            
            # ================================================================
            # STEP 4: VISUALIZATION AGENT (INTERNAL - Rule-based)
            # ================================================================
            if with_viz and len(data_result['data']) > 0:
                logger.info("📈 Step 4: Creating visualization with VisualizationAgent (Internal)")
                viz_start = time.time()
                
                try:
                    fig = self.viz_agent.create_visualization(
                        data=data_result['data'],
                        question=query
                    )
                    viz_time = time.time() - viz_start
                    
                    # Monitor internal agent (traditional metrics)
                    if self.enable_monitoring and self.monitor:
                        self.monitor.track_internal_agent(
                            agent_name='VisualizationAgent',
                            operation='create_visualization',
                            input_data=data_result['data'],
                            output_data=fig,
                            execution_time=viz_time,
                            success=fig is not None
                        )
                    
                    if fig:
                        response['visualization'] = fig
                        agents_used.append('VisualizationAgent')
                        logger.info("✅ Visualization created")
                    else:
                        logger.warning("⚠️ Visualization returned None")
                        
                except Exception as e:
                    viz_time = time.time() - viz_start
                    logger.warning(f"⚠️ Visualization failed: {e}")
                    
                    if self.enable_monitoring and self.monitor:
                        self.monitor.track_internal_agent(
                            agent_name='VisualizationAgent',
                            operation='create_visualization',
                            input_data=data_result['data'],
                            output_data=None,
                            execution_time=viz_time,
                            success=False,
                            error=str(e)
                        )
            
            # ================================================================
            # TRACK OVERALL ORCHESTRATION
            # ================================================================
            total_time = time.time() - orchestration_start
            
            if self.enable_monitoring and self.monitor:
                # 🔧 FIX: Serialize response before tracking
                serialized_response = self._serialize_for_json(response)
                self.monitor.track_orchestrator(
                    query=query,
                    total_time=total_time,
                    agents_used=agents_used,
                    overall_success=True,
                    response=serialized_response
                )
            
            logger.info(f"✅ Query processing complete: {total_time:.2f}s, {len(agents_used)} agents")
            
            return response
            
        except Exception as e:
            total_time = time.time() - orchestration_start
            logger.error(f"❌ Orchestration failed: {e}")
            
            # Track failed orchestration
            if self.enable_monitoring and self.monitor:
                self.monitor.track_orchestrator(
                    query=query,
                    total_time=total_time,
                    agents_used=agents_used,
                    overall_success=False,
                    response={'error': str(e)}
                )
            
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'agents_used': agents_used
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get status including monitoring stats"""
        
        try:
            # Access the monitor
            if self.monitor:
                dashboard_data = self.monitor.get_dashboard_data()
                
                return {
                    'initialized': True,
                    'monitoring_enabled': self.enable_monitoring,
                    'monitoring_stats': {
                        'total_queries': dashboard_data.get('total_queries', 0),
                        'total_agent_calls': dashboard_data.get('total_agent_calls', 0),
                        'ai_agent_calls': dashboard_data.get('ai_agent_calls', 0),
                        'internal_agent_calls': dashboard_data.get('internal_agent_calls', 0),
                        'avg_query_time': dashboard_data.get('avg_query_time', 0),
                        'success_rate': dashboard_data.get('success_rate', 0)
                    }
                }
            else:
                return {
                    'initialized': True,
                    'monitoring_enabled': False,
                    'monitoring_stats': {
                        'total_queries': 0,
                        'avg_query_time': 0,
                        'success_rate': 0
                    }
                }
        
        except Exception as e:
            logger.warning(f"Failed to get status: {e}")
            return {
                'initialized': False,
                'error': str(e),
                'monitoring_stats': {
                    'total_queries': 0,
                    'avg_query_time': 0,
                    'success_rate': 0
                }
            }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report across all agents
        
        Returns:
            Dict with performance metrics for each agent type
        """
        if not self.enable_monitoring or not self.monitor:
            return {'error': 'Monitoring not enabled'}
        
        report = {
            'timestamp': time.time(),
            'ai_agents': {},
            'internal_agents': {},
            'orchestrator': {}
        }
        
        # AI Agents (with TruLens metrics)
        for agent_name in ['DataAgent', 'InsightAgent', 'BenchmarkAgent']:
            stats = self.monitor.get_agent_stats(agent_name)
            if stats:
                report['ai_agents'][agent_name] = stats
        
        # Internal Agents (traditional metrics)
        viz_stats = self.monitor.get_agent_stats('VisualizationAgent')
        if viz_stats:
            report['internal_agents']['VisualizationAgent'] = viz_stats
        
        # Orchestrator stats
        report['orchestrator'] = self.monitor.get_dashboard_data()
        
        return report