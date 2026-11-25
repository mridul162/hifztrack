from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, insert, literal, select

from app.auth.csrf import SESSION_COOKIE_NAME
from app.auth.sessions import issue_session
from app.db.session import get_db
from app.groups.service import create_membership
from app.main import app
from app.models import Group, GroupSharingSettings, MemorizationEntry, QuranAyah, RevisionSession, User, UserAyahProgress
from app.quran.importer import import_reference
from app.quran.reference import SOURCE_PATH, load_reference_file


PERSONAL = "/dashboard/me"
ACTIVITY_DATE = date(2026, 11, 20)
CREATED_AT = datetime(2026, 11, 20, 10, tzinfo=timezone.utc)
RANGE = dict(start_surah_number=1, start_ayah_number=1, end_surah_number=1, end_ayah_number=3)


@pytest.fixture
def dashboard_client(pg_sessions):
    def override_db():
        with pg_sessions() as db:
            yield db

    with pg_sessions.begin() as db:
        import_reference(db, load_reference_file(SOURCE_PATH))
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app, base_url="https://testserver") as client:
            yield client, pg_sessions
    finally:
        app.dependency_overrides.pop(get_db, None)


def account(db, name):
    user = User(email=f"{name.lower()}@example.com", full_name=name, password_hash="test-only")
    db.add(user)
    db.flush()
    return user, issue_session(db, user)


def group(db, owner, name):
    row = Group(name=name, creator_id=owner.id)
    db.add(row)
    db.flush()
    return row


def membership(db, group, user, role="MEMBER", state="ACTIVE", **preferences):
    row = create_membership(db, group.id, user.id, role, state)
    settings = db.scalar(select(GroupSharingSettings).where(GroupSharingSettings.membership_id == row.id))
    for name, value in preferences.items():
        setattr(settings, name, value)
    return row


def add_coverage(db, user_id, count, status="MEMORIZED"):
    coordinates = select(
        literal(user_id), QuranAyah.surah_number, QuranAyah.ayah_number,
        literal(status), literal(CREATED_AT),
    ).order_by(QuranAyah.surah_number, QuranAyah.ayah_number).limit(count)
    db.execute(insert(UserAyahProgress).from_select([
        "user_id", "surah_number", "ayah_number", "memorization_status", "updated_at",
    ], coordinates))


def use_session(client, token):
    client.cookies.set(SESSION_COOKIE_NAME, token)


def read(client, path, *, expected=200, **params):
    response = client.get(path, params=params)
    assert response.status_code == expected, response.text
    if expected == 200:
        assert response.headers["cache-control"] == "private, no-store"
    return response.json()


def write(client, method, path, payload=None, *, expected=200):
    token = client.get("/auth/csrf").json()["csrf_token"]
    response = client.request(method, path, json=payload, headers={
        "X-CSRF-Token": token, "Origin": "http://localhost:3000",
    })
    assert response.status_code == expected, response.text
    return response.json()


def group_path(group):
    return f"/groups/{group.id}/dashboard"


