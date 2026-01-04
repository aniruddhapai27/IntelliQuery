from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status

from auth.dependencies import require_user
from ai.schemas import QueryRequest, QueryResponse
from ai.ai_router import ai_router

router = APIRouter(prefix="/ai", tags=["ai"])


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
    3. Generate the query using fine-tuned LLMs (Ollama) or Groq fallback
    4. Validate the query is read-only
    5. Execute and return results
    """
    response = await ai_router.route_query(
        natural_query=request.query,
        datasource_id=request.datasource_id,
        user_id=str(user["id"])
    )
    
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
    Check health of AI services (Ollama and Groq).
    """
    from ai.llm.ollama import check_ollama_health
    from ai.llm.groq_fallback import get_groq_client
    
    ollama_healthy = await check_ollama_health()
    groq_available = get_groq_client() is not None
    
    return {
        "ollama": {
            "available": ollama_healthy,
            "url": "http://127.0.0.1:11434",
            "models": ["qwen-text2sql:latest", "qwen-text2mongo:latest", "qwen-text2pandas:latest"]
        },
        "groq": {
            "available": groq_available,
            "model": "meta-llama/llama-4-scout-17b-16e-instruct"
        },
        "status": "healthy" if (ollama_healthy or groq_available) else "degraded"
    }
