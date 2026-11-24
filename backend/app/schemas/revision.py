from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


RevisionType = Literal["RECENT", "OLD", "FULL_JUZ", "FULL_QURAN"]


class RevisionSessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_surah_number: int = Field(ge=1, le=114)
    start_ayah_number: int = Field(ge=1, le=286)
    end_surah_number: int = Field(ge=1, le=114)
    end_ayah_number: int = Field(ge=1, le=286)
    revision_type: RevisionType
    activity_date: date
    time_spent_minutes: int = Field(ge=0, le=32767)
    self_rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class RevisionSessionRead(BaseModel):
    id: UUID
    start_surah_number: int
    start_ayah_number: int
    end_surah_number: int
    end_ayah_number: int
    revision_type: RevisionType
    activity_date: date
    time_spent_minutes: int
    self_rating: int | None
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
