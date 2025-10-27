"""
Agent Monitor - Tracks AI and internal agent performance
Provides monitoring for multi-agent orchestration with optional Cortex evaluation
UPDATED: Includes metrics_history for dashboard compatibility
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class AgentMonitor:
    """
    Monitor for tracking agent performance and orchestration metrics
    
    Supports multiple evaluation modes:
    - BASIC: No LLM evaluation, just performance tracking
    - CORTEX: Uses Snowflake Cortex for FREE LLM evaluation
    
    Tracks:
    - AI agents (DataAgent, InsightAgent, BenchmarkAgent)
    - Internal agents (VisualizationAgent)
    - Overall orchestration performance
    """
    
    def __init__(self, session=None, use_cortex_eval=False):
        """
        Initialize AgentMonitor
        
        Args:
            session: Snowflake session (required if use_cortex_eval=True)
            use_cortex_eval: Whether to use Cortex for LLM response evaluation
        """
        self.session = session
        self.use_cortex_eval = use_cortex_eval
        self.evaluator = None
        
        # Initialize Cortex evaluator if requested
        if use_cortex_eval:
            if not session:
                logger.warning("⚠️ Cortex evaluation requested but no session provided")
                self.use_cortex_eval = False
            else:
                try:
                    from .cortex_evaluator import CortexEvaluator
                    self.evaluator = CortexEvaluator(session)
                    logger.info("✅ AgentMonitor initialized with Cortex evaluation")
                except ImportError as e:
                    logger.warning(f"⚠️ Could not import CortexEvaluator: {e}")
                    self.use_cortex_eval = False
                except Exception as e:
                    logger.warning(f"⚠️ Could not initialize CortexEvaluator: {e}")
                    self.use_cortex_eval = False
        
        # Storage for metrics
        self.ai_agent_calls = []
        self.internal_agent_calls = []
        self.orchestrator_calls = []
        
        # ✅ NEW: Metrics history for dashboard time-series charts
        self.metrics_history = []
        
        # Summary statistics
        self.stats = {
            'total_queries': 0,
            'total_agent_calls': 0,
            'ai_agent_calls': 0,
            'internal_agent_calls': 0,
            'success_count': 0,
            'failure_count': 0
        }
        
        if not use_cortex_eval:
            logger.info("✅ AgentMonitor initialized (BASIC mode - no evaluation)")
    
    def track_ai_agent(
        self,
        agent_name: str,
        query: str,
        response: Dict[str, Any],
        context: List[str] = None,
        execution_time: float = 0
    ):
        """
        Track an AI agent call (LLM-based agents)
        
        Args:
            agent_name: Name of the agent (e.g., 'DataAgent', 'InsightAgent')
            query: User query
            response: Agent response
            context: Additional context (SQL, data, etc.)
            execution_time: Time taken in seconds
        """
        try:
            # Extract response text for evaluation
            response_text = ""
            if isinstance(response, dict):
                # Try to get text from various possible keys
                response_text = (
                    response.get('insights', '') or 
                    response.get('text', '') or 
                    str(response.get('data', ''))[:500]  # First 500 chars of data
                )
            else:
                response_text = str(response)
            
            call_record = {
                'timestamp': datetime.now().isoformat(),
                'agent_name': agent_name,
                'query': query,
                'response': response,
                'context': context or [],
                'execution_time': execution_time,
                'success': response.get('success', True) if isinstance(response, dict) else True
            }
            
            # Optionally evaluate with Cortex
            if self.use_cortex_eval and self.evaluator and response_text:
                try:
                    eval_result = self.evaluator.evaluate_quality(
                        query=query,
                        response=response_text,
                        context=context
                    )
                    call_record['evaluation'] = eval_result
                    logger.debug(f"📊 Evaluated {agent_name}: {eval_result.get('overall_score', 0):.2f}")
                except Exception as e:
                    logger.warning(f"⚠️ Evaluation failed for {agent_name}: {e}")
            
            self.ai_agent_calls.append(call_record)
            self.stats['total_agent_calls'] += 1
            self.stats['ai_agent_calls'] += 1
            
            if call_record['success']:
                self.stats['success_count'] += 1
            else:
                self.stats['failure_count'] += 1
            
            # ✅ NEW: Add to metrics history for time-series tracking
            self._update_metrics_history(agent_name, execution_time, call_record.get('evaluation'))
            
            logger.debug(f"📊 Tracked AI agent: {agent_name} ({execution_time:.2f}s)")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to track AI agent: {e}")
    
    def track_internal_agent(
        self,
        agent_name: str,
        operation: str,
        input_data: Any,
        output_data: Any,
        execution_time: float = 0,
        success: bool = True,
        error: str = None
    ):
        """
        Track an internal agent call (rule-based agents)
        
        Args:
            agent_name: Name of the agent (e.g., 'VisualizationAgent')
            operation: Operation performed
            input_data: Input data
            output_data: Output data
            execution_time: Time taken in seconds
            success: Whether the operation succeeded
            error: Error message if failed
        """
        try:
            call_record = {
                'timestamp': datetime.now().isoformat(),
                'agent_name': agent_name,
                'operation': operation,
                'execution_time': execution_time,
                'success': success,
                'error': error
            }
            
            self.internal_agent_calls.append(call_record)
            self.stats['total_agent_calls'] += 1
            self.stats['internal_agent_calls'] += 1
            
            if success:
                self.stats['success_count'] += 1
            else:
                self.stats['failure_count'] += 1
            
            # ✅ NEW: Add to metrics history
            self._update_metrics_history(agent_name, execution_time, None)
            
            logger.debug(f"📊 Tracked internal agent: {agent_name}.{operation} ({execution_time:.2f}s)")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to track internal agent: {e}")
    
    def track_orchestrator(
        self,
        query: str,
        total_time: float,
        agents_used: List[str],
        overall_success: bool,
        response: Dict[str, Any]
    ):
        """
        Track overall orchestration metrics
        
        Args:
            query: User query
            total_time: Total execution time
            agents_used: List of agents that were called
            overall_success: Whether the orchestration succeeded
            response: Final response
        """
        try:
            call_record = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'total_time': total_time,
                'agents_used': agents_used,
                'num_agents': len(agents_used),
                'overall_success': overall_success,
                'response': response
            }
            
            self.orchestrator_calls.append(call_record)
            self.stats['total_queries'] += 1
            
            logger.debug(f"📊 Tracked orchestration: {len(agents_used)} agents, {total_time:.2f}s")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to track orchestration: {e}")
    
    def _update_metrics_history(self, agent_name: str, execution_time: float, evaluation: Dict = None):
        """
        ✅ NEW: Update metrics history for time-series tracking
        
        Args:
            agent_name: Name of the agent
            execution_time: Execution time in seconds
            evaluation: Optional evaluation results
        """
        history_entry = {
            'timestamp': datetime.now(),
            'agent_name': agent_name,
            'execution_time': execution_time,
        }
        
        # Add evaluation scores if available
        if evaluation:
            history_entry['relevance_score'] = evaluation.get('relevance_score', 0)
            history_entry['groundedness_score'] = evaluation.get('groundedness_score', 0)
            history_entry['coherence_score'] = evaluation.get('coherence_score', 0)
            history_entry['overall_score'] = evaluation.get('overall_score', 0)
        
        self.metrics_history.append(history_entry)
        
        # Keep only last 100 entries to prevent memory issues
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
    
    def get_agent_stats(self, agent_name: str = None) -> Dict[str, Any]:
        """
        Get statistics for a specific agent or all agents
        
        Args:
            agent_name: Name of agent (optional, None for all)
            
        Returns:
            Dict with agent statistics
        """
        if agent_name:
            # Filter for specific agent
            ai_calls = [c for c in self.ai_agent_calls if c['agent_name'] == agent_name]
            internal_calls = [c for c in self.internal_agent_calls if c['agent_name'] == agent_name]
            all_calls = ai_calls + internal_calls
            
            if not all_calls:
                return {}
            
            total_time = sum(c['execution_time'] for c in all_calls)
            avg_time = total_time / len(all_calls) if all_calls else 0
            success_rate = sum(1 for c in all_calls if c.get('success', True)) / len(all_calls) if all_calls else 0
            
            stats = {
                'agent_name': agent_name,
                'total_calls': len(all_calls),
                'total_time': round(total_time, 2),
                'avg_time': round(avg_time, 2),
                'success_rate': round(success_rate, 2)
            }
            
            # Add average evaluation scores if available
            if self.use_cortex_eval:
                evaluations = [c.get('evaluation') for c in ai_calls if c.get('evaluation')]
                if evaluations:
                    avg_relevance = sum(e.get('relevance_score', 0) for e in evaluations) / len(evaluations)
                    avg_groundedness = sum(e.get('groundedness_score', 0) for e in evaluations) / len(evaluations)
                    avg_coherence = sum(e.get('coherence_score', 0) for e in evaluations) / len(evaluations)
                    avg_overall = sum(e.get('overall_score', 0) for e in evaluations) / len(evaluations)
                    
                    stats['avg_quality_scores'] = {
                        'relevance': round(avg_relevance, 2),
                        'groundedness': round(avg_groundedness, 2),
                        'coherence': round(avg_coherence, 2),
                        'overall': round(avg_overall, 2)
                    }
            
            return stats
        else:
            # Return overall stats
            return self.stats.copy()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data
        
        Returns:
            Dict with all monitoring metrics
        """
        total_time = sum(c['total_time'] for c in self.orchestrator_calls)
        avg_query_time = total_time / len(self.orchestrator_calls) if self.orchestrator_calls else 0
        
        success_rate = (self.stats['success_count'] / 
                       max(self.stats['total_agent_calls'], 1))
        
        # Get per-agent statistics
        agent_stats = {}
        all_agents = set(
            [c['agent_name'] for c in self.ai_agent_calls] +
            [c['agent_name'] for c in self.internal_agent_calls]
        )
        
        for agent in all_agents:
            agent_stats[agent] = self.get_agent_stats(agent)
        
        dashboard = {
            'total_queries': self.stats['total_queries'],
            'total_agent_calls': self.stats['total_agent_calls'],
            'ai_agent_calls': self.stats['ai_agent_calls'],
            'internal_agent_calls': self.stats['internal_agent_calls'],
            'success_count': self.stats['success_count'],
            'failure_count': self.stats['failure_count'],
            'success_rate': round(success_rate, 2),
            'avg_query_time': round(avg_query_time, 2),
            'agent_stats': agent_stats,
            'recent_queries': self.orchestrator_calls[-10:] if self.orchestrator_calls else [],
            'monitoring_mode': 'CORTEX' if self.use_cortex_eval else 'BASIC'
        }
        
        return dashboard
    
    def reset(self):
        """Reset all monitoring data"""
        self.ai_agent_calls = []
        self.internal_agent_calls = []
        self.orchestrator_calls = []
        self.metrics_history = []  # ✅ NEW: Reset metrics history too
        self.stats = {
            'total_queries': 0,
            'total_agent_calls': 0,
            'ai_agent_calls': 0,
            'internal_agent_calls': 0,
            'success_count': 0,
            'failure_count': 0
        }
        logger.info("🔄 Monitor reset")

logger.info("✅ AgentMonitor class defined")