from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier, Event
from time import monotonic
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request

from app.api.groups import accept_invite, create_invitation, leave_group
from app.groups import rate_limit, service
from app.models import (Group, GroupInvitation, GroupMembership, GroupRateLimit, GroupSharingSettings, User)
from app.schemas.groups import InvitationAccept, InvitationCreate


def _user(db, label: str) -> User:
    user = User(email=f"{label}-{uuid4().hex}@example.test", full_name=label,
        password_hash="postgres-integration-test-hash")
    db.add(user)
    db.flush()
    return user


def _group(db, admin_count: int = 1) -> tuple[Group, list[User]]:
    admins = [_user(db, f"admin-{i}") for i in range(admin_count)]
    group = Group(name="PostgreSQL verification", group_type="COMMUNITY",
        creator_id=admins[0].id, lifecycle="ACTIVE")
    db.add(group)
    db.flush()
    for admin in admins:
        db.add(GroupMembership(group_id=group.id, user_id=admin.id, role="ADMIN", state="ACTIVE",
            joined_at=datetime.now(timezone.utc)))
    db.flush()
    return group, admins


def _invitation(db, group: Group, admin: User, max_uses: int) -> tuple[GroupInvitation, str]:
    token = f"pg-{uuid4().hex}-{uuid4().hex}"
    invitation = GroupInvitation(group_id=group.id, created_by=admin.id,
        token_digest=service.token_digest(token), expires_at=datetime.now(timezone.utc) + timedelta(days=2),
        max_uses=max_uses, used_count=0)
    db.add(invitation)
    db.flush()
    return invitation, token