def test_owner_dashboard_calculates_statuses_and_isolates_users(dashboard_client):
    client, sessions = dashboard_client
    with sessions.begin() as db:
        owner, owner_token = account(db, "Owner")
        peer, peer_token = account(db, "Peer")
        circle = group(db, owner, "Personal study")
        membership(db, circle, owner, "ADMIN", overall_progress_visibility="PRIVATE")
        membership(db, circle, peer, state="SUSPENDED")
        add_coverage(db, peer.id, 40)

    read(client, PERSONAL, expected=401)
    read(client, group_path(circle), expected=401)
    use_session(client, owner_token)
    empty = read(client, PERSONAL)
    assert empty["progress"] == {
        "total_memorized_ayahs": 0, "completion_percentage": 0,
        "status_counts": {"not_started": 6236, "learning": 0, "memorized": 0, "strong": 0},
    }
    assert empty["recent_sabaq"] == empty["recent_revision"] == []
    assert empty["memberships"] == [{
        "group_id": str(circle.id), "group_name": "Personal study", "role": "ADMIN", "lifecycle": "ACTIVE",
    }]
    for ayah, status in enumerate(("NOT_STARTED", "LEARNING", "MEMORIZED", "STRONG"), 1):
        write(client, "PUT", f"/memorization/progress/1/{ayah}", {
            "memorization_status": status, "confirm_strong": status == "STRONG",
        })
    progress = read(client, PERSONAL, user_id=str(peer.id))["progress"]
    assert progress == {
        "total_memorized_ayahs": 2, "completion_percentage": 0.03,
        "status_counts": {"not_started": 6233, "learning": 1, "memorized": 1, "strong": 1},
    }
    assert sum(progress["status_counts"].values()) == 6236
    read(client, f"/dashboard/{peer.id}", expected=404)

    for start in (1, 2, 1):
        write(client, "POST", "/memorization/submissions", {
            **RANGE, "start_ayah_number": start, "activity_date": str(ACTIVITY_DATE), "notes": "private Sabaq",
        }, expected=201)
    write(client, "POST", "/revision", {
        **RANGE, "activity_date": str(ACTIVITY_DATE), "revision_type": "OLD", "time_spent_minutes": 8,
    }, expected=201)
    after_activity = read(client, PERSONAL)
    assert after_activity["progress"] == progress
    assert len(after_activity["recent_sabaq"]) == 3
    assert len(after_activity["recent_revision"]) == 1

    write(client, "PUT", "/memorization/progress/1/4", {"memorization_status": "NOT_STARTED"})
    regressed = read(client, PERSONAL)["progress"]
    assert regressed == {
        "total_memorized_ayahs": 1, "completion_percentage": 0.02,
        "status_counts": {"not_started": 6234, "learning": 1, "memorized": 1, "strong": 0},
    }
    use_session(client, peer_token)
    other = read(client, PERSONAL, user_id=str(owner.id))
    assert other["progress"]["total_memorized_ayahs"] == 40
    assert other["memberships"] == other["recent_sabaq"] == other["recent_revision"] == []


def test_full_quran_and_incomplete_reference_handling(dashboard_client):
    client, sessions = dashboard_client
    with sessions.begin() as db:
        owner, token = account(db, "Owner")
        full, full_token = account(db, "Full")
        circle = group(db, owner, "Reference check")
        membership(db, circle, owner, "ADMIN")
        add_coverage(db, full.id, 6236)
    use_session(client, full_token)
    assert read(client, PERSONAL)["progress"] == {
        "total_memorized_ayahs": 6236, "completion_percentage": 100,
        "status_counts": {"not_started": 0, "learning": 0, "memorized": 6236, "strong": 0},
    }
    with sessions.begin() as db:
        db.execute(delete(UserAyahProgress).where(UserAyahProgress.user_id == full.id))
        db.execute(delete(QuranAyah).where(QuranAyah.surah_number == 114, QuranAyah.ayah_number == 6))
    use_session(client, token)
    expected_error = {"detail": "Canonical Quran references are incomplete"}
    assert read(client, PERSONAL, expected=503) == expected_error
    assert read(client, group_path(circle), expected=503) == expected_error
    write(client, "PATCH", f"/groups/{circle.id}/sharing/me", {"overall_progress_visibility": "PRIVATE"})
    assert read(client, group_path(circle))["average_completion_percentage"] is None


