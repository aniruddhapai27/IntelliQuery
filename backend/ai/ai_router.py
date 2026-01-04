import logging
from typing import Any, Dict, Optional

from ai.agents.sql_agent import SQLAgent
from ai.agents.mongo_agent import MongoAgent
from ai.agents.pandas_agent import PandasAgent
from ai.schemas import DataSourceType, QueryResponse
from datasources.store import get_datasource_by_id

logger = logging.getLogger(__name__)


class AIRouter:
    """
    AI Router that routes natural language queries to the appropriate agent
    based on the datasource type (SQL, MongoDB, Pandas).
    """
    
    def __init__(self):
        self.sql_agent = SQLAgent()
        self.mongo_agent = MongoAgent()
        self.pandas_agent = PandasAgent()
        
        # Agent mapping by datasource type
        self._agents = {
            "mysql": self.sql_agent,
            "psql": self.sql_agent,
            "sql": self.sql_agent,
            "mongo": self.mongo_agent,
            "mongodb": self.mongo_agent,
            "pandas": self.pandas_agent,
            "csv": self.pandas_agent,
            "excel": self.pandas_agent,
        }
    
    def _get_agent(self, datasource_type: str):
        """Get the appropriate agent for the datasource type."""
        agent = self._agents.get(datasource_type.lower())
        if not agent:
            raise ValueError(f"Unsupported datasource type: {datasource_type}")
        return agent
    
    def _get_datasource_enum(self, datasource_type: str) -> DataSourceType:
        """Convert datasource type string to enum."""
        type_mapping = {
            "mysql": DataSourceType.SQL,
            "psql": DataSourceType.SQL,
            "sql": DataSourceType.SQL,
            "mongo": DataSourceType.MONGO,
            "mongodb": DataSourceType.MONGO,
            "pandas": DataSourceType.PANDAS,
            "csv": DataSourceType.PANDAS,
            "excel": DataSourceType.PANDAS,
        }
        return type_mapping.get(datasource_type.lower(), DataSourceType.SQL)
    
    async def route_query(
        self,
        natural_query: str,
        datasource_id: str,
        user_id: str
    ) -> QueryResponse:
        """
        Route a natural language query to the appropriate agent and execute it.
        
        Args:
            natural_query: The natural language query from the user
            datasource_id: The ID of the datasource to query
            user_id: The ID of the current user
            
        Returns:
            QueryResponse with results or error
        """
        # Get datasource details
        datasource = get_datasource_by_id(datasource_id)
        
        if not datasource:
            return QueryResponse(
                success=False,
                query=natural_query,
                generated_query="",
                datasource_type=DataSourceType.SQL,
                error="Datasource not found",
                llm_used="none"
            )
        
        # Verify user owns this datasource
        if str(datasource.get("user_id")) != user_id:
            return QueryResponse(
                success=False,
                query=natural_query,
                generated_query="",
                datasource_type=DataSourceType.SQL,
                error="Access denied to this datasource",
                llm_used="none"
            )
        
        datasource_type = datasource.get("type", "")
        
        try:
            # Get the appropriate agent
            agent = self._get_agent(datasource_type)
            datasource_enum = self._get_datasource_enum(datasource_type)
            
            # Process the query through the agent
            result = await agent.process(natural_query, datasource)
            
            return QueryResponse(
                success=result.get("success", False),
                query=natural_query,
                generated_query=result.get("generated_query", ""),
                datasource_type=datasource_enum,
                results=result.get("results"),
                columns=result.get("columns"),
                row_count=result.get("row_count"),
                error=result.get("error"),
                llm_used=result.get("llm_used", "none")
            )
            
        except ValueError as e:
            return QueryResponse(
                success=False,
                query=natural_query,
                generated_query="",
                datasource_type=DataSourceType.SQL,
                error=str(e),
                llm_used="none"
            )
        except Exception as e:
            logger.error(f"Error routing query: {e}")
            return QueryResponse(
                success=False,
                query=natural_query,
                generated_query="",
                datasource_type=self._get_datasource_enum(datasource_type),
                error=f"Internal error: {str(e)}",
                llm_used="none"
            )
    
    async def get_schema_info(self, datasource_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get schema information for a datasource.
        
        Args:
            datasource_id: The ID of the datasource
            user_id: The ID of the current user
            
        Returns:
            Schema information dict
        """
        datasource = get_datasource_by_id(datasource_id)
        
        if not datasource:
            return {"error": "Datasource not found"}
        
        if str(datasource.get("user_id")) != user_id:
            return {"error": "Access denied"}
        
        datasource_type = datasource.get("type", "")
        
        try:
            if datasource_type in ["mysql", "psql"]:
                tables = await self.sql_agent.get_tables_info(datasource)
                return {
                    "type": "sql",
                    "tables": tables
                }
            elif datasource_type == "mongo":
                collections = await self.mongo_agent.get_collections_info(datasource)
                return {
                    "type": "mongo",
                    "collections": collections
                }
            elif datasource_type == "pandas":
                info = await self.pandas_agent.get_dataframe_info(datasource)
                return {
                    "type": "pandas",
                    **info
                }
            else:
                return {"error": f"Unknown datasource type: {datasource_type}"}
                
        except Exception as e:
            logger.error(f"Error getting schema info: {e}")
            return {"error": str(e)}


# Singleton instance
ai_router = AIRouter()
