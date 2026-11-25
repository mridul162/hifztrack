from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.groups.service import group_for_update, require_member
from app.memorization.progress import (
    completion_percentage,
    count_memorized_ayahs,
    require_complete_ayah_references,
)
from app.models import (
    GroupMembership,
    GroupSharingSettings,
    MemorizationEntry,
    QuranAyah,
    RevisionSession,
    User,
    UserAyahProgress,
)
from app.schemas.sharing import (
    SharedAyahStatus,
    SharedMemberData,
    SharedMemorizationLog,
    SharedProgressSummary,
    SharedRevisionLog,
    SharingSettingsRead,
    SharingSettingsUpdate,
)


router = APIRouter(tags=["group-sharing"])


def _owner_membership(
    db: Session, group_id: UUID, owner_id: UUID, *, lock: bool = False
) -> GroupMembership:
    query = select(GroupMembership).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == owner_id,
            GroupMembership.state == "ACTIVE",
        )
    if lock:
        query = query.with_for_update()
    membership = db.scalar(query)
    if not membership:
        raise HTTPException(404, "Group membership not found")
    return membership


def _settings_for(db: Session, membership_id: UUID) -> GroupSharingSettings:
    settings = db.scalar(
        select(GroupSharingSettings).where(GroupSharingSettings.membership_id == membership_id)
    )
    if settings is None:
        raise HTTPException(500, "Sharing settings are unavailable")
    return settings


@router.get("/groups/{group_id}/sharing/me", response_model=SharingSettingsRead)
def get_my_sharing_settings(
    group_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    membership = _owner_membership(db, group_id, user.id)
    return _settings_for(db, membership.id)


@router.patch("/groups/{group_id}/sharing/me", response_model=SharingSettingsRead)
def update_my_sharing_settings(
    group_id: UUID,
    payload: SharingSettingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group = group_for_update(db, group_id)
    if group.lifecycle != "ACTIVE":
        raise HTTPException(409, "Sharing settings cannot be changed for an archived group")
    membership = _owner_membership(db, group_id, user.id, lock=True)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "Provide at least one sharing setting")
    settings = db.scalar(
        select(GroupSharingSettings)
        .where(GroupSharingSettings.membership_id == membership.id)
        .with_for_update()
    )
    if settings is None:
        raise HTTPException(500, "Sharing settings are unavailable")
    for field, value in changes.items():
        if value is None:
            raise HTTPException(422, "Explicit null is not allowed")
        setattr(settings, field, value)
    settings.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(settings)
    return settings


@router.get(
    "/groups/{group_id}/members/{membership_id}/shared",
    response_model=SharedMemberData,
    response_model_exclude_none=True,
)
def get_shared_member_data(
    group_id: UUID,
    membership_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_member(db, group_id, user.id)
    owner_membership = db.scalar(
        select(GroupMembership).where(
            GroupMembership.id == membership_id,
            GroupMembership.group_id == group_id,
            GroupMembership.state == "ACTIVE",
        )
    )
    if owner_membership is None:
        raise HTTPException(404, "Shared member is unavailable")
    settings = _settings_for(db, owner_membership.id)
    response = SharedMemberData(overall_progress_visibility=settings.overall_progress_visibility)

    if settings.overall_progress_visibility == "SUMMARY":
        total = count_memorized_ayahs(db, owner_membership.user_id)
        response.progress_summary = SharedProgressSummary(
            total_memorized_ayahs=total,
            completion_percentage=completion_percentage(total),
        )
    elif settings.overall_progress_visibility == "DETAILED":
        require_complete_ayah_references(db)
        rows = db.execute(
            select(QuranAyah.surah_number, QuranAyah.ayah_number, UserAyahProgress.memorization_status)
            .outerjoin(
                UserAyahProgress,
                (UserAyahProgress.surah_number == QuranAyah.surah_number)
                & (UserAyahProgress.ayah_number == QuranAyah.ayah_number)
                & (UserAyahProgress.user_id == owner_membership.user_id),
            )
            .order_by(QuranAyah.surah_number, QuranAyah.ayah_number)
        ).all()
        response.detailed_progress = [
            SharedAyahStatus(
                surah_number=surah_number,
                ayah_number=ayah_number,
                memorization_status=memorization_status or "NOT_STARTED",
            )
            for surah_number, ayah_number, memorization_status in rows
        ]

    if settings.share_memorization_logs:
        rows = db.scalars(
            select(MemorizationEntry)
            .where(MemorizationEntry.user_id == owner_membership.user_id)
            .order_by(MemorizationEntry.created_at.desc(), MemorizationEntry.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        response.memorization_logs = [
            SharedMemorizationLog(
                start_surah_number=row.start_surah_number,
                start_ayah_number=row.start_ayah_number,
                end_surah_number=row.end_surah_number,
                end_ayah_number=row.end_ayah_number,
                created_at=row.created_at,
                status=row.status,
            )
            for row in rows
        ]

    if settings.share_revision_logs:
        rows = db.scalars(
            select(RevisionSession)
            .where(RevisionSession.user_id == owner_membership.user_id)
            .order_by(RevisionSession.activity_date.desc(), RevisionSession.created_at.desc(), RevisionSession.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        response.revision_logs = [
            SharedRevisionLog(
                start_surah_number=row.start_surah_number,
                start_ayah_number=row.start_ayah_number,
                end_surah_number=row.end_surah_number,
                end_ayah_number=row.end_ayah_number,
                revision_type=row.revision_type,
                activity_date=row.activity_date,
                time_spent_minutes=row.time_spent_minutes,
                self_rating=row.self_rating,
            )
            for row in rows
        ]
    return response
