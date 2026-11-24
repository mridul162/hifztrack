from datetime import date
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.quran.importer import import_reference
from app.quran.reference import load_reference_file, SOURCE_PATH


@pytest.fixture
def quran_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

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
    with TestClient(app, base_url="https://testserver") as client:
        yield client, session_factory
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def csrf_headers(client):
    token = client.get("/auth/csrf").json()["csrf_token"]
    return {"Origin": "http://localhost:3000", "X-CSRF-Token": token}


def register(client, email):
    return client.post(
        "/auth/register",
        headers=csrf_headers(client),
        json={"email": email, "full_name": "Memorization User", "password": "correct-horse-battery"},
    )


def submission(start=(2, 1), end=(2, 3), **overrides):
    payload = {
        "start_surah_number": start[0],
        "start_ayah_number": start[1],
        "end_surah_number": end[0],
        "end_ayah_number": end[1],
        "activity_date": "2026-11-24",
    }
    payload.update(overrides)
    return payload


def test_progress_is_private_unique_per_ayah_and_strong_requires_confirmation(quran_client):
    client, session_factory = quran_client
    assert register(client, "learner@example.com").status_code == 201
    headers = csrf_headers(client)

    assert client.get("/memorization/progress").json() == []
    unconfirmed = client.put(
        "/memorization/progress/2/255",
        headers=headers,
        json={"memorization_status": "STRONG"},
    )
    assert unconfirmed.status_code == 422

    for status in ("LEARNING", "MEMORIZED", "STRONG"):
        response = client.put(
            "/memorization/progress/2/255",
            headers=headers,
            json={"memorization_status": status, "confirm_strong": status == "STRONG"},
        )
        assert response.status_code == 200
        assert response.json()["memorization_status"] == status
    regression = client.put(
        "/memorization/progress/2/255",
        headers=headers,
        json={"memorization_status": "LEARNING"},
    )
    assert regression.status_code == 200
    assert regression.json()["memorization_status"] == "LEARNING"
    rows = client.get("/memorization/progress?surah_number=2").json()
    assert len(rows) == 1
    assert rows[0]["ayah_number"] == 255

    with session_factory() as db:
        from app.models.memorization import UserAyahProgress

        assert db.query(UserAyahProgress).count() == 1


def test_submissions_preserve_overlaps_and_never_change_progress(quran_client):
    client, _session_factory = quran_client
    assert register(client, "sabaq@example.com").status_code == 201
    headers = csrf_headers(client)
    assert client.put(
        "/memorization/progress/2/1",
        headers=headers,
        json={"memorization_status": "LEARNING"},
    ).status_code == 200

    for _ in range(2):
        response = client.post(
            "/memorization/submissions",
            headers=headers,
            json=submission(start=(1, 7), end=(2, 2), notes="Practice", time_spent_minutes=15),
        )
        assert response.status_code == 201
        assert response.json()["status"] == "SUBMITTED"

    history = client.get("/memorization/submissions").json()
    assert len(history) == 2
    assert history[0]["id"] != history[1]["id"]
    first_page = client.get("/memorization/submissions?limit=1&offset=0").json()
    second_page = client.get("/memorization/submissions?limit=1&offset=1").json()
    assert len(first_page) == len(second_page) == 1
    assert first_page[0]["id"] != second_page[0]["id"]
    assert client.get("/memorization/progress").json()[0]["memorization_status"] == "LEARNING"


def test_invalid_ranges_and_unknown_ayahs_are_rejected(quran_client):
    client, _session_factory = quran_client
    assert register(client, "ranges@example.com").status_code == 201
    headers = csrf_headers(client)

    assert client.post(
        "/memorization/submissions", headers=headers,
        json=submission(start=(2, 3), end=(2, 2)),
    ).status_code == 422
    assert client.post(
        "/memorization/submissions", headers=headers,
        json=submission(start=(2, 287), end=(3, 1)),
    ).status_code == 422
    assert client.post(
        "/memorization/submissions", headers=headers,
        json=submission(start=(2, 286), end=(3, 1)),
    ).status_code == 201
    assert client.put(
        "/memorization/progress/2/287", headers=headers,
        json={"memorization_status": "LEARNING"},
    ).status_code == 404


