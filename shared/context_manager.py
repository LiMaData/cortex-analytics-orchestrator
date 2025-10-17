
import json
import hashlib
import logging
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)

class SharedContextManager:
  """
  Manages shared state and caching across orchestrators
  
  Features:
  - Query result caching
  - User context storage
  - Cross-orchestrator data sharing
  """
  
  def __init__(self, storage_path: str = "./shared_data", cache_ttl: int = 3600):
      """
      Initialize context manager
      
      Args:
          storage_path: Directory for cached data
          cache_ttl: Cache time-to-live in seconds (default 1 hour)
      """
      self.storage_path = Path(storage_path)
      self.storage_path.mkdir(exist_ok=True)
      self.cache_ttl = cache_ttl
      
      logger.info(f"SharedContextManager initialized at {self.storage_path}")
  
  def save_query_result(self, query: str, result: Any) -> str:
      """
      Save query result to cache
      
      Args:
          query: The query string
          result: Result to cache
          
      Returns:
          Cache key (hash of query)
      """
      try:
          cache_key = self._hash_query(query)
          cache_file = self.storage_path / f"cache_{cache_key}.json"
          
          cache_data = {
              'query': query,
              'result': result,
              'timestamp': datetime.now().isoformat(),
              'ttl': self.cache_ttl
          }
          
          with open(cache_file, 'w') as f:
              json.dump(cache_data, f, indent=2, default=str)
          
          logger.debug(f"Cached query result: {cache_key}")
          return cache_key
          
      except Exception as e:
          logger.error(f"Error saving query result: {e}")
          return None
  
  def get_query_result(self, query: str) -> Optional[Any]:
      """
      Retrieve cached query result
      
      Args:
          query: The query string
          
      Returns:
          Cached result or None if not found/expired
      """
      try:
          cache_key = self._hash_query(query)
          cache_file = self.storage_path / f"cache_{cache_key}.json"
          
          if not cache_file.exists():
              logger.debug(f"Cache miss: {cache_key}")
              return None
          
          with open(cache_file, 'r') as f:
              cache_data = json.load(f)
          
          # Check if cache is still valid
          cached_time = datetime.fromisoformat(cache_data['timestamp'])
          ttl = cache_data.get('ttl', self.cache_ttl)
          
          if datetime.now() - cached_time > timedelta(seconds=ttl):
              logger.debug(f"Cache expired: {cache_key}")
              cache_file.unlink()  # Delete expired cache
              return None
          
          logger.debug(f"Cache hit: {cache_key}")
          return cache_data['result']
          
      except Exception as e:
          logger.error(f"Error retrieving query result: {e}")
          return None
  
  def save_user_context(self, user_id: str, context: Dict) -> bool:
      """
      Save user conversation context
      
      Args:
          user_id: User identifier
          context: Context data to save
          
      Returns:
          Success status
      """
      try:
          context_file = self.storage_path / f"user_{user_id}.json"
          
          context_data = {
              'user_id': user_id,
              'context': context,
              'last_updated': datetime.now().isoformat()
          }
          
          with open(context_file, 'w') as f:
              json.dump(context_data, f, indent=2, default=str)
          
          logger.debug(f"Saved context for user: {user_id}")
          return True
          
      except Exception as e:
          logger.error(f"Error saving user context: {e}")
          return False
  
  def get_user_context(self, user_id: str) -> Optional[Dict]:
      """
      Retrieve user conversation context
      
      Args:
          user_id: User identifier
          
      Returns:
          User context or None
      """
      try:
          context_file = self.storage_path / f"user_{user_id}.json"
          
          if not context_file.exists():
              return None
          
          with open(context_file, 'r') as f:
              context_data = json.load(f)
          
          return context_data['context']
          
      except Exception as e:
          logger.error(f"Error retrieving user context: {e}")
          return None
  
  def clear_cache(self) -> int:
      """
      Clear all cached data
      
      Returns:
          Number of files deleted
      """
      try:
          count = 0
          for cache_file in self.storage_path.glob("cache_*.json"):
              cache_file.unlink()
              count += 1
          
          logger.info(f"Cleared {count} cache files")
          return count
          
      except Exception as e:
          logger.error(f"Error clearing cache: {e}")
          return 0
  
  def _hash_query(self, query: str) -> str:
      """Generate hash for query string"""
      return hashlib.md5(query.lower().strip().encode()).hexdigest()

# Example usage
if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  
  # Initialize context manager
  context = SharedContextManager()
  
  # Test caching
  query = "What were sales last quarter?"
  result = {"revenue": 1000000, "count": 500}
  
  context.save_query_result(query, result)
  cached = context.get_query_result(query)
  print(f"Cached result: {cached}")
  
  # Test user context
  context.save_user_context("user123", {"last_query": query})
  user_ctx = context.get_user_context("user123")
  print(f"User context: {user_ctx}")

  
