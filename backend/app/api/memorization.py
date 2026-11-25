from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.models.memorization import UserAyahProgress
from app.memorization.service import cancel, correct, set_progress, submit
from app.memorization.service import list_submissions as list_user_submissions
from app.schemas.memorization import (
    MemorizationEntryCreate,
    MemorizationEntryRead,
    ProgressRead,
    ProgressUpdate,
)


router = APIRouter(prefix="/memorization", tags=["personal-memorization"])


@router.get("/progress", response_model=list[ProgressRead])
def list_progress(
    surah_number: int | None = Query(default=None, ge=1, le=114),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(UserAyahProgress).where(UserAyahProgress.user_id == user.id)
    if surah_number is not None:
        query = query.where(UserAyahProgress.surah_number == surah_number)
    return db.scalars(
        query.order_by(UserAyahProgress.surah_number, UserAyahProgress.ayah_number)
    ).all()


@router.put("/progress/{surah_number}/{ayah_number}", response_model=ProgressRead)
def update_progress(
    surah_number: int,
    ayah_number: int,
    payload: ProgressUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.memorization_status == "STRONG" and not payload.confirm_strong:
        raise HTTPException(422, "Explicit confirmation is required to mark an Ayah STRONG")
    return set_progress(db, user.id, surah_number, ayah_number, payload.memorization_status)


@router.post("/submissions", response_model=MemorizationEntryRead, status_code=201)
def create_submission(
    payload: MemorizationEntryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return submit(db, user.id, payload)


@router.get("/submissions", response_model=list[MemorizationEntryRead])
def list_submissions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return list_user_submissions(db, user.id, limit, offset)


@router.post("/submissions/{entry_id}/cancel", response_model=MemorizationEntryRead)
def cancel_submission(
    entry_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cancel(db, user.id, entry_id)


@router.post(
    "/submissions/{entry_id}/correct",
    response_model=MemorizationEntryRead,
    status_code=201,
)
def correct_submission(
    entry_id: UUID,
    payload: MemorizationEntryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return correct(db, user.id, entry_id, payload)