def test_group_average_is_permission_scoped_and_rounded_once(dashboard_client):
    client, sessions = dashboard_client
    with sessions.begin() as db:
        admin, admin_token = account(db, "Admin")
        mentor, mentor_token = account(db, "Mentor")
        reader, reader_token = account(db, "Reader")
        private, private_token = account(db, "Private")
        circle = group(db, admin, "First group")
        admin_member = membership(db, circle, admin, "ADMIN")
        mentor_member = membership(db, circle, mentor, "MENTOR", overall_progress_visibility="DETAILED")
        reader_member = membership(db, circle, reader)
        private_member = membership(db, circle, private, overall_progress_visibility="PRIVATE")
        other = group(db, private, "Second group")
        membership(db, other, private, "ADMIN")
        membership(db, other, reader, overall_progress_visibility="PRIVATE")
        add_coverage(db, mentor.id, 1, "STRONG")
        add_coverage(db, reader.id, 11)
        add_coverage(db, private.id, 43)

    expected_members = {
        str(admin_member.id): ("ADMIN", {"total_memorized_ayahs": 0, "completion_percentage": 0}),
        str(mentor_member.id): ("MENTOR", {"total_memorized_ayahs": 1, "completion_percentage": 0.02}),
        str(reader_member.id): ("MEMBER", {"total_memorized_ayahs": 11, "completion_percentage": 0.18}),
        str(private_member.id): ("MEMBER", None),
    }
    for token in (admin_token, mentor_token, reader_token):
        use_session(client, token)
        data = read(client, group_path(circle))
        assert data["active_member_count"] == 4
        assert data["contributor_count"] == 3
        # 12 / (3 × 6,236) rounds to 0.06%. Averaging rounded member percentages gives 0.07%.
        assert data["average_completion_percentage"] == 0.06
        assert {row["membership_id"]: (row["role"], row["progress"]) for row in data["members"]} == expected_members
        assert all(set(row) == {"membership_id", "display_name", "role", "progress"} for row in data["members"])
        assert data["recent_sabaq"] == data["recent_revision"] == []

    assert read(client, group_path(other))["contributor_count"] == 1
    assert read(client, group_path(other))["average_completion_percentage"] == 0.69
    use_session(client, admin_token)
    read(client, group_path(other), expected=404)
    page = read(client, group_path(circle), limit=1, offset=1)
    assert (len(page["members"]), page["member_limit"], page["member_offset"]) == (1, 1, 1)
    empty_page = read(client, group_path(circle), limit=1, offset=9)
    assert empty_page["members"] == []
    assert empty_page["active_member_count"] == 4
    assert empty_page["average_completion_percentage"] == 0.06

    for token in (mentor_token, reader_token):
        use_session(client, token)
        write(client, "PATCH", f"/groups/{circle.id}/sharing/me", {"overall_progress_visibility": "PRIVATE"})
    use_session(client, admin_token)
    zero = read(client, group_path(circle))
    assert (zero["average_completion_percentage"], zero["contributor_count"]) == (0, 1)
    write(client, "PATCH", f"/groups/{circle.id}/sharing/me", {"overall_progress_visibility": "PRIVATE"})
    unavailable = read(client, group_path(circle))
    assert (unavailable["average_completion_percentage"], unavailable["contributor_count"]) == (None, 0)
    assert all(row["progress"] is None for row in unavailable["members"])

    use_session(client, private_token)
    assert read(client, group_path(other))["average_completion_percentage"] == 0.69


def test_group_lifecycle_excludes_inactive_viewers_targets_and_activity(dashboard_client):
    client, sessions = dashboard_client
    with sessions.begin() as db:
        admin, admin_token = account(db, "Admin")
        active, active_token = account(db, "Active")
        circle = group(db, admin, "Lifecycle check")
        membership(db, circle, admin, "ADMIN")
        active_membership = membership(db, circle, active, share_revision_logs=True)
        denied_tokens = []
        for state in ("PENDING", "SUSPENDED", "LEFT"):
            inactive, token = account(db, state)
            denied_tokens.append(token)
            membership(db, circle, inactive, state=state, share_memorization_logs=True, share_revision_logs=True)
            add_coverage(db, inactive.id, 100)
            db.add(MemorizationEntry(**RANGE, user_id=inactive.id, activity_date=ACTIVITY_DATE))
            db.add(RevisionSession(**RANGE, user_id=inactive.id, activity_date=ACTIVITY_DATE,
                revision_type="RECENT", time_spent_minutes=5))
        db.add(RevisionSession(**RANGE, user_id=active.id, activity_date=ACTIVITY_DATE,
            revision_type="RECENT", time_spent_minutes=5))
    for token in denied_tokens:
        use_session(client, token)
        read(client, group_path(circle), expected=404)
    use_session(client, admin_token)
    visible = read(client, group_path(circle))
    assert [item["display_name"] for item in visible["members"]] == ["Admin", "Active"]
    assert (visible["active_member_count"], visible["contributor_count"], visible["average_completion_percentage"]) == (2, 2, 0)
    assert visible["recent_sabaq"] == []
    assert [log["display_name"] for log in visible["recent_revision"]] == ["Active"]

    active_path = f"/groups/{circle.id}/members/{active_membership.id}"
    write(client, "PATCH", active_path, {"state": "SUSPENDED"})
    suspended = read(client, group_path(circle))
    assert suspended["active_member_count"] == suspended["contributor_count"] == 1
    assert suspended["recent_revision"] == []
    use_session(client, active_token)
    read(client, group_path(circle), expected=404)
    use_session(client, admin_token)
    write(client, "PATCH", active_path, {"state": "ACTIVE"})
    write(client, "POST", f"/groups/{circle.id}/archive")
    assert read(client, group_path(circle)) == visible
    write(client, "PATCH", f"/groups/{circle.id}/sharing/me", {"share_memorization_logs": True}, expected=409)
    use_session(client, active_token)
    assert read(client, group_path(circle)) == visible
    assert read(client, PERSONAL)["memberships"][0]["lifecycle"] == "ARCHIVED"
    write(client, "POST", f"/groups/{circle.id}/leave")
    read(client, group_path(circle), expected=404)
    assert read(client, PERSONAL)["memberships"] == []
    use_session(client, admin_token)
    remaining = read(client, group_path(circle))
    assert remaining["active_member_count"] == remaining["contributor_count"] == 1
    assert remaining["recent_revision"] == []


