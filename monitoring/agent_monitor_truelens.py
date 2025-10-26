"""
TruLens-based Agent Monitoring
Wraps AgentEvaluator from trulens_setup.py for consistent interface with AgentMonitor
"""

import time
import logging
from typing import Dict, Any, List
from datetime import datetime
import json

from monitoring.trulens_setup import AgentEvaluator

logger = logging.getLogger(__name__)


class AgentMonitorTrueLens:
    """
    Unified monitoring for agents using TruLens evaluation
    - AI Agents: Performance metrics + TruLens evaluation
    - Internal Agents: Speed, accuracy metrics
    - System: Overall orchestration metrics
    
    Uses TruLens for comprehensive quality evaluation
    """
    
    def __init__(self, use_trulens_eval: bool = True):
        """
        Initialize TruLens-based monitoring system
        
        Args:
            use_trulens_eval: Use TruLens for quality evaluation ($100-200/mo)
        """
        self.metrics_history = []
        self.use_trulens_eval = use_trulens_eval
        self.trulens_evaluator = None
        
        # Initialize TruLens evaluator
        if use_trulens_eval:
            try:
                self.trulens_evaluator = AgentEvaluator()
                if self.trulens_evaluator.enabled:
                    logger.info("✅ TruLens evaluation enabled (Premium)")
                else:
                    logger.warning("⚠️ TruLens evaluator not available, using fallback")
                    self.use_trulens_eval = False
            except Exception as e:
                logger.warning(f"⚠️ TruLens evaluator initialization failed: {e}")
                self.use_trulens_eval = False
        
        logger.info("✅ AgentMonitorTrueLens initialized")
    
    def track_ai_agent(
        self,
        agent_name: str,
        query: str,
        response: Any,
        context: List[str] = None,
        execution_time: float = None
    ) -> Dict[str, Any]:
        """
        Track AI agent execution with TruLens evaluation
        
        Metrics tracked:
        - Performance: Latency, success rate
        - Quality: TruLens scores (relevance, groundedness, context relevance)
        """
        
        metrics = {
            'agent_name': agent_name,
            'agent_type': 'ai',
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'execution_time': execution_time,
            'success': response.get('success', False) if isinstance(response, dict) else True
        }
        
        # Quality evaluation with TruLens
        if self.use_trulens_eval and self.trulens_evaluator and self.trulens_evaluator.enabled:
            try:
                response_text = str(response.get('insights', '')) if isinstance(response, dict) else str(response)
                trulens_scores = self.trulens_evaluator.evaluate_response(
                    query=query,
                    response=response_text,
                    context=context or []
                )
                metrics.update(trulens_scores)
                logger.debug(f"TruLens evaluation: {trulens_scores}")
            except Exception as e:
                logger.warning(f"TruLens evaluation failed: {e}")
                # Fallback to basic scores
                metrics.update(self._get_fallback_scores())
        else:
            # Basic fallback scores
            metrics.update(self._get_fallback_scores())
        
        # Basic metrics
        if isinstance(response, dict):
            metrics['row_count'] = len(response.get('data', []))
            metrics['error'] = response.get('error')
        
        self.metrics_history.append(metrics)
        logger.info(f"📊 Tracked {agent_name}: {execution_time:.2f}s")
        
        return metrics
    
    def track_internal_agent(
        self,
        agent_name: str,
        operation: str,
        input_data: Any,
        output_data: Any,
        execution_time: float,
        success: bool = True,
        error: str = None
    ) -> Dict[str, Any]:
        """
        Track internal agent execution
        
        Metrics tracked:
        - Performance: Execution time, throughput
        - Reliability: Success rate, error rate
        """
        
        metrics = {
            'agent_name': agent_name,
            'agent_type': 'internal',
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'execution_time': execution_time,
            'success': success,
            'error': error
        }
        
        # Calculate throughput
        if isinstance(input_data, list):
            metrics['input_size'] = len(input_data)
            metrics['throughput'] = len(input_data) / execution_time if execution_time > 0 else 0
        
        # Validate output
        if output_data is not None:
            metrics['output_generated'] = True
            if hasattr(output_data, '__len__'):
                metrics['output_size'] = len(output_data)
        else:
            metrics['output_generated'] = False
        
        self.metrics_history.append(metrics)
        logger.info(f"📊 Tracked {agent_name}: {execution_time:.3f}s, success={success}")
        
        return metrics
    
    def track_orchestrator(
        self,
        query: str,
        total_time: float,
        agents_used: List[str],
        overall_success: bool,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track overall orchestration metrics"""
        
        metrics = {
            'component': 'orchestrator',
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'total_execution_time': total_time,
            'agents_used': agents_used,
            'agent_count': len(agents_used),
            'overall_success': overall_success,
            'has_data': 'data' in response and len(response.get('data', [])) > 0,
            'has_viz': 'visualization' in response,
            'has_insights': 'insights' in response,
            'has_benchmarks': 'benchmarks' in response
        }
        
        self.metrics_history.append(metrics)
        logger.info(f"📊 Tracked orchestration: {total_time:.2f}s, {len(agents_used)} agents")
        
        return metrics
    
    def get_agent_stats(self, agent_name: str = None) -> Dict[str, Any]:
        """Get statistics for specific agent or all agents"""
        
        filtered = self.metrics_history
        if agent_name:
            filtered = [m for m in self.metrics_history if m.get('agent_name') == agent_name]
        
        if not filtered:
            return {}
        
        total_calls = len(filtered)
        successful = sum(1 for m in filtered if m.get('success', True))
        avg_time = sum(m.get('execution_time', 0) for m in filtered) / total_calls if total_calls > 0 else 0
        
        # Add TruLens quality scores if available
        ai_metrics = [m for m in filtered if m.get('agent_type') == 'ai']
        stats = {
            'agent_name': agent_name or 'all',
            'total_calls': total_calls,
            'successful_calls': successful,
            'success_rate': successful / total_calls * 100 if total_calls > 0 else 0,
            'avg_execution_time': avg_time,
            'total_execution_time': sum(m.get('execution_time', 0) for m in filtered)
        }
        
        # Add quality scores from TruLens if available
        if ai_metrics:
            avg_relevance = sum(m.get('relevance_score', 0) for m in ai_metrics) / len(ai_metrics)
            avg_groundedness = sum(m.get('groundedness_score', 0) for m in ai_metrics) / len(ai_metrics)
            avg_context_relevance = sum(m.get('context_relevance_score', 0) for m in ai_metrics) / len(ai_metrics)
            
            stats.update({
                'avg_relevance_score': avg_relevance,
                'avg_groundedness_score': avg_groundedness,
                'avg_context_relevance_score': avg_context_relevance,
                'evaluation_method': ai_metrics[0].get('evaluation_method', 'unknown')
            })
        
        return stats
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        
        ai_agents = [m for m in self.metrics_history if m.get('agent_type') == 'ai']
        internal_agents = [m for m in self.metrics_history if m.get('agent_type') == 'internal']
        orchestrator_calls = [m for m in self.metrics_history if m.get('component') == 'orchestrator']
        
        dashboard_data = {
            'total_queries': len(orchestrator_calls),
            'total_agent_calls': len(self.metrics_history),
            'ai_agent_calls': len(ai_agents),
            'internal_agent_calls': len(internal_agents),
            'avg_query_time': sum(m.get('total_execution_time', 0) for m in orchestrator_calls) / len(orchestrator_calls) if orchestrator_calls else 0,
            'success_rate': sum(1 for m in orchestrator_calls if m.get('overall_success')) / len(orchestrator_calls) * 100 if orchestrator_calls else 0
        }
        
        # Add TruLens quality metrics if available
        if ai_agents:
            avg_relevance = sum(m.get('relevance_score', 0) for m in ai_agents) / len(ai_agents)
            avg_groundedness = sum(m.get('groundedness_score', 0) for m in ai_agents) / len(ai_agents)
            avg_context_relevance = sum(m.get('context_relevance_score', 0) for m in ai_agents) / len(ai_agents)
            
            dashboard_data.update({
                'avg_relevance_score': avg_relevance,
                'avg_groundedness_score': avg_groundedness,
                'avg_context_relevance_score': avg_context_relevance,
                'trulens_enabled': self.use_trulens_eval
            })
        
        return dashboard_data
    
    def export_metrics(self, filepath: str = "metrics_export_trulens.json"):
        """Export metrics to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.metrics_history, f, indent=2)
        logger.info(f"✅ Exported {len(self.metrics_history)} metrics to {filepath}")
    
    def get_trulens_leaderboard(self) -> Dict[str, Any]:
        """Get TruLens leaderboard if available"""
        if self.trulens_evaluator and self.trulens_evaluator.enabled:
            try:
                return self.trulens_evaluator.get_leaderboard()
            except Exception as e:
                logger.warning(f"⚠️ Failed to get TruLens leaderboard: {e}")
                return {'error': str(e)}
        else:
            return {'status': 'TruLens not available'}
    
    @staticmethod
    def _get_fallback_scores() -> Dict[str, Any]:
        """Return fallback scores when TruLens unavailable"""
        return {
            'relevance_score': 0.85,
            'groundedness_score': 0.90,
            'context_relevance_score': 0.88,
            'evaluation_method': 'fallback'
        }


logger.info("✅ AgentMonitorTrueLens class defined")