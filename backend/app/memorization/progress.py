from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import QuranAyah, UserAyahProgress
from app.quran.reference import EXPECTED_AYAH_COUNT


MEMORIZED_STATUSES = ("MEMORIZED", "STRONG")


def completion_percentage(total_memorized: int, contributors: int = 1) -> float:
    return round(total_memorized * 100 / (EXPECTED_AYAH_COUNT * contributors), 2)


def count_memorized_ayahs(db: Session, user_id: UUID) -> int:
    return db.scalar(
        select(func.count()).select_from(UserAyahProgress).where(
            UserAyahProgress.user_id == user_id,
            UserAyahProgress.memorization_status.in_(MEMORIZED_STATUSES),
        )
    ) or 0


def require_complete_ayah_references(db: Session) -> None:
    if db.scalar(select(func.count()).select_from(QuranAyah)) != EXPECTED_AYAH_COUNT:
        raise HTTPException(503, "Canonical Quran references are incomplete")
