import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import logging

from ai.llm.ollama import generate_with_ollama, check_ollama_health
from ai.llm.groq_fallback import generate_with_groq

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all query agents.
    Handles LLM generation with Ollama primary and Groq fallback.
    """
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.llm_used = "ollama"
    
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
3. For find: {{"operation": "find", "filter": {{}}, "projection": {{}}, "sort": {{}}, "limit": null}}
4. For aggregate: {{"operation": "aggregate", "pipeline": []}}
5. Do not include any explanation

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
        Generate a query from natural language using Ollama or Groq fallback.
        
        Returns:
            Tuple of (generated_query, llm_used)
        """
        schema_context = await self.get_schema_context(datasource)
        
        # Try Ollama first
        if await check_ollama_health():
            prompt = self.build_prompt(natural_query, schema_context)
            result = await generate_with_ollama(prompt, self.agent_type)
            if result:
                self.llm_used = "ollama"
                return self._clean_generated_query(result), "ollama"
        
        # Fallback to Groq
        logger.info(f"Falling back to Groq for {self.agent_type} query generation")
        result = await generate_with_groq(natural_query, self.agent_type, schema_context)
        if result:
            self.llm_used = "groq"
            return self._clean_generated_query(result), "groq"
        
        return None, "none"
    
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
        Full pipeline: generate query -> validate -> execute -> return results
        """
        # Generate query
        generated_query, llm_used = await self.generate_query(natural_query, datasource)
        
        if not generated_query:
            return {
                "success": False,
                "error": "Failed to generate query from natural language",
                "llm_used": llm_used
            }
        
        # Validate read-only
        is_valid, validation_error = self.validate_readonly(generated_query)
        if not is_valid:
            return {
                "success": False,
                "generated_query": generated_query,
                "error": f"Query validation failed: {validation_error}",
                "llm_used": llm_used
            }
        
        # Execute query
        success, result = await self.execute_query(generated_query, datasource)
        
        if success:
            return {
                "success": True,
                "generated_query": generated_query,
                "results": result.get("data", []),
                "columns": result.get("columns", []),
                "row_count": result.get("row_count", 0),
                "llm_used": llm_used
            }
        else:
            return {
                "success": False,
                "generated_query": generated_query,
                "error": str(result),
                "llm_used": llm_used
            }
