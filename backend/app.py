import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from auth.middleware import AuthMiddleware
from auth.router import router as auth_router
from datasources.router import router as datasources_router
from auth.store import ensure_indexes
from utils.db import ping_db

load_dotenv()

app = FastAPI()

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


@app.on_event("startup")
def _startup() -> None:
    ping_db()
    ensure_indexes()

@app.get('/')
def root():
    return({"msg":"Welcome"})

