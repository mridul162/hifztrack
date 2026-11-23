import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Group, GroupInvitation, GroupMembership, GroupMembershipEvent, User


def token_digest(token: str) -> str:
    secret = settings.security_secret_key.get_secret_value().encode()
    return hmac.new(secret, b"group-invite-v1\0" + token.encode(), hashlib.sha256).hexdigest()


def require_member(db: Session, group_id: UUID, user_id: UUID) -> GroupMembership:
    result = db.scalar(select(GroupMembership).where(GroupMembership.group_id == group_id,
        GroupMembership.user_id == user_id, GroupMembership.state == "ACTIVE"))
    if not result:
        raise HTTPException(404, "Group not found")
    return result


def require_admin(db: Session, group_id: UUID, user_id: UUID) -> GroupMembership:
    result = require_member(db, group_id, user_id)
    if result.role != "ADMIN":
        raise HTTPException(404, "Group not found")
    return result


def group_for_update(db: Session, group_id: UUID) -> Group:
    group = db.scalar(select(Group).where(Group.id == group_id).with_for_update())
    if not group:
        raise HTTPException(404, "Group not found")
    return group


def record_event(db: Session, row: GroupMembership, actor_id: UUID, event_type: str,
                 previous: str | None = None, new: str | None = None) -> None:
    db.add(GroupMembershipEvent(membership_id=row.id, group_id=row.group_id, actor_id=actor_id,
        event_type=event_type, previous_value=previous, new_value=new))


def revoke_admin_invitations(db: Session, group_id: UUID, user_id: UUID) -> None:
    for invite in db.scalars(select(GroupInvitation).where(GroupInvitation.group_id == group_id,
            GroupInvitation.created_by == user_id, GroupInvitation.revoked_at.is_(None))).all():
        invite.revoked_at = datetime.now(timezone.utc)


def create_invitation(db: Session, group_id: UUID, user_id: UUID, expires_days: int,
                      max_uses: int) -> tuple[GroupInvitation, str]:
    group = group_for_update(db, group_id)
    if group.lifecycle != "ACTIVE":
        raise HTTPException(409, "Group is archived")
    require_admin(db, group_id, user_id)
    token = secrets.token_urlsafe(32)
    invite = GroupInvitation(group_id=group_id, created_by=user_id, token_digest=token_digest(token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days), max_uses=max_uses, used_count=0)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite, token


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def accept_invitation(db: Session, token: str, user: User) -> GroupMembership:
    digest = token_digest(token)
    invite = db.scalar(select(GroupInvitation).where(GroupInvitation.token_digest == digest))
    now = datetime.now(timezone.utc)
    if not invite or invite.revoked_at or _as_utc(invite.expires_at) <= now:
        raise HTTPException(400, "Invitation is invalid or unavailable")
    group = group_for_update(db, invite.group_id)
    invite = db.scalar(select(GroupInvitation).where(GroupInvitation.id == invite.id).with_for_update())
    if not invite or invite.revoked_at or _as_utc(invite.expires_at) <= now:
        raise HTTPException(400, "Invitation is invalid or unavailable")
    if group.lifecycle != "ACTIVE" or (invite.max_uses is not None and invite.used_count >= invite.max_uses):
        raise HTTPException(400, "Invitation is invalid or unavailable")
    current = db.scalar(select(GroupMembership).where(GroupMembership.group_id == group.id,
        GroupMembership.user_id == user.id, GroupMembership.state.in_(["PENDING", "ACTIVE", "SUSPENDED"])))
    if current:
        raise HTTPException(409, "Membership already exists")
    row = GroupMembership(group_id=group.id, user_id=user.id, role="MEMBER", state="ACTIVE", joined_at=now)
    db.add(row)
    db.flush()
    record_event(db, row, user.id, "JOINED", None, "ACTIVE")
    invite.used_count += 1
    db.commit()
    db.refresh(row)
    return row
