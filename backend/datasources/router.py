import os
import shutil
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, status, Depends
from sqlalchemy import create_engine, text
from pymongo import MongoClient
import pandas as pd

from auth.dependencies import require_user
from datasources.schemas import (
    SQLConnectionRequest,
    MongoConnectionRequest,
    DataSourceResponse,
    SQLType
)
from datasources.store import save_datasource, list_datasources

router = APIRouter(prefix="/datasources", tags=["datasources"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[dict])
def get_datasources(user: dict = Depends(require_user)):
    """
    List all saved data sources for the current user.
    """
    return list_datasources(str(user["id"]))

@router.post("/sql/connect", response_model=DataSourceResponse)
def connect_sql(payload: SQLConnectionRequest, user: dict = Depends(require_user)):
    """
    Connect to a SQL database (MySQL or PostgreSQL).
    """
    db_url = ""
    if payload.type == SQLType.MYSQL:
        db_url = f"mysql+pymysql://{payload.username}:{payload.password}@{payload.host}:{payload.port}/{payload.database}"
    elif payload.type == SQLType.POSTGRESQL:
        db_url = f"postgresql+psycopg2://{payload.username}:{payload.password}@{payload.host}:{payload.port}/{payload.database}"
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            
        # Save connection details
        save_datasource(str(user["id"]), payload.type.value, payload.dict())
        
        return DataSourceResponse(
            message=f"Successfully connected to {payload.type.value} database",
            status="success",
            details={"database": payload.database, "host": payload.host}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to database: {str(e)}"
        )

@router.post("/mongo/connect", response_model=DataSourceResponse)
def connect_mongo(payload: MongoConnectionRequest, user: dict = Depends(require_user)):
    """
    Connect to a MongoDB database.
    """
    try:
        client = MongoClient(payload.uri, serverSelectionTimeoutMS=5000)
        # Trigger a connection to verify validity
        client.admin.command('ping')
        
        # Check if database exists or we can access it
        db = client[payload.database]
        # List collections to ensure we have access
        db.list_collection_names()
        
        # Save connection details
        save_datasource(str(user["id"]), "mongo", payload.dict())
        
        return DataSourceResponse(
            message="Successfully connected to MongoDB",
            status="success",
            details={"database": payload.database}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to MongoDB: {str(e)}"
        )

@router.post("/pandas/upload", response_model=DataSourceResponse)
async def upload_pandas(file: UploadFile = File(...), user: dict = Depends(require_user)):
    """
    Upload a CSV or Excel file for Pandas analysis.
    """
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a CSV or Excel file."
        )
    
    # Use user ID in filename to avoid collisions or organize folders
    user_upload_dir = os.path.join(UPLOAD_DIR, str(user["id"]))
    os.makedirs(user_upload_dir, exist_ok=True)
    file_path = os.path.join(user_upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Verify if it can be read by pandas
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        # Save datasource details
        details = {
            "filename": file.filename,
            "path": file_path,
            "rows": len(df),
            "columns": list(df.columns)
        }
        save_datasource(str(user["id"]), "pandas", details)
            
        return DataSourceResponse(
            message="Successfully uploaded and verified file",
            status="success",
            details=details
        )
    except Exception as e:
        # Clean up if failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}"
        )
