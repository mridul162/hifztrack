from hashlib import sha256

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select

from app.db.session import get_db
from app.main import app
from app.models import QuranAyah, QuranJuz, QuranPage, QuranReferenceSource, QuranSurah
from app.quran import importer, metadata, pages
from app.quran.importer import import_reference
from app.quran.pages import EDITION_ID, PAGE_CATEGORY, PAGE_SOURCE_SHA256, load_page_ranges
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


def test_postgres_page_import_extends_numeric_data_and_resolves_every_page(pg_quran_api, pg_sessions):
    client = pg_quran_api
    data = load_reference_file()
    with pg_sessions.begin() as db:
        import_reference(db, data)

    assert client.get("/quran/metadata-availability").json() == {
        "arabic_surah_names": False,
        "latin_surah_names": False,
        "juz_mapping": False,
        "mushaf_pages": False,
    }
    assert client.get("/quran/pages").status_code == 503
    assert client.get("/quran/ayahs/2/255/page").status_code == 503
    assert client.get("/quran/ayahs/2/255").json() == {"surah_number": 2, "ayah_number": 255}

    for _ in range(2):
        with pg_sessions.begin() as db:
            import_reference(db, data, with_pages=True)

    response = client.get("/quran/pages")
    assert response.status_code == 200
    payload = response.json()
    assert payload["edition"]["id"] == EDITION_ID
    assert payload["edition"]["source_url"] == pages.PAGE_SOURCE_URL
    assert payload["edition"]["license_url"] == pages.PAGE_LICENSE_URL
    assert "Normalized by HifzTrack" in payload["edition"]["attribution"]
    assert client.get("/quran/metadata-availability").json()["mushaf_pages"]
    actual = [
        (
            page["page_number"],
            (page["start"]["surah_number"], page["start"]["ayah_number"]),
            (page["end"]["surah_number"], page["end"]["ayah_number"]),
        )
        for page in payload["pages"]
    ]
    assert actual == [(page.page_number, page.start, page.end) for page in load_page_ranges(data.ayahs)]
    # The approved edition ends page 120 at 5:77. Page 604 spans three Surahs.
    assert actual[119][2] == (5, 77)
    assert actual[120][1] == (5, 78)
    assert actual[-1] == (604, (112, 1), (114, 6))
    last_page = {"edition": payload["edition"], "page": payload["pages"][-1]}
    assert client.get("/quran/pages/604").json() == last_page
    for coordinate in ("112/1", "113/2", "114/6"):
        assert client.get(f"/quran/ayahs/{coordinate}/page").json() == last_page
    assert client.get("/quran/ayahs/5/77/page").json()["page"]["page_number"] == 120
    assert client.get("/quran/ayahs/5/78/page").json()["page"]["page_number"] == 121
    for path in ("/quran/pages/0", "/quran/pages/605", "/quran/ayahs/2/287/page"):
        assert client.get(path).status_code == 404

    with pg_sessions() as db:
        assert db.scalar(select(func.count()).select_from(QuranPage)) == 604
        assert db.get(QuranReferenceSource, PAGE_CATEGORY).source_sha256 == PAGE_SOURCE_SHA256
        coordinates = db.execute(
            select(QuranAyah.surah_number, QuranAyah.ayah_number)
            .order_by(QuranAyah.surah_number, QuranAyah.ayah_number)
        ).all()
        assert coordinates == list(data.ayahs)

    with pg_sessions.begin() as db:
        # This still gives 604 ordered ranges with complete coverage, but changes page 121.
        db.get(QuranPage, 121).start_ayah_number = 79
    assert client.get("/quran/pages").status_code == 503
    assert client.get("/quran/pages/121").status_code == 503
    assert client.get("/quran/ayahs/5/78/page").status_code == 503
    assert not client.get("/quran/metadata-availability").json()["mushaf_pages"]

    with pg_sessions.begin() as db:
        db.get(QuranPage, 121).start_ayah_number = 78
        db.delete(db.get(QuranPage, 604))
    assert client.get("/quran/pages").status_code == 503
    assert not client.get("/quran/metadata-availability").json()["mushaf_pages"]
    with pytest.raises(ValueError, match="different or partial"):
        with pg_sessions.begin() as db:
            import_reference(db, data, with_pages=True)


