"""
Monitoring configuration - Easy switching between TruLens and Cortex
"""

import os
from enum import Enum

class MonitoringMode(Enum):
    """Monitoring system options"""
    NONE = "none"           # No evaluation
    BASIC = "basic"         # Basic metrics only
    CORTEX = "cortex"       # Snowflake Cortex evaluation
    TRULENS = "trulens"     # TruLens evaluation

class MonitoringConfig:
    """Centralized monitoring configuration"""
    
    # Default mode - change this to switch systems
    MODE = MonitoringMode.CORTEX  # ← Change here to switch
    
    # TruLens settings (only used if MODE = TRULENS)
    TRULENS_ENABLED = False
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Cortex evaluation settings (only used if MODE = CORTEX)
    CORTEX_EVAL_ENABLED = True
    CORTEX_MODEL = 'mistral-large'
    
    # Basic settings
    TRACK_PERFORMANCE = True
    TRACK_ERRORS = True
    EXPORT_METRICS = True
    
    @classmethod
    def get_mode(cls) -> MonitoringMode:
        """Get current monitoring mode"""
        return cls.MODE
    
    @classmethod
    def is_trulens_enabled(cls) -> bool:
        """Check if TruLens should be used"""
        return cls.MODE == MonitoringMode.TRULENS and cls.TRULENS_ENABLED
    
    @classmethod
    def is_cortex_enabled(cls) -> bool:
        """Check if Cortex evaluation should be used"""
        return cls.MODE == MonitoringMode.CORTEX and cls.CORTEX_EVAL_ENABLED
    
    @classmethod
    def switch_to_trulens(cls):
        """Switch to TruLens monitoring"""
        cls.MODE = MonitoringMode.TRULENS
        print("✅ Switched to TruLens monitoring")
    
    @classmethod
    def switch_to_cortex(cls):
        """Switch to Cortex monitoring"""
        cls.MODE = MonitoringMode.CORTEX
        print("✅ Switched to Cortex monitoring")
    
    @classmethod
    def switch_to_basic(cls):
        """Switch to basic monitoring (no evaluation)"""
        cls.MODE = MonitoringMode.BASIC
        print("✅ Switched to basic monitoring")