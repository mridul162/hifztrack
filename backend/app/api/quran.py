from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import QuranAyah, QuranReferenceSource, QuranSurah
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
from app.schemas.quran import (
    AyahReferenceRead,
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


@router.get("/surahs", response_model=list[SurahReferenceRead])
def list_surahs(db: Session = Depends(get_db)):
    _require_reference_data(db)
    return db.scalars(select(QuranSurah).order_by(QuranSurah.surah_number)).all()


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
    return QuranMetadataAvailabilityRead(
        arabic_surah_names=False,
        latin_surah_names=False,
        juz_mapping=False,
        mushaf_pages=_reference_issue(db) is None and read_page_ranges(db) is not None,
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
