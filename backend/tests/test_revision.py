from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import RevisionSession, User
from app.quran.importer import import_reference
from app.quran.reference import SOURCE_PATH, load_reference_file


@pytest.fixture
def revision_client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with session_factory.begin() as db:
        import_reference(db, load_reference_file(SOURCE_PATH))
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client, session_factory
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def _csrf_headers(client):
    token = client.get("/auth/csrf").json()["csrf_token"]
    return {"Origin": "http://localhost:3000", "X-CSRF-Token": token}


def _register(client, email):
    return client.post(
        "/auth/register",
        headers=_csrf_headers(client),
        json={
            "email": email,
            "full_name": "Revision Learner",
            "password": "correct-horse-battery",
        },
    )


def _session_payload(**overrides):
    payload = {
        "start_surah_number": 1,
        "start_ayah_number": 1,
        "end_surah_number": 2,
        "end_ayah_number": 2,
        "revision_type": "RECENT",
        "activity_date": "2026-11-24",
        "time_spent_minutes": 20,
        "self_rating": 4,
        "notes": "Reviewed after Fajr",
    }
    payload.update(overrides)
    return payload


def test_revision_sessions_are_owner_scoped_immutable_history_and_status_independent(
    revision_client,
):
    client, _session_factory = revision_client
    assert client.get("/revision/me").status_code == 401
    assert _register(client, "revision-owner@example.com").status_code == 201
    owner_headers = _csrf_headers(client)
    assert client.get("/revision/me").json() == []

    progress = client.put(
        "/memorization/progress/2/1",
        headers=owner_headers,
        json={"memorization_status": "LEARNING"},
    )
    assert progress.status_code == 200

    first = client.post("/revision", headers=owner_headers, json=_session_payload())
    second = client.post(
        "/revision",
        headers=owner_headers,
        json=_session_payload(
            start_surah_number=2,
            start_ayah_number=1,
            end_surah_number=2,
            end_ayah_number=3,
            revision_type="OLD",
            activity_date="2026-11-25",
            self_rating=None,
            notes=None,
        ),
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert "status" not in first.json()
    history = client.get("/revision/me?limit=1&offset=0")
    assert history.status_code == 200
    assert history.json() == [second.json()]
    assert client.get("/revision/me?limit=1&offset=1").json() == [first.json()]

    with TestClient(app, base_url="https://testserver") as other:
        assert _register(other, "revision-other@example.com").status_code == 201
        assert other.get("/revision/me").json() == []

    for method in ("put", "patch", "delete"):
        request = getattr(client, method)
        arguments = {"headers": owner_headers}
        if method != "delete":
            arguments["json"] = {}
        response = request(f"/revision/{first.json()['id']}", **arguments)
        assert response.status_code == 404
    assert client.get("/revision/me?limit=100&offset=0").json() == [second.json(), first.json()]
    assert client.get("/memorization/progress").json()[0]["memorization_status"] == "LEARNING"

    revision_paths = {
        path: methods for path, methods in app.openapi()["paths"].items()
        if path == "/revision" or path.startswith("/revision/")
    }
    assert set(revision_paths["/revision"]) == {"post"}
    assert set(revision_paths["/revision/me"]) == {"get"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"start_surah_number": 2, "start_ayah_number": 3,
         "end_surah_number": 2, "end_ayah_number": 1},
        {"revision_type": "UNAPPROVED"},
        {"self_rating": 6},
        {"time_spent_minutes": -1},
        {"status": "CANCELLED"},
    ],
)
def test_revision_rejects_invalid_payloads(revision_client, overrides):
    client, _session_factory = revision_client
    assert _register(client, "revision-validation@example.com").status_code == 201
    response = client.post(
        "/revision", headers=_csrf_headers(client), json=_session_payload(**overrides)
    )
    assert response.status_code == 422
    assert client.get("/revision/me").json() == []


def test_revision_requires_existing_canonical_ayah_references(revision_client):
    client, _session_factory = revision_client
    assert _register(client, "revision-reference@example.com").status_code == 201
    response = client.post(
        "/revision",
        headers=_csrf_headers(client),
        json=_session_payload(end_surah_number=114, end_ayah_number=286),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Ayah reference not found"
    assert client.get("/revision/me").json() == []


def test_revision_database_constraints(revision_client):
    _client, session_factory = revision_client
    with session_factory.begin() as db:
        user = User(
            email=f"revision-constraints-{uuid4().hex}@example.test",
            full_name="Constraint Test",
            password_hash="test-hash",
        )
        db.add(user)
        db.flush()
        user_id = user.id

    invalid_sessions = [
        RevisionSession(
            user_id=user_id, start_surah_number=1, start_ayah_number=1,
            end_surah_number=1, end_ayah_number=2, revision_type="INVALID",
            activity_date=date(2026, 11, 24), time_spent_minutes=1,
        ),
        RevisionSession(
            user_id=user_id, start_surah_number=1, start_ayah_number=1,
            end_surah_number=1, end_ayah_number=2, revision_type="RECENT",
            activity_date=date(2026, 11, 24), time_spent_minutes=-1,
        ),
        RevisionSession(
            user_id=user_id, start_surah_number=1, start_ayah_number=1,
            end_surah_number=1, end_ayah_number=2, revision_type="RECENT",
            activity_date=date(2026, 11, 24), time_spent_minutes=1, self_rating=6,
        ),
        RevisionSession(
            user_id=user_id, start_surah_number=2, start_ayah_number=2,
            end_surah_number=1, end_ayah_number=1, revision_type="RECENT",
            activity_date=date(2026, 11, 24), time_spent_minutes=1,
        ),
        RevisionSession(
            user_id=user_id, start_surah_number=1, start_ayah_number=1,
            end_surah_number=2, end_ayah_number=287, revision_type="RECENT",
            activity_date=date(2026, 11, 24), time_spent_minutes=1,
        ),
    ]
    for invalid in invalid_sessions:
        with session_factory() as db:
            with pytest.raises(IntegrityError):
                db.add(invalid)
                db.commit()
            db.rollback()
    with session_factory() as db:
        assert db.scalar(select(RevisionSession)) is None


def test_revision_insert_failure_rolls_back(revision_client):
    _client, session_factory = revision_client
    engine = session_factory.kw["bind"]

    def fail_revision_insert(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().lower().startswith("insert into revision_sessions"):
            raise RuntimeError("injected revision insert failure")

    event.listen(engine, "before_cursor_execute", fail_revision_insert)
    try:
        with session_factory() as db:
            user = User(
                email=f"revision-rollback-{uuid4().hex}@example.test",
                full_name="Rollback Test",
                password_hash="test-hash",
            )
            db.add(user)
            db.commit()
            payload = _session_payload()
            with pytest.raises(RuntimeError, match="injected revision insert failure"):
                from app.revision.service import create_session
                from app.schemas.revision import RevisionSessionCreate

                create_session(db, user.id, RevisionSessionCreate(**payload))
    finally:
        event.remove(engine, "before_cursor_execute", fail_revision_insert)

    with session_factory() as db:
        assert db.scalar(select(RevisionSession)) is None
