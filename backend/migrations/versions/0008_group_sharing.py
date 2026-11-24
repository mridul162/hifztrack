"""Add membership-scoped owner sharing settings.

Revision ID: 0008_group_sharing
Revises: 0007_revision_tracking
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008_group_sharing"
down_revision: str | None = "0007_revision_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "group_sharing_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column("overall_progress_visibility", sa.String(length=16), server_default="SUMMARY", nullable=False),
        sa.Column("share_memorization_logs", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("share_revision_logs", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("share_goals", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("share_assessments", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "overall_progress_visibility IN ('PRIVATE', 'SUMMARY', 'DETAILED')",
            name="ck_group_sharing_settings_progress_visibility",
        ),
        sa.ForeignKeyConstraint(["membership_id"], ["group_memberships.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("membership_id", name="uq_group_sharing_settings_membership"),
    )
    # Existing episodes receive the same baseline as newly created episodes.
    op.execute(sa.text("""
        INSERT INTO group_sharing_settings (id, membership_id)
        SELECT id, id FROM group_memberships
    """))


def downgrade() -> None:
    op.drop_table("group_sharing_settings")
