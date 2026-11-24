from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictBool


ProgressVisibility = Literal["PRIVATE", "SUMMARY", "DETAILED"]


class SharingSettingsRead(BaseModel):
    membership_id: UUID
    overall_progress_visibility: ProgressVisibility
    share_memorization_logs: bool
    share_revision_logs: bool
    share_goals: bool
    share_assessments: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SharingSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_progress_visibility: ProgressVisibility | None = None
    share_memorization_logs: StrictBool | None = None
    share_revision_logs: StrictBool | None = None
    share_goals: StrictBool | None = None
    share_assessments: StrictBool | None = None


class SharedProgressSummary(BaseModel):
    total_memorized_ayahs: int
    completion_percentage: float


class SharedAyahStatus(BaseModel):
    surah_number: int
    ayah_number: int
    memorization_status: Literal["NOT_STARTED", "LEARNING", "MEMORIZED", "STRONG"]


class SharedMemorizationLog(BaseModel):
    start_surah_number: int
    start_ayah_number: int
    end_surah_number: int
    end_ayah_number: int
    created_at: datetime
    status: Literal["SUBMITTED", "CANCELLED"]


class SharedRevisionLog(BaseModel):
    start_surah_number: int
    start_ayah_number: int
    end_surah_number: int
    end_ayah_number: int
    revision_type: Literal["RECENT", "OLD", "FULL_JUZ", "FULL_QURAN"]
    activity_date: date
    time_spent_minutes: int
    self_rating: int | None


class SharedMemberData(BaseModel):
    overall_progress_visibility: ProgressVisibility
    progress_summary: SharedProgressSummary | None = None
    detailed_progress: list[SharedAyahStatus] | None = None
    memorization_logs: list[SharedMemorizationLog] | None = None
    revision_logs: list[SharedRevisionLog] | None = None
