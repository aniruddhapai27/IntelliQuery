import re
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, field_validator


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
    normal_form: Optional[str] = None  # SQL-only heuristic label (2NF/3NF)
    results: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: Optional[int] = None
    error: Optional[str] = None
    llm_used: str  # Which LLM was used (groq)
    confidence: Optional[float] = None  # LLM Validation Confidence
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
# Export / Email schemas
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class ExportCSVRequest(BaseModel):
    """Request schema for CSV export."""
    results: List[Dict[str, Any]]
    columns: Optional[List[str]] = None
    filename: Optional[str] = "query_results.csv"


class EmailResultsRequest(BaseModel):
    """Request schema for emailing results + chart to recipients."""
    recipients: List[str]
    results: List[Dict[str, Any]]
    columns: Optional[List[str]] = None
    chart_data: Optional[Dict[str, Any]] = None  # Plotly JSON figure
    query_context: Optional[str] = None  # Original natural language query
    subject: Optional[str] = "IntelliQuery — Your Query Results"
    message: Optional[str] = None

    @field_validator("recipients")
    @classmethod
    def validate_recipients(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("At least one recipient email address is required.")
        if len(v) > 20:
            raise ValueError("Cannot send to more than 20 recipients at once.")
        cleaned: List[str] = []
        for addr in v:
            addr = addr.strip().lower()
            if not addr:
                continue
            if not _EMAIL_RE.match(addr):
                raise ValueError(f"Invalid email address: {addr}")
            cleaned.append(addr)
        if not cleaned:
            raise ValueError("No valid email addresses provided.")
        return cleaned


class EmailResultsResponse(BaseModel):
    """Response schema for email sending."""
    success: bool
    message: str
    recipients: List[str]
    error: Optional[str] = None


class SpeechToTextResponse(BaseModel):
    """Response schema for speech-to-text transcription."""
    success: bool
    text: str
    error: Optional[str] = None
