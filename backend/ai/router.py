from typing import Dict, Any, List, Optional
import logging
import re
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import StreamingResponse
import io

from auth.dependencies import require_user
from ai.schemas import (
    QueryRequest, 
    QueryResponse,
    VisualizationSuggestRequest,
    VisualizationSuggestResponse,
    VisualizationGenerateRequest,
    VisualizationGenerateResponse,
    AutocompleteRequest,
    AutocompleteResponse,
    ExportCSVRequest,
    EmailExportRequest,
    EmailExportResponse,
)
from ai.ai_router import ai_router
from ai.agents.visualization_agent import visualization_agent
from ai.autocomplete import autocomplete
from ai.history_store import (
    create_session_id,
    save_history_entry,
    list_sessions,
    get_session_messages,
    delete_session,
)
from utils.email_service import (
    results_to_csv_bytes,
    send_results_email,
    render_plotly_chart_to_png,
)

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


@router.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    user: dict = Depends(require_user)
) -> QueryResponse:
    """
    Execute a natural language query against a datasource.
    
    The AI router will:
    1. Determine the datasource type (SQL, MongoDB, Pandas)
    2. Route to the appropriate agent
    3. Generate the query using Groq LLM
    4. Validate the query is read-only
    5. Execute and return results
    6. Persist the exchange in query history
    """
    # Resolve or create session
    session_id = request.session_id or create_session_id()

    response = await ai_router.route_query(
        natural_query=request.query,
        datasource_id=request.datasource_id,
        user_id=str(user["id"])
    )

    # Persist to history (fire-and-forget; don't block response on failure)
    try:
        # Convert results to a serialisable list (cap at 200 rows to keep docs small)
        raw_results = response.results
        stored_results = None
        if raw_results is not None:
            if isinstance(raw_results, list):
                stored_results = raw_results[:200]
            elif isinstance(raw_results, dict):
                stored_results = raw_results

        save_history_entry(
            user_id=str(user["id"]),
            session_id=session_id,
            datasource_id=request.datasource_id,
            datasource_type=response.datasource_type,
            natural_query=request.query,
            generated_query=response.generated_query,
            success=response.success,
            row_count=response.row_count,
            llm_used=response.llm_used,
            error=response.error,
            results=stored_results,
            columns=response.columns,
        )
    except Exception as exc:
        logger.warning("Failed to persist query history: %s", exc)

    # Attach session_id so frontend can keep using it
    response.session_id = session_id

    return response


