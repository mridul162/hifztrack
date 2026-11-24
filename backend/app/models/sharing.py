from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, Uuid, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GroupSharingSettings(Base):
    __tablename__ = "group_sharing_settings"
    __table_args__ = (
        UniqueConstraint("membership_id", name="uq_group_sharing_settings_membership"),
        CheckConstraint(
            "overall_progress_visibility IN ('PRIVATE', 'SUMMARY', 'DETAILED')",
            name="ck_group_sharing_settings_progress_visibility",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    membership_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("group_memberships.id", ondelete="RESTRICT"),
        nullable=False,
    )
    overall_progress_visibility: Mapped[str] = mapped_column(
        String(16), nullable=False, default="SUMMARY", server_default=text("'SUMMARY'")
    )
    share_memorization_logs: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )
    share_revision_logs: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )
    share_goals: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )
    share_assessments: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )
