"""Add groups, membership episodes, invitations and invitation throttles.

Revision ID: 0003_groups
Revises: 0002_auth
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_groups"
down_revision: str | None = "0002_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "groups",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("group_type", sa.String(16), nullable=False),
        sa.Column("creator_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("lifecycle", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("group_type IN ('COMMUNITY', 'CLASS', 'COHORT')", name="ck_groups_group_type"),
        sa.CheckConstraint("lifecycle IN ('ACTIVE', 'ARCHIVED')", name="ck_groups_lifecycle"),
    )
    op.create_index("ix_groups_organization_id", "groups", ["organization_id"])
    op.create_index("ix_groups_creator_id", "groups", ["creator_id"])
    op.create_table(
        "group_memberships",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("group_id", sa.Uuid(), sa.ForeignKey("groups.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True)),
        sa.Column("left_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('ADMIN', 'MENTOR', 'MEMBER')", name="ck_group_memberships_role"),
        sa.CheckConstraint("state IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'LEFT')", name="ck_group_memberships_state"),
    )
    op.create_index("uq_group_memberships_current", "group_memberships", ["group_id", "user_id"],
        unique=True, postgresql_where=sa.text("state IN ('PENDING', 'ACTIVE', 'SUSPENDED')"),
        sqlite_where=sa.text("state IN ('PENDING', 'ACTIVE', 'SUSPENDED')"))
    op.create_index("ix_group_memberships_user_group", "group_memberships", ["user_id", "group_id"])
    op.create_table(
        "group_invitations",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("group_id", sa.Uuid(), sa.ForeignKey("groups.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("token_digest", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_uses", sa.Integer()),
        sa.Column("used_count", sa.Integer(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("max_uses IS NULL OR max_uses > 0", name="ck_group_invitations_max_uses_positive"),
        sa.CheckConstraint("used_count >= 0", name="ck_group_invitations_used_count_nonnegative"),
        sa.UniqueConstraint("token_digest", name="uq_group_invitations_token_digest"),
    )
    op.create_index("ix_group_invitations_group", "group_invitations", ["group_id", "created_at"])
    op.create_table(
        "group_membership_events",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("membership_id", sa.Uuid(), sa.ForeignKey("group_memberships.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("group_id", sa.Uuid(), sa.ForeignKey("groups.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("previous_value", sa.String(32)),
        sa.Column("new_value", sa.String(32)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_group_membership_events_membership_id", "group_membership_events", ["membership_id"])
    op.create_index("ix_group_membership_events_group_id", "group_membership_events", ["group_id"])
    op.create_table(
        "group_rate_limits",
        sa.Column("scope", sa.String(40), primary_key=True, nullable=False),
        sa.Column("key_digest", sa.String(64), primary_key=True, nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), primary_key=True, nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_group_rate_limits_expires_at", "group_rate_limits", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_group_rate_limits_expires_at", table_name="group_rate_limits")
    op.drop_table("group_rate_limits")
    op.drop_index("ix_group_membership_events_group_id", table_name="group_membership_events")
    op.drop_index("ix_group_membership_events_membership_id", table_name="group_membership_events")
    op.drop_table("group_membership_events")
    op.drop_index("ix_group_invitations_group", table_name="group_invitations")
    op.drop_table("group_invitations")
    op.drop_index("ix_group_memberships_user_group", table_name="group_memberships")
    op.drop_index("uq_group_memberships_current", table_name="group_memberships")
    op.drop_table("group_memberships")
    op.drop_index("ix_groups_creator_id", table_name="groups")
    op.drop_index("ix_groups_organization_id", table_name="groups")
    op.drop_table("groups")
    op.drop_table("organizations")
