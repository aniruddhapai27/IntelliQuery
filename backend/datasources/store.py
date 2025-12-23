import os
import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pymongo.collection import Collection
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from utils.db import get_db

def datasources_collection() -> Collection:
    return get_db()["datasources"]

def _get_cipher_suite() -> Fernet:
    # Derive a key from AUTH_JWT_SECRET
    secret = os.getenv("AUTH_JWT_SECRET", "change-me")
    salt = b"static-salt-for-datasources" # In production, use a proper key management
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    return Fernet(key)

def encrypt_password(password: str) -> str:
    if not password:
        return ""
    f = _get_cipher_suite()
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    if not encrypted_password:
        return ""
    f = _get_cipher_suite()
    return f.decrypt(encrypted_password.encode()).decode()

def save_datasource(user_id: str, type: str, details: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    
    # Encrypt password if present
    if "password" in details:
        details["password"] = encrypt_password(details["password"])
        
    doc = {
        "user_id": ObjectId(user_id),
        "type": type,
        "details": details,
        "created_at": now,
        "updated_at": now
    }
    
    # Check if exists to update or insert
    # We assume uniqueness by user_id, type, and database/host
    # But for simplicity, we'll just insert a new one or update if we can identify it.
    # Let's just insert for now, or maybe update if same host/db.
    
    query = {
        "user_id": ObjectId(user_id),
        "type": type,
    }
    
    if type in ["mysql", "psql"]:
        query["details.host"] = details["host"]
        query["details.database"] = details["database"]
    elif type == "mongo":
        query["details.database"] = details["database"]
        # URI might be different but pointing to same DB, hard to tell.
    
    update = {
        "$set": {
            "details": details,
            "updated_at": now
        },
        "$setOnInsert": {
            "created_at": now
        }
    }
    
    res = datasources_collection().update_one(query, update, upsert=True)
    
    # If upserted, we need to find it to get ID. If updated, same.
    saved_doc = datasources_collection().find_one(query)
    return saved_doc

def list_datasources(user_id: str) -> List[Dict[str, Any]]:
    cursor = datasources_collection().find({"user_id": ObjectId(user_id)})
    results = []
    for doc in cursor:
        # Decrypt password for internal use? 
        # No, we shouldn't return password to frontend usually.
        # But the user said "without giving credentials again".
        # We will return the doc, but maybe mask the password.
        # The backend will use the encrypted password internally when connecting.
        
        # For the list endpoint, we return metadata.
        item = {
            "id": str(doc["_id"]),
            "type": doc["type"],
            "created_at": doc["created_at"],
            "details": {k: v for k, v in doc["details"].items() if k != "password"}
        }
        results.append(item)
    return results

def get_datasource_by_id(datasource_id: str) -> Optional[Dict[str, Any]]:
    try:
        doc = datasources_collection().find_one({"_id": ObjectId(datasource_id)})
        if doc and "password" in doc["details"]:
            doc["details"]["password"] = decrypt_password(doc["details"]["password"])
        return doc
    except:
        return None
