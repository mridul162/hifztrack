from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import QuranAyah
from app.models.revision import RevisionSession
from app.schemas.revision import RevisionSessionCreate


def _validate_range(db: Session, payload: RevisionSessionCreate) -> None:
    start = (payload.start_surah_number, payload.start_ayah_number)
    end = (payload.end_surah_number, payload.end_ayah_number)
    if start > end:
        raise HTTPException(422, "Start Ayah must not follow end Ayah")
    for coordinate in (start, end):
        if db.get(QuranAyah, coordinate) is None:
            raise HTTPException(404, "Ayah reference not found")


def create_session(
    db: Session, user_id: UUID, payload: RevisionSessionCreate
) -> RevisionSession:
    _validate_range(db, payload)
    session = RevisionSession(user_id=user_id, **payload.model_dump())
    db.add(session)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Could not record revision session") from exc
    except Exception:
        db.rollback()
        raise
    db.refresh(session)
    return session


def list_sessions(
    db: Session, user_id: UUID, limit: int, offset: int
) -> list[RevisionSession]:
    return db.scalars(
        select(RevisionSession)
        .where(RevisionSession.user_id == user_id)
        .order_by(
            RevisionSession.activity_date.desc(),
            RevisionSession.created_at.desc(),
            RevisionSession.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    ).all()
