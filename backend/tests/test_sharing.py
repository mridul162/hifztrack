from datetime import date, datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import (
    GroupMembership,
    GroupSharingSettings,
    MemorizationEntry,
    RevisionSession,
    User,
    UserAyahProgress,
)
from app.quran.importer import import_reference
from app.quran.reference import SOURCE_PATH, load_reference_file


@pytest.fixture
def sharing_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with factory.begin() as db:
        import_reference(db, load_reference_file(SOURCE_PATH))
    with TestClient(app, base_url="https://testserver") as client:
        yield client, factory
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def csrf(client):
    token = client.get("/auth/csrf").json()["csrf_token"]
    return {"Origin": "http://localhost:3000", "X-CSRF-Token": token}


def register(client, email, name=None):
    return client.post("/auth/register", headers=csrf(client), json={
        "email": email,
        "full_name": name or email.split("@")[0],
        "password": "correct-horse-battery",
    })


def login(client, email):
    return client.post("/auth/login", headers=csrf(client), json={
        "email": email,
        "password": "correct-horse-battery",
    })


def switch_to(client, email):
    client.post("/auth/logout", headers=csrf(client))
    assert login(client, email).status_code == 200


def accept(client, token):
    return client.post("/invitations/accept", headers=csrf(client), json={"token": token})


def settings_path(group_id):
    return f"/groups/{group_id}/sharing/me"


def test_settings_default_per_group_and_new_membership_episode(sharing_client):
    client, factory = sharing_client
    assert register(client, "owner@example.com", "Owner").status_code == 201
    first = client.post("/groups", headers=csrf(client), json={"name": "First"}).json()
    second = client.post("/groups", headers=csrf(client), json={"name": "Second"}).json()
    expected = {
        "overall_progress_visibility": "SUMMARY",
        "share_memorization_logs": False,
        "share_revision_logs": False,
        "share_goals": False,
        "share_assessments": False,
    }
    for group in (first, second):
        response = client.get(settings_path(group["id"]))
        assert response.status_code == 200
        assert {key: response.json()[key] for key in expected} == expected

    with factory() as db:
        first_membership = db.query(GroupMembership).filter_by(group_id=UUID(first["id"])).one()
        duplicate = GroupSharingSettings(membership_id=first_membership.id)
        db.add(duplicate)
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()
        settings = db.query(GroupSharingSettings).filter_by(membership_id=first_membership.id).one()
        settings.overall_progress_visibility = "INVALID"
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()

    changed = client.patch(settings_path(first["id"]), headers=csrf(client), json={
        "overall_progress_visibility": "PRIVATE",
        "share_goals": True,
    })
    assert changed.status_code == 200
    assert client.get(settings_path(first["id"])).json()["share_goals"] is True
    assert client.get(settings_path(second["id"])).json()["overall_progress_visibility"] == "SUMMARY"

    invite = client.post(f"/groups/{first['id']}/invitations", headers=csrf(client),
        json={"max_uses": 2}).json()["token"]
    switch_to(client, "owner@example.com")
    assert register(client, "member@example.com", "Member").status_code == 201
    old_episode = accept(client, invite).json()
    assert client.get(settings_path(first["id"])).json()["overall_progress_visibility"] == "SUMMARY"
    assert client.patch(settings_path(first["id"]), headers=csrf(client), json={
        "overall_progress_visibility": "DETAILED", "share_revision_logs": True,
    }).status_code == 200
    assert client.post(f"/groups/{first['id']}/leave", headers=csrf(client)).json()["state"] == "LEFT"
    switch_to(client, "owner@example.com")
    rejoin_token = client.post(f"/groups/{first['id']}/invitations", headers=csrf(client),
        json={}).json()["token"]
    switch_to(client, "member@example.com")
    new_episode = accept(client, rejoin_token).json()
    new_settings = client.get(settings_path(first["id"]))
    assert new_episode["id"] != old_episode["id"]
    assert {key: new_settings.json()[key] for key in expected} == expected
    with factory() as db:
        old = db.scalar(db.query(GroupSharingSettings).join(GroupMembership).filter(
            GroupMembership.id == UUID(old_episode["id"])
        ).statement)
        assert old.overall_progress_visibility == "DETAILED"
        assert old.share_revision_logs is True


