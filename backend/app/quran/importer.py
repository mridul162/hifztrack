from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import QuranAyah, QuranJuz, QuranPage, QuranReferenceSource, QuranSurah
from app.quran.metadata import ARABIC_NAMES, LATIN_NAMES, juz_source, juz_starts, load_juz_ranges, load_names, name_source
from app.quran.pages import (
    EDITION_NAME,
    PAGE_CATEGORY,
    PAGE_RELATIVE_PATH,
    PAGE_SOURCE_SHA256,
    PAGE_SOURCE_URL,
    PAGE_SOURCE_VERSION,
    PAGE_USAGE,
    PAGE_VERIFICATION,
    load_page_ranges,
    page_starts,
)
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


def _stage_mushaf_pages(db: Session, data: QuranReferenceData) -> None:
    ranges = load_page_ranges(data.ayahs)
    expected = [(page.page_number, page.start) for page in ranges]
    source_fields = {
        "category": PAGE_CATEGORY,
        "source_name": f"Quran.ws Quran SVG Elements, {EDITION_NAME}",
        "source_version": PAGE_SOURCE_VERSION,
        "source_path": PAGE_RELATIVE_PATH,
        "source_sha256": PAGE_SOURCE_SHA256,
        "source_url": PAGE_SOURCE_URL,
        "usage_conditions": PAGE_USAGE,
        "verification_method": PAGE_VERIFICATION,
    }
    existing_starts = page_starts(db)
    existing_source = db.get(QuranReferenceSource, PAGE_CATEGORY)
    if existing_starts or existing_source is not None:
        if existing_starts == expected and existing_source is not None and all(
            getattr(existing_source, key) == value for key, value in source_fields.items()
        ):
            return
        raise ValueError("Mushaf page tables contain different or partial data; refusing to overwrite it")

    db.add(QuranReferenceSource(**source_fields))
    db.add_all(
        QuranPage(
            page_number=number,
            start_surah_number=start[0],
            start_ayah_number=start[1],
        )
        for number, start in expected
    )
    db.flush()


def _source_matches(existing: QuranReferenceSource, expected: QuranReferenceSource) -> bool:
    return all(
        getattr(existing, key) == getattr(expected, key)
        for key in (
            "category", "source_name", "source_version", "source_path", "source_sha256",
            "source_url", "usage_conditions", "verification_method",
        )
    )


def _stage_display_metadata(db: Session, data: QuranReferenceData) -> None:
    names = load_names()
    starts = [(number, start) for number, start, _ in load_juz_ranges(data.ayahs)]
    surahs = db.scalars(select(QuranSurah).order_by(QuranSurah.surah_number)).all()
    for category in (ARABIC_NAMES, LATIN_NAMES):
        source = name_source(category)
        existing_source = db.get(QuranReferenceSource, source.category)
        values = [getattr(surah, category.field) for surah in surahs]
        expected = [row[category.field] for row in names]
        if existing_source is not None or any(value is not None for value in values):
            if existing_source is None or not _source_matches(existing_source, source) or values != expected:
                raise ValueError(f"{source.category} contains different or partial data; refusing to overwrite it")
            continue
        for surah, name in zip(surahs, expected, strict=True):
            setattr(surah, category.field, name)
        db.add(source)

    source = juz_source()
    existing_source = db.get(QuranReferenceSource, source.category)
    existing_starts = juz_starts(db)
    if existing_source is not None or existing_starts:
        if existing_source is None or not _source_matches(existing_source, source) or existing_starts != starts:
            raise ValueError("Juz mappings contain different or partial data; refusing to overwrite them")
    else:
        db.add(source)
        db.add_all(
            QuranJuz(juz_number=number, start_surah_number=start[0], start_ayah_number=start[1])
            for number, start in starts
        )
    db.flush()


def _stage_numeric_reference(db: Session, data: QuranReferenceData) -> ImportResult:
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
    existing_source = db.get(QuranReferenceSource, SOURCE_CATEGORY)
    has_existing = bool(surahs or ayahs or existing_source)

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
        same_source = existing_source is not None and _source_matches(existing_source, source)
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


def import_reference(
    db: Session,
    data: QuranReferenceData,
    *,
    with_pages: bool = False,
    with_metadata: bool = False,
) -> ImportResult:
    """Stage canonical coordinates and the requested optional metadata in one transaction."""
    result = _stage_numeric_reference(db, data)
    if with_metadata:
        _stage_display_metadata(db, data)
    if with_pages:
        _stage_mushaf_pages(db, data)
    return result
