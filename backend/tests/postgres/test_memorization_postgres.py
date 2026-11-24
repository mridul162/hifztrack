from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier, local
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import event, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.memorization.service import cancel, correct, set_progress, submit
from app.models import QuranAyah, QuranSurah, User
from app.models.memorization import MemorizationEntry, UserAyahProgress
from app.schemas.memorization import MemorizationEntryCreate


@pytest.fixture
def pg_reference(pg_sessions):
    with pg_sessions.begin() as db:
        db.add(QuranSurah(surah_number=1, ayah_count=2))
        db.flush()
        db.add_all([
            QuranAyah(surah_number=1, ayah_number=1),
            QuranAyah(surah_number=1, ayah_number=2),
        ])
    return pg_sessions


@pytest.fixture
def pg_memorization_api(pg_reference, monkeypatch):
    def override_db():
        with pg_reference() as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, override_db)
    with TestClient(app, base_url="https://testserver") as client:
        yield client


def _user(db: Session, label: str) -> User:
    user = User(
        email=f"{label}-{uuid4().hex}@example.test",
        full_name=label,
        password_hash="postgres-integration-test-hash",
    )
    db.add(user)
    db.flush()
    return user


def _payload(start: tuple[int, int] = (1, 1), end: tuple[int, int] = (1, 2)):
    return MemorizationEntryCreate(
        start_surah_number=start[0],
        start_ayah_number=start[1],
        end_surah_number=end[0],
        end_ayah_number=end[1],
        activity_date=date(2026, 11, 24),
    )


def _run_two(factory, operation):
    barrier = Barrier(2)

    def run(index):
        with factory() as db:
            barrier.wait(timeout=15)
            try:
                return "ok", operation(db, index)
            except HTTPException as exc:
                db.rollback()
                return "http", exc.status_code
            except Exception:
                db.rollback()
                raise

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(run, range(2)))


def _register(client, email):
    token = client.get("/auth/csrf").json()["csrf_token"]
    return client.post(
        "/auth/register",
        headers={"Origin": "http://localhost:3000", "X-CSRF-Token": token},
        json={"email": email, "full_name": "Postgres Learner", "password": "correct-horse-battery"},
    )


def _csrf_headers(client):
    token = client.get("/auth/csrf").json()["csrf_token"]
    return {"Origin": "http://localhost:3000", "X-CSRF-Token": token}


def test_memorization_constraints_are_enforced_by_postgresql(pg_reference):
    with pg_reference() as db:
        user = _user(db, "constraints")
        user_id = user.id
        db.commit()

    with pg_reference.begin() as db:
        db.execute(insert(UserAyahProgress).values(
            user_id=user_id,
            surah_number=1,
            ayah_number=1,
            memorization_status="LEARNING",
        ))

    invalid_rows = [
        insert(UserAyahProgress).values(
            user_id=user_id,
            surah_number=1,
            ayah_number=1,
            memorization_status="MEMORIZED",
        ),  # duplicate user/Ayah primary key
        insert(UserAyahProgress).values(
            user_id=user_id,
            surah_number=1,
            ayah_number=2,
            memorization_status="UNAPPROVED",
        ),  # status check
        insert(UserAyahProgress).values(
            user_id=user_id,
            surah_number=1,
            ayah_number=3,
            memorization_status="LEARNING",
        ),  # composite Quran Ayah FK
        insert(MemorizationEntry).values(
            id=uuid4(), user_id=user_id,
            start_surah_number=1, start_ayah_number=3,
            end_surah_number=1, end_ayah_number=3,
            activity_date=date(2026, 11, 24), status="SUBMITTED",
        ),  # Sabaq composite Quran Ayah FK
        insert(MemorizationEntry).values(
            id=uuid4(), user_id=user_id,
            start_surah_number=1, start_ayah_number=2,
            end_surah_number=1, end_ayah_number=1,
            activity_date=date(2026, 11, 24), status="SUBMITTED",
        ),  # range-order check
    ]
    for statement in invalid_rows:
        with pg_reference() as db:
            with pytest.raises(IntegrityError):
                db.execute(statement)
                db.commit()
            db.rollback()


def test_memorization_api_is_authenticated_and_owner_scoped(pg_memorization_api):
    owner = pg_memorization_api
    assert owner.get("/memorization/progress").status_code == 401
    assert _register(owner, f"owner-{uuid4().hex}@example.com").status_code == 201
    owner_headers = _csrf_headers(owner)
    created = owner.put(
        "/memorization/progress/1/1",
        headers=owner_headers,
        json={"memorization_status": "LEARNING"},
    )
    assert created.status_code == 200
    submission = owner.post(
        "/memorization/submissions",
        headers=owner_headers,
        json={
            "start_surah_number": 1, "start_ayah_number": 1,
            "end_surah_number": 1, "end_ayah_number": 2,
            "activity_date": "2026-11-24",
        },
    )
    assert submission.status_code == 201

    with TestClient(app, base_url="https://testserver") as other:
        assert _register(other, f"other-{uuid4().hex}@example.com").status_code == 201
        assert other.get("/memorization/progress").json() == []
        assert other.get("/memorization/submissions").json() == []
        response = other.post(
            f"/memorization/submissions/{submission.json()['id']}/cancel",
            headers=_csrf_headers(other),
        )
        assert response.status_code == 404


