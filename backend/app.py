import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from auth.middleware import AuthMiddleware
from auth.router import router as auth_router
from datasources.router import router as datasources_router
from ai.router import router as ai_router
from auth.store import ensure_indexes
from utils.db import ping_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()

app = FastAPI(
    title="IntelliQuery API",
    description="Voice-driven database chat platform with AI-powered query generation",
    version="1.0.0"
)

cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(AuthMiddleware)
app.include_router(auth_router)
app.include_router(datasources_router)
app.include_router(ai_router)


@app.on_event("startup")
async def _startup() -> None:
    ping_db()
    ensure_indexes()
    
    # Log AI service status
    from ai.llm.ollama import check_ollama_health
    ollama_status = await check_ollama_health()
    logging.getLogger(__name__).info(f"Ollama status: {'available' if ollama_status else 'unavailable'}")

@app.get('/')
def root():
    return({"msg":"Welcome to IntelliQuery API"})

