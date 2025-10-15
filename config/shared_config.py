import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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
      self.config_dir = Path("config")
      
      # Load configurations
      self.snowflake = self._load_snowflake_config()
      self.agent_config = self._load_agent_config()
      self.semantic_model = self._load_semantic_model()
      
      logger.info("SharedConfig initialized")
  
  def _load_snowflake_config(self) -> Dict[str, str]:
      """Load Snowflake credentials from environment"""
      return {
          'account': os.getenv('SNOWFLAKE_ACCOUNT'),
          'user': os.getenv('SNOWFLAKE_USER'),
          'password': os.getenv('SNOWFLAKE_PASSWORD'),
          'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
          'database': os.getenv('SNOWFLAKE_DATABASE'),
          'schema': os.getenv('SNOWFLAKE_SCHEMA'),
          'role': os.getenv('SNOWFLAKE_ROLE')
      }
  
  def _load_agent_config(self) -> Dict[str, Any]:
      """Load agent configuration from YAML"""
      config_file = self.config_dir / "agent_config.yaml"
      
      if not config_file.exists():
          logger.warning(f"Agent config not found, using defaults")
          return self._default_agent_config()
      
      try:
          with open(config_file, 'r') as f:
              return yaml.safe_load(f)
      except Exception as e:
          logger.error(f"Error loading agent config: {e}")
          return self._default_agent_config()
  
  def _load_semantic_model(self) -> Dict[str, Any]:
      """Load semantic model from YAML"""
      config_file = self.config_dir / "marketing_semantic_model.yaml"
      
      if not config_file.exists():
          logger.warning(f"Semantic model not found, using defaults")
          return {}
      
      try:
          with open(config_file, 'r') as f:
              return yaml.safe_load(f)
      except Exception as e:
          logger.error(f"Error loading semantic model: {e}")
          return {}
  
  def _default_agent_config(self) -> Dict[str, Any]:
      """Default agent configuration"""
      return {
          'data_agent': {
              'model': 'cortex-analyst',
              'timeout': 30,
              'retry_attempts': 3
          },
          'visualization_agent': {
              'default_chart_type': 'plotly',
              'theme': 'plotly_white',
              'color_scheme': 'blues'
          },
          'insight_agent': {
              'model': 'llama3.1-70b',
              'temperature': 0.7,
              'max_tokens': 500
          }
      }
  
  def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
      """Get configuration for specific agent"""
      return self.agent_config.get(agent_name, {})
  
  def validate(self) -> bool:
      """Validate that required configurations are present"""
      required_sf_keys = ['account', 'user', 'password', 'warehouse']
      
      for key in required_sf_keys:
          if not self.snowflake.get(key):
              logger.error(f"Missing required Snowflake config: {key}")
              return False
      
      return True

# Example usage
if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  
  # Get config instance
  config = SharedConfig()
  
  # Validate
  if config.validate():
      print("✅ Configuration valid")
      print(f"Snowflake Account: {config.snowflake['account']}")
      print(f"Agent Config: {config.agent_config}")
  else:
      print("❌ Configuration invalid")