def test_owner_settings_validation_and_cannot_target_other_membership(sharing_client):
    client, factory = sharing_client
    assert register(client, "admin@example.com", "Admin").status_code == 201
    group = client.post("/groups", headers=csrf(client), json={"name": "Owner controls"}).json()
    token = client.post(f"/groups/{group['id']}/invitations", headers=csrf(client), json={}).json()["token"]
    switch_to(client, "admin@example.com")
    assert register(client, "member@example.com", "Member").status_code == 201
    member = accept(client, token).json()
    assert client.get(settings_path(group["id"])).status_code == 200
    assert client.get(settings_path(group["id"])).json()["membership_id"] == member["id"]

    # The self-scoped route has no target membership ID for an admin/mentor to substitute.
    for invalid in (
        {"overall_progress_visibility": "ALL"},
        {"share_memorization_logs": "yes"},
        {"share_goals": None},
        {"unexpected": True},
        {},
    ):
        assert client.patch(settings_path(group["id"]), headers=csrf(client), json=invalid).status_code == 422
    assert client.get(f"/groups/{group['id']}/members/{member['id']}/sharing").status_code == 404

    switch_to(client, "admin@example.com")
    settings = client.get(settings_path(group["id"]))
    assert settings.status_code == 200
    assert settings.json()["membership_id"] == group["my_membership_id"]
    assert client.patch(f"/groups/{group['id']}/members/{member['id']}",
        headers=csrf(client), json={"role": "MENTOR"}).status_code == 200
    assert client.patch(settings_path(group["id"]), headers=csrf(client), json={
        "overall_progress_visibility": "PRIVATE",
    }).status_code == 200
    with factory() as db:
        target_settings = db.query(GroupSharingSettings).join(GroupMembership).filter(
            GroupMembership.id == UUID(member["id"])
        ).one()
        assert target_settings.overall_progress_visibility == "SUMMARY"

    switch_to(client, "member@example.com")
    assert client.patch(settings_path(group["id"]), headers=csrf(client), json={
        "overall_progress_visibility": "DETAILED",
    }).status_code == 200
    switch_to(client, "admin@example.com")
    assert client.get(settings_path(group["id"])).json()["overall_progress_visibility"] == "PRIVATE"


