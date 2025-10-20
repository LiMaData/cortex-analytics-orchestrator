"""
Shared configuration manager - Singleton pattern
Loads Snowflake credentials from .env file
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class SharedConfig:
    """
    Singleton configuration manager
    All orchestrators share the same config instance
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.config_dir = Path(__file__).parent  # Points to config/ directory
        
        # Load configurations
        self.snowflake = self._load_snowflake_config()
        self.agent_config = self._load_agent_config()
        self.semantic_model_stage = self._load_semantic_model_path()
        
        logger.info("SharedConfig initialized")
    
    def _load_snowflake_config(self) -> Dict[str, str]:
        """Load Snowflake credentials from environment variables"""
        config = {
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'user': os.getenv('SNOWFLAKE_USER'),
            'password': os.getenv('SNOWFLAKE_PASSWORD'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
            'database': os.getenv('SNOWFLAKE_DATABASE'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA'),
            'role': os.getenv('SNOWFLAKE_ROLE')
        }
        
        # Validate that all required configs are present
        missing = [k for k, v in config.items() if v is None]
        if missing:
            logger.warning(f"Missing Snowflake config values: {missing}")
            logger.warning("Make sure .env file exists with all SNOWFLAKE_* variables")
        
        return config
    
    def _load_semantic_model_path(self) -> str:
        """Load semantic model stage path from environment"""
        stage_path = os.getenv('SEMANTIC_MODEL_STAGE', '@semantic_models/marketing_semantic_model.yaml')
        
        if not stage_path:
            logger.warning("SEMANTIC_MODEL_STAGE not set, using default")
            stage_path = '@semantic_models/marketing_semantic_model.yaml'
        
        return stage_path
    
    def _load_agent_config(self) -> Dict[str, Any]:
        """Load agent configuration from YAML file"""
        config_file = self.config_dir / "agent_config.yaml"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    logger.info(f"Loaded agent config from {config_file}")
                    return config or {}
            except Exception as e:
                logger.warning(f"Failed to load agent config from {config_file}: {e}")
                return self._default_agent_config()
        else:
            logger.warning(f"Agent config file not found: {config_file}")
            logger.info("Using default agent configuration")
            return self._default_agent_config()
    
    def _default_agent_config(self) -> Dict[str, Any]:
        """Default agent configuration if YAML file is missing"""
        return {
            'data_agent': {
                'enabled': True,
                'cache_ttl': 3600,  # 1 hour
                'max_retries': 3
            },
            'visualization_agent': {
                'enabled': True,
                'default_chart_type': 'auto',
                'chart_height': 600
            },
            'insight_agent': {
                'enabled': True,
                'model': 'mistral-large',
                'max_insights': 5
            },
            'benchmark_agent': {
                'enabled': False,  # Not implemented yet
                'web_search_enabled': False
            },
            'distribution_agent': {
                'enabled': False  # Not implemented yet
            }
        }
    
    def get_agent_setting(self, agent_name: str, setting: str, default: Any = None) -> Any:
        """
        Get a specific setting for an agent
        
        Args:
            agent_name: Name of the agent (e.g., 'data_agent')
            setting: Setting key (e.g., 'cache_ttl')
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        return self.agent_config.get(agent_name, {}).get(setting, default)
    
    def validate(self) -> bool:
        """
        Validate that all required configuration is present
        
        Returns:
            True if valid, False otherwise
        """
        required_snowflake_keys = ['account', 'user', 'password', 'warehouse', 'database', 'schema']
        
        missing = []
        for key in required_snowflake_keys:
            if not self.snowflake.get(key):
                missing.append(key)
        
        if missing:
            logger.error(f"Missing required Snowflake configuration: {missing}")
            logger.error("Please create a .env file with all SNOWFLAKE_* variables")
            return False
        
        if not self.semantic_model_stage:
            logger.warning("Semantic model stage path not configured")
        
        logger.info("✅ Configuration validation passed")
        return True
    
    def __repr__(self):
        """String representation (hiding password)"""
        safe_config = {k: v if k != 'password' else '***' for k, v in self.snowflake.items()}
        return f"SharedConfig(snowflake={safe_config}, semantic_model={self.semantic_model_stage})"


# Convenience function for testing
def test_config():
    """Test function to validate configuration"""
    config = SharedConfig()
    
    print("🔍 Configuration Status:")
    print(f"   Config directory: {config.config_dir}")
    print(f"   Snowflake account: {config.snowflake.get('account')}")
    print(f"   Snowflake user: {config.snowflake.get('user')}")
    print(f"   Snowflake database: {config.snowflake.get('database')}")
    print(f"   Semantic model: {config.semantic_model_stage}")
    print(f"\n   Agent config keys: {list(config.agent_config.keys())}")
    
    is_valid = config.validate()
    
    if is_valid:
        print("\n✅ Configuration is valid and ready to use!")
    else:
        print("\n❌ Configuration has errors - check logs above")
    
    return is_valid


if __name__ == "__main__":
    # Run test when executed directly
    test_config()