def test_cancel_and_correction_preserve_original_history_and_are_owner_only(quran_client):
    client, _session_factory = quran_client
    assert register(client, "owner@example.com").status_code == 201
    headers = csrf_headers(client)
    original = client.post(
        "/memorization/submissions", headers=headers, json=submission()
    ).json()

    client.put(
        "/memorization/progress/2/1", headers=headers,
        json={"memorization_status": "LEARNING"},
    )
    with TestClient(app, base_url="https://testserver") as other:
        assert register(other, "other@example.com").status_code == 201
        other_headers = csrf_headers(other)
        assert other.get("/memorization/progress").json() == []
        assert other.get("/memorization/submissions").json() == []
        assert other.get(f"/memorization/submissions/{original['id']}/cancel").status_code == 405
        assert other.post(
            f"/memorization/submissions/{original['id']}/cancel", headers=other_headers
        ).status_code == 404

    corrected = client.post(
        f"/memorization/submissions/{original['id']}/correct",
        headers=headers,
        json=submission(start=(2, 2), end=(2, 4)),
    )
    assert corrected.status_code == 201
    assert corrected.json()["id"] != original["id"]
    history = {row["id"]: row for row in client.get("/memorization/submissions").json()}
    assert len(history) == 2
    assert history[original["id"]]["status"] == "CANCELLED"
    assert history[corrected.json()["id"]]["status"] == "SUBMITTED"
    assert client.post(
        f"/memorization/submissions/{original['id']}/cancel", headers=headers
    ).status_code == 409


def test_cancellation_does_not_mutate_ayah_status_and_requires_auth(quran_client):
    client, _session_factory = quran_client
    assert client.get("/memorization/progress").status_code == 401
    assert client.get("/memorization/submissions").status_code == 401
    assert register(client, "independent@example.com").status_code == 201
    headers = csrf_headers(client)
    client.put(
        "/memorization/progress/1/1", headers=headers,
        json={"memorization_status": "MEMORIZED"},
    )
    entry = client.post(
        "/memorization/submissions", headers=headers, json=submission((1, 1), (1, 1))
    ).json()
    assert client.post(
        f"/memorization/submissions/{entry['id']}/cancel", headers=headers
    ).json()["status"] == "CANCELLED"
    assert client.get("/memorization/progress").json()[0]["memorization_status"] == "MEMORIZED"


def test_browser_preflight_allows_status_put(quran_client):
    client, _session_factory = quran_client
    response = client.options(
        "/memorization/progress/2/1",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "content-type,x-csrf-token",
        },
    )

    assert response.status_code == 200
    assert "PUT" in response.headers["access-control-allow-methods"]


def test_database_constraints_reject_invalid_status_and_noncanonical_references(quran_client):
    client, session_factory = quran_client
    user_id = UUID(register(client, "constraints@example.com").json()["id"])

    from app.models.memorization import MemorizationEntry, UserAyahProgress

    with session_factory() as db:
        valid_progress = UserAyahProgress(
            user_id=user_id,
            surah_number=2,
            ayah_number=1,
            memorization_status="LEARNING",
        )
        db.add(valid_progress)
        db.commit()
        db.expunge(valid_progress)
        db.add(UserAyahProgress(
            user_id=user_id,
            surah_number=2,
            ayah_number=1,
            memorization_status="MEMORIZED",
        ))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        db.add(UserAyahProgress(
            user_id=user_id,
            surah_number=2,
            ayah_number=2,
            memorization_status="UNAPPROVED",
        ))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        db.add(MemorizationEntry(
            user_id=user_id,
            start_surah_number=2,
            start_ayah_number=999,
            end_surah_number=2,
            end_ayah_number=999,
            activity_date=date(2026, 11, 24),
            status="SUBMITTED",
        ))
        with pytest.raises(IntegrityError):
            db.commit()