def test_postgres_page_import_rolls_back_new_numeric_data_on_bad_end(pg_sessions, tmp_path, monkeypatch):
    data = load_reference_file()
    contents = pages.PAGE_PATH.read_text(encoding="utf-8")
    invalid = contents.replace('"end_ayah_number": 7}', '"end_ayah_number": 6}', 1)
    assert invalid != contents
    path = tmp_path / "bad-boundaries.json"
    path.write_text(invalid, encoding="utf-8")
    with pytest.raises(ValueError, match="approved dataset checksum"):
        pages.load_page_ranges(data.ayahs, path)

    # Exercise structural rejection separately from the production checksum gate.
    monkeypatch.setattr(pages, "PAGE_DATA_SHA256", sha256(invalid.encode("utf-8")).hexdigest())
    monkeypatch.setattr(importer, "load_page_ranges", lambda coordinates: pages.load_page_ranges(coordinates, path))
    with pytest.raises(ValueError, match="without gaps or overlaps"):
        with pg_sessions.begin() as db:
            import_reference(db, data, with_pages=True)

    with pg_sessions() as db:
        for model in (QuranSurah, QuranAyah, QuranPage, QuranReferenceSource):
            assert db.scalar(select(func.count()).select_from(model)) == 0


def test_postgres_page_import_preserves_learner_history_and_dashboard(pg_quran_api, pg_sessions):
    client = pg_quran_api
    data = load_reference_file()
    with pg_sessions.begin() as db:
        import_reference(db, data)

    def csrf_headers():
        token = client.get("/auth/csrf").json()["csrf_token"]
        return {"Origin": "http://localhost:3000", "X-CSRF-Token": token}

    assert client.post("/auth/register", headers=csrf_headers(), json={
        "email": "quran-page-test@example.com",
        "full_name": "Reference Test Learner",
        "password": "reference-fixture-passphrase",
    }).status_code == 201
    activity = {
        "start_surah_number": 112, "start_ayah_number": 1,
        "end_surah_number": 114, "end_ayah_number": 6, "activity_date": "2026-11-24",
    }
    assert client.post("/memorization/submissions", headers=csrf_headers(), json=activity).status_code == 201
    assert client.post("/revision", headers=csrf_headers(), json={
        **activity, "revision_type": "RECENT", "time_spent_minutes": 10,
    }).status_code == 201
    assert client.put("/memorization/progress/112/1", headers=csrf_headers(), json={
        "memorization_status": "MEMORIZED",
    }).status_code == 200
    group = client.post("/groups", headers=csrf_headers(), json={"name": "Page Import Test"})
    assert group.status_code == 201
    group_path = f"/groups/{group.json()['id']}"
    paths = (
        "/memorization/submissions", "/revision/me", "/dashboard/me",
        f"{group_path}/sharing/me", f"{group_path}/dashboard",
    )
    before = [client.get(path) for path in paths]
    assert all(response.status_code == 200 for response in before)

    with pg_sessions.begin() as db:
        import_reference(db, data, with_pages=True, with_metadata=True)

    assert [client.get(path).json() for path in paths] == [response.json() for response in before]


