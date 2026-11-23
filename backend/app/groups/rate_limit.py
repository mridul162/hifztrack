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
from app.models import GroupRateLimit


def _digest(scope: str, subject: str, bucket: int) -> str:
    message = f"group-rate-v1\0{scope}\0{bucket}\0{subject}".encode()
    key = settings.security_secret_key.get_secret_value().encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def consume(db: Session, limits: list[tuple[str, str, int, int]]) -> None:
    timestamp = time.time()
    now = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    db.execute(delete(GroupRateLimit).where(GroupRateLimit.expires_at < now))
    retry = 0
    for scope, subject, maximum, seconds in limits:
        bucket = math.floor(timestamp / seconds)
        start = datetime.fromtimestamp(bucket * seconds, tz=timezone.utc)
        key = _digest(scope, subject, bucket)
        insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
        stmt = insert(GroupRateLimit).values(scope=scope, key_digest=key, window_start=start,
            attempts=1, expires_at=start + timedelta(seconds=seconds, days=1))
        stmt = stmt.on_conflict_do_update(index_elements=["scope", "key_digest", "window_start"],
            set_={"attempts": GroupRateLimit.attempts + 1})
        db.execute(stmt)
        count = db.scalar(select(GroupRateLimit.attempts).where(GroupRateLimit.scope == scope,
            GroupRateLimit.key_digest == key, GroupRateLimit.window_start == start)) or 0
        if count > maximum:
            retry = max(retry, math.ceil((bucket + 1) * seconds - timestamp))
    db.commit()
    if retry:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Try again later.", headers={"Retry-After": str(max(1, retry))})
