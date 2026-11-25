from uuid import UUID

from sqlalchemy import and_, func, select, true
from sqlalchemy.orm import Session

from app.groups.service import require_member
from app.memorization.progress import (
    MEMORIZED_STATUSES,
    completion_percentage,
    require_complete_ayah_references,
)
from app.memorization.service import list_submissions
from app.models import (
    Group,
    GroupMembership,
    GroupSharingSettings,
    MemorizationEntry,
    RevisionSession,
    User,
    UserAyahProgress,
)
from app.quran.reference import EXPECTED_AYAH_COUNT
from app.revision.service import list_sessions
from app.schemas.dashboard import (
    AyahStatusCounts,
    DashboardMember,
    DashboardMembership,
    DashboardRevisionActivity,
    DashboardSabaqActivity,
    GroupDashboard,
    PersonalDashboard,
    PersonalProgress,
)
from app.schemas.sharing import SharedMemorizationLog, SharedProgressSummary, SharedRevisionLog


def _progress_summary(total: int) -> SharedProgressSummary:
    return SharedProgressSummary(
        total_memorized_ayahs=total,
        completion_percentage=completion_percentage(total),
    )


def personal_dashboard(db: Session, user_id: UUID, activity_limit: int) -> PersonalDashboard:
    require_complete_ayah_references(db)
    ayah_status = UserAyahProgress.memorization_status
    counts = dict(db.execute(
        select(ayah_status, func.count())
        .where(UserAyahProgress.user_id == user_id, ayah_status != "NOT_STARTED")
        .group_by(ayah_status)
    ).tuples().all())
    memorized = sum(counts.get(status, 0) for status in MEMORIZED_STATUSES)
    status_counts = AyahStatusCounts(
        not_started=EXPECTED_AYAH_COUNT - sum(counts.values()),
        learning=counts.get("LEARNING", 0),
        memorized=counts.get("MEMORIZED", 0),
        strong=counts.get("STRONG", 0),
    )
    memberships = db.execute(
        select(Group.id.label("group_id"), Group.name.label("group_name"), GroupMembership.role, Group.lifecycle)
        .join(GroupMembership, GroupMembership.group_id == Group.id)
        .where(GroupMembership.user_id == user_id, GroupMembership.state == "ACTIVE")
        .order_by(Group.created_at.desc(), Group.id.desc())
    ).mappings()
    return PersonalDashboard(
        progress=PersonalProgress(
            total_memorized_ayahs=memorized,
            completion_percentage=completion_percentage(memorized),
            status_counts=status_counts,
        ),
        recent_sabaq=list_submissions(db, user_id, activity_limit, 0),
        recent_revision=list_sessions(db, user_id, activity_limit, 0),
        memberships=[DashboardMembership.model_validate(row) for row in memberships],
    )


def group_dashboard(
    db: Session, group_id: UUID, user_id: UUID, activity_limit: int, member_limit: int, member_offset: int,
) -> GroupDashboard:
    require_member(db, group_id, user_id)
    active_members = (
        select(
            GroupMembership.id.label("membership_id"), GroupMembership.user_id, GroupMembership.role,
            GroupMembership.created_at, User.full_name.label("display_name"),
            GroupSharingSettings.overall_progress_visibility,
            GroupSharingSettings.share_memorization_logs, GroupSharingSettings.share_revision_logs,
        )
        .join(User, User.id == GroupMembership.user_id)
        .outerjoin(GroupSharingSettings, GroupSharingSettings.membership_id == GroupMembership.id)
        .where(GroupMembership.group_id == group_id, GroupMembership.state == "ACTIVE")
        .cte("active_members")
    )
    members = active_members.c
    coverage = (
        select(members.membership_id, func.count(UserAyahProgress.user_id).label("memorized"))
        .select_from(active_members)
        .outerjoin(UserAyahProgress, and_(
            UserAyahProgress.user_id == members.user_id,
            UserAyahProgress.memorization_status.in_(MEMORIZED_STATUSES),
        ))
        .where(members.overall_progress_visibility.in_(("SUMMARY", "DETAILED")))
        .group_by(members.membership_id)
        .cte("shared_coverage")
    )
    totals = select(
        select(func.count()).select_from(active_members).scalar_subquery().label("active_member_count"),
        func.count(coverage.c.membership_id).label("contributor_count"),
        func.coalesce(func.sum(coverage.c.memorized), 0).label("total_memorized"),
    ).cte("dashboard_totals")
    roster = (
        select(members.membership_id, members.display_name, members.role, members.created_at, coverage.c.memorized)
        .select_from(active_members)
        .outerjoin(coverage, coverage.c.membership_id == members.membership_id)
        .order_by(members.created_at, members.membership_id)
        .limit(member_limit)
        .offset(member_offset)
        .subquery()
    )
    # Keep the whole-group totals even when the requested roster page is empty.
    rows = db.execute(
        select(totals, roster).select_from(totals).outerjoin(roster, true())
        .order_by(roster.c.created_at, roster.c.membership_id)
    ).all()
    totals_row = rows[0]
    contributors = totals_row.contributor_count
    if contributors:
        require_complete_ayah_references(db)

    sabaq = MemorizationEntry
    sabaq_rows = db.execute(
        select(
            members.membership_id, members.display_name, sabaq.start_surah_number, sabaq.start_ayah_number,
            sabaq.end_surah_number, sabaq.end_ayah_number, sabaq.created_at, sabaq.status,
        )
        .join(active_members, members.user_id == sabaq.user_id)
        .where(members.share_memorization_logs.is_(True))
        .order_by(sabaq.created_at.desc(), sabaq.id.desc())
        .limit(activity_limit)
    ).mappings()
    revision = RevisionSession
    revision_rows = db.execute(
        select(
            members.membership_id, members.display_name, revision.start_surah_number, revision.start_ayah_number,
            revision.end_surah_number, revision.end_ayah_number, revision.revision_type, revision.activity_date,
            revision.time_spent_minutes, revision.self_rating,
        )
        .join(active_members, members.user_id == revision.user_id)
        .where(members.share_revision_logs.is_(True))
        .order_by(revision.activity_date.desc(), revision.created_at.desc(), revision.id.desc())
        .limit(activity_limit)
    ).mappings()
    return GroupDashboard(
        active_member_count=totals_row.active_member_count,
        members=[
            DashboardMember(
                membership_id=row.membership_id, display_name=row.display_name, role=row.role,
                progress=_progress_summary(row.memorized) if row.memorized is not None else None,
            )
            for row in rows if row.membership_id is not None
        ],
        member_limit=member_limit,
        member_offset=member_offset,
        contributor_count=contributors,
        average_completion_percentage=(
            completion_percentage(int(totals_row.total_memorized), contributors) if contributors else None
        ),
        recent_sabaq=[
            DashboardSabaqActivity(
                membership_id=row.membership_id, display_name=row.display_name,
                log=SharedMemorizationLog.model_validate(row),
            )
            for row in sabaq_rows
        ],
        recent_revision=[
            DashboardRevisionActivity(
                membership_id=row.membership_id, display_name=row.display_name,
                log=SharedRevisionLog.model_validate(row),
            )
            for row in revision_rows
        ],
    )
