import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select

from app.db.session import get_db
from app.main import app
from app.models import QuranAyah, QuranReferenceSource, QuranSurah
from app.quran.importer import import_reference
from app.quran.reference import (
    SOURCE_CATEGORY,
    SOURCE_NAME,
    SOURCE_PATH,
    SOURCE_RELATIVE_PATH,
    SOURCE_URL,
    SOURCE_VERSION,
    USAGE_CONDITIONS,
    QuranReferenceData,
    SurahReference,
    load_reference_file,
)


@pytest.fixture
def pg_quran_api(pg_sessions, monkeypatch):
    def override_db():
        with pg_sessions() as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, override_db)
    with TestClient(app, base_url="https://testserver") as client:
        yield client


def test_postgres_import_matches_every_numeric_coordinate_and_provenance(pg_sessions):
    data = load_reference_file(SOURCE_PATH)

    with pg_sessions.begin() as db:
        result = import_reference(db, data)
        assert (result.surah_count, result.ayah_count, result.already_loaded) == (114, 6236, False)

    with pg_sessions() as db:
        surahs = db.scalars(select(QuranSurah).order_by(QuranSurah.surah_number)).all()
        coordinates = [
            tuple(row)
            for row in db.execute(
                select(QuranAyah.surah_number, QuranAyah.ayah_number)
                .order_by(QuranAyah.surah_number, QuranAyah.ayah_number)
            )
        ]
        ayah_counts = dict(db.execute(
            select(QuranAyah.surah_number, func.count())
            .group_by(QuranAyah.surah_number)
        ).all())
        assert [(row.surah_number, row.ayah_count) for row in surahs] == [
            (row.surah_number, row.ayah_count) for row in data.surahs
        ]
        assert len(coordinates) == 6236
        assert coordinates == list(data.ayahs)
        assert ayah_counts == {row.surah_number: row.ayah_count for row in data.surahs}

        source = db.get(QuranReferenceSource, SOURCE_CATEGORY)
        assert source is not None
        assert source.source_name == SOURCE_NAME
        assert source.source_version == SOURCE_VERSION
        assert source.source_path == SOURCE_RELATIVE_PATH
        assert source.source_sha256 == data.source_sha256
        assert source.source_url == SOURCE_URL
        assert source.usage_conditions == USAGE_CONDITIONS
        assert "Strict XML parse" in source.verification_method
        assert "6,236 Ayah coordinates checked" in source.verification_method
        assert "No independent Mushaf page-boundary verification is claimed" in source.verification_method

    with pg_sessions.begin() as db:
        repeated = import_reference(db, data)
        assert (repeated.surah_count, repeated.ayah_count, repeated.already_loaded) == (114, 6236, True)
    with pg_sessions() as db:
        assert db.scalar(select(func.count()).select_from(QuranSurah)) == 114
        assert db.scalar(select(func.count()).select_from(QuranAyah)) == 6236
        assert db.scalar(select(func.count()).select_from(QuranReferenceSource)) == 1


@pytest.mark.parametrize("invalid_kind", ["partial", "inconsistent_coordinates"])
def test_postgres_import_rejects_incomplete_input_without_writes(pg_sessions, invalid_kind):
    source_data = load_reference_file(SOURCE_PATH)
    if invalid_kind == "partial":
        invalid_data = QuranReferenceData(
            surahs=(SurahReference(1, 1),),
            ayahs=((1, 1),),
            source_sha256="0" * 64,
        )
    else:
        coordinates = list(source_data.ayahs)
        coordinates[0] = (1, 2)
        invalid_data = QuranReferenceData(
            surahs=source_data.surahs,
            ayahs=tuple(coordinates),
            source_sha256=source_data.source_sha256,
        )

    with pytest.raises(ValueError, match="incomplete or inconsistent"):
        with pg_sessions.begin() as db:
            import_reference(db, invalid_data)

    with pg_sessions() as db:
        assert db.scalar(select(func.count()).select_from(QuranSurah)) == 0
        assert db.scalar(select(func.count()).select_from(QuranAyah)) == 0
        assert db.scalar(select(func.count()).select_from(QuranReferenceSource)) == 0


