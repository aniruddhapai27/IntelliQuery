import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import logging

from ai.llm.groq import generate_with_groq, classify_query_relevance, refine_query_with_groq

logger = logging.getLogger(__name__)

# Maximum number of LLM refinement iterations for query generation
MAX_REFINEMENT_ITERATIONS = 3


class BaseAgent(ABC):
    """
    Base class for all query agents.
    Handles LLM generation using Groq.
    """
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.llm_used = "groq"
    
    @abstractmethod
    async def get_schema_context(self, datasource: Dict[str, Any]) -> str:
        """
        Extract schema information from the datasource for LLM context.
        Must be implemented by each agent.
        """
        pass
    
    @abstractmethod
    def validate_readonly(self, generated_query: str) -> Tuple[bool, str]:
        """
        Validate that the generated query is read-only.
        Returns (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, datasource: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Execute the generated query against the datasource.
        Returns (success, results_or_error)
        """
        pass

    def classify_normal_form(self, generated_query: str) -> Optional[str]:
        """Return a datasource-specific normal-form label when applicable."""
        return None
    
    def build_prompt(self, natural_query: str, schema_context: str) -> str:
        """Build the prompt for the LLM."""
        prompts = {
            "sql": f"""Given the following database schema:
{schema_context}

Convert the following natural language query to a valid SQL SELECT query:
"{natural_query}"

Rules:
1. ONLY generate SELECT queries
2. Do not include any explanation, just the raw SQL
3. Ensure the query is syntactically correct
4. Use appropriate JOINs if needed
5. Handle NULL values appropriately

SQL Query:""",
            
            "mongo": f"""Given the following MongoDB collection schema:
{schema_context}

Convert the following natural language query to a valid MongoDB query:
"{natural_query}"

Rules:
1. ONLY generate read operations (find or aggregate)
2. Return the query as a JSON object
3. For aggregate operations: {{"aggregate": [pipeline stages]}}
   Example: {{"aggregate": [{{"$group": {{"_id": "$field", "count": {{"$sum": 1}}}}}}, {{"$sort": {{"count": -1}}}}]}}
4. For find operations: {{"find": {{}}, "projection": {{}}, "sort": {{}}, "limit": 10}}
5. Do not include any explanation or markdown

MongoDB Query:""",
            
            "pandas": f"""Given a DataFrame 'df' with the following columns:
{schema_context}

Convert the following natural language query to valid Pandas code:
"{natural_query}"

Rules:
1. ONLY generate read operations (no inplace modifications)
2. Assume the DataFrame is named 'df'
3. Return only the code, no explanations
4. The result should be a DataFrame or Series
5. Use appropriate filtering, grouping, sorting as needed

Pandas Code:"""
        }
        return prompts.get(self.agent_type, prompts["sql"])
    
    async def generate_query(self, natural_query: str, datasource: Dict[str, Any]) -> Tuple[Optional[str], str]:
        """
        Generate a query from natural language using Groq LLM.
        Iteratively refines the query up to MAX_REFINEMENT_ITERATIONS times
        if validation fails.
        
        Returns:
            Tuple of (generated_query, llm_used)
        """
        schema_context = await self.get_schema_context(datasource)
        
        result = await generate_with_groq(natural_query, self.agent_type, schema_context)
        if not result:
            return None, "none"
        
        self.llm_used = "groq"
        generated = self._clean_generated_query(result)
        
        # Iterative refinement: validate and refine up to N times
        for iteration in range(MAX_REFINEMENT_ITERATIONS):
            is_valid, validation_error = self.validate_readonly(generated)
            if is_valid:
                logger.info(f"Query validated successfully on iteration {iteration + 1}")
                return generated, "groq"
            
            logger.warning(
                f"Query validation failed on iteration {iteration + 1}: {validation_error}. "
                f"Requesting LLM refinement..."
            )
            refined = await refine_query_with_groq(
                original_query=natural_query,
                generated_query=generated,
                error_message=validation_error,
                query_type=self.agent_type,
                schema_context=schema_context
            )
            if not refined:
                logger.error("LLM refinement returned nothing, stopping iterations")
                break
            generated = self._clean_generated_query(refined)
        
        # Return the last generated query even if validation still fails.
        # The caller (process) will run its own validation check.
        return generated, "groq"
    
    def _clean_generated_query(self, query: str) -> str:
        """Clean up the generated query by removing markdown code blocks etc."""
        # Remove markdown code blocks
        query = re.sub(r'^```[\w]*\n?', '', query)
        query = re.sub(r'\n?```$', '', query)
        query = query.strip()
        
        # Remove common prefixes
        prefixes_to_remove = ['SQL:', 'Query:', 'MongoDB Query:', 'Pandas Code:']
        for prefix in prefixes_to_remove:
            if query.lower().startswith(prefix.lower()):
                query = query[len(prefix):].strip()
        
        return query
    
    async def process(self, natural_query: str, datasource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full pipeline: guardrail check -> generate query -> validate -> execute -> (retry on exec error) -> return results
        """
        # --- Guardrail: reject non-data-analytical questions ---
        relevance = await classify_query_relevance(natural_query)
        if not relevance["is_relevant"]:
            reason = relevance.get("reason", "")
            return {
                "success": False,
                "error": (
                    "This question does not appear to be a data-analytical query. "
                    "Please ask a question that involves querying, filtering, aggregating, "
                    "or analyzing data from your connected datasource."
                    + (f" ({reason})" if reason else "")
                ),
                "llm_used": "groq"
            }

        # Generate query (with iterative validation refinement)
        generated_query, llm_used = await self.generate_query(natural_query, datasource)
        
        if not generated_query:
            return {
                "success": False,
                "error": "Failed to generate query from natural language",
                "llm_used": llm_used
            }
        
        # Validate read-only
        is_valid, validation_error = self.validate_readonly(generated_query)
        normal_form = self.classify_normal_form(generated_query)
        if not is_valid:
            return {
                "success": False,
                "generated_query": generated_query,
                "normal_form": normal_form,
                "error": f"Query validation failed: {validation_error}",
                "llm_used": llm_used
            }
        
        # Execute query with retry-on-execution-error refinement
        schema_context = await self.get_schema_context(datasource)
        last_query = generated_query

        for attempt in range(MAX_REFINEMENT_ITERATIONS):
            success, result = await self.execute_query(last_query, datasource)

            if success:
                return {
                    "success": True,
                    "generated_query": last_query,
                    "normal_form": self.classify_normal_form(last_query),
                    "results": result.get("data", []),
                    "columns": result.get("columns", []),
                    "row_count": result.get("row_count", 0),
                    "llm_used": llm_used
                }

            # Execution failed — try to refine the query
            error_msg = str(result)
            logger.warning(
                f"Query execution failed on attempt {attempt + 1}: {error_msg}. "
                f"Requesting LLM refinement..."
            )
            refined = await refine_query_with_groq(
                original_query=natural_query,
                generated_query=last_query,
                error_message=error_msg,
                query_type=self.agent_type,
                schema_context=schema_context
            )

            if not refined:
                break

            refined_query = self._clean_generated_query(refined)

            # Validate refined query before re-executing
            is_valid, validation_error = self.validate_readonly(refined_query)
            if not is_valid:
                logger.warning(f"Refined query also failed validation: {validation_error}")
                break

            last_query = refined_query

        # All attempts exhausted
        return {
            "success": False,
            "generated_query": last_query,
            "normal_form": self.classify_normal_form(last_query),
            "error": str(result),
            "llm_used": llm_used
        }
