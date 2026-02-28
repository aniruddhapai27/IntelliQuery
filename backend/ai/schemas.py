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
    session_id: Optional[str] = None  # If omitted, a new session is created


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
    llm_used: str  # Which LLM was used (groq)
    session_id: Optional[str] = None  # Returned so frontend can persist it


class SchemaInfo(BaseModel):
    """Schema information for a datasource."""
    datasource_type: DataSourceType
    tables: Optional[List[Dict[str, Any]]] = None  # For SQL
    collections: Optional[List[Dict[str, Any]]] = None  # For MongoDB
    columns: Optional[List[str]] = None  # For Pandas
    sample_data: Optional[Dict[str, Any]] = None


class VisualizationSuggestRequest(BaseModel):
    """Request schema for visualization suggestions."""
    results: List[Dict[str, Any]]
    query_context: Optional[str] = None


class VisualizationSuggestResponse(BaseModel):
    """Response schema for visualization suggestions."""
    success: bool
    recommendations: List[Dict[str, Any]]
    data_insights: Optional[str] = None
    data_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class VisualizationGenerateRequest(BaseModel):
    """Request schema for generating a specific visualization."""
    results: List[Dict[str, Any]]
    chart_type: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    group_by: Optional[str] = None
    customization: Optional[Dict[str, Any]] = None


class VisualizationGenerateResponse(BaseModel):
    """Response schema for generated visualization."""
    success: bool
    chart_type: str
    chart_data: Optional[Dict[str, Any]] = None  # Plotly JSON
    config: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AutocompleteRequest(BaseModel):
    """Request schema for query autocomplete."""
    partial_query: str
    datasource_id: str
    limit: Optional[int] = 5


class AutocompleteResponse(BaseModel):
    """Response schema for query autocomplete."""
    success: bool
    suggestions: List[str]
    partial_query: str
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Export schemas
# ---------------------------------------------------------------------------

class ExportCSVRequest(BaseModel):
    """Request schema for exporting query results as CSV."""
    results: List[Dict[str, Any]]
    columns: Optional[List[str]] = None
    filename: Optional[str] = "query_results.csv"


class EmailExportRequest(BaseModel):
    """Request schema for emailing query results and chart to recipients."""
    recipients: List[str]
    results: List[Dict[str, Any]]
    columns: Optional[List[str]] = None
    chart_data: Optional[Dict[str, Any]] = None  # Plotly JSON figure
    query_context: Optional[str] = None  # Original natural language query
    subject: Optional[str] = None  # Custom email subject


class EmailExportResponse(BaseModel):
    """Response schema for email export."""
    success: bool
    message: str
    recipients: List[str]
    error: Optional[str] = None
