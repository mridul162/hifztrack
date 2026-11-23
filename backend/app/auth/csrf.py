import hashlib
import hmac
import secrets
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

CSRF_COOKIE_NAME = "__Host-hifztrack_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"
SESSION_COOKIE_NAME = "__Host-hifztrack_session"


def create_csrf_token(secret: str) -> str:
    nonce = secrets.token_urlsafe(32)
    signature = hmac.new(
        secret.encode("utf-8"), f"csrf-v1:{nonce}".encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{nonce}.{signature}"


def is_valid_csrf_token(token: str, secret: str) -> bool:
    try:
        nonce, signature = token.split(".", maxsplit=1)
    except ValueError:
        return False
    if not nonce or not signature:
        return False
    expected = hmac.new(
        secret.encode("utf-8"), f"csrf-v1:{nonce}".encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            return await call_next(request)

        origin = request.headers.get("origin")
        if origin not in settings.cors_origins_list:
            return JSONResponse({"detail": "Request validation failed"}, status_code=403)

        cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
        header_token = request.headers.get(CSRF_HEADER_NAME, "")
        secret = settings.security_secret_key.get_secret_value()
        if (
            not cookie_token
            or not header_token
            or not hmac.compare_digest(cookie_token, header_token)
            or not is_valid_csrf_token(header_token, secret)
        ):
            return JSONResponse({"detail": "Request validation failed"}, status_code=403)

        return await call_next(request)
