from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import QuranAyah, QuranReferenceSource, QuranSurah
from app.quran.metadata import ARABIC_NAMES, JUZ_COUNT, LATIN_NAMES, names_available, read_juz_ranges
from app.quran.pages import (
    EDITION_ID,
    EDITION_NAME,
    PAGE_COUNT,
    PAGE_LICENSE_URL,
    PAGE_SOURCE_URL,
    PAGE_USAGE,
    PageRange,
    read_page_ranges,
)
from app.quran.reference import SOURCE_CATEGORY
from app.quran.ranges import Range
from app.schemas.quran import (
    AyahReferenceRead,
    JuzListRead,
    JuzRead,
    MushafEditionRead,
    MushafPageListRead,
    MushafPageLookupRead,
    MushafPageRead,
    QuranMetadataAvailabilityRead,
    QuranReferenceSourceRead,
    SurahAyahListRead,
    SurahReferenceRead,
)


router = APIRouter(prefix="/quran", tags=["quran-reference"])
PROVENANCE_LINK = '</quran/reference-source>; rel="describedby"'


def _reference_issue(db: Session) -> str | None:
    if db.get(QuranReferenceSource, SOURCE_CATEGORY) is None:
        return "Quran reference data has not been loaded"
    surah_count = db.scalar(select(func.count()).select_from(QuranSurah))
    ayah_count = db.scalar(select(func.count()).select_from(QuranAyah))
    if surah_count != 114 or ayah_count != 6236:
        return "Quran reference data is incomplete"
    return None


def _require_reference_data(db: Session) -> None:
    issue = _reference_issue(db)
    if issue is not None:
        raise HTTPException(503, issue)


@router.get("/reference-source", response_model=list[QuranReferenceSourceRead])
def list_reference_sources(db: Session = Depends(get_db)):
    _require_reference_data(db)
    return db.scalars(
        select(QuranReferenceSource).order_by(QuranReferenceSource.category)
    ).all()


@router.get("/surahs", response_model=list[SurahReferenceRead], response_model_exclude_none=True)
def list_surahs(response: Response, db: Session = Depends(get_db)):
    _require_reference_data(db)
    surahs = list(db.scalars(select(QuranSurah).order_by(QuranSurah.surah_number)))
    arabic = names_available(db, surahs, ARABIC_NAMES)
    latin = names_available(db, surahs, LATIN_NAMES)
    if arabic or latin:
        response.headers["Link"] = PROVENANCE_LINK
    return [
        SurahReferenceRead(
            surah_number=row.surah_number, ayah_count=row.ayah_count,
            name_ar=row.name_ar if arabic else None,
            name_latin=row.name_latin if latin else None,
        )
        for row in surahs
    ]


@router.get("/surahs/{surah_number}/ayahs", response_model=SurahAyahListRead)
def list_surah_ayahs(surah_number: int, db: Session = Depends(get_db)):
    _require_reference_data(db)
    surah = db.get(QuranSurah, surah_number)
    if surah is None:
        raise HTTPException(404, "Surah not found")
    ayah_numbers = db.scalars(
        select(QuranAyah.ayah_number)
        .where(QuranAyah.surah_number == surah_number)
        .order_by(QuranAyah.ayah_number)
    ).all()
    if len(ayah_numbers) != surah.ayah_count:
        raise HTTPException(503, "Quran reference data failed its count check")
    return SurahAyahListRead(surah_number=surah_number, ayah_numbers=ayah_numbers)


@router.get("/ayahs/{surah_number}/{ayah_number}", response_model=AyahReferenceRead)
def resolve_ayah(surah_number: int, ayah_number: int, db: Session = Depends(get_db)):
    _require_reference_data(db)
    ayah = db.get(QuranAyah, (surah_number, ayah_number))
    if ayah is None:
        raise HTTPException(404, "Ayah reference not found")
    return ayah


MUSHAF_EDITION = MushafEditionRead(
    id=EDITION_ID,
    name=EDITION_NAME,
    source_url=PAGE_SOURCE_URL,
    license_url=PAGE_LICENSE_URL,
    attribution=PAGE_USAGE,
)


def _require_mushaf_pages(db: Session) -> list[PageRange]:
    pages = read_page_ranges(db)
    if pages is None:
        raise HTTPException(503, "Mushaf page mappings are unavailable")
    return pages