def test_postgres_import_transaction_rolls_back_after_surah_insert_failure(pg_sessions):
    data = load_reference_file(SOURCE_PATH)
    engine = pg_sessions.kw["bind"]

    def fail_ayah_insert(_connection, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().lower().startswith("insert into quran_ayahs"):
            raise RuntimeError("injected PostgreSQL import failure")

    event.listen(engine, "before_cursor_execute", fail_ayah_insert)
    try:
        with pytest.raises(RuntimeError, match="injected PostgreSQL import failure"):
            with pg_sessions.begin() as db:
                import_reference(db, data)
    finally:
        event.remove(engine, "before_cursor_execute", fail_ayah_insert)

    with pg_sessions() as db:
        assert db.scalar(select(func.count()).select_from(QuranSurah)) == 0
        assert db.scalar(select(func.count()).select_from(QuranAyah)) == 0
        assert db.scalar(select(func.count()).select_from(QuranReferenceSource)) == 0


def test_postgres_quran_api_reports_unavailable_for_empty_and_partial_imports(pg_quran_api, pg_sessions):
    client = pg_quran_api
    for path in (
        "/quran/surahs",
        "/quran/reference-source",
        "/quran/surahs/1/ayahs",
        "/quran/ayahs/1/1",
    ):
        assert client.get(path).status_code == 503

    with pg_sessions.begin() as db:
        db.add(QuranSurah(surah_number=1, ayah_count=1))
        db.flush()
        db.add(QuranAyah(surah_number=1, ayah_number=1))
        db.add(QuranReferenceSource(
            category=SOURCE_CATEGORY,
            source_name="Synthetic partial test fixture",
            source_version=SOURCE_VERSION,
            source_path=SOURCE_RELATIVE_PATH,
            source_sha256="a" * 64,
            source_url=SOURCE_URL,
            usage_conditions=USAGE_CONDITIONS,
            verification_method="Partial test fixture only.",
        ))

    for path in (
        "/quran/surahs",
        "/quran/reference-source",
        "/quran/surahs/1/ayahs",
        "/quran/ayahs/1/1",
    ):
        response = client.get(path)
        assert response.status_code == 503
        assert response.json()["detail"] == "Quran reference data is incomplete"


def test_postgres_read_only_apis_serve_canonical_numeric_responses(pg_quran_api, pg_sessions):
    client = pg_quran_api
    data = load_reference_file(SOURCE_PATH)
    with pg_sessions.begin() as db:
        import_reference(db, data)

    response = client.get("/quran/surahs")
    assert response.status_code == 200
    assert response.json() == [
        {"surah_number": row.surah_number, "ayah_count": row.ayah_count}
        for row in data.surahs
    ]
    assert client.get("/quran/surahs/1/ayahs").json() == {
        "surah_number": 1, "ayah_numbers": list(range(1, 8)),
    }
    assert client.get("/quran/surahs/2/ayahs").json() == {
        "surah_number": 2, "ayah_numbers": list(range(1, 287)),
    }
    assert client.get("/quran/surahs/114/ayahs").json() == {
        "surah_number": 114, "ayah_numbers": list(range(1, 7)),
    }
    assert client.get("/quran/ayahs/2/255").json() == {
        "surah_number": 2, "ayah_number": 255,
    }
    assert client.get("/quran/surahs/115/ayahs").status_code == 404
    assert client.get("/quran/ayahs/2/287").status_code == 404
    assert client.get("/quran/ayahs/115/1").status_code == 404

    source_response = client.get("/quran/reference-source")
    assert source_response.status_code == 200
    source = source_response.json()[0]
    assert set(source) == {
        "category", "source_name", "source_version", "source_url", "source_sha256",
        "usage_conditions", "verification_method",
    }
    assert source["category"] == SOURCE_CATEGORY
    assert source["source_name"] == SOURCE_NAME
    assert source["source_version"] == SOURCE_VERSION
    assert source["source_sha256"] == data.source_sha256
    assert "text" not in source

    quran_paths = {
        path: methods for path, methods in app.openapi()["paths"].items()
        if path.startswith("/quran/")
    }
    assert quran_paths
    assert all(set(methods) == {"get"} for methods in quran_paths.values())

