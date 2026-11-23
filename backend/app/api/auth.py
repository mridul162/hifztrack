from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.csrf import CSRF_COOKIE_NAME, create_csrf_token
from app.auth.dependencies import get_auth_session, get_current_user
from app.auth.passwords import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.auth.rate_limit import limit_login, limit_registration
from app.auth.sessions import clear_session_cookie, issue_session, revoke_session, set_session_cookie
from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.repositories.users import create_user, get_user_by_email
from app.schemas.auth import CsrfTokenResponse, LoginRequest, RegisterRequest, UserProfileUpdate, UserRead

router = APIRouter()


def normalize_email(email: str) -> str:
    return email.strip().casefold()


@router.get("/auth/csrf", response_model=CsrfTokenResponse)
def csrf_token(response: Response) -> CsrfTokenResponse:
    token = create_csrf_token(settings.security_secret_key.get_secret_value())
    response.set_cookie(
        CSRF_COOKIE_NAME, token, path="/", secure=settings.session_cookie_secure,
        httponly=False, samesite="lax",
    )
    return CsrfTokenResponse(csrf_token=token)


@router.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> UserRead:
    limit_registration(db, request)
    email = normalize_email(str(payload.email))
    if get_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    try:
        user = create_user(db, email=email, full_name=payload.full_name, password_hash=hash_password(payload.password))
        token = issue_session(db, user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from None
    set_session_cookie(response, token)
    return user


@router.post("/auth/login", response_model=UserRead)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> UserRead:
    email = normalize_email(str(payload.email))
    limit_login(db, request, email)
    user = get_user_by_email(db, email)
    password_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
    valid = verify_password(password_hash, payload.password)
    if not user or not valid or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = issue_session(db, user)
    db.commit()
    set_session_cookie(response, token)
    return user


@router.post("/auth/logout")
def logout(response: Response, auth=Depends(get_auth_session), db: Session = Depends(get_db)) -> dict[str, bool]:
    revoke_session(db, auth)
    db.commit()
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/users/me", response_model=UserRead)
def read_profile(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/users/me", response_model=UserRead)
def update_profile(payload: UserProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    user.full_name = payload.full_name
    db.commit()
    db.refresh(user)
    return user
