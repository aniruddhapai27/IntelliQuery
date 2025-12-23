from enum import Enum
from typing import Optional
from pydantic import BaseModel

class SQLType(str, Enum):
    MYSQL = "mysql"
    POSTGRESQL = "psql"

class SQLConnectionRequest(BaseModel):
    type: SQLType
    host: str
    port: int
    username: str
    password: str
    database: str

class MongoConnectionRequest(BaseModel):
    uri: str
    database: str

class DataSourceResponse(BaseModel):
    message: str
    status: str
    details: Optional[dict] = None
