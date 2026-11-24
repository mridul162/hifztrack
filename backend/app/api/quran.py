from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import QuranAyah, QuranReferenceSource, QuranSurah
from app.quran.reference import SOURCE_CATEGORY
from app.schemas.quran import (
    AyahReferenceRead,
    QuranReferenceSourceRead,
    SurahAyahListRead,
    SurahReferenceRead,
)


router = APIRouter(prefix="/quran", tags=["quran-reference"])


def _require_reference_data(db: Session) -> None:
    if db.get(QuranReferenceSource, SOURCE_CATEGORY) is None:
        raise HTTPException(503, "Quran reference data has not been loaded")
    surah_count = db.scalar(select(func.count()).select_from(QuranSurah))
    ayah_count = db.scalar(select(func.count()).select_from(QuranAyah))
    if surah_count != 114 or ayah_count != 6236:
        raise HTTPException(503, "Quran reference data is incomplete")


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
