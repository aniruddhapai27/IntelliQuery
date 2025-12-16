import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from passlib.context import CryptContext


# NOTE:
# - bcrypt can be problematic on some Windows setups depending on package versions.
# - bcrypt also has a 72-byte password limit.
# pbkdf2_sha256 is reliable cross-platform and avoids the bcrypt length limit.
_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class AuthConfigError(RuntimeError):
    pass


def _jwt_secret() -> str:
    secret = os.getenv("AUTH_JWT_SECRET")
    if not secret:
        raise AuthConfigError("AUTH_JWT_SECRET is not set")
    return secret


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_access_token(*, user_id: str) -> str:
    minutes = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "60"))
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
    }

    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, _jwt_secret(), algorithms=["HS256"])


def cookie_name() -> str:
    return os.getenv("AUTH_COOKIE_NAME", "session")


def cookie_secure() -> bool:
    return os.getenv("COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes"}


def cookie_samesite() -> str:
    value = os.getenv("COOKIE_SAMESITE", "lax").strip().lower()
    if value not in {"lax", "strict", "none"}:
        return "lax"
    return value


def cookie_max_age_seconds() -> int:
    minutes = int(os.getenv("AUTH_TOKEN_EXPIRE_MINUTES", "60"))
    return max(60, minutes * 60)
