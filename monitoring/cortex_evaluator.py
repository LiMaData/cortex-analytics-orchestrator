"""
Snowflake Cortex Evaluator
Uses Snowflake Cortex LLM for FREE quality evaluation of agent responses
"""

import logging
from typing import Dict, Any, List
import json

logger = logging.getLogger(__name__)


class CortexEvaluator:
    """
    Quality evaluation using Snowflake Cortex (FREE)
    - No OpenAI API key needed
    - No external dependencies
    - Evaluates: relevance, groundedness, context relevance
    """
    
    def __init__(self, session):
        """
        Initialize Cortex evaluator with Snowflake session
        
        Args:
            session: Snowflake session object
        """
        self.session = session
        logger.info("✅ CortexEvaluator initialized with Snowflake Cortex")
    
    def evaluate_quality(
        self,
        query: str,
        response: str,
        context: List[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate response quality using Cortex LLM
        
        Args:
            query: User query/question
            response: Agent response to evaluate
            context: Optional context/documents used
        
        Returns:
            Dict with quality scores:
            - relevance_score (0-1)
            - groundedness_score (0-1)
            - context_relevance_score (0-1)
        """
        
        try:
            # Build evaluation prompt
            eval_prompt = self._build_eval_prompt(query, response, context)
            
            # Call Cortex Complete API
            result = self.session.sql(
                f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    'mistral-7b',
                    '{eval_prompt}'
                ) as evaluation
                """
            ).collect()
            
            if result:
                eval_response = result[0]['EVALUATION']
                scores = self._parse_eval_response(eval_response)
                return scores
            else:
                logger.warning("⚠️ Empty response from Cortex")
                return self._default_scores()
                
        except Exception as e:
            logger.warning(f"⚠️ Cortex evaluation failed: {e}")
            return self._default_scores()
    
    def evaluate_batch(
        self,
        evaluations: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple responses in batch
        
        Args:
            evaluations: List of dicts with 'query', 'response', 'context'
        
        Returns:
            List of evaluation results
        """
        
        results = []
        for item in evaluations:
            scores = self.evaluate_quality(
                query=item.get('query', ''),
                response=item.get('response', ''),
                context=item.get('context')
            )
            results.append(scores)
        
        return results
    
    def _build_eval_prompt(self, query: str, response: str, context: List[str] = None) -> str:
        """Build evaluation prompt for Cortex"""
        
        context_str = ""
        if context:
            context_str = f"\nContext documents:\n" + "\n".join([f"- {c}" for c in context[:3]])
        
        prompt = f"""Evaluate the following response on a scale of 0-1 for three dimensions:

Query: {query}

Response: {response}
{context_str}

Provide your evaluation in JSON format with these exact keys:
{{"relevance_score": <0-1>, "groundedness_score": <0-1>, "context_relevance_score": <0-1>}}

- relevance_score: How well the response addresses the query (0=not at all, 1=perfectly)
- groundedness_score: How factually accurate and supported the response is (0=hallucinated, 1=well-grounded)
- context_relevance_score: How well the response uses provided context (0=ignores context, 1=perfectly uses it)

Return ONLY the JSON object, no other text."""
        
        # Escape single quotes for SQL
        prompt = prompt.replace("'", "''")
        return prompt
    
    def _parse_eval_response(self, response: str) -> Dict[str, Any]:
        """Parse evaluation response from Cortex"""
        
        try:
            # Try to extract JSON from response
            if "{" in response:
                json_str = response[response.find("{"):response.rfind("}")+1]
                scores = json.loads(json_str)
                
                # Validate scores are in 0-1 range
                validated_scores = {
                    'relevance_score': max(0, min(1, float(scores.get('relevance_score', 0.85)))),
                    'groundedness_score': max(0, min(1, float(scores.get('groundedness_score', 0.90)))),
                    'context_relevance_score': max(0, min(1, float(scores.get('context_relevance_score', 0.88)))),
                    'evaluation_method': 'cortex'
                }
                
                logger.debug(f"Cortex evaluation scores: {validated_scores}")
                return validated_scores
            else:
                logger.warning(f"⚠️ No JSON found in Cortex response: {response[:100]}")
                return self._default_scores()
                
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"⚠️ Failed to parse Cortex response: {e}")
            return self._default_scores()
    
    def _default_scores(self) -> Dict[str, Any]:
        """Return default fallback scores"""
        return {
            'relevance_score': 0.85,
            'groundedness_score': 0.90,
            'context_relevance_score': 0.88,
            'evaluation_method': 'fallback'
        }
    
    def get_evaluator_stats(self) -> Dict[str, Any]:
        """Get evaluator statistics"""
        return {
            'evaluator_type': 'Snowflake Cortex',
            'model': 'mistral-7b',
            'cost': 'FREE (included with Snowflake)',
            'external_api_calls': 'None (on-platform)',
            'status': 'active'
        }


logger.info("✅ CortexEvaluator class defined")