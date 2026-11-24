from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import QuranAyah, QuranJuz, QuranPage, QuranReferenceSource, QuranSurah
from app.quran.reference import (
    EXPECTED_AYAH_COUNT,
    EXPECTED_SURAH_COUNT,
    SOURCE_CATEGORY,
    SOURCE_NAME,
    SOURCE_RELATIVE_PATH,
    SOURCE_URL,
    SOURCE_VERSION,
    USAGE_CONDITIONS,
    QuranReferenceData,
)


@dataclass(frozen=True)
class ImportResult:
    surah_count: int
    ayah_count: int
    already_loaded: bool


def _validate_reference_data(data: QuranReferenceData) -> None:
    expected_surah_numbers = list(range(1, EXPECTED_SURAH_COUNT + 1))
    if len(data.surahs) != EXPECTED_SURAH_COUNT:
        raise ValueError("Quran reference data is incomplete or inconsistent")

    if [row.surah_number for row in data.surahs] != expected_surah_numbers or any(
        row.ayah_count < 1 or row.ayah_count > 286 for row in data.surahs
    ):
        raise ValueError("Quran reference data is incomplete or inconsistent")

    expected_ayahs = tuple(
        (row.surah_number, ayah_number)
        for row in data.surahs
        for ayah_number in range(1, row.ayah_count + 1)
    )
    if len(expected_ayahs) != EXPECTED_AYAH_COUNT or data.ayahs != expected_ayahs:
        raise ValueError("Quran reference data is incomplete or inconsistent")

    if len(data.source_sha256) != 64 or any(
        character not in "0123456789abcdef" for character in data.source_sha256
    ):
        raise ValueError("Quran reference data has an invalid source checksum")


def import_reference(db: Session, data: QuranReferenceData) -> ImportResult:
    """Stage numeric references in the caller's transaction; never import text or names."""
    source = QuranReferenceSource(
        category=SOURCE_CATEGORY,
        source_name=SOURCE_NAME,
        source_version=SOURCE_VERSION,
        source_path=SOURCE_RELATIVE_PATH,
        source_sha256=data.source_sha256,
        source_url=SOURCE_URL,
        usage_conditions=USAGE_CONDITIONS,
        verification_method=(
            "Strict XML parse; required source notice checked; sequential Surah/Ayah "
            "indexes validated; exactly 114 Surahs and 6,236 Ayah coordinates checked. "
            "No independent Mushaf page-boundary verification is claimed."
        ),
    )

    surahs = db.scalars(select(QuranSurah).order_by(QuranSurah.surah_number)).all()
    ayahs = db.scalars(
        select(QuranAyah).order_by(QuranAyah.surah_number, QuranAyah.ayah_number)
    ).all()
    juzs = db.scalars(select(QuranJuz)).all()
    pages = db.scalars(select(QuranPage)).all()
    existing_source = db.get(QuranReferenceSource, SOURCE_CATEGORY)
    has_existing = bool(surahs or ayahs or juzs or pages or existing_source)

    if has_existing:
        try:
            _validate_reference_data(data)
        except ValueError as exc:
            raise ValueError(
                "Quran reference tables already contain different or partial data; "
                "refusing to overwrite it"
            ) from exc
    else:
        _validate_reference_data(data)

    expected_surahs = [(row.surah_number, row.ayah_count) for row in data.surahs]
    actual_surahs = [(row.surah_number, row.ayah_count) for row in surahs]
    expected_ayahs = list(data.ayahs)
    actual_ayahs = [(row.surah_number, row.ayah_number) for row in ayahs]

    if has_existing:
        same_source = existing_source is not None and all(
            getattr(existing_source, key) == getattr(source, key)
            for key in (
                "category", "source_name", "source_version", "source_path", "source_sha256",
                "source_url", "usage_conditions", "verification_method",
            )
        )
        matches_existing = (
            same_source
            and actual_surahs == expected_surahs
            and actual_ayahs == expected_ayahs
        )
        if matches_existing:
            return ImportResult(len(surahs), len(ayahs), True)
        raise ValueError(
            "Quran reference tables already contain different or partial data; "
            "refusing to overwrite it"
        )

    db.add_all(
        QuranSurah(surah_number=row.surah_number, ayah_count=row.ayah_count)
        for row in data.surahs
    )
    db.flush()
    db.add_all(
        QuranAyah(surah_number=surah_number, ayah_number=ayah_number)
        for surah_number, ayah_number in data.ayahs
    )
    db.add(source)
    db.flush()
    return ImportResult(len(data.surahs), len(data.ayahs), False)
