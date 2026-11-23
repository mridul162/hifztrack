from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.models import GroupInvitation, GroupMembership


def register(client, csrf, email, name="Member"):
    return client.post("/auth/register", headers=csrf, json={"email": email,
        "full_name": name, "password": "correct-horse-battery"})


def test_group_creation_membership_and_roster_privacy(client, csrf_headers):
    assert register(client, csrf_headers, "admin@example.com", "Group Admin").status_code == 201
    created = client.post("/groups", headers=csrf_headers, json={"name": "Circle", "group_type": "COMMUNITY"})
    assert created.status_code == 201
    group = created.json()
    assert group["my_role"] == "ADMIN" and group["my_state"] == "ACTIVE"
    assert client.get("/groups").json()[0]["id"] == group["id"]
    roster = client.get(f"/groups/{group['id']}/members")
    assert roster.status_code == 200
    assert roster.json()["items"][0]["display_name"] == "Group Admin"
    assert "email" not in roster.text and "password_hash" not in roster.text


def test_group_access_is_membership_scoped(client, csrf_headers):
    register(client, csrf_headers, "one@example.com", "One")
    group = client.post("/groups", headers=csrf_headers, json={"name": "Private"}).json()
    client.post("/auth/logout", headers=csrf_headers)
    register(client, csrf_headers, "two@example.com", "Two")
    assert client.get(f"/groups/{group['id']}").status_code == 404
    assert client.get(f"/groups/{group['id']}/members").status_code == 404
    assert client.patch(f"/groups/{group['id']}", headers=csrf_headers,
        json={"name": "Taken over"}).status_code == 404


def test_organization_association_does_not_grant_group_access(client, csrf_headers):
    from app.db.session import get_db
    from app.main import app
    from app.models import Organization
    register(client, csrf_headers, "org-owner@example.com", "Org Owner")
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        org = Organization(name="Metadata only")
        db.add(org)
        db.commit()
        organization_id = str(org.id)
    finally:
        db.close()
    group = client.post("/groups", headers=csrf_headers, json={"name": "Org group",
        "organization_id": organization_id}).json()
    assert group["organization_id"] == organization_id
    client.post("/auth/logout", headers=csrf_headers)
    register(client, csrf_headers, "org-outsider@example.com", "Outsider")
    assert client.get(f"/groups/{group['id']}").status_code == 404


