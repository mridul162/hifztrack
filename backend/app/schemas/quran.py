from pydantic import BaseModel


class SurahReferenceRead(BaseModel):
    surah_number: int
    ayah_count: int
    name_ar: str | None = None
    name_latin: str | None = None


class AyahReferenceRead(BaseModel):
    surah_number: int
    ayah_number: int


class SurahAyahListRead(BaseModel):
    surah_number: int
    ayah_numbers: list[int]


class MushafEditionRead(BaseModel):
    id: str
    name: str
    source_url: str
    license_url: str
    attribution: str


class MushafPageRead(BaseModel):
    page_number: int
    start: AyahReferenceRead
    end: AyahReferenceRead


class MushafPageListRead(BaseModel):
    edition: MushafEditionRead
    pages: list[MushafPageRead]


class MushafPageLookupRead(BaseModel):
    edition: MushafEditionRead
    page: MushafPageRead


class JuzRead(BaseModel):
    juz_number: int
    start: AyahReferenceRead
    end: AyahReferenceRead


class JuzListRead(BaseModel):
    juzs: list[JuzRead]


class QuranMetadataAvailabilityRead(BaseModel):
    arabic_surah_names: bool
    latin_surah_names: bool
    juz_mapping: bool
    mushaf_pages: bool


class QuranReferenceSourceRead(BaseModel):
    category: str
    source_name: str
    source_version: str
    source_url: str
    source_sha256: str
    usage_conditions: str
    verification_method: str