def test_postgres_names_and_juz_extend_numeric_references_idempotently(pg_quran_api, pg_sessions):
    client = pg_quran_api
    data = load_reference_file()
    with pg_sessions.begin() as db:
        import_reference(db, data)

    assert client.get("/quran/surahs").json()[0] == {"surah_number": 1, "ayah_count": 7}
    assert client.get("/quran/juzs").status_code == 503
    assert client.get("/quran/ayahs/3/93/juz").status_code == 503
    assert client.get("/quran/metadata-availability").json() == {
        "arabic_surah_names": False, "latin_surah_names": False, "juz_mapping": False, "mushaf_pages": False,
    }

    for _ in range(2):
        with pg_sessions.begin() as db:
            assert import_reference(db, data, with_metadata=True).already_loaded

    assert client.get("/quran/metadata-availability").json() == {
        "arabic_surah_names": True, "latin_surah_names": True, "juz_mapping": True, "mushaf_pages": False,
    }
    names_response = client.get("/quran/surahs")
    assert names_response.headers["link"] == '</quran/reference-source>; rel="describedby"'
    names = names_response.json()
    assert names == [
        {**name, "ayah_count": surah.ayah_count}
        for name, surah in zip(metadata.load_names(), data.surahs, strict=True)
    ]
    assert names[0] == {
        "surah_number": 1, "ayah_count": 7, "name_ar": "الفاتحة", "name_latin": "Al-Fatihah",
    }
    assert names[20]["name_latin"] == "Al-Anbiya"
    assert names[54]["name_latin"] == "Ar-Rahman"
    assert names[113]["name_latin"] == "An-Nas"

    entries = client.get("/quran/juzs").json()["juzs"]
    actual = [
        (entry["juz_number"],
         (entry["start"]["surah_number"], entry["start"]["ayah_number"]),
         (entry["end"]["surah_number"], entry["end"]["ayah_number"]))
        for entry in entries
    ]
    assert actual == metadata.load_juz_ranges(data.ayahs)
    indexed = {coordinate: rank for rank, coordinate in enumerate(data.ayahs)}
    assert tuple(
        coordinate for _, start, end in actual
        for coordinate in data.ayahs[indexed[start]:indexed[end] + 1]
    ) == data.ayahs

    # Publisher marker-backed starts at 3:93 and 9:93 and endpoints on both sides.
    assert actual[3] == (4, (3, 93), (4, 23))
    assert actual[10] == (11, (9, 93), (11, 5))
    for coordinate, number in (("3/92", 3), ("3/93", 4), ("4/23", 4),
                               ("9/92", 10), ("9/93", 11), ("114/6", 30)):
        assert client.get(f"/quran/ayahs/{coordinate}/juz").json() == entries[number - 1]
        assert client.get(f"/quran/juzs/{number}").json() == entries[number - 1]
    for path in ("/quran/juzs/0", "/quran/juzs/31", "/quran/ayahs/114/7/juz"):
        assert client.get(path).status_code == 404

    with pg_sessions() as db:
        assert db.scalar(select(func.count()).select_from(QuranJuz)) == 30
        assert db.scalar(select(func.count()).select_from(QuranReferenceSource)) == 4
        assert db.execute(
            select(QuranAyah.surah_number, QuranAyah.ayah_number)
            .order_by(QuranAyah.surah_number, QuranAyah.ayah_number)
        ).all() == list(data.ayahs)


def test_postgres_corrupt_names_and_juz_fail_independently(pg_quran_api, pg_sessions):
    client = pg_quran_api
    data = load_reference_file()
    with pg_sessions.begin() as db:
        import_reference(db, data, with_metadata=True, with_pages=True)
        db.get(QuranSurah, 1).name_latin = "Changed"
        db.get(QuranJuz, 4).start_ayah_number = 94

    assert client.get("/quran/metadata-availability").json() == {
        "arabic_surah_names": True, "latin_surah_names": False, "juz_mapping": False, "mushaf_pages": True,
    }
    assert client.get("/quran/surahs").json()[0] == {
        "surah_number": 1, "ayah_count": 7, "name_ar": "الفاتحة",
    }
    assert client.get("/quran/juzs").status_code == 503
    assert client.get("/quran/juzs/4").status_code == 503
    assert client.get("/quran/ayahs/3/93/juz").status_code == 503
    assert client.get("/quran/ayahs/3/93").status_code == 200
    assert client.get("/quran/pages").status_code == 200
    with pytest.raises(ValueError, match="SURAH_NAMES_LATIN contains different or partial data"):
        with pg_sessions.begin() as db:
            import_reference(db, data, with_metadata=True)


def test_postgres_juz_conflict_rolls_back_initial_name_import(pg_quran_api, pg_sessions):
    data = load_reference_file()
    with pg_sessions.begin() as db:
        import_reference(db, data)
        db.add(QuranJuz(juz_number=1, start_surah_number=1, start_ayah_number=1))

    with pytest.raises(ValueError, match="Juz mappings contain different or partial data"):
        with pg_sessions.begin() as db:
            import_reference(db, data, with_metadata=True, with_pages=True)

    with pg_sessions() as db:
        assert db.get(QuranSurah, 1).name_ar is None
        assert db.get(QuranSurah, 1).name_latin is None
        assert db.get(QuranReferenceSource, metadata.ARABIC_NAMES.category) is None
        assert db.get(QuranReferenceSource, metadata.LATIN_NAMES.category) is None
        assert db.scalar(select(func.count()).select_from(QuranJuz)) == 1
        assert db.scalar(select(func.count()).select_from(QuranPage)) == 0
        assert db.scalar(select(func.count()).select_from(QuranAyah)) == 6236
    assert pg_quran_api.get("/quran/juzs").status_code == 503


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

