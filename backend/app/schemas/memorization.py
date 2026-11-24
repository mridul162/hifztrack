from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


AyahStatus = Literal["NOT_STARTED", "LEARNING", "MEMORIZED", "STRONG"]
EntryStatus = Literal["SUBMITTED", "CANCELLED"]


class ProgressRead(BaseModel):
    surah_number: int
    ayah_number: int
    memorization_status: AyahStatus
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProgressUpdate(BaseModel):
    memorization_status: AyahStatus
    confirm_strong: bool = False


class MemorizationEntryCreate(BaseModel):
    start_surah_number: int = Field(ge=1, le=114)
    start_ayah_number: int = Field(ge=1, le=286)
    end_surah_number: int = Field(ge=1, le=114)
    end_ayah_number: int = Field(ge=1, le=286)
    activity_date: date
    notes: str | None = None
    time_spent_minutes: int | None = Field(default=None, ge=0, le=32767)


class MemorizationEntryRead(BaseModel):
    id: UUID
    start_surah_number: int
    start_ayah_number: int
    end_surah_number: int
    end_ayah_number: int
    activity_date: date
    notes: str | None
    time_spent_minutes: int | None
    status: EntryStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
