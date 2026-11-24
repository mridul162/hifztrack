"""Add immutable personal revision session history.

Revision ID: 0007_revision_tracking
Revises: 0006_memorization
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007_revision_tracking"
down_revision: str | None = "0006_memorization"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "revision_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("start_surah_number", sa.SmallInteger(), nullable=False),
        sa.Column("start_ayah_number", sa.SmallInteger(), nullable=False),
        sa.Column("end_surah_number", sa.SmallInteger(), nullable=False),
        sa.Column("end_ayah_number", sa.SmallInteger(), nullable=False),
        sa.Column("revision_type", sa.String(length=16), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("time_spent_minutes", sa.SmallInteger(), nullable=False),
        sa.Column("self_rating", sa.SmallInteger(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "revision_type IN ('RECENT', 'OLD', 'FULL_JUZ', 'FULL_QURAN')",
            name="ck_revision_sessions_type",
        ),
        sa.CheckConstraint(
            "time_spent_minutes >= 0", name="ck_revision_sessions_time_nonnegative"
        ),
        sa.CheckConstraint(
            "self_rating IS NULL OR self_rating BETWEEN 1 AND 5",
            name="ck_revision_sessions_rating",
        ),
        sa.CheckConstraint(
            "start_surah_number < end_surah_number OR "
            "(start_surah_number = end_surah_number AND start_ayah_number <= end_ayah_number)",
            name="ck_revision_sessions_range_order",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["start_surah_number", "start_ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            ondelete="RESTRICT",
            name="fk_revision_sessions_start_ayah",
        ),
        sa.ForeignKeyConstraint(
            ["end_surah_number", "end_ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            ondelete="RESTRICT",
            name="fk_revision_sessions_end_ayah",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_revision_sessions_user_activity",
        "revision_sessions",
        ["user_id", "activity_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_revision_sessions_user_activity", table_name="revision_sessions")
    op.drop_table("revision_sessions")
