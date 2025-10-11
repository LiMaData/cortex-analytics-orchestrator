"""
Base Orchestrator
Provides shared initialization and utilities for all orchestrators
"""

import logging
from typing import Dict, Any, Optional
from shared.context_manager import SharedContextManager
from config.shared_config import SharedConfig

logger = logging.getLogger(__name__)

class BaseOrchestrator:
  """
  Base class for all orchestrators
  
  Provides:
  - Shared configuration
  - Shared context manager
  - Common utilities
  - Agent initialization framework
  """
  
  def __init__(self):
      """Initialize base orchestrator with shared components"""
      
      # Load shared configuration
      self.config = SharedConfig()
      
      # Validate configuration
      if not self.config.validate():
          raise ValueError("Invalid configuration. Check your .env file.")
      
      # Initialize shared context manager
      self.context = SharedContextManager()
      
      # Initialize agent registry
      self.agents: Dict[str, Any] = {}
      
      # Orchestrator metadata
      self.name = self.__class__.__name__
      self.mode = "base"
      
      logger.info(f"{self.name} initialized")
  
  def register_agent(self, agent_name: str, agent_instance: Any):
      """
      Register an agent with the orchestrator
      
      Args:
          agent_name: Unique identifier for the agent
          agent_instance: The agent instance
      """
      self.agents[agent_name] = agent_instance
      logger.debug(f"Registered agent: {agent_name}")
  
  def get_agent(self, agent_name: str) -> Optional[Any]:
      """
      Get agent by name
      
      Args:
          agent_name: Agent identifier
          
      Returns:
          Agent instance or None
      """
      return self.agents.get(agent_name)
  
  def _check_cache(self, query: str) -> Optional[Any]:
      """
      Check if query result is cached
      
      Args:
          query: Query string
          
      Returns:
          Cached result or None
      """
      cached = self.context.get_query_result(query)
      if cached:
          logger.info(f"Cache hit for query: {query[:50]}...")
          return cached
      return None
  
  def _save_to_cache(self, query: str, result: Any):
      """
      Save query result to cache
      
      Args:
          query: Query string
          result: Result to cache
      """
      self.context.save_query_result(query, result)
      logger.debug(f"Cached result for query: {query[:50]}...")
  
  def get_status(self) -> Dict[str, Any]:
      """
      Get orchestrator status
      
      Returns:
          Status dictionary
      """
      return {
          'name': self.name,
          'mode': self.mode,
          'agents_loaded': list(self.agents.keys()),
          'config_valid': self.config.validate()
      }

# Example usage
if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  
  # Initialize base orchestrator
  orch = BaseOrchestrator()
  
  # Check status
  status = orch.get_status()
  print(f"Status: {status}")
  
  # Test cache
  orch._save_to_cache("test query", {"result": "test"})
  cached = orch._check_cache("test query")
  print(f"Cached: {cached}")
