from dataclasses import dataclass
from hashlib import sha256
import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import QuranJuz, QuranReferenceSource, QuranSurah
from app.quran.ranges import Coordinate, Range, checked_stored_ranges, ordered_digest, range_boundaries
from app.quran.reference import EXPECTED_SURAH_COUNT, reference_file_path


VERSION = "1.0.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
NAMES_PATH = "data/quran/derived/reference/surahs-v1.json"
NAMES_SHA256 = "ffa2bb94cc21f98b45f95e6939d9cb3941ab218169caed4a4e393c1cac9c8438"
NAMES_URL = "https://github.com/quran-ws/docs/blob/d1d6be33be9d/standards/terminology/registries/surahs.tsv"
JUZ_COUNT = 30
JUZ_CATEGORY = "JUZ_BOUNDARIES"
JUZ_PATH = "data/quran/derived/reference/juzs-v1.json"
JUZ_SHA256 = "abc8c423b6b12f0b20499019192c49b7781d3acf5c8602a4cc32562a47ab9798"
JUZ_RANGES_SHA256 = "09ccb7049b09cb78988babcd4be763a7f628535aa0b432bad7772f9b1288fd96"
JUZ_URL = "https://cdn.quran.ws/svg/elements/v1.1.1/index/divisions.json"


@dataclass(frozen=True)
class NameCategory:
    category: str
    field: str
    digest: str
    description: str


ARABIC_NAMES = NameCategory(
    "SURAH_NAMES_AR", "name_ar",
    "8c28908dd33d2b00b20242676b12b7228442b8f509f2a69f2412d31d91f0048e",
    "Plain Arabic headings checked against 114 KFGQPC publisher headings.",
)
LATIN_NAMES = NameCategory(
    "SURAH_NAMES_LATIN", "name_latin",
    "d51748b8c742152f310ab4b38fe4aa96702c2619f4ad81cd6f26bf6f427c9e6b",
    "English display transliteration compiled from the licensed headings and documented spelling rules.",
)


def _load_metadata(path: str, checksum: str) -> dict:
    contents = reference_file_path(path).read_text(encoding="utf-8")
    if sha256(contents.encode("utf-8")).hexdigest() != checksum:
        raise ValueError(f"{path} does not match the approved dataset checksum")
    data = json.loads(contents)
    if data["version"] != VERSION:
        raise ValueError(f"{path} has an unexpected metadata version")
    return data


def _matches_names(names: list[tuple[int, str | None]], category: NameCategory) -> bool:
    return (
        [number for number, _ in names] == list(range(1, EXPECTED_SURAH_COUNT + 1))
        and ordered_digest(names) == category.digest
    )


def load_names() -> list[dict]:
    names = _load_metadata(NAMES_PATH, NAMES_SHA256)["surahs"]
    for category, alphabet in ((ARABIC_NAMES, r"[\u0621-\u064a ]+"), (LATIN_NAMES, r"[A-Za-z' -]+")):
        if not _matches_names([(row["surah_number"], row[category.field]) for row in names], category):
            raise ValueError(f"{category.category} does not match the approved headings")
        if any(re.fullmatch(alphabet, row[category.field]) is None for row in names):
            raise ValueError(f"{category.category} has invalid display text")
    return names


def load_juz_ranges(coordinates: tuple[Coordinate, ...]) -> list[Range]:
    data = _load_metadata(JUZ_PATH, JUZ_SHA256)
    ranges = [
        (
            row["juz_number"],
            (row["start_surah_number"], row["start_ayah_number"]),
            (row["end_surah_number"], row["end_ayah_number"]),
        )
        for row in data["juzs"]
    ]
    expected = range_boundaries([(number, start) for number, start, _ in ranges],
                                coordinates, count=JUZ_COUNT, label="Juz")
    if expected != ranges or ordered_digest(ranges) != JUZ_RANGES_SHA256:
        raise ValueError("Juz ranges do not match approved canonical boundaries")
    return ranges


def name_source(category: NameCategory) -> QuranReferenceSource:
    return QuranReferenceSource(
        category=category.category,
        source_name="HifzTrack Surah display names, adapted from the Quran.ws Surah registry",
        source_version=VERSION,
        source_path=NAMES_PATH,
        source_sha256=NAMES_SHA256,
        source_url=NAMES_URL,
        usage_conditions=f"Quran.ws Surah registry, CC BY 4.0 ({LICENSE_URL}). "
        "HifzTrack normalized the Arabic headings and adapted the Latin display spellings.",
        verification_method=category.description,
    )


def juz_source() -> QuranReferenceSource:
    return QuranReferenceSource(
        category=JUZ_CATEGORY,
        source_name="HifzTrack Hafs Kufan Juz ranges, compiled from Quran.ws Quran SVG Elements v1.1.1",
        source_version=VERSION,
        source_path=JUZ_PATH,
        source_sha256=JUZ_SHA256,
        source_url=JUZ_URL,
        usage_conditions=f"Quran.ws division index v1.1.1, CC BY 4.0 ({LICENSE_URL}). "
        "HifzTrack compiled the 30 Juz starts into inclusive canonical ranges.",
        verification_method="All 30 starts checked against KFGQPC assignments and inline quarter marks. "
        "Juz 4 starts at 3:93 and Juz 11 at 9:93. All 6,236 numbered Ayahs covered exactly once.",
    )


def juz_starts(db: Session) -> list[tuple[int, Coordinate]]:
    rows = db.execute(
        select(QuranJuz.juz_number, QuranJuz.start_surah_number, QuranJuz.start_ayah_number)
        .order_by(QuranJuz.juz_number)
    )
    return [(number, (surah, ayah)) for number, surah, ayah in rows]


def _has_source(db: Session, category: str, checksum: str) -> bool:
    source = db.get(QuranReferenceSource, category)
    return source is not None and (source.source_version, source.source_sha256) == (VERSION, checksum)


def names_available(db: Session, surahs: list[QuranSurah], category: NameCategory) -> bool:
    return _has_source(db, category.category, NAMES_SHA256) and _matches_names(
        [(row.surah_number, getattr(row, category.field)) for row in surahs], category
    )


def read_juz_ranges(db: Session) -> list[Range] | None:
    if not _has_source(db, JUZ_CATEGORY, JUZ_SHA256):
        return None
    return checked_stored_ranges(db, juz_starts(db), count=JUZ_COUNT, label="Juz", digest=JUZ_RANGES_SHA256)