def test_recent_activity_limits_tie_breaks_and_shared_allowlists(dashboard_client):
    client, sessions = dashboard_client
    with sessions.begin() as db:
        admin, admin_token = account(db, "Admin")
        author, author_token = account(db, "Author")
        circle = group(db, admin, "Activity check")
        membership(db, circle, admin, "ADMIN")
        author_member = membership(db, circle, author, overall_progress_visibility="PRIVATE", share_memorization_logs=True)
        for number in range(1, 7):
            coords = {**RANGE, "end_ayah_number": number}
            db.add(MemorizationEntry(**coords, id=UUID(int=number), user_id=author.id,
                activity_date=ACTIVITY_DATE, created_at=CREATED_AT, time_spent_minutes=20,
                status="CANCELLED" if number == 6 else "SUBMITTED", notes="private Sabaq marker"))
            db.add(RevisionSession(**coords, id=UUID(int=number), user_id=author.id,
                activity_date=ACTIVITY_DATE, created_at=CREATED_AT, time_spent_minutes=9,
                revision_type="OLD", self_rating=4, notes="private revision marker"))
        db.add(MemorizationEntry(**{**RANGE, "end_ayah_number": 7}, id=UUID(int=7), user_id=author.id,
            activity_date=ACTIVITY_DATE - timedelta(days=1), created_at=CREATED_AT + timedelta(hours=1)))
        db.add(RevisionSession(**{**RANGE, "end_ayah_number": 7}, id=UUID(int=7), user_id=author.id,
            activity_date=ACTIVITY_DATE - timedelta(days=1), created_at=CREATED_AT + timedelta(hours=1),
            revision_type="RECENT", time_spent_minutes=7))
    use_session(client, author_token)
    personal = read(client, PERSONAL)
    assert [row["end_ayah_number"] for row in personal["recent_sabaq"]] == [6, 5, 4, 3, 2]
    assert [row["end_ayah_number"] for row in personal["recent_revision"]] == [6, 5, 4, 3, 2]
    assert personal["recent_sabaq"][0]["notes"] == "private Sabaq marker"
    assert personal["recent_revision"][0]["notes"] == "private revision marker"
    assert len(read(client, PERSONAL, activity_limit=1)["recent_revision"]) == 1
    read(client, PERSONAL, activity_limit=0, expected=422)

    use_session(client, admin_token)
    shared = read(client, group_path(circle))
    assert [row["log"]["end_ayah_number"] for row in shared["recent_sabaq"]] == [7, 6, 5, 4, 3]
    assert shared["recent_revision"] == []
    assert set(shared["recent_sabaq"][0]) == {"membership_id", "display_name", "log"}
    assert shared["recent_sabaq"][0]["membership_id"] == str(author_member.id)
    assert shared["recent_sabaq"][1]["log"]["status"] == "CANCELLED"
    assert set(shared["recent_sabaq"][0]["log"]) == {*RANGE, "created_at", "status"}
    assert len(read(client, group_path(circle), activity_limit=1)["recent_sabaq"]) == 1
    read(client, group_path(circle), activity_limit=21, expected=422)
    read(client, group_path(circle), limit=101, expected=422)

    use_session(client, author_token)
    write(client, "PATCH", f"/groups/{circle.id}/sharing/me", {
        "share_memorization_logs": False, "share_revision_logs": True,
    })
    use_session(client, admin_token)
    updated = read(client, group_path(circle))
    assert updated["recent_sabaq"] == []
    assert [row["log"]["end_ayah_number"] for row in updated["recent_revision"]] == [6, 5, 4, 3, 2]
    assert set(updated["recent_revision"][0]["log"]) == {
        *RANGE, "activity_date", "revision_type", "time_spent_minutes", "self_rating",
    }
    assert updated["recent_revision"][0]["log"]["self_rating"] == 4
