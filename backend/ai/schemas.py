from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


class DataSourceType(str, Enum):
    SQL = "sql"
    MONGO = "mongo"
    PANDAS = "pandas"


class QueryRequest(BaseModel):
    """Request schema for natural language query."""
    query: str
    datasource_id: str


class QueryResponse(BaseModel):
    """Response schema for query execution."""
    success: bool
    query: str  # The natural language query
    generated_query: str  # SQL/MongoDB/Pandas query generated
    datasource_type: DataSourceType
    results: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: Optional[int] = None
    error: Optional[str] = None
    llm_used: str  # Which LLM was used (ollama or groq)


class SchemaInfo(BaseModel):
    """Schema information for a datasource."""
    datasource_type: DataSourceType
    tables: Optional[List[Dict[str, Any]]] = None  # For SQL
    collections: Optional[List[Dict[str, Any]]] = None  # For MongoDB
    columns: Optional[List[str]] = None  # For Pandas
    sample_data: Optional[Dict[str, Any]] = None
