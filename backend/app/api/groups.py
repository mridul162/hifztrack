import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.groups.rate_limit import consume
from app.groups.service import (accept_invitation, group_for_update, record_event, require_admin,
    create_membership, require_member, revoke_admin_invitations, token_digest)
from app.models import Group, GroupInvitation, GroupMembership, GroupMembershipEvent, Organization, User
from app.schemas.groups import (GroupCreate, GroupRead, GroupUpdate, InvitationAccept,
    InvitationCreate, InvitationCreated, InvitationRead, MemberPage, MemberRead, MemberUpdate,
    MembershipRead)

router = APIRouter()


def _admin(db: Session, group_id: UUID, user_id: UUID) -> GroupMembership:
    group = group_for_update(db, group_id)
    if group.lifecycle != "ACTIVE":
        raise HTTPException(409, "Group is archived")
    return require_admin(db, group_id, user_id)


def _group_read(group: Group, membership: GroupMembership) -> GroupRead:
    return GroupRead(**{key: getattr(group, key) for key in ("id", "organization_id", "name",
        "description", "group_type", "creator_id", "lifecycle", "created_at", "updated_at")},
        my_role=membership.role, my_state=membership.state, my_membership_id=membership.id)


@router.post("/groups", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.organization_id and not db.get(Organization, payload.organization_id):
        raise HTTPException(422, "Organization is unavailable")
    try:
        group = Group(name=payload.name.strip(), description=payload.description,
            group_type=payload.group_type, organization_id=payload.organization_id, creator_id=user.id,
            lifecycle="ACTIVE")
        db.add(group)
        db.flush()
        member = create_membership(db, group.id, user.id, "ADMIN", "ACTIVE", datetime.now(timezone.utc))
        record_event(db, member, user.id, "JOINED", None, "ACTIVE")
        db.commit()
        db.refresh(group)
        db.refresh(member)
        return _group_read(group, member)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Could not create group") from None


@router.get("/groups", response_model=list[GroupRead])
def list_groups(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(select(Group, GroupMembership).join(GroupMembership,
        GroupMembership.group_id == Group.id).where(GroupMembership.user_id == user.id,
        GroupMembership.state == "ACTIVE").order_by(Group.created_at.desc())).all()
    return [_group_read(group, member) for group, member in rows]


@router.get("/groups/{group_id}", response_model=GroupRead)
def get_group(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    member = require_member(db, group_id, user.id)
    group = db.get(Group, group_id)
    return _group_read(group, member)


@router.patch("/groups/{group_id}", response_model=GroupRead)
def update_group(group_id: UUID, payload: GroupUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _admin(db, group_id, user.id)
    group = group_for_update(db, group_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None or key == "description":
            setattr(group, key, value.strip() if key == "name" and value else value)
    db.commit()
    db.refresh(group)
    return _group_read(group, require_member(db, group_id, user.id))


@router.post("/groups/{group_id}/archive", response_model=GroupRead)
def archive_group(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _admin(db, group_id, user.id)
    group = group_for_update(db, group_id)
    if group.lifecycle == "ACTIVE":
        group.lifecycle = "ARCHIVED"
        now = datetime.now(timezone.utc)
        for invite in db.scalars(select(GroupInvitation).where(GroupInvitation.group_id == group_id,
                GroupInvitation.revoked_at.is_(None))).all():
            invite.revoked_at = now
        db.commit()
    db.refresh(group)
    return _group_read(group, require_member(db, group_id, user.id))


@router.get("/groups/{group_id}/members", response_model=MemberPage)
def list_members(group_id: UUID, limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0),
                 db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_member(db, group_id, user.id)
    query = select(GroupMembership, User.full_name).join(User, User.id == GroupMembership.user_id).where(
        GroupMembership.group_id == group_id).order_by(GroupMembership.created_at, GroupMembership.id)
    total = db.scalar(select(func.count()).select_from(GroupMembership).where(GroupMembership.group_id == group_id)) or 0
    rows = db.execute(query.limit(limit).offset(offset)).all()
    return MemberPage(items=[MemberRead(id=row.id, display_name=name, role=row.role, state=row.state,
        joined_at=row.joined_at, left_at=row.left_at, created_at=row.created_at, updated_at=row.updated_at)
        for row, name in rows], limit=limit, offset=offset, total=total)


@router.post("/groups/{group_id}/invitations", response_model=InvitationCreated, status_code=201)
def create_invitation(group_id: UUID, payload: InvitationCreate, request: Request,
                      db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _admin(db, group_id, user.id)
    ip = request.client.host if request.client else "unknown"
    consume(db, [("invite-user", str(user.id), 10, 3600), ("invite-group", str(group_id), 30, 3600),
        ("invite-ip", ip, 20, 3600)])
    from app.groups.service import create_invitation as make_invite
    invitation, token = make_invite(db, group_id, user.id, payload.expires_in_days, payload.max_uses)
    return InvitationCreated(id=invitation.id, token=token, expires_at=invitation.expires_at,
        max_uses=invitation.max_uses or 1)


@router.get("/groups/{group_id}/invitations", response_model=list[InvitationRead])
def list_invitations(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _admin(db, group_id, user.id)
    return db.scalars(select(GroupInvitation).where(GroupInvitation.group_id == group_id)
        .order_by(GroupInvitation.created_at.desc())).all()


@router.post("/groups/{group_id}/invitations/{invitation_id}/revoke", response_model=InvitationRead)
def revoke_invitation(group_id: UUID, invitation_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _admin(db, group_id, user.id)
    invite = db.scalar(select(GroupInvitation).where(GroupInvitation.id == invitation_id,
        GroupInvitation.group_id == group_id).with_for_update())
    if not invite:
        raise HTTPException(404, "Invitation not found")
    if not invite.revoked_at:
        invite.revoked_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(invite)
    return invite


@router.post("/invitations/accept", response_model=MembershipRead, status_code=201)
def accept_invite(payload: InvitationAccept, request: Request, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    secret = settings.security_secret_key.get_secret_value().encode()
    raw = f"accept-ip\0{request.client.host if request.client else 'unknown'}".encode()
    ip_digest = hmac.new(secret, raw, hashlib.sha256).hexdigest()
    token_hash = token_digest(payload.token)
    consume(db, [("accept-ip", ip_digest, 30, 900), ("accept-token", token_hash, 10, 900)])
    try:
        return accept_invitation(db, payload.token, user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Membership already exists or invitation is unavailable") from None


@router.patch("/groups/{group_id}/members/{membership_id}", response_model=MembershipRead)
def update_member(group_id: UUID, membership_id: UUID, payload: MemberUpdate, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    _admin(db, group_id, user.id)
    group = group_for_update(db, group_id)
    if group.lifecycle != "ACTIVE":
        raise HTTPException(409, "Group is archived")
    row = db.scalar(select(GroupMembership).where(GroupMembership.id == membership_id,
        GroupMembership.group_id == group_id).with_for_update())
    if not row or row.state == "LEFT" or row.user_id == user.id:
        raise HTTPException(404, "Membership not found")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "Provide a role or state")
    if row.role == "ADMIN" and row.state == "ACTIVE" and (changes.get("role", row.role) != "ADMIN" or changes.get("state", row.state) != "ACTIVE"):
        count = db.scalar(select(func.count()).select_from(GroupMembership).where(GroupMembership.group_id == group_id,
            GroupMembership.role == "ADMIN", GroupMembership.state == "ACTIVE")) or 0
        if count <= 1:
            raise HTTPException(409, "A group must retain an active admin")
    for field, value in changes.items():
        previous = getattr(row, field)
        if previous != value:
            setattr(row, field, value)
            record_event(db, row, user.id, "ROLE_CHANGED" if field == "role" else "STATE_CHANGED", previous, value)
    if row.state == "LEFT":
        row.left_at = datetime.now(timezone.utc)
    if row.state != "ACTIVE" or row.role != "ADMIN":
        revoke_admin_invitations(db, group_id, row.user_id)
    db.commit()
    db.refresh(row)
    return row


@router.post("/groups/{group_id}/leave", response_model=MembershipRead)
def leave_group(group_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    group = group_for_update(db, group_id)
    row = db.scalar(select(GroupMembership).where(GroupMembership.group_id == group_id,
        GroupMembership.user_id == user.id, GroupMembership.state == "ACTIVE").with_for_update())
    if not row:
        raise HTTPException(404, "Group membership not found")
    if row.role == "ADMIN":
        count = db.scalar(select(func.count()).select_from(GroupMembership).where(GroupMembership.group_id == group_id,
            GroupMembership.role == "ADMIN", GroupMembership.state == "ACTIVE")) or 0
        if count <= 1:
            raise HTTPException(409, "Transfer admin role before leaving")
    row.state = "LEFT"
    row.left_at = datetime.now(timezone.utc)
    record_event(db, row, user.id, "LEFT", "ACTIVE", "LEFT")
    revoke_admin_invitations(db, group_id, user.id)
    db.commit()
    db.refresh(row)
    return row
