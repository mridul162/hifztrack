import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import QuranAyah, QuranJuz, QuranPage, QuranSurah


@pytest.fixture
def quran_db():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            yield db
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_reference_coordinates_use_surah_and_ayah_as_composite_identity(quran_db):
    quran_db.add(QuranSurah(surah_number=2, ayah_count=255))
    quran_db.flush()
    quran_db.add(QuranAyah(surah_number=2, ayah_number=255))
    quran_db.commit()

    assert quran_db.get(QuranAyah, (2, 255)) is not None


@pytest.mark.parametrize("surah_number", [0, 115])
def test_surah_number_is_within_canonical_range(quran_db, surah_number):
    quran_db.add(QuranSurah(surah_number=surah_number, ayah_count=1))

    with pytest.raises(IntegrityError):
        quran_db.commit()


@pytest.mark.parametrize("ayah_number", [0, -1])
def test_ayah_number_must_be_positive(quran_db, ayah_number):
    quran_db.add(QuranSurah(surah_number=1, ayah_count=1))
    quran_db.add(QuranAyah(surah_number=1, ayah_number=ayah_number))

    with pytest.raises(IntegrityError):
        quran_db.commit()


def test_juz_and_page_anchors_must_reference_existing_ayah(quran_db):
    quran_db.add(QuranSurah(surah_number=1, ayah_count=1))
    quran_db.flush()
    quran_db.add(QuranAyah(surah_number=1, ayah_number=1))
    quran_db.add_all([
        QuranJuz(juz_number=1, start_surah_number=1, start_ayah_number=1),
        QuranPage(page_number=1, start_surah_number=1, start_ayah_number=1),
    ])
    quran_db.commit()

    assert quran_db.get(QuranJuz, 1) is not None
    assert quran_db.get(QuranPage, 1) is not None

    quran_db.add(QuranJuz(juz_number=2, start_surah_number=1, start_ayah_number=2))
    with pytest.raises(IntegrityError):
        quran_db.commit()


@pytest.mark.parametrize("page_number", [0, 605])
def test_page_number_is_within_approved_madani_range(quran_db, page_number):
    quran_db.add(QuranPage(page_number=page_number, start_surah_number=1, start_ayah_number=1))

    with pytest.raises(IntegrityError):
        quran_db.commit()


@pytest.mark.parametrize("juz_number", [0, 31])
def test_juz_number_is_within_canonical_range(quran_db, juz_number):
    quran_db.add(QuranJuz(juz_number=juz_number, start_surah_number=1, start_ayah_number=1))

    with pytest.raises(IntegrityError):
        quran_db.commit()
