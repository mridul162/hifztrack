from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.revision.service import create_session, list_sessions
from app.schemas.revision import RevisionSessionCreate, RevisionSessionRead


router = APIRouter(prefix="/revision", tags=["personal-revision"])


@router.post("", response_model=RevisionSessionRead, status_code=status.HTTP_201_CREATED)
def create_revision_session(
    payload: RevisionSessionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_session(db, user.id, payload)


@router.get("/me", response_model=list[RevisionSessionRead])
def list_my_revision_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_sessions(db, user.id, limit, offset)
