from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.auth.sessions import AuthenticatedSession, get_authenticated_session
from app.db.session import get_db


def get_auth_session(
    request: Request, db: Session = Depends(get_db)
) -> AuthenticatedSession:
    return get_authenticated_session(request, db)


def get_current_user(auth: AuthenticatedSession = Depends(get_auth_session)):
    return auth.user
