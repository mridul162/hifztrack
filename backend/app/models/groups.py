from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, UniqueConstraint, text)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Group(Base):
    __tablename__ = "groups"
    __table_args__ = (
        CheckConstraint("group_type IN ('COMMUNITY', 'CLASS', 'COHORT')", name="ck_groups_group_type"),
        CheckConstraint("lifecycle IN ('ACTIVE', 'ARCHIVED')", name="ck_groups_lifecycle"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_type: Mapped[str] = mapped_column(String(16), nullable=False, default="COMMUNITY")
    creator_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    lifecycle: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class GroupMembership(Base):
    __tablename__ = "group_memberships"
    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'MENTOR', 'MEMBER')", name="ck_group_memberships_role"),
        CheckConstraint("state IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'LEFT')", name="ck_group_memberships_state"),
        Index("uq_group_memberships_current", "group_id", "user_id", unique=True, postgresql_where=text("state IN ('PENDING', 'ACTIVE', 'SUSPENDED')"), sqlite_where=text("state IN ('PENDING', 'ACTIVE', 'SUSPENDED')")),
        Index("ix_group_memberships_user_group", "user_id", "group_id"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    group_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("groups.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="MEMBER")
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class GroupInvitation(Base):
    __tablename__ = "group_invitations"
    __table_args__ = (
        CheckConstraint("max_uses IS NULL OR max_uses > 0", name="ck_group_invitations_max_uses_positive"),
        CheckConstraint("used_count >= 0", name="ck_group_invitations_used_count_nonnegative"),
        UniqueConstraint("token_digest", name="uq_group_invitations_token_digest"),
        Index("ix_group_invitations_group", "group_id", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    group_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("groups.id", ondelete="RESTRICT"), nullable=False)
    created_by: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    token_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True, default=1)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class GroupMembershipEvent(Base):
    __tablename__ = "group_membership_events"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("group_memberships.id", ondelete="RESTRICT"), nullable=False, index=True)
    group_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("groups.id", ondelete="RESTRICT"), nullable=False, index=True)
    actor_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_value: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class GroupRateLimit(Base):
    __tablename__ = "group_rate_limits"
    __table_args__ = (Index("ix_group_rate_limits_expires_at", "expires_at"),)
    scope: Mapped[str] = mapped_column(String(40), primary_key=True)
    key_digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
