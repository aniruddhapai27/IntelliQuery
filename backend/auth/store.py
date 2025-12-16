from datetime import datetime, timezone
from typing import Any, Dict, Optional

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from utils.db import get_db


def users_collection() -> Collection:
    return get_db()["users"]


def ensure_indexes() -> None:
    col = users_collection()
    col.create_index("email", unique=True)
    col.create_index("username", unique=True)


def user_public_from_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "username": doc["username"],
        "email": doc["email"],
    }


def create_user(*, username: str, email: str, password_hash: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    doc = {
        "username": username,
        "email": email.lower().strip(),
        "password_hash": password_hash,
        "created_at": now,
    }

    try:
        res = users_collection().insert_one(doc)
    except DuplicateKeyError as e:
        raise ValueError("User already exists") from e

    doc["_id"] = res.inserted_id
    return doc


def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return users_collection().find_one({"email": email.lower().strip()})


def find_user_public_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None

    doc = users_collection().find_one({"_id": oid}, {"password_hash": 0})
    if not doc:
        return None
    return user_public_from_doc(doc)