def test_shared_responses_filter_fields_by_group_settings_and_membership(sharing_client):
    client, factory = sharing_client
    assert register(client, "owner@example.com", "Owner").status_code == 201
    first_group = client.post("/groups", headers=csrf(client), json={"name": "Detailed"}).json()
    invite = client.post(f"/groups/{first_group['id']}/invitations", headers=csrf(client),
        json={"max_uses": 3}).json()["token"]
    switch_to(client, "owner@example.com")
    assert register(client, "admin-viewer@example.com", "Admin Viewer").status_code == 201
    admin_membership = accept(client, invite).json()
    switch_to(client, "owner@example.com")
    assert register(client, "mentor-viewer@example.com", "Mentor Viewer").status_code == 201
    mentor_membership = accept(client, invite).json()
    switch_to(client, "owner@example.com")
    assert register(client, "member-viewer@example.com", "Member Viewer").status_code == 201
    member_membership = accept(client, invite).json()
    switch_to(client, "owner@example.com")
    assert client.patch(f"/groups/{first_group['id']}/members/{admin_membership['id']}",
        headers=csrf(client), json={"role": "ADMIN"}).status_code == 200
    assert client.patch(f"/groups/{first_group['id']}/members/{mentor_membership['id']}",
        headers=csrf(client), json={"role": "MENTOR"}).status_code == 200

    with factory.begin() as db:
        owner = db.query(User).filter_by(email="owner@example.com").one()
        db.add(UserAyahProgress(user_id=owner.id, surah_number=1, ayah_number=1,
            memorization_status="MEMORIZED"))
        db.add(MemorizationEntry(user_id=owner.id, start_surah_number=1, start_ayah_number=1,
            end_surah_number=1, end_ayah_number=3, activity_date=date(2026, 11, 1),
            notes="private memorization note", time_spent_minutes=12, status="SUBMITTED",
            created_at=datetime(2026, 11, 1, 12, tzinfo=timezone.utc)))
        db.add(RevisionSession(user_id=owner.id, start_surah_number=1, start_ayah_number=1,
            end_surah_number=1, end_ayah_number=3, revision_type="RECENT",
            activity_date=date(2026, 11, 2), time_spent_minutes=8, self_rating=4,
            notes="private revision note", created_at=datetime(2026, 11, 2, 12, tzinfo=timezone.utc)))

    owner_membership_id = first_group["my_membership_id"]
    assert client.patch(settings_path(first_group["id"]), headers=csrf(client), json={
        "overall_progress_visibility": "DETAILED",
        "share_memorization_logs": True,
    }).status_code == 200
    switch_to(client, "member-viewer@example.com")
    initial_shared = client.get(
        f"/groups/{first_group['id']}/members/{owner_membership_id}/shared"
    ).json()
    assert "memorization_logs" in initial_shared and "revision_logs" not in initial_shared
    switch_to(client, "owner@example.com")
    assert client.patch(settings_path(first_group["id"]), headers=csrf(client), json={
        "share_revision_logs": True,
    }).status_code == 200
    for email in ("admin-viewer@example.com", "mentor-viewer@example.com", "member-viewer@example.com"):
        switch_to(client, email)
        response = client.get(f"/groups/{first_group['id']}/members/{owner_membership_id}/shared")
        assert response.status_code == 200
        data = response.json()
        assert len(data["detailed_progress"]) == 6236
        assert data["detailed_progress"][0] == {
            "surah_number": 1, "ayah_number": 1, "memorization_status": "MEMORIZED",
        }
        assert data["memorization_logs"][0]["status"] == "SUBMITTED"
        assert "notes" not in response.text
        assert "time_spent_minutes" not in data["memorization_logs"][0]
        assert "activity_date" not in data["memorization_logs"][0]
        assert set(data["memorization_logs"][0]) == {
            "start_surah_number", "start_ayah_number", "end_surah_number", "end_ayah_number",
            "created_at", "status",
        }
        assert "time_spent_minutes" in data["revision_logs"][0]
        assert "self_rating" in data["revision_logs"][0]
        assert "notes" not in data["revision_logs"][0]
        assert set(data["revision_logs"][0]) == {
            "start_surah_number", "start_ayah_number", "end_surah_number", "end_ayah_number",
            "revision_type", "activity_date", "time_spent_minutes", "self_rating",
        }

    switch_to(client, "owner@example.com")
    summary = client.patch(settings_path(first_group["id"]), headers=csrf(client), json={
        "overall_progress_visibility": "SUMMARY",
        "share_memorization_logs": False,
        "share_revision_logs": False,
    })
    assert summary.status_code == 200
    switch_to(client, "member-viewer@example.com")
    data = client.get(f"/groups/{first_group['id']}/members/{owner_membership_id}/shared").json()
    assert data["progress_summary"] == {"total_memorized_ayahs": 1, "completion_percentage": 0.02}
    assert "detailed_progress" not in data
    assert "memorization_logs" not in data and "revision_logs" not in data

    switch_to(client, "owner@example.com")
    assert client.patch(settings_path(first_group["id"]), headers=csrf(client), json={
        "overall_progress_visibility": "PRIVATE",
    }).status_code == 200
    switch_to(client, "member-viewer@example.com")
    private = client.get(f"/groups/{first_group['id']}/members/{owner_membership_id}/shared").json()
    assert private == {"overall_progress_visibility": "PRIVATE"}

    # An ACTIVE member cannot read through a suspended member episode, even as a group peer.
    assert client.get(f"/groups/{first_group['id']}/members/{member_membership['id']}/shared").status_code == 200
    switch_to(client, "owner@example.com")
    assert client.patch(f"/groups/{first_group['id']}/members/{member_membership['id']}",
        headers=csrf(client), json={"state": "SUSPENDED"}).status_code == 200
    switch_to(client, "admin-viewer@example.com")
    assert client.get(f"/groups/{first_group['id']}/members/{member_membership['id']}/shared").status_code == 404
    assert client.get(f"/groups/{first_group['id']}/members/{owner_membership_id}/shared").status_code == 200
    switch_to(client, "member-viewer@example.com")
    assert client.get(f"/groups/{first_group['id']}/members/{owner_membership_id}/shared").status_code == 404

    with factory.begin() as db:
        pending_membership = db.get(GroupMembership, UUID(mentor_membership["id"]))
        pending_membership.state = "PENDING"
    switch_to(client, "mentor-viewer@example.com")
    assert client.get(f"/groups/{first_group['id']}/members/{owner_membership_id}/shared").status_code == 404

    # Non-active viewers and targets cannot access shared records; group IDs remain scoped.
    switch_to(client, "owner@example.com")
    assert client.patch(f"/groups/{first_group['id']}/members/{member_membership['id']}",
        headers=csrf(client), json={"state": "LEFT"}).status_code == 200
    other_group = client.post("/groups", headers=csrf(client), json={"name": "Other group"}).json()
    other_invitation = client.post(f"/groups/{other_group['id']}/invitations", headers=csrf(client),
        json={}).json()["token"]
    switch_to(client, "member-viewer@example.com")
    assert client.get(f"/groups/{first_group['id']}/members/{owner_membership_id}/shared").status_code == 404
    switch_to(client, "admin-viewer@example.com")
    assert client.get(f"/groups/{first_group['id']}/members/{member_membership['id']}/shared").status_code == 404
    assert accept(client, other_invitation).status_code == 201
    other_owner_membership = other_group["my_membership_id"]
    other_data = client.get(
        f"/groups/{other_group['id']}/members/{other_owner_membership}/shared"
    )
    assert other_data.status_code == 200
    assert other_data.json()["overall_progress_visibility"] == "SUMMARY"
    assert "memorization_logs" not in other_data.json()
    assert client.get(f"/groups/{other_group['id']}/members/{owner_membership_id}/shared").status_code == 404