def test_sharing_settings_database_defaults_and_membership_uniqueness(pg_sessions):
    with pg_sessions() as db:
        group, admins = _group(db)
        membership = db.scalar(select(GroupMembership).where(
            GroupMembership.group_id == group.id, GroupMembership.user_id == admins[0].id
        ))
        settings = GroupSharingSettings(membership_id=membership.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        assert settings.overall_progress_visibility == "SUMMARY"
        assert settings.share_memorization_logs is False
        assert settings.share_revision_logs is False
        assert settings.share_goals is False
        assert settings.share_assessments is False

        db.add(GroupSharingSettings(membership_id=membership.id))
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()


def _accept_concurrently(factory, token: str, user_ids: list):
    barrier = Barrier(len(user_ids))

    def attempt(user_id):
        with factory() as db:
            user = db.get(User, user_id)
            barrier.wait(timeout=10)
            try:
                membership = service.accept_invitation(db, token, user)
                return ("accepted", membership.id)
            except HTTPException as error:
                db.rollback()
                return ("rejected", error.status_code)
            except Exception:
                db.rollback()
                raise

    with ThreadPoolExecutor(max_workers=len(user_ids)) as pool:
        return list(pool.map(attempt, user_ids))


def _request_from(ip: str) -> Request:
    return Request({"type": "http", "http_version": "1.1", "method": "POST", "scheme": "http",
        "path": "/", "raw_path": b"/", "query_string": b"", "headers": [],
        "client": (ip, 50000), "server": ("localhost", 8000)})


def _wait_for_postgres_lock_wait(engine, application_name, timeout=10):
    deadline = monotonic() + timeout
    query = text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_stat_activity
            WHERE application_name = :application_name AND wait_event_type = 'Lock'
        )
    """)
    while monotonic() < deadline:
        with engine.connect() as observer:
            if observer.scalar(query, {"application_name": application_name}):
                return
        Event().wait(0.01)
    pytest.fail(f"PostgreSQL connection {application_name!r} did not enter a lock wait")


def _create_invite_as(factory, group_id, admin_id, ip: str):
    with factory() as db:
        try:
            result = create_invitation(group_id, InvitationCreate(), _request_from(ip), db, db.get(User, admin_id))
            return "created", result.id
        except HTTPException as error:
            db.rollback()
            return error.status_code, error.headers


@pytest.mark.parametrize(("max_uses", "contenders"), [(1, 2), (2, 5)])
def test_invitation_use_cap_is_atomic_under_concurrent_acceptance(pg_sessions, max_uses, contenders):
    with pg_sessions() as db:
        group, admins = _group(db)
        invitation, token = _invitation(db, group, admins[0], max_uses)
        invite_id, group_id = invitation.id, group.id
        users = [_user(db, f"invitee-{i}") for i in range(contenders)]
        user_ids = [user.id for user in users]
        db.commit()

    outcomes = _accept_concurrently(pg_sessions, token, user_ids)
    assert sum(outcome[0] == "accepted" for outcome in outcomes) == max_uses
    assert sum(outcome == ("rejected", 400) for outcome in outcomes) == contenders - max_uses
    with pg_sessions() as db:
        invitation = db.get(GroupInvitation, invite_id)
        assert invitation.used_count == max_uses
        assert db.scalar(select(func.count()).select_from(GroupMembership).where(
            GroupMembership.group_id == group_id, GroupMembership.role == "MEMBER",
            GroupMembership.state == "ACTIVE")) == max_uses


def test_last_active_admin_is_preserved_under_concurrent_leaves(pg_sessions):
    with pg_sessions() as db:
        group, admins = _group(db, admin_count=2)
        group_id = group.id
        admin_ids = [admin.id for admin in admins]
        db.commit()
    barrier = Barrier(2)

    def leave(admin_id):
        with pg_sessions() as db:
            user = db.get(User, admin_id)
            barrier.wait(timeout=10)
            try:
                leave_group(group_id, db, user)
                return "left"
            except HTTPException as error:
                db.rollback()
                return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(leave, admin_ids))
    assert sorted(outcomes, key=str) == [409, "left"]
    with pg_sessions() as db:
        assert db.scalar(select(func.count()).select_from(GroupMembership).where(
            GroupMembership.group_id == group_id, GroupMembership.role == "ADMIN",
            GroupMembership.state == "ACTIVE")) == 1


def test_single_active_admin_cannot_leave(pg_sessions):
    with pg_sessions() as db:
        group, admins = _group(db)
        group_id, admin_id = group.id, admins[0].id
        db.commit()
    with pg_sessions() as db:
        with pytest.raises(HTTPException) as error:
            leave_group(group_id, db, db.get(User, admin_id))
        assert error.value.status_code == 409
        db.rollback()
    with pg_sessions() as db:
        assert db.scalar(select(func.count()).select_from(GroupMembership).where(
            GroupMembership.group_id == group_id, GroupMembership.role == "ADMIN",
            GroupMembership.state == "ACTIVE")) == 1


def test_partial_unique_index_rejects_concurrent_current_memberships_and_allows_left(pg_sessions):
    with pg_sessions() as db:
        group, _ = _group(db)
        target = _user(db, "race-member")
        group_id, user_id = group.id, target.id
        db.commit()
    barrier = Barrier(2)

    def insert_current(_):
        with pg_sessions() as db:
            barrier.wait(timeout=10)
            db.add(GroupMembership(group_id=group_id, user_id=user_id, role="MEMBER", state="ACTIVE"))
            try:
                db.commit()
                return "inserted"
            except IntegrityError:
                db.rollback()
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(insert_current, range(2)))
    assert outcomes.count("inserted") == 1
    assert outcomes.count("conflict") == 1
    with pg_sessions() as db:
        db.add_all([
            GroupMembership(group_id=group_id, user_id=user_id, role="MEMBER", state="LEFT"),
            GroupMembership(group_id=group_id, user_id=user_id, role="MEMBER", state="LEFT"),
        ])
        db.commit()
        assert db.scalar(select(func.count()).select_from(GroupMembership).where(
            GroupMembership.group_id == group_id, GroupMembership.user_id == user_id,
            GroupMembership.state == "LEFT")) == 2
        index_definition = db.scalar(text("""
            SELECT indexdef FROM pg_indexes
            WHERE schemaname = 'public' AND indexname = 'uq_group_memberships_current'
        """))
        assert "UNIQUE INDEX uq_group_memberships_current" in index_definition
        assert all(state in index_definition for state in ("PENDING", "ACTIVE", "SUSPENDED"))
        assert "LEFT" not in index_definition


def test_expiry_is_rechecked_after_waiting_for_group_lock(pg_sessions, monkeypatch):
    fixed_now = datetime(2030, 1, 1, tzinfo=timezone.utc)
    expires_at = fixed_now + timedelta(seconds=1)
    with pg_sessions() as db:
        group, admins = _group(db)
        invitee = _user(db, "expiry-waiter")
        invitation, token = _invitation(db, group, admins[0], 1)
        invitation.expires_at = expires_at
        group_id, invite_id, invitee_id = group.id, invitation.id, invitee.id
        db.commit()

    clock = {"now": fixed_now}
    monkeypatch.setattr(service, "utcnow", lambda: clock["now"])
    application_name = f"ht-expiry-{uuid4().hex[:12]}"
    with pg_sessions() as lock_session:
        lock_session.execute(select(Group).where(Group.id == group_id).with_for_update()).one()

        def attempt():
            with pg_sessions() as db:
                db.execute(text("SELECT set_config('application_name', :name, false)"),
                           {"name": application_name})
                user = db.get(User, invitee_id)
                try:
                    service.accept_invitation(db, token, user)
                    return "accepted"
                except HTTPException as error:
                    db.rollback()
                    return error.status_code

        with ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(attempt)
            _wait_for_postgres_lock_wait(lock_session.get_bind(), application_name)
            clock["now"] = fixed_now + timedelta(seconds=2)
            lock_session.commit()
            outcome = result.result(timeout=10)
    assert outcome == 400
    with pg_sessions() as db:
        assert db.get(GroupInvitation, invite_id).used_count == 0
        assert db.scalar(select(func.count()).select_from(GroupMembership).where(
            GroupMembership.group_id == group_id, GroupMembership.user_id == invitee_id)) == 0


def test_invitation_revocation_wins_when_it_holds_group_lock_first(pg_sessions, monkeypatch):
    with pg_sessions() as db:
        group, admins = _group(db)
        invitee = _user(db, "revocation-racer")
        invitation, token = _invitation(db, group, admins[0], 1)
        group_id, invite_id, invitee_id = group.id, invitation.id, invitee.id
        db.commit()
    application_name = f"ht-revoke-{uuid4().hex[:12]}"
    with pg_sessions() as revoker:
        revoker.execute(select(Group).where(Group.id == group_id).with_for_update()).one()

        def attempt():
            with pg_sessions() as db:
                db.execute(text("SELECT set_config('application_name', :name, false)"),
                           {"name": application_name})
                try:
                    service.accept_invitation(db, token, db.get(User, invitee_id))
                    return "accepted"
                except HTTPException as error:
                    db.rollback()
                    return error.status_code

        with ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(attempt)
            _wait_for_postgres_lock_wait(revoker.get_bind(), application_name)
            invitation = revoker.get(GroupInvitation, invite_id)
            invitation.revoked_at = datetime.now(timezone.utc)
            revoker.commit()
            outcome = result.result(timeout=10)
    assert outcome == 400
    with pg_sessions() as db:
        invite = db.get(GroupInvitation, invite_id)
        assert invite.revoked_at is not None and invite.used_count == 0
        assert db.scalar(select(func.count()).select_from(GroupMembership).where(
            GroupMembership.group_id == group_id, GroupMembership.user_id == invitee_id)) == 0


@pytest.mark.parametrize(("scope", "subject", "maximum", "window"), [
    ("invite-user", "user-identifier", 10, 3600),
    ("invite-group", "group-identifier", 30, 3600),
    ("invite-ip", "198.51.100.12", 20, 3600),
    ("accept-ip", "ip-digest-identifier", 30, 900),
    ("accept-token", "token-digest-identifier", 10, 900),
])
def test_each_invitation_rate_scope_enforces_exact_boundary_and_hmac_storage(
    pg_sessions, monkeypatch, scope, subject, maximum, window
):
    fixed_timestamp = 1_900_000_000.0
    monkeypatch.setattr(rate_limit.time, "time", lambda: fixed_timestamp)
    for _ in range(maximum):
        with pg_sessions() as db:
            rate_limit.consume(db, [(scope, subject, maximum, window)])
    with pg_sessions() as db:
        with pytest.raises(HTTPException) as error:
            rate_limit.consume(db, [(scope, subject, maximum, window)])
        assert error.value.status_code == 429
        assert error.value.detail == "Too many requests. Try again later."
        retry_after = int(error.value.headers["Retry-After"])
        assert retry_after > 0
        row = db.scalar(select(GroupRateLimit).where(GroupRateLimit.scope == scope))
        assert row.attempts == maximum + 1
        assert row.key_digest != subject and subject not in row.key_digest


def test_concurrent_rate_limit_requests_cannot_exceed_the_allowed_successes(pg_sessions, monkeypatch):
    fixed_timestamp = 1_900_000_000.0
    monkeypatch.setattr(rate_limit.time, "time", lambda: fixed_timestamp)
    subject = "shared-ip-203.0.113.55"
    contenders, maximum = 24, 20
    barrier = Barrier(contenders)

    def request(_):
        with pg_sessions() as db:
            barrier.wait(timeout=10)
            try:
                rate_limit.consume(db, [("invite-ip", subject, maximum, 3600)])
                return "allowed"
            except HTTPException as error:
                assert error.status_code == 429
                assert int(error.headers["Retry-After"]) > 0
                return "blocked"

    with ThreadPoolExecutor(max_workers=contenders) as pool:
        results = list(pool.map(request, range(contenders)))
    assert results.count("allowed") == maximum
    assert results.count("blocked") == contenders - maximum
    with pg_sessions() as db:
        row = db.scalar(select(GroupRateLimit).where(GroupRateLimit.scope == "invite-ip"))
        assert row.attempts == contenders
        assert subject not in row.key_digest


def test_rate_limit_subjects_are_isolated_and_expired_rows_are_cleaned(pg_sessions, monkeypatch):
    fixed_timestamp = 1_900_000_000.0
    monkeypatch.setattr(rate_limit.time, "time", lambda: fixed_timestamp)
    for subject in ("user-a", "user-b", "group-a", "ip-a", "token-a"):
        with pg_sessions() as db:
            rate_limit.consume(db, [("identity-test", subject, 2, 900)])
    with pg_sessions() as db:
        rows = db.scalars(select(GroupRateLimit).where(GroupRateLimit.scope == "identity-test")).all()
        assert len(rows) == 5
        assert all(row.attempts == 1 for row in rows)
        assert all(row.key_digest not in {"user-a", "user-b", "group-a", "ip-a", "token-a"} for row in rows)
        expired = GroupRateLimit(scope="old-scope", key_digest="a" * 64,
            window_start=datetime.fromtimestamp(fixed_timestamp - 7200, timezone.utc),
            attempts=1, expires_at=datetime.fromtimestamp(fixed_timestamp - 1, timezone.utc))
        db.add(expired)
        db.commit()
    with pg_sessions() as db:
        rate_limit.consume(db, [("cleanup-trigger", "one", 5, 900)])
    with pg_sessions() as db:
        assert db.scalar(select(func.count()).select_from(GroupRateLimit).where(
            GroupRateLimit.scope == "old-scope")) == 0


def test_creation_user_limit_is_bound_to_user_not_group_or_ip(pg_sessions, monkeypatch):
    monkeypatch.setattr(rate_limit.time, "time", lambda: 1_900_000_000.0)
    with pg_sessions() as db:
        group, admins = _group(db, admin_count=2)
        group_id, first_id, second_id = group.id, admins[0].id, admins[1].id
        db.commit()
    outcomes = [_create_invite_as(pg_sessions, group_id, first_id, "198.51.100.31") for _ in range(10)]
    assert all(result[0] == "created" for result in outcomes)
    blocked = _create_invite_as(pg_sessions, group_id, first_id, "198.51.100.31")
    assert blocked[0] == 429 and int(blocked[1]["Retry-After"]) > 0
    other_user = _create_invite_as(pg_sessions, group_id, second_id, "198.51.100.31")
    assert other_user[0] == "created"


def test_creation_group_limit_is_bound_to_group_not_user_or_ip(pg_sessions, monkeypatch):
    monkeypatch.setattr(rate_limit.time, "time", lambda: 1_900_000_000.0)
    with pg_sessions() as db:
        group, admins = _group(db, admin_count=31)
        group_id, admin_ids = group.id, [admin.id for admin in admins]
        other_group, other_admins = _group(db)
        other_group_id, other_admin_id = other_group.id, other_admins[0].id
        db.commit()
    outcomes = [_create_invite_as(pg_sessions, group_id, user_id, f"198.51.100.{i + 1}")
        for i, user_id in enumerate(admin_ids[:30])]
    assert all(result[0] == "created" for result in outcomes)
    blocked = _create_invite_as(pg_sessions, group_id, admin_ids[30], "198.51.101.99")
    assert blocked[0] == 429 and int(blocked[1]["Retry-After"]) > 0
    other_group_result = _create_invite_as(pg_sessions, other_group_id, other_admin_id, "198.51.102.99")
    assert other_group_result[0] == "created"


def test_creation_ip_limit_is_bound_to_ip_not_user_or_group(pg_sessions, monkeypatch):
    monkeypatch.setattr(rate_limit.time, "time", lambda: 1_900_000_000.0)
    with pg_sessions() as db:
        group, admins = _group(db, admin_count=21)
        group_id, admin_ids = group.id, [admin.id for admin in admins]
        other_group, other_admins = _group(db)
        other_group_id, other_admin_id = other_group.id, other_admins[0].id
        db.commit()
    outcomes = [_create_invite_as(pg_sessions, group_id, user_id, "203.0.113.25")
        for user_id in admin_ids[:20]]
    assert all(result[0] == "created" for result in outcomes)
    blocked = _create_invite_as(pg_sessions, group_id, admin_ids[20], "203.0.113.25")
    assert blocked[0] == 429 and int(blocked[1]["Retry-After"]) > 0
    other_ip_result = _create_invite_as(pg_sessions, other_group_id, other_admin_id, "203.0.113.26")
    assert other_ip_result[0] == "created"


def _accept_invalid_as(factory, user_id, token: str, ip: str):
    with factory() as db:
        try:
            accept_invite(InvitationAccept(token=token), _request_from(ip), db, db.get(User, user_id))
            return "accepted"
        except HTTPException as error:
            db.rollback()
            if error.status_code == 429:
                return error.status_code, error.headers
            return error.status_code


def test_acceptance_ip_limit_is_independent_of_token_digest(pg_sessions, monkeypatch):
    monkeypatch.setattr(rate_limit.time, "time", lambda: 1_900_000_000.0)
    with pg_sessions() as db:
        user = _user(db, "accept-rate-user")
        user_id = user.id
        db.commit()
    outcomes = [_accept_invalid_as(pg_sessions, user_id, f"token-{i:02d}-" + "x" * 40, "192.0.2.44")
        for i in range(30)]
    assert outcomes == [400] * 30
    blocked = _accept_invalid_as(pg_sessions, user_id, "token-30-" + "x" * 40, "192.0.2.44")
    assert blocked[0] == 429 and int(blocked[1]["Retry-After"]) > 0
    assert _accept_invalid_as(pg_sessions, user_id, "different-ip-token-" + "x" * 40, "192.0.2.45") == 400


def test_acceptance_token_limit_is_independent_of_other_token_digests(pg_sessions, monkeypatch):
    monkeypatch.setattr(rate_limit.time, "time", lambda: 1_900_000_000.0)
    with pg_sessions() as db:
        user = _user(db, "accept-token-user")
        user_id = user.id
        db.commit()
    token = "repeated-token-" + "x" * 40
    outcomes = [_accept_invalid_as(pg_sessions, user_id, token, "192.0.2.71") for _ in range(10)]
    assert outcomes == [400] * 10
    blocked = _accept_invalid_as(pg_sessions, user_id, token, "192.0.2.71")
    assert blocked[0] == 429 and int(blocked[1]["Retry-After"]) > 0
    assert _accept_invalid_as(pg_sessions, user_id, "different-token-" + "x" * 40, "192.0.2.71") == 400