def _page_response(page: PageRange) -> MushafPageRead:
    return MushafPageRead(
        page_number=page.page_number,
        start=AyahReferenceRead(surah_number=page.start[0], ayah_number=page.start[1]),
        end=AyahReferenceRead(surah_number=page.end[0], ayah_number=page.end[1]),
    )


@router.get("/metadata-availability", response_model=QuranMetadataAvailabilityRead)
def metadata_availability(db: Session = Depends(get_db)):
    if _reference_issue(db) is not None:
        return QuranMetadataAvailabilityRead(
            arabic_surah_names=False, latin_surah_names=False, juz_mapping=False, mushaf_pages=False
        )
    surahs = list(db.scalars(select(QuranSurah).order_by(QuranSurah.surah_number)))
    return QuranMetadataAvailabilityRead(
        arabic_surah_names=names_available(db, surahs, ARABIC_NAMES),
        latin_surah_names=names_available(db, surahs, LATIN_NAMES),
        juz_mapping=read_juz_ranges(db) is not None,
        mushaf_pages=read_page_ranges(db) is not None,
    )


@router.get("/pages", response_model=MushafPageListRead)
def list_pages(db: Session = Depends(get_db)):
    _require_reference_data(db)
    return MushafPageListRead(
        edition=MUSHAF_EDITION,
        pages=[_page_response(page) for page in _require_mushaf_pages(db)],
    )


@router.get("/pages/{page_number}", response_model=MushafPageLookupRead)
def resolve_page(page_number: int, db: Session = Depends(get_db)):
    if not 1 <= page_number <= PAGE_COUNT:
        raise HTTPException(404, "Mushaf page not found")
    _require_reference_data(db)
    pages = _require_mushaf_pages(db)
    return MushafPageLookupRead(edition=MUSHAF_EDITION, page=_page_response(pages[page_number - 1]))


@router.get("/ayahs/{surah_number}/{ayah_number}/page", response_model=MushafPageLookupRead)
def resolve_ayah_page(surah_number: int, ayah_number: int, db: Session = Depends(get_db)):
    resolve_ayah(surah_number, ayah_number, db)
    coordinate = (surah_number, ayah_number)
    pages = _require_mushaf_pages(db)
    page = next((page for page in pages if page.start <= coordinate <= page.end), None)
    if page is None:
        raise HTTPException(503, "Mushaf page mappings are unavailable")
    return MushafPageLookupRead(edition=MUSHAF_EDITION, page=_page_response(page))


def _require_juz_ranges(db: Session) -> list[Range]:
    ranges = read_juz_ranges(db)
    if ranges is None:
        raise HTTPException(503, "Juz mappings are unavailable")
    return ranges


def _juz_response(row: Range) -> JuzRead:
    number, start, end = row
    return JuzRead(
        juz_number=number,
        start=AyahReferenceRead(surah_number=start[0], ayah_number=start[1]),
        end=AyahReferenceRead(surah_number=end[0], ayah_number=end[1]),
    )


@router.get("/juzs", response_model=JuzListRead)
def list_juzs(response: Response, db: Session = Depends(get_db)):
    _require_reference_data(db)
    ranges = _require_juz_ranges(db)
    response.headers["Link"] = PROVENANCE_LINK
    return JuzListRead(juzs=[_juz_response(row) for row in ranges])


@router.get("/juzs/{juz_number}", response_model=JuzRead)
def resolve_juz(juz_number: int, response: Response, db: Session = Depends(get_db)):
    if not 1 <= juz_number <= JUZ_COUNT:
        raise HTTPException(404, "Juz not found")
    _require_reference_data(db)
    ranges = _require_juz_ranges(db)
    response.headers["Link"] = PROVENANCE_LINK
    return _juz_response(ranges[juz_number - 1])


@router.get("/ayahs/{surah_number}/{ayah_number}/juz", response_model=JuzRead)
def resolve_ayah_juz(surah_number: int, ayah_number: int, response: Response, db: Session = Depends(get_db)):
    resolve_ayah(surah_number, ayah_number, db)
    coordinate = (surah_number, ayah_number)
    match = next((row for row in _require_juz_ranges(db) if row[1] <= coordinate <= row[2]), None)
    if match is None:
        raise HTTPException(503, "Juz mappings are unavailable")
    response.headers["Link"] = PROVENANCE_LINK
    return _juz_response(match)
