from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from auth.security import cookie_name, decode_access_token
from auth.store import find_user_public_by_id


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None

        token = request.cookies.get(cookie_name())
        if token:
            try:
                payload = decode_access_token(token)
                user_id = payload.get("sub")
                if user_id:
                    request.state.user = find_user_public_by_id(user_id)
            except Exception:
                # Invalid/expired token: treat as anonymous.
                request.state.user = None

        return await call_next(request)
