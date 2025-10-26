"""
Monitoring module - Agent performance tracking and evaluation
Provides factory function to get appropriate monitor based on mode
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Import main monitoring class
from .agent_monitor import AgentMonitor

# Import Cortex evaluator
try:
    from .cortex_evaluator import CortexEvaluator
    logger.info("✅ CortexEvaluator available")
except ImportError as e:
    CortexEvaluator = None
    logger.warning(f"⚠️ CortexEvaluator not available: {e}")

# Import TruLens-based monitor (optional)
try:
    from .agent_monitor_truelens import AgentMonitorTrueLens
    logger.info("✅ AgentMonitorTrueLens available")
except ImportError as e:
    AgentMonitorTrueLens = None
    logger.debug(f"AgentMonitorTrueLens not available: {e}")

# Import TruLens setup (evaluator) (optional)
try:
    from .trulens_setup import AgentEvaluator
    logger.info("✅ TruLens AgentEvaluator available")
except ImportError as e:
    AgentEvaluator = None
    logger.debug(f"TruLens AgentEvaluator not available: {e}")

# Import monitoring config if available (optional)
try:
    from ..config.monitoring_config import MonitoringMode, MonitoringConfig
    logger.info("✅ MonitoringConfig available")
except ImportError:
    logger.debug("MonitoringConfig not available - using defaults")
    MonitoringMode = None
    MonitoringConfig = None


def get_agent_monitor(mode: str = "BASIC", session=None):
    """
    Factory function to get appropriate agent monitor based on mode
    
    Args:
        mode: Monitoring mode - "BASIC", "CORTEX", or "TRULENS"
        session: Snowflake session (required for Cortex mode)
    
    Returns:
        AgentMonitor, AgentMonitorTrueLens, or None
    
    Examples:
        # Basic monitoring (no evaluation)
        monitor = get_agent_monitor("BASIC")
        
        # Cortex monitoring (FREE, on-platform)
        monitor = get_agent_monitor("CORTEX", session=snowflake_session)
        
        # TruLens monitoring (Premium)
        monitor = get_agent_monitor("TRULENS")
    """
    
    mode = mode.upper()
    
    # MODE 1: BASIC (No evaluation)
    if mode == "BASIC":
        logger.info("📊 Using BASIC monitoring (no evaluation)")
        return AgentMonitor(session=session, use_cortex_eval=False)
    
    # MODE 2: CORTEX (FREE, on-platform)
    elif mode == "CORTEX":
        if not session:
            logger.warning("⚠️ Cortex mode requires Snowflake session, falling back to BASIC")
            return AgentMonitor(session=None, use_cortex_eval=False)
        
        if not CortexEvaluator:
            logger.warning("⚠️ CortexEvaluator not available, falling back to BASIC")
            return AgentMonitor(session=session, use_cortex_eval=False)
        
        logger.info("📊 Using CORTEX monitoring (FREE, Snowflake Cortex LLM)")
        return AgentMonitor(session=session, use_cortex_eval=True)
    
    # MODE 3: TRULENS (Premium, external LLM)
    elif mode == "TRULENS":
        if not AgentMonitorTrueLens:
            logger.warning("⚠️ TruLens not available, falling back to BASIC")
            return AgentMonitor(session=session, use_cortex_eval=False)
        
        logger.info("📊 Using TRULENS monitoring (Premium, OpenAI LLM)")
        return AgentMonitorTrueLens(use_trulens_eval=True)
    
    # Default: BASIC
    else:
        logger.warning(f"⚠️ Unknown monitoring mode '{mode}', using BASIC")
        return AgentMonitor(session=session, use_cortex_eval=False)


def get_monitoring_mode():
    """Get current monitoring mode from config if available"""
    if MonitoringConfig:
        try:
            return MonitoringConfig.get_mode()
        except Exception as e:
            logger.warning(f"⚠️ Failed to get mode from config: {e}")
    return "BASIC"


__all__ = [
    'AgentMonitor',
    'AgentMonitorTrueLens',
    'CortexEvaluator',
    'AgentEvaluator',
    'MonitoringMode',
    'MonitoringConfig',
    'get_agent_monitor',
    'get_monitoring_mode'
]

logger.info("✅ Monitoring module initialized with get_agent_monitor factory")