from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import QuranAyah
from app.models.memorization import MemorizationEntry, UserAyahProgress
from app.schemas.memorization import MemorizationEntryCreate


def require_ayah(db: Session, surah_number: int, ayah_number: int) -> None:
    if db.get(QuranAyah, (surah_number, ayah_number)) is None:
        raise HTTPException(404, "Ayah reference not found")


def validate_range(db: Session, payload: MemorizationEntryCreate) -> None:
    start = (payload.start_surah_number, payload.start_ayah_number)
    end = (payload.end_surah_number, payload.end_ayah_number)
    if start > end:
        raise HTTPException(422, "Start Ayah must not follow end Ayah")
    require_ayah(db, *start)
    require_ayah(db, *end)


def entry_for_owner(db: Session, user_id: UUID, entry_id: UUID) -> MemorizationEntry:
    entry = db.scalar(
        select(MemorizationEntry)
        .where(MemorizationEntry.id == entry_id, MemorizationEntry.user_id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if entry is None:
        raise HTTPException(404, "Sabaq submission not found")
    return entry


def set_progress(
    db: Session, user_id: UUID, surah_number: int, ayah_number: int, status: str
) -> UserAyahProgress:
    require_ayah(db, surah_number, ayah_number)
    progress = db.scalar(
        select(UserAyahProgress)
        .where(
            UserAyahProgress.user_id == user_id,
            UserAyahProgress.surah_number == surah_number,
            UserAyahProgress.ayah_number == ayah_number,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if progress is None:
        progress = UserAyahProgress(
            user_id=user_id,
            surah_number=surah_number,
            ayah_number=ayah_number,
            memorization_status=status,
        )
        db.add(progress)
    else:
        progress.memorization_status = status
        progress.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Progress changed concurrently; retry the update") from exc
    db.refresh(progress)
    return progress


def submit(db: Session, user_id: UUID, payload: MemorizationEntryCreate) -> MemorizationEntry:
    validate_range(db, payload)
    entry = MemorizationEntry(user_id=user_id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def cancel(db: Session, user_id: UUID, entry_id: UUID) -> MemorizationEntry:
    entry = entry_for_owner(db, user_id, entry_id)
    if entry.status != "SUBMITTED":
        raise HTTPException(409, "Only submitted Sabaq activity can be cancelled")
    entry.status = "CANCELLED"
    db.commit()
    db.refresh(entry)
    return entry


def correct(
    db: Session, user_id: UUID, entry_id: UUID, payload: MemorizationEntryCreate
) -> MemorizationEntry:
    original = entry_for_owner(db, user_id, entry_id)
    if original.status != "SUBMITTED":
        raise HTTPException(409, "Only submitted Sabaq activity can be corrected")
    validate_range(db, payload)
    replacement = MemorizationEntry(user_id=user_id, **payload.model_dump())
    original.status = "CANCELLED"
    db.add(replacement)
    db.commit()
    db.refresh(replacement)
    return replacement
