from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.models import QuranAyah, QuranSurah, RevisionSession, User


@pytest.fixture
def pg_revision(pg_sessions):
    with pg_sessions.begin() as db:
        db.add_all([
            QuranSurah(surah_number=1, ayah_count=2),
            QuranSurah(surah_number=2, ayah_count=1),
        ])
        db.flush()
        db.add_all([
            QuranAyah(surah_number=1, ayah_number=1),
            QuranAyah(surah_number=1, ayah_number=2),
            QuranAyah(surah_number=2, ayah_number=1),
        ])
    return pg_sessions


@pytest.fixture
def pg_revision_api(pg_revision, monkeypatch):
    def override_db():
        with pg_revision() as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, override_db)
    with TestClient(app, base_url="https://testserver") as client:
        yield client


def _user(db: Session, label: str) -> User:
    user = User(
            email=f"{label}-{uuid4().hex}@example.com",
        full_name=label,
        password_hash="postgres-integration-test-hash",
    )
    db.add(user)
    db.flush()
    return user


def _csrf_headers(client):
    token = client.get("/auth/csrf").json()["csrf_token"]
    return {"Origin": "http://localhost:3000", "X-CSRF-Token": token}


def _register(client, label):
    return client.post(
        "/auth/register",
        headers=_csrf_headers(client),
        json={
            "email": f"{label}-{uuid4().hex}@example.com",
            "full_name": label,
            "password": "correct-horse-battery",
        },
    )


def _valid_row(user_id, **values):
    row = {
        "id": uuid4(),
        "user_id": user_id,
        "start_surah_number": 1,
        "start_ayah_number": 1,
        "end_surah_number": 1,
        "end_ayah_number": 2,
        "revision_type": "RECENT",
        "activity_date": date(2026, 11, 24),
        "time_spent_minutes": 15,
        "self_rating": None,
        "notes": None,
        "created_at": datetime(2026, 11, 24, tzinfo=timezone.utc),
    }
    row.update(values)
    return row


def test_postgres_revision_constraints_reject_invalid_values_and_references(pg_revision):
    with pg_revision() as db:
        user_id = _user(db, "revision-constraints").id
        db.commit()

    invalid_rows = [
        _valid_row(user_id, revision_type="UNAPPROVED"),
        _valid_row(user_id, time_spent_minutes=-1),
        _valid_row(user_id, self_rating=6),
        _valid_row(user_id, start_surah_number=2, start_ayah_number=1,
                   end_surah_number=1, end_ayah_number=2),
        _valid_row(user_id, end_surah_number=2, end_ayah_number=2),
    ]
    for row in invalid_rows:
        with pg_revision() as db:
            with pytest.raises(IntegrityError):
                db.execute(insert(RevisionSession).values(**row))
                db.commit()
            db.rollback()

    with pg_revision() as db:
        assert db.scalar(select(RevisionSession)) is None


def test_postgres_revision_api_is_owner_scoped_append_only_and_status_independent(pg_revision_api):
    client = pg_revision_api
    assert client.get("/revision/me").status_code == 401
    registration = _register(client, "revision-owner")
    assert registration.status_code == 201, registration.text
    headers = _csrf_headers(client)
    status_update = client.put(
        "/memorization/progress/1/1",
        headers=headers,
        json={"memorization_status": "MEMORIZED"},
    )
    assert status_update.status_code == 200

    payload = {
        "start_surah_number": 1,
        "start_ayah_number": 1,
        "end_surah_number": 2,
        "end_ayah_number": 1,
        "revision_type": "FULL_JUZ",
        "activity_date": "2026-11-24",
        "time_spent_minutes": 30,
        "self_rating": 5,
        "notes": "Cross-Surah revision range",
    }
    first = client.post("/revision", headers=headers, json=payload)
    duplicate = client.post("/revision", headers=headers, json=payload)
    assert first.status_code == duplicate.status_code == 201
    assert first.json()["id"] != duplicate.json()["id"]
    assert "status" not in first.json()
    assert len(client.get("/revision/me").json()) == 2
    assert client.get("/memorization/progress").json()[0]["memorization_status"] == "MEMORIZED"

    with TestClient(app, base_url="https://testserver") as other:
        assert _register(other, "revision-other").status_code == 201
        assert other.get("/revision/me").json() == []

    for method in ("put", "patch", "delete"):
        request = getattr(client, method)
        arguments = {"headers": headers}
        if method != "delete":
            arguments["json"] = {}
        response = request(f"/revision/{first.json()['id']}", **arguments)
        assert response.status_code == 404
    assert len(client.get("/revision/me").json()) == 2


def test_postgres_revision_create_rolls_back_on_insert_failure(pg_revision):
    with pg_revision() as db:
        user_id = _user(db, "revision-rollback").id
        db.commit()

    engine = pg_revision.kw["bind"]

    def fail_revision_insert(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().lower().startswith("insert into revision_sessions"):
            raise RuntimeError("injected PostgreSQL revision insert failure")

    event.listen(engine, "before_cursor_execute", fail_revision_insert)
    try:
        with pytest.raises(RuntimeError, match="injected PostgreSQL revision insert failure"):
            with pg_revision() as db:
                from app.revision.service import create_session
                from app.schemas.revision import RevisionSessionCreate

                create_session(
                    db,
                    user_id,
                    RevisionSessionCreate(
                        start_surah_number=1,
                        start_ayah_number=1,
                        end_surah_number=1,
                        end_ayah_number=2,
                        revision_type="OLD",
                        activity_date=date(2026, 11, 24),
                        time_spent_minutes=10,
                    ),
                )
    finally:
        event.remove(engine, "before_cursor_execute", fail_revision_insert)

    with pg_revision() as db:
        assert db.scalar(select(RevisionSession)) is None
