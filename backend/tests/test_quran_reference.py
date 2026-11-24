import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import QuranAyah, QuranReferenceSource, QuranSurah
from app.quran.importer import import_reference
from app.quran.reference import (
    SOURCE_CATEGORY,
    SOURCE_PATH,
    QuranReferenceData,
    SurahReference,
    load_reference_file,
    parse_coordinate_xml,
)


@pytest.fixture
def quran_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client, test_session
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_existing_tanzil_source_loads_only_verified_numeric_coordinates():
    data = load_reference_file(SOURCE_PATH)

    assert len(data.surahs) == 114
    assert len(data.ayahs) == 6236
    assert data.surahs[0] == SurahReference(surah_number=1, ayah_count=7)
    assert data.surahs[-1] == SurahReference(surah_number=114, ayah_count=6)
    assert data.ayahs[0] == (1, 1)
    assert data.ayahs[-1] == (114, 6)
    assert len(data.source_sha256) == 64


def test_coordinate_parser_rejects_nonsequential_ayah_indexes():
    surahs = []
    for surah_number in range(1, 115):
        first_ayah = 2 if surah_number == 1 else 1
        surahs.append(
            f'<sura index="{surah_number}"><aya index="{first_ayah}" /></sura>'
        )
    contents = ("<quran>" + "".join(surahs) + "</quran>").encode()

    with pytest.raises(ValueError, match="must be sequential"):
        parse_coordinate_xml(contents)


def test_importer_writes_numeric_reference_rows_and_provenance_atomically(quran_client):
    _client, session_factory = quran_client
    data = load_reference_file(SOURCE_PATH)

    with session_factory.begin() as db:
        result = import_reference(db, data)
        assert result.surah_count == 114
        assert result.ayah_count == 6236
        assert not result.already_loaded

    with session_factory() as db:
        assert db.get(QuranSurah, 2).ayah_count == 286
        assert db.get(QuranAyah, (2, 255)) is not None
        assert db.get(QuranReferenceSource, SOURCE_CATEGORY).source_sha256 == data.source_sha256
        assert db.scalar(
            select(QuranAyah).where(QuranAyah.ayah_number == 255)
        ).surah_number == 2

        result = import_reference(db, data)
        assert result.already_loaded


def test_importer_refuses_to_overwrite_partial_reference_data(quran_client):
    _client, session_factory = quran_client
    data = QuranReferenceData(
        surahs=(SurahReference(1, 1),),
        ayahs=((1, 1),),
        source_sha256="0" * 64,
    )
    with session_factory.begin() as db:
        db.add(QuranSurah(surah_number=1, ayah_count=1))
        db.flush()
        db.add(QuranAyah(surah_number=1, ayah_number=1))

    with session_factory() as db:
        with pytest.raises(ValueError, match="refusing to overwrite"):
            import_reference(db, data)


def test_reference_api_reports_not_loaded_until_source_provenance_exists(quran_client):
    client, _session_factory = quran_client

    response = client.get("/quran/surahs")

    assert response.status_code == 503


def test_reference_api_rejects_partial_dataset_even_when_provenance_exists(quran_client):
    client, session_factory = quran_client
    with session_factory.begin() as db:
        db.add(QuranSurah(surah_number=1, ayah_count=1))
        db.flush()
        db.add(QuranAyah(surah_number=1, ayah_number=1))
        db.add(QuranReferenceSource(
            category=SOURCE_CATEGORY,
            source_name="Synthetic test fixture",
            source_version="test-only",
            source_path="tests only",
            source_sha256="a" * 64,
            source_url="https://example.invalid",
            usage_conditions="Synthetic fixture; not canonical data.",
            verification_method="Test-only partial dataset.",
        ))

    assert client.get("/quran/surahs").status_code == 503


def test_reference_api_lists_surahs_and_resolves_composite_ayah_identity(quran_client):
    client, session_factory = quran_client
    data = load_reference_file(SOURCE_PATH)
    with session_factory.begin() as db:
        import_reference(db, data)

    surahs = client.get("/quran/surahs").json()
    assert len(surahs) == 114
    assert surahs[1] == {"surah_number": 2, "ayah_count": 286}
    assert client.get("/quran/surahs/2/ayahs").json() == {
        "surah_number": 2,
        "ayah_numbers": list(range(1, 287)),
    }
    assert client.get("/quran/ayahs/2/255").json() == {
        "surah_number": 2,
        "ayah_number": 255,
    }
    assert client.get("/quran/ayahs/2/287").status_code == 404
    sources = client.get("/quran/reference-source").json()
    assert sources[0]["source_version"] == "1.1"
    assert "tanzil.net" in sources[0]["usage_conditions"]
