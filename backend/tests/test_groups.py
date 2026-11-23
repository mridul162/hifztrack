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
