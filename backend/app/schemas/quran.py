from pydantic import BaseModel


class SurahReferenceRead(BaseModel):
    surah_number: int
    ayah_count: int


class AyahReferenceRead(BaseModel):
    surah_number: int
    ayah_number: int


class SurahAyahListRead(BaseModel):
    surah_number: int
    ayah_numbers: list[int]


class QuranReferenceSourceRead(BaseModel):
    category: str
    source_name: str
    source_version: str
    source_url: str
    source_sha256: str
    usage_conditions: str
    verification_method: str
