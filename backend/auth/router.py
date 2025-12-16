from fastapi import APIRouter, HTTPException, Response, status

from auth.schemas import LoginRequest, RegisterRequest, UserPublic
from auth.security import (
    cookie_max_age_seconds,
    cookie_name,
    cookie_samesite,
    cookie_secure,
    create_access_token,
    hash_password,
    verify_password,
)
from auth.store import create_user, find_user_by_email, user_public_from_doc


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    password_hash = hash_password(payload.password)

    try:
        doc = create_user(username=payload.username.strip(), email=payload.email, password_hash=password_hash)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    return user_public_from_doc(doc)


@router.post("/login", response_model=UserPublic)
def login(payload: LoginRequest, response: Response):
    user = find_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user_id=str(user["_id"]))

    response.set_cookie(
        key=cookie_name(),
        value=token,
        httponly=True,
        secure=cookie_secure(),
        samesite=cookie_samesite(),
        max_age=cookie_max_age_seconds(),
        path="/",
    )

    return user_public_from_doc(user)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=cookie_name(), path="/")
    return {"ok": True}
