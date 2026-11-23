import hashlib
import hmac
import math
import time
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AuthRateLimit

WINDOW_SECONDS = 15 * 60
RETENTION = timedelta(days=1)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _digest(scope: str, subject: str, bucket: int) -> str:
    message = f"rate-limit-v1\0{scope}\0{bucket}\0{subject}".encode("utf-8")
    key = settings.security_secret_key.get_secret_value().encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def _increment(db: Session, scope: str, subject: str, bucket: int, now: datetime) -> int:
    window_start = datetime.fromtimestamp(bucket * WINDOW_SECONDS, tz=timezone.utc)
    key_digest = _digest(scope, subject, bucket)
    values = {
        "scope": scope,
        "key_digest": key_digest,
        "window_start": window_start,
        "attempts": 1,
        "expires_at": window_start + RETENTION,
    }
    dialect = db.get_bind().dialect.name
    insert = pg_insert if dialect == "postgresql" else sqlite_insert
    statement = insert(AuthRateLimit).values(**values)
    statement = statement.on_conflict_do_update(
        index_elements=["scope", "key_digest", "window_start"],
        set_={"attempts": AuthRateLimit.attempts + 1},
    )
    db.execute(statement)
    return db.scalar(
        select(AuthRateLimit.attempts).where(
            AuthRateLimit.scope == scope,
            AuthRateLimit.key_digest == key_digest,
            AuthRateLimit.window_start == window_start,
        )
    ) or 0


def _consume(db: Session, request: Request, limits: list[tuple[str, str, int]]) -> None:
    timestamp = time.time()
    bucket = math.floor(timestamp / WINDOW_SECONDS)
    now = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    db.execute(delete(AuthRateLimit).where(AuthRateLimit.expires_at < now))

    exceeded: list[int] = []
    for scope, subject, maximum in limits:
        attempts = _increment(db, scope, subject, bucket, now)
        if attempts > maximum:
            exceeded.append((bucket + 1) * WINDOW_SECONDS - timestamp)
    db.commit()

    if exceeded:
        retry_after = max(1, math.ceil(max(exceeded)))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def limit_registration(db: Session, request: Request) -> None:
    _consume(db, request, [("register-ip", _client_ip(request), 5)])


def limit_login(db: Session, request: Request, normalized_email: str) -> None:
    ip = _client_ip(request)
    _consume(
        db,
        request,
        [
            ("login-ip-email", f"{ip}\0{normalized_email}", 10),
            ("login-ip", ip, 30),
        ],
    )
