from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    group_type: str = Field(default="COMMUNITY", pattern="^(COMMUNITY|CLASS|COHORT)$")
    organization_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Group name must not be blank")
        return value


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Group name must not be blank")
        return value


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organization_id: UUID | None
    name: str
    description: str | None
    group_type: str
    creator_id: UUID
    lifecycle: str
    created_at: datetime
    updated_at: datetime
    my_role: str
    my_state: str
    my_membership_id: UUID


class MemberRead(BaseModel):
    id: UUID
    display_name: str
    role: str
    state: str
    joined_at: datetime | None
    left_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MemberPage(BaseModel):
    items: list[MemberRead]
    limit: int
    offset: int
    total: int


class MemberUpdate(BaseModel):
    role: str | None = Field(default=None, pattern="^(ADMIN|MENTOR|MEMBER)$")
    state: str | None = Field(default=None, pattern="^(ACTIVE|SUSPENDED|LEFT)$")

    @field_validator("role", "state", mode="before")
    @classmethod
    def reject_explicit_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Explicit null is not allowed")
        return value


class InvitationCreate(BaseModel):
    expires_in_days: int = Field(default=7, ge=1, le=30)
    max_uses: int = Field(default=1, ge=1, le=100)


class InvitationCreated(BaseModel):
    id: UUID
    token: str
    expires_at: datetime
    max_uses: int


class InvitationRead(BaseModel):
    id: UUID
    created_by: UUID
    expires_at: datetime
    max_uses: int | None
    used_count: int
    revoked_at: datetime | None
    created_at: datetime


class InvitationAccept(BaseModel):
    token: str = Field(min_length=32, max_length=256)


class MembershipRead(BaseModel):
    id: UUID
    group_id: UUID
    user_id: UUID
    role: str
    state: str
    joined_at: datetime | None
    left_at: datetime | None
