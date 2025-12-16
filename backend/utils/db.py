import os
from typing import Optional

from pymongo import MongoClient
from pymongo.database import Database


_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_db() -> Database:
    db_name = os.getenv("MONGO_DB_NAME", "intelliquery")
    return get_mongo_client()[db_name]


def ping_db() -> None:
    # Forces a connection attempt early so startup fails fast if Mongo is unreachable.
    get_db().command("ping")
