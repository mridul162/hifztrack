from uuid import UUID

from pydantic import BaseModel

from app.schemas.memorization import MemorizationEntryRead
from app.schemas.revision import RevisionSessionRead
from app.schemas.sharing import SharedMemorizationLog, SharedProgressSummary, SharedRevisionLog


class AyahStatusCounts(BaseModel):
    not_started: int
    learning: int
    memorized: int
    strong: int


class PersonalProgress(SharedProgressSummary):
    status_counts: AyahStatusCounts


class DashboardMembership(BaseModel):
    group_id: UUID
    group_name: str
    role: str
    lifecycle: str


class PersonalDashboard(BaseModel):
    progress: PersonalProgress
    recent_sabaq: list[MemorizationEntryRead]
    recent_revision: list[RevisionSessionRead]
    memberships: list[DashboardMembership]


class DashboardMember(BaseModel):
    membership_id: UUID
    display_name: str
    role: str
    progress: SharedProgressSummary | None


class SharedActivityMember(BaseModel):
    membership_id: UUID
    display_name: str


class DashboardSabaqActivity(SharedActivityMember):
    log: SharedMemorizationLog


class DashboardRevisionActivity(SharedActivityMember):
    log: SharedRevisionLog


class GroupDashboard(BaseModel):
    active_member_count: int
    members: list[DashboardMember]
    member_limit: int
    member_offset: int
    average_completion_percentage: float | None
    contributor_count: int
    recent_sabaq: list[DashboardSabaqActivity]
    recent_revision: list[DashboardRevisionActivity]