def test_concurrent_first_progress_creation_keeps_one_user_ayah_row(pg_reference):
    with pg_reference() as db:
        user_id = _user(db, "first-progress").id
        db.commit()

    factory = pg_reference
    engine = factory.kw["bind"]
    query_barrier = Barrier(2)
    thread_state = local()

    def synchronize_after_missing_row_select(_connection, _cursor, statement, _params, _context, _many):
        if getattr(thread_state, "wait_for_progress_select", False) and "from user_ayah_progress" in statement.lower():
            thread_state.wait_for_progress_select = False
            query_barrier.wait(timeout=15)

    event.listen(engine, "after_cursor_execute", synchronize_after_missing_row_select)
    try:
        def set_state(db, index):
            thread_state.wait_for_progress_select = True
            return set_progress(db, user_id, 1, 1, ("LEARNING", "MEMORIZED")[index]).memorization_status

        outcomes = _run_two(factory, set_state)
    finally:
        event.remove(engine, "after_cursor_execute", synchronize_after_missing_row_select)

    assert sorted((kind, value if kind == "http" else 200) for kind, value in outcomes) == [
        ("http", 409), ("ok", 200)
    ]
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(UserAyahProgress).where(
            UserAyahProgress.user_id == user_id,
            UserAyahProgress.surah_number == 1,
            UserAyahProgress.ayah_number == 1,
        )) == 1


def test_concurrent_updates_lock_existing_progress(pg_reference):
    with pg_reference() as db:
        user_id = _user(db, "update-progress").id
        db.commit()
    with pg_reference() as db:
        set_progress(db, user_id, 1, 1, "LEARNING")

    outcomes = _run_two(
        pg_reference,
        lambda db, index: set_progress(db, user_id, 1, 1, ("MEMORIZED", "STRONG")[index]).memorization_status,
    )

    assert [kind for kind, _value in outcomes] == ["ok", "ok"]
    with pg_reference() as db:
        saved = db.get(UserAyahProgress, (user_id, 1, 1))
        assert saved.memorization_status in {"MEMORIZED", "STRONG"}
        assert db.scalar(select(func.count()).select_from(UserAyahProgress).where(
            UserAyahProgress.user_id == user_id,
            UserAyahProgress.surah_number == 1,
            UserAyahProgress.ayah_number == 1,
        )) == 1


def test_concurrent_cancellation_commits_once(pg_reference):
    with pg_reference() as db:
        user_id = _user(db, "cancel-race").id
        db.commit()
    with pg_reference() as db:
        entry = submit(db, user_id, _payload())
        entry_id = entry.id

    outcomes = _run_two(pg_reference, lambda db, _index: cancel(db, user_id, entry_id).status)

    assert sorted((kind, value if kind == "http" else 200) for kind, value in outcomes) == [
        ("http", 409), ("ok", 200)
    ]
    with pg_reference() as db:
        assert db.get(MemorizationEntry, entry_id).status == "CANCELLED"
        assert db.scalar(select(func.count()).select_from(MemorizationEntry)) == 1


def test_concurrent_correction_preserves_one_replacement(pg_reference):
    with pg_reference() as db:
        user_id = _user(db, "correct-race").id
        db.commit()
    with pg_reference() as db:
        entry_id = submit(db, user_id, _payload()).id

    outcomes = _run_two(
        pg_reference,
        lambda db, index: correct(
            db, user_id, entry_id,
            _payload((1, 1), (1, 1) if index == 0 else (1, 2)),
        ).id,
    )

    successful = [value for kind, value in outcomes if kind == "ok"]
    assert len(successful) == 1
    assert [value for kind, value in outcomes if kind == "http"] == [409]
    with pg_reference() as db:
        original = db.get(MemorizationEntry, entry_id)
        assert original.status == "CANCELLED"
        assert db.scalar(select(func.count()).select_from(MemorizationEntry)) == 2
        replacement = db.get(MemorizationEntry, successful[0])
        assert replacement.status == "SUBMITTED"


def test_sabaq_submit_cancel_and_correct_never_change_progress(pg_reference):
    with pg_reference() as db:
        user_id = _user(db, "status-independent").id
        db.commit()
    with pg_reference() as db:
        set_progress(db, user_id, 1, 1, "LEARNING")
        original = submit(db, user_id, _payload())
        corrected = correct(db, user_id, original.id, _payload((1, 2), (1, 2)))
        cancel(db, user_id, corrected.id)
        saved = db.get(UserAyahProgress, (user_id, 1, 1))
        assert saved.memorization_status == "LEARNING"
        assert db.get(MemorizationEntry, original.id).status == "CANCELLED"
        assert db.get(MemorizationEntry, corrected.id).status == "CANCELLED"