@router.get("/schema/{datasource_id}")
async def get_datasource_schema(
    datasource_id: str,
    user: dict = Depends(require_user)
) -> Dict[str, Any]:
    """
    Get schema information for a datasource.
    
    Returns:
    - For SQL: List of tables with columns
    - For MongoDB: List of collections with fields
    - For Pandas: DataFrame columns and stats
    """
    schema_info = await ai_router.get_schema_info(
        datasource_id=datasource_id,
        user_id=str(user["id"])
    )
    
    if "error" in schema_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=schema_info["error"]
        )
    
    return schema_info


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Check health of AI services (Groq).
    """
    from ai.llm.groq import get_groq_client, GROQ_MODEL
    
    groq_available = get_groq_client() is not None
    
    return {
        "groq": {
            "available": groq_available,
            "model": GROQ_MODEL
        },
        "status": "healthy" if groq_available else "degraded"
    }


@router.post("/visualize/suggest", response_model=VisualizationSuggestResponse)
async def suggest_visualizations(
    request: VisualizationSuggestRequest,
    user: dict = Depends(require_user)
) -> VisualizationSuggestResponse:
    """
    Analyze query results and suggest appropriate visualizations using Groq LLM.
    
    This endpoint:
    1. Analyzes the data structure (columns, types, distributions)
    2. Uses Groq LLM to intelligently suggest chart types
    3. Returns ranked recommendations with reasons
    
    Returns:
    - List of recommended chart types with configuration
    - Data insights and summary
    """
    try:
        suggestions = await visualization_agent.suggest_visualizations(
            results=request.results,
            query_context=request.query_context
        )
        
        return VisualizationSuggestResponse(**suggestions)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate visualization suggestions: {str(e)}"
        )


@router.post("/visualize/generate", response_model=VisualizationGenerateResponse)
async def generate_visualization(
    request: VisualizationGenerateRequest,
    user: dict = Depends(require_user)
) -> VisualizationGenerateResponse:
    """
    Generate a specific visualization chart based on user selection.
    
    Parameters:
    - results: Query results to visualize
    - chart_type: Type of chart (line, bar, pie, scatter, etc.)
    - x_axis: Column name for X axis (optional, auto-detected)
    - y_axis: Column name for Y axis (optional, auto-detected)
    - group_by: Column for grouping/coloring (optional)
    - customization: Dict with colors, theme, height, width, etc.
    
    Customization options:
    - colors: List of color codes or Plotly color palette
    - title: Chart title
    - theme: plotly, plotly_white, plotly_dark, ggplot2, seaborn, simple_white
    - height: Chart height in pixels (default 500)
    - width: Chart width in pixels (default 800)
    - show_legend: Boolean (default True)
    - hovermode: closest, x, y, x unified, y unified
    
    Returns Plotly JSON that can be rendered using Plotly.js or plotly-react
    """
    try:
        chart = await visualization_agent.generate_visualization(
            results=request.results,
            chart_type=request.chart_type,
            x_axis=request.x_axis,
            y_axis=request.y_axis,
            group_by=request.group_by,
            customization=request.customization
        )
        
        return VisualizationGenerateResponse(**chart)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate visualization: {str(e)}"
        )


@router.post("/autocomplete", response_model=AutocompleteResponse)
async def query_autocomplete(
    request: AutocompleteRequest,
    user: dict = Depends(require_user)
) -> AutocompleteResponse:
    """
    Get real-time query suggestions as user types (Google-style autocomplete).
    
    Features:
    - Fast, sub-second response using Groq LLM
    - Context-aware suggestions based on datasource schema
    - Intelligent caching for performance
    - Fallback suggestions if LLM is unavailable
    
    Parameters:
    - partial_query: User's current input (e.g., "show me all")
    - datasource_id: Selected datasource ID
    - limit: Max suggestions to return (default 5, max 10)
    
    Returns:
    - List of natural language query suggestions
    - Optimized for real-time typing experience
    
    Usage:
    - Call on every keystroke (debounced on frontend)
    - Minimum 2 characters required
    - Results cached for 5 minutes per datasource
    
    Example:
    Input: "show me"
    Output: [
        "show me all records",
        "show me top 10 items",
        "show me records from today",
        "show me unique values",
        "show me summary statistics"
    ]
    """
    try:
        # Validate limit
        limit = min(request.limit or 5, 10)  # Max 10 suggestions
        
        # Get suggestions
        suggestions = await autocomplete.get_suggestions(
            partial_query=request.partial_query,
            datasource_id=request.datasource_id,
            user_id=str(user["id"]),
            limit=limit
        )
        
        return AutocompleteResponse(
            success=True,
            suggestions=suggestions,
            partial_query=request.partial_query
        )
        
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        # Return fallback on error
        return AutocompleteResponse(
            success=False,
            suggestions=[],
            partial_query=request.partial_query,
            error=str(e)
        )


@router.delete("/autocomplete/cache/{datasource_id}")
async def clear_autocomplete_cache(
    datasource_id: str,
    user: dict = Depends(require_user)
) -> Dict[str, Any]:
    """
    Clear autocomplete cache for a specific datasource.
    
    Use this when:
    - Datasource schema has changed
    - You want fresh suggestions
    - Testing autocomplete behavior
    """
    try:
        autocomplete.clear_cache(datasource_id)
        return {
            "success": True,
            "message": f"Cache cleared for datasource {datasource_id}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to clear cache: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Export endpoints
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


@router.post("/export/csv")
async def export_csv(
    request: ExportCSVRequest,
    user: dict = Depends(require_user),
):
    """
    Export query results as a downloadable CSV file.

    Accepts the results list-of-dicts returned by /ai/query.
    Returns a streaming CSV response (UTF-8 with BOM for Excel).
    """
    if not request.results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No results to export.",
        )

    csv_bytes = results_to_csv_bytes(request.results, request.columns)

    filename = request.filename or "query_results.csv"
    if not filename.endswith(".csv"):
        filename += ".csv"

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/export/email", response_model=EmailExportResponse)
async def export_email(
    request: EmailExportRequest,
    user: dict = Depends(require_user),
) -> EmailExportResponse:
    """
    Send query results (CSV) and optional chart image to email recipients.

    Validation rules:
    - At least one recipient is required.
    - Maximum 10 recipients per request.
    - All recipient addresses must be valid email format.
    - The logged-in user's own email is NOT allowed as a recipient.
    - Results must not be empty.
    """
    # --- Validate recipients list ---
    if not request.recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one recipient email is required.",
        )

    if len(request.recipients) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 recipients allowed per request.",
        )

    user_email = (user.get("email") or "").lower().strip()
    cleaned_recipients: list[str] = []

    for addr in request.recipients:
        addr = addr.strip().lower()

        if not EMAIL_RE.match(addr):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid email address: {addr}",
            )

        if addr == user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot send results to your own login email. Use a different recipient.",
            )

        if addr in cleaned_recipients:
            continue  # deduplicate silently
        cleaned_recipients.append(addr)

    if not cleaned_recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid recipient emails after processing.",
        )

    # --- Validate results ---
    if not request.results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No results to send. Run a query first.",
        )

    # --- Build attachments ---
    csv_bytes = results_to_csv_bytes(request.results, request.columns)

    chart_image_bytes = None
    if request.chart_data:
        chart_image_bytes = render_plotly_chart_to_png(request.chart_data)

    # --- Compose email ---
    query_label = request.query_context or "IntelliQuery Results"
    subject = request.subject or f"IntelliQuery – {query_label[:80]}"

    row_count = len(request.results)
    col_count = len(request.results[0]) if request.results else 0

    body_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;">
        <h2 style="color:#2563eb;">IntelliQuery – Query Results</h2>
        <p><strong>Query:</strong> {query_label}</p>
        <p><strong>Rows:</strong> {row_count} &nbsp;|&nbsp; <strong>Columns:</strong> {col_count}</p>
        <hr/>
        <p>The query results are attached as a CSV file.</p>
        {"<p>A chart visualization is also attached as a PNG image.</p>" if chart_image_bytes else ""}
        <br/>
        <p style="color:#6b7280;font-size:12px;">
            Sent via <strong>IntelliQuery</strong> by {user.get("username", "a team member")}.
        </p>
    </div>
    """

    # --- Send ---
    try:
        send_results_email(
            recipients=cleaned_recipients,
            subject=subject,
            body_html=body_html,
            csv_bytes=csv_bytes,
            chart_image_bytes=chart_image_bytes,
        )
    except RuntimeError as exc:
        # SMTP not configured
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Email send failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(exc)}",
        )

    return EmailExportResponse(
        success=True,
        message=f"Results sent to {len(cleaned_recipients)} recipient(s).",
        recipients=cleaned_recipients,
    )


# ---------------------------------------------------------------------------
# Query History endpoints
# ---------------------------------------------------------------------------

@router.get("/history")
async def get_history(
    datasource_id: Optional[str] = Query(None),
    user: dict = Depends(require_user),
) -> List[dict]:
    """
    List chat sessions for the current user.

    Optionally filter by ``datasource_id``.
    Returns sessions sorted by most-recently-active first.
    """
    return list_sessions(str(user["id"]), datasource_id)


@router.get("/history/{session_id}")
async def get_session(
    session_id: str,
    user: dict = Depends(require_user),
) -> List[dict]:
    """Return all message entries for a specific session."""
    messages = get_session_messages(str(user["id"]), session_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found")
    return messages


@router.delete("/history/{session_id}")
async def remove_session(
    session_id: str,
    user: dict = Depends(require_user),
) -> Dict[str, Any]:
    """Delete a chat session and all its messages."""
    deleted = delete_session(str(user["id"]), session_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "deleted_count": deleted}