def test_invitation_is_digest_only_and_join_leave_rejoin_preserves_episode(client, csrf_headers):
    from app.main import app
    from app.db.session import get_db
    register(client, csrf_headers, "owner@example.com", "Owner")
    group = client.post("/groups", headers=csrf_headers, json={"name": "Study"}).json()
    invitation = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={})
    assert invitation.status_code == 201
    token = invitation.json()["token"]
    assert invitation.json()["max_uses"] == 1
    expires_at = datetime.fromisoformat(invitation.json()["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    remaining = expires_at - datetime.now(timezone.utc)
    assert timedelta(days=6, hours=23) < remaining <= timedelta(days=7)
    listed = client.get(f"/groups/{group['id']}/invitations")
    assert listed.status_code == 200
    assert token not in listed.text
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        stored = db.query(GroupInvitation).one()
        assert stored.token_digest != token and len(stored.token_digest) == 64
    finally:
        db.close()
    client.post("/auth/logout", headers=csrf_headers)
    register(client, csrf_headers, "joiner@example.com", "Joiner")
    assert client.post("/invitations/accept", headers=csrf_headers, json={"token": "invalid"}).status_code == 422
    joined = client.post("/invitations/accept", headers=csrf_headers, json={"token": token})
    assert joined.status_code == 201 and joined.json()["role"] == "MEMBER"
    assert client.post("/invitations/accept", headers=csrf_headers, json={"token": token}).status_code == 400
    old_id = joined.json()["id"]
    client.post("/auth/logout", headers=csrf_headers)
    client.post("/auth/login", headers=csrf_headers, json={"email": "owner@example.com", "password": "correct-horse-battery"})
    assert client.patch(f"/groups/{group['id']}/members/{old_id}", headers=csrf_headers,
        json={"role": "MENTOR"}).json()["role"] == "MENTOR"
    client.post("/auth/logout", headers=csrf_headers)
    client.post("/auth/login", headers=csrf_headers, json={"email": "joiner@example.com", "password": "correct-horse-battery"})
    assert client.get(f"/groups/{group['id']}").status_code == 200
    assert client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).status_code == 404
    assert client.post(f"/groups/{group['id']}/leave", headers=csrf_headers).json()["state"] == "LEFT"
    client.post("/auth/logout", headers=csrf_headers)
    # Log back in as the group admin to issue a new single-use invitation.
    client.post("/auth/login", headers=csrf_headers, json={"email": "owner@example.com", "password": "correct-horse-battery"})
    second = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()["token"]
    client.post("/auth/logout", headers=csrf_headers)
    client.post("/auth/login", headers=csrf_headers, json={"email": "joiner@example.com", "password": "correct-horse-battery"})
    rejoined = client.post("/invitations/accept", headers=csrf_headers, json={"token": second})
    assert rejoined.status_code == 201 and rejoined.json()["id"] != old_id
    client.post("/auth/logout", headers=csrf_headers)
    client.post("/auth/login", headers=csrf_headers, json={"email": "owner@example.com", "password": "correct-horse-battery"})
    assert client.patch(f"/groups/{group['id']}/members/{rejoined.json()['id']}", headers=csrf_headers,
        json={"state": "SUSPENDED"}).json()["state"] == "SUSPENDED"
    another = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()["token"]
    client.post("/auth/logout", headers=csrf_headers)
    client.post("/auth/login", headers=csrf_headers, json={"email": "joiner@example.com", "password": "correct-horse-battery"})
    assert client.get(f"/groups/{group['id']}").status_code == 404
    assert client.post("/invitations/accept", headers=csrf_headers, json={"token": another}).status_code == 409
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        assert db.query(GroupMembership).filter_by(group_id=UUID(group["id"]), state="LEFT").count() == 1
    finally:
        db.close()


def test_last_active_admin_is_protected_and_archive_revokes_invites(client, csrf_headers):
    from app.main import app
    from app.db.session import get_db
    register(client, csrf_headers, "solo@example.com", "Solo Admin")
    group = client.post("/groups", headers=csrf_headers, json={"name": "Solo"}).json()
    membership_id = group["my_membership_id"]
    assert client.patch(f"/groups/{group['id']}/members/{membership_id}", headers=csrf_headers,
        json={"state": "SUSPENDED"}).status_code == 404
    assert client.post(f"/groups/{group['id']}/leave", headers=csrf_headers).status_code == 409
    invite = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()
    archived = client.post(f"/groups/{group['id']}/archive", headers=csrf_headers)
    assert archived.status_code == 200 and archived.json()["lifecycle"] == "ARCHIVED"
    assert client.post("/invitations/accept", headers=csrf_headers, json={"token": invite["token"]}).status_code == 400
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        assert db.query(GroupInvitation).one().revoked_at is not None
    finally:
        db.close()


def test_invitation_expiry_and_rate_limits(client, csrf_headers):
    from app.main import app
    from app.db.session import get_db
    register(client, csrf_headers, "rate-owner@example.com", "Owner")
    group = client.post("/groups", headers=csrf_headers, json={"name": "Rate"}).json()
    token = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()["token"]
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        row = db.query(GroupInvitation).one()
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()
    assert client.post("/invitations/accept", headers=csrf_headers, json={"token": token}).status_code == 400


def test_revoked_invitation_cannot_be_accepted(client, csrf_headers):
    register(client, csrf_headers, "revoke-owner@example.com", "Owner")
    group = client.post("/groups", headers=csrf_headers, json={"name": "Revoked"}).json()
    invite = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()
    assert client.post(f"/groups/{group['id']}/invitations/{invite['id']}/revoke",
        headers=csrf_headers).status_code == 200
    assert client.post("/invitations/accept", headers=csrf_headers,
        json={"token": invite["token"]}).status_code == 400


def test_group_mutations_require_csrf(client):
    response = client.post("/groups", headers={"Origin": "http://localhost:3000"}, json={"name": "No CSRF"})
    assert response.status_code == 403


def test_group_reads_require_authentication(client):
    assert client.get("/groups").status_code == 401


def test_member_update_rejects_explicit_null_and_accepts_valid_partial_updates(client, csrf_headers):
    register(client, csrf_headers, "null-owner@example.com", "Owner")
    group = client.post("/groups", headers=csrf_headers, json={"name": "Null validation"}).json()
    token = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()["token"]
    client.post("/auth/logout", headers=csrf_headers)
    register(client, csrf_headers, "null-member@example.com", "Member")
    member = client.post("/invitations/accept", headers=csrf_headers, json={"token": token}).json()
    client.post("/auth/logout", headers=csrf_headers)
    client.post("/auth/login", headers=csrf_headers, json={"email": "null-owner@example.com", "password": "correct-horse-battery"})
    url = f"/groups/{group['id']}/members/{member['id']}"
    for payload in ({"role": None}, {"state": None}, {"role": None, "state": "ACTIVE"}, {}):
        assert client.patch(url, headers=csrf_headers, json=payload).status_code == 422
    role_only = client.patch(url, headers=csrf_headers, json={"role": "MENTOR"})
    assert role_only.status_code == 200
    assert role_only.json()["role"] == "MENTOR" and role_only.json()["state"] == "ACTIVE"
    state_only = client.patch(url, headers=csrf_headers, json={"state": "SUSPENDED"})
    assert state_only.status_code == 200
    assert state_only.json()["state"] == "SUSPENDED" and state_only.json()["role"] == "MENTOR"


def test_acceptance_rechecks_expiry_with_fresh_time_after_locks(client, csrf_headers, monkeypatch):
    from app.db.session import get_db
    from app.groups import service
    from app.main import app
    from app.models import User
    from fastapi import HTTPException

    register(client, csrf_headers, "fresh-time-owner@example.com", "Owner")
    group = client.post("/groups", headers=csrf_headers, json={"name": "Fresh time"}).json()
    token = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()["token"]
    client.post("/auth/logout", headers=csrf_headers)
    register(client, csrf_headers, "fresh-time-member@example.com", "Member")
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    initial = datetime(2030, 1, 1, tzinfo=timezone.utc)
    try:
        invite = db.query(GroupInvitation).one()
        invite.expires_at = initial + timedelta(seconds=1)
        db.commit()
        user = db.query(User).filter_by(email="fresh-time-member@example.com").one()
        times = iter((initial, initial + timedelta(seconds=2)))
        monkeypatch.setattr(service, "utcnow", lambda: next(times))
        try:
            service.accept_invitation(db, token, user)
            raise AssertionError("expired-after-lock invitation was accepted")
        except HTTPException as error:
            assert error.status_code == 400
        db.refresh(invite)
        assert invite.used_count == 0
        assert db.query(GroupMembership).filter_by(group_id=UUID(group["id"]), user_id=user.id).count() == 0
    finally:
        db.close()


def test_archived_group_remains_readable_and_member_can_leave(client, csrf_headers):
    register(client, csrf_headers, "archive-owner@example.com", "Owner")
    group = client.post("/groups", headers=csrf_headers, json={"name": "Archived read"}).json()
    token = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()["token"]
    client.post("/auth/logout", headers=csrf_headers)
    register(client, csrf_headers, "archive-member@example.com", "Member")
    assert client.post("/invitations/accept", headers=csrf_headers, json={"token": token}).status_code == 201
    client.post("/auth/logout", headers=csrf_headers)
    client.post("/auth/login", headers=csrf_headers, json={"email": "archive-owner@example.com", "password": "correct-horse-battery"})
    assert client.post(f"/groups/{group['id']}/archive", headers=csrf_headers).status_code == 200
    assert client.patch(f"/groups/{group['id']}", headers=csrf_headers,
        json={"name": "No changes"}).status_code == 409
    client.post("/auth/logout", headers=csrf_headers)
    client.post("/auth/login", headers=csrf_headers, json={"email": "archive-member@example.com", "password": "correct-horse-battery"})
    assert client.get(f"/groups/{group['id']}").status_code == 200
    assert client.post(f"/groups/{group['id']}/leave", headers=csrf_headers).json()["state"] == "LEFT"


def test_losing_admin_role_revokes_invitations_created_by_that_admin(client, csrf_headers):
    from app.db.session import get_db
    from app.main import app
    register(client, csrf_headers, "demote-owner@example.com", "Owner")
    group = client.post("/groups", headers=csrf_headers, json={"name": "Demote admin"}).json()
    member_token = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()["token"]
    client.post("/auth/logout", headers=csrf_headers)
    register(client, csrf_headers, "demote-member@example.com", "Second Admin")
    member = client.post("/invitations/accept", headers=csrf_headers, json={"token": member_token}).json()
    client.post("/auth/logout", headers=csrf_headers)
    client.post("/auth/login", headers=csrf_headers, json={"email": "demote-owner@example.com", "password": "correct-horse-battery"})
    assert client.patch(f"/groups/{group['id']}/members/{member['id']}", headers=csrf_headers,
        json={"role": "ADMIN"}).status_code == 200
    owner_id = client.get("/users/me").json()["id"]
    pending_token = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()["token"]
    client.post("/auth/logout", headers=csrf_headers)
    client.post("/auth/login", headers=csrf_headers, json={"email": "demote-member@example.com", "password": "correct-horse-battery"})
    assert client.patch(f"/groups/{group['id']}/members/{group['my_membership_id']}", headers=csrf_headers,
        json={"role": "MEMBER"}).status_code == 200
    client.post("/auth/logout", headers=csrf_headers)
    register(client, csrf_headers, "demote-invitee@example.com", "Invitee")
    assert client.post("/invitations/accept", headers=csrf_headers,
        json={"token": pending_token}).status_code == 400
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        invitation = db.query(GroupInvitation).filter_by(group_id=UUID(group["id"]),
            created_by=UUID(owner_id)).order_by(GroupInvitation.created_at.desc()).first()
        assert invitation is not None and invitation.revoked_at is not None
    finally:
        db.close()


def test_admin_leave_revokes_that_admins_invitations(client, csrf_headers):
    register(client, csrf_headers, "leave-admin@example.com", "Owner")
    group = client.post("/groups", headers=csrf_headers, json={"name": "Admin leave"}).json()
    first_token = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()["token"]
    client.post("/auth/logout", headers=csrf_headers)
    register(client, csrf_headers, "leave-second-admin@example.com", "Second")
    invited = client.post("/invitations/accept", headers=csrf_headers, json={"token": first_token}).json()
    client.post("/auth/logout", headers=csrf_headers)
    client.post("/auth/login", headers=csrf_headers, json={"email": "leave-admin@example.com", "password": "correct-horse-battery"})
    assert client.patch(f"/groups/{group['id']}/members/{invited['id']}", headers=csrf_headers,
        json={"role": "ADMIN"}).status_code == 200
    pending_token = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).json()["token"]
    assert client.post(f"/groups/{group['id']}/leave", headers=csrf_headers).json()["state"] == "LEFT"
    assert client.post("/invitations/accept", headers=csrf_headers,
        json={"token": pending_token}).status_code == 400


