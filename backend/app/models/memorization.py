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


class UserAyahProgress(Base):
    __tablename__ = "user_ayah_progress"
    __table_args__ = (
        CheckConstraint(
            "memorization_status IN ('NOT_STARTED', 'LEARNING', 'MEMORIZED', 'STRONG')",
            name="ck_user_ayah_progress_status",
        ),
        ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(
            ["surah_number", "ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            ondelete="RESTRICT",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    surah_number: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    ayah_number: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    memorization_status: Mapped[str] = mapped_column(String(16), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class MemorizationEntry(Base):
    __tablename__ = "memorization_entries"
    __table_args__ = (
        CheckConstraint(
            "status IN ('SUBMITTED', 'CANCELLED')", name="ck_memorization_entries_status"
        ),
        CheckConstraint(
            "time_spent_minutes IS NULL OR time_spent_minutes >= 0",
            name="ck_memorization_entries_time_nonnegative",
        ),
        ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(
            ["start_surah_number", "start_ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            ondelete="RESTRICT",
            name="fk_memorization_entries_start_ayah",
        ),
        ForeignKeyConstraint(
            ["end_surah_number", "end_ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            ondelete="RESTRICT",
            name="fk_memorization_entries_end_ayah",
        ),
        CheckConstraint(
            "start_surah_number < end_surah_number OR "
            "(start_surah_number = end_surah_number AND start_ayah_number <= end_ayah_number)",
            name="ck_memorization_entries_range_order",
        ),
        Index("ix_memorization_entries_user_activity", "user_id", "activity_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    start_surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_ayah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    end_surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    end_ayah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    time_spent_minutes: Mapped[int | None] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="SUBMITTED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
