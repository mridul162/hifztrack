from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Index,
    SmallInteger,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RevisionSession(Base):
    __tablename__ = "revision_sessions"
    __table_args__ = (
        CheckConstraint(
            "revision_type IN ('RECENT', 'OLD', 'FULL_JUZ', 'FULL_QURAN')",
            name="ck_revision_sessions_type",
        ),
        CheckConstraint(
            "time_spent_minutes >= 0", name="ck_revision_sessions_time_nonnegative"
        ),
        CheckConstraint(
            "self_rating IS NULL OR self_rating BETWEEN 1 AND 5",
            name="ck_revision_sessions_rating",
        ),
        CheckConstraint(
            "start_surah_number < end_surah_number OR "
            "(start_surah_number = end_surah_number AND start_ayah_number <= end_ayah_number)",
            name="ck_revision_sessions_range_order",
        ),
        ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(
            ["start_surah_number", "start_ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            ondelete="RESTRICT",
            name="fk_revision_sessions_start_ayah",
        ),
        ForeignKeyConstraint(
            ["end_surah_number", "end_ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            ondelete="RESTRICT",
            name="fk_revision_sessions_end_ayah",
        ),
        Index("ix_revision_sessions_user_activity", "user_id", "activity_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    start_surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_ayah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    end_surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    end_ayah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    revision_type: Mapped[str] = mapped_column(String(16), nullable=False)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    time_spent_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    self_rating: Mapped[int | None] = mapped_column(SmallInteger)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