def test_invitation_creation_rate_limits_user_scope(client, csrf_headers):
    register(client, csrf_headers, "limit@example.com", "Limit Owner")
    group = client.post("/groups", headers=csrf_headers, json={"name": "Limit"}).json()
    for _ in range(10):
        assert client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={}).status_code == 201
    blocked = client.post(f"/groups/{group['id']}/invitations", headers=csrf_headers, json={})
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Too many requests. Try again later."
    assert blocked.headers.get("Retry-After")


def test_partial_unique_index_allows_left_history_but_blocks_current_duplicates(client, csrf_headers):
    from sqlalchemy.exc import IntegrityError
    from app.db.session import get_db
    from app.main import app
    register(client, csrf_headers, "history@example.com", "History User")
    group = client.post("/groups", headers=csrf_headers, json={"name": "History"}).json()
    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        current = db.query(GroupMembership).filter_by(group_id=UUID(group["id"])).one()
        db.add(GroupMembership(group_id=current.group_id, user_id=current.user_id, role="MEMBER", state="ACTIVE"))
        try:
            db.flush()
            raise AssertionError("partial unique index did not reject a duplicate current episode")
        except IntegrityError:
            db.rollback()
        db.add(GroupMembership(group_id=current.group_id, user_id=current.user_id, role="MEMBER", state="LEFT"))
        db.commit()
        assert db.query(GroupMembership).filter_by(group_id=UUID(group["id"]), state="LEFT").count() == 1
    finally:
        db.close()


def test_invitation_acceptance_rate_limits_per_token_digest(client, csrf_headers):
    register(client, csrf_headers, "accept-limit@example.com", "Rate Reader")
    for _ in range(10):
        response = client.post("/invitations/accept", headers=csrf_headers,
            json={"token": "t" * 43})
        assert response.status_code == 400
    blocked = client.post("/invitations/accept", headers=csrf_headers,
        json={"token": "t" * 43})
    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After")
