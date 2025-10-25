"""
Monitoring package with automatic mode detection
Supports: Basic, Cortex, and TruLens monitoring
"""

import logging
from config.monitoring_config import MonitoringConfig, MonitoringMode

logger = logging.getLogger(__name__)

def get_agent_monitor(session=None):
    """
    Factory function to get appropriate monitor based on config
    
    Args:
        session: Snowflake session (for Cortex evaluation)
        
    Returns:
        AgentMonitor instance configured for current mode
    """
    
    mode = MonitoringConfig.get_mode()
    
    if mode == MonitoringMode.TRULENS:
        try:
            from monitoring.agent_monitoring import AgentMonitor
            return AgentMonitor(use_trulens=True)
        except ImportError:
            logger.warning("⚠️ TruLens not available, falling back to Cortex")
            mode = MonitoringMode.CORTEX
    
    if mode == MonitoringMode.CORTEX:
        from monitoring.agent_monitoring_cortex_evaluator import AgentMonitor
        return AgentMonitor(session=session, use_cortex_eval=True)
    
    # Default: Basic monitoring
    from monitoring.agent_monitoring_cortex_evaluator import AgentMonitor
    return AgentMonitor(session=session, use_cortex_eval=False)

__all__ = ['get_agent_monitor', 'MonitoringConfig', 'MonitoringMode']