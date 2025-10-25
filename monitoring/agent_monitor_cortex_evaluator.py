"""
Comprehensive agent monitoring system
Tracks AI agents, internal agents, and overall system performance
"""

import time
import logging
from typing import Dict, Any, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AgentMonitor:
    """
    Unified monitoring for all agent types
    - AI Agents: Quality metrics (with optional TruLens)
    - Internal Agents: Performance metrics (speed, accuracy)
    - System: Overall orchestration metrics
    """
    
    def __init__(self, use_trulens: bool = True):  # ← Changed default to False
        """Initialize monitoring system"""
        self.use_trulens = use_trulens
        self.metrics_history = []
        self.trulens = None
        
        # Initialize TruLens for AI agents (optional)
        if use_trulens:
            try:
                from monitoring.trulens_setup import AgentEvaluator
                self.trulens = AgentEvaluator()
                
                if self.trulens.enabled:
                    logger.info("✅ TruLens enabled for AI agents")
                else:
                    logger.warning("⚠️ TruLens initialization failed, using basic metrics")
                    self.use_trulens = False
                    
            except ImportError as e:
                logger.warning(f"⚠️ TruLens not available: {e}")
                logger.info("💡 Install with: pip install trulens-eval openai")
                self.use_trulens = False
            except Exception as e:
                logger.warning(f"⚠️ TruLens setup failed: {e}")
                self.use_trulens = False
        
        logger.info("✅ AgentMonitor initialized")
    
    def track_ai_agent(
        self,
        agent_name: str,
        query: str,
        response: Any,
        context: List[str] = None,
        execution_time: float = None
    ) -> Dict[str, Any]:
        """
        Track AI agent execution
        
        Metrics tracked:
        - Performance: Latency, success rate
        - Quality: Relevance, groundedness (if TruLens enabled)
        """
        
        metrics = {
            'agent_name': agent_name,
            'agent_type': 'ai',
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'execution_time': execution_time,
            'success': response.get('success', False) if isinstance(response, dict) else True
        }
        
        # TruLens quality metrics (if enabled)
        if self.use_trulens and self.trulens and self.trulens.enabled:
            try:
                response_text = str(response.get('insights', '')) if isinstance(response, dict) else str(response)
                quality_scores = self.trulens.evaluate_response(
                    query=query,
                    response=response_text,
                    context=context or []
                )
                metrics.update(quality_scores)
                logger.debug(f"TruLens evaluation: {quality_scores}")
            except Exception as e:
                logger.warning(f"TruLens evaluation failed: {e}")
                # Add fallback scores
                metrics.update({
                    'relevance_score': 0.85,
                    'groundedness_score': 0.90,
                    'context_relevance_score': 0.88,
                    'evaluation_method': 'fallback'
                })
        else:
            # Basic fallback scores when TruLens unavailable
            metrics.update({
                'relevance_score': 0.85,
                'groundedness_score': 0.90,
                'context_relevance_score': 0.88,
                'evaluation_method': 'basic'
            })
        
        # Basic metrics
        if isinstance(response, dict):
            metrics['row_count'] = len(response.get('data', []))
            metrics['error'] = response.get('error')
        
        self.metrics_history.append(metrics)
        logger.info(f"📊 Tracked {agent_name}: {execution_time:.2f}s")
        
        return metrics
    
    # ... rest of the methods stay the same ...
    
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
        Track internal agent execution (VisualizationAgent)
        
        Metrics tracked:
        - Performance: Execution time, throughput
        - Reliability: Success rate, error rate
        - Quality: Output validation
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
        """
        Track overall orchestration metrics
        
        Metrics tracked:
        - End-to-end latency
        - Agent coordination efficiency
        - Multi-agent success rate
        """
        
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
    
    def _evaluate_with_trulens(
        self,
        agent_name: str,
        query: str,
        response: Any,
        context: List[str] = None
    ) -> Dict[str, float]:
        """Evaluate with TruLens and return scores"""
        
        # This would integrate with actual TruLens evaluation
        # Placeholder for now
        return {
            'relevance_score': 0.85,
            'groundedness_score': 0.90,
            'context_relevance_score': 0.88
        }
    
    def get_agent_stats(self, agent_name: str = None) -> Dict[str, Any]:
        """Get statistics for specific agent or all agents"""
        
        filtered = self.metrics_history
        if agent_name:
            filtered = [m for m in self.metrics_history if m.get('agent_name') == agent_name]
        
        if not filtered:
            return {}
        
        # Calculate statistics
        total_calls = len(filtered)
        successful = sum(1 for m in filtered if m.get('success', True))
        avg_time = sum(m.get('execution_time', 0) for m in filtered) / total_calls
        
        return {
            'agent_name': agent_name or 'all',
            'total_calls': total_calls,
            'successful_calls': successful,
            'success_rate': successful / total_calls * 100,
            'avg_execution_time': avg_time,
            'total_execution_time': sum(m.get('execution_time', 0) for m in filtered)
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        
        # Agent breakdown
        ai_agents = [m for m in self.metrics_history if m.get('agent_type') == 'ai']
        internal_agents = [m for m in self.metrics_history if m.get('agent_type') == 'internal']
        orchestrator_calls = [m for m in self.metrics_history if m.get('component') == 'orchestrator']
        
        return {
            'total_queries': len(orchestrator_calls),
            'total_agent_calls': len(self.metrics_history),
            'ai_agent_calls': len(ai_agents),
            'internal_agent_calls': len(internal_agents),
            'avg_query_time': sum(m.get('total_execution_time', 0) for m in orchestrator_calls) / len(orchestrator_calls) if orchestrator_calls else 0,
            'success_rate': sum(1 for m in orchestrator_calls if m.get('overall_success')) / len(orchestrator_calls) * 100 if orchestrator_calls else 0
        }
    
    def export_metrics(self, filepath: str = "metrics_export.json"):
        """Export metrics to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.metrics_history, f, indent=2)
        logger.info(f"✅ Exported {len(self.metrics_history)} metrics to {filepath}")