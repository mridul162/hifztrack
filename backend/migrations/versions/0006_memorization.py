"""Add personal Ayah progress and Sabaq history.

Revision ID: 0006_memorization
Revises: 0005_quran_reference_sources
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006_memorization"
down_revision: str | None = "0005_quran_reference_sources"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_ayah_progress",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("surah_number", sa.SmallInteger(), nullable=False),
        sa.Column("ayah_number", sa.SmallInteger(), nullable=False),
        sa.Column("memorization_status", sa.String(length=16), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "memorization_status IN ('NOT_STARTED', 'LEARNING', 'MEMORIZED', 'STRONG')",
            name="ck_user_ayah_progress_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["surah_number", "ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("user_id", "surah_number", "ayah_number"),
    )
    op.create_table(
        "memorization_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("start_surah_number", sa.SmallInteger(), nullable=False),
        sa.Column("start_ayah_number", sa.SmallInteger(), nullable=False),
        sa.Column("end_surah_number", sa.SmallInteger(), nullable=False),
        sa.Column("end_ayah_number", sa.SmallInteger(), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("time_spent_minutes", sa.SmallInteger(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('SUBMITTED', 'CANCELLED')", name="ck_memorization_entries_status"
        ),
        sa.CheckConstraint(
            "time_spent_minutes IS NULL OR time_spent_minutes >= 0",
            name="ck_memorization_entries_time_nonnegative",
        ),
        sa.CheckConstraint(
            "start_surah_number < end_surah_number OR "
            "(start_surah_number = end_surah_number AND start_ayah_number <= end_ayah_number)",
            name="ck_memorization_entries_range_order",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["start_surah_number", "start_ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            ondelete="RESTRICT",
            name="fk_memorization_entries_start_ayah",
        ),
        sa.ForeignKeyConstraint(
            ["end_surah_number", "end_ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            ondelete="RESTRICT",
            name="fk_memorization_entries_end_ayah",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_memorization_entries_user_activity",
        "memorization_entries",
        ["user_id", "activity_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_memorization_entries_user_activity", table_name="memorization_entries")
    op.drop_table("memorization_entries")
    op.drop_table("user_ayah_progress")
