from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import QuranPage, QuranReferenceSource, QuranSurah
from app.quran.reference import reference_file_path


PAGE_COUNT = 604
EDITION_ID = "madani-1441h-hafs"
EDITION_NAME = "KFGQPC Madani Mushaf (1441H, Hafs, 604 pages)"
PAGE_CATEGORY = "MUSHAF_PAGES"
PAGE_RELATIVE_PATH = "data/quran/derived/reference/madani-1441h-pages.json"
PAGE_PATH = reference_file_path(PAGE_RELATIVE_PATH)
PAGE_SOURCE_URL = "https://cdn.quran.ws/svg/elements/v1.1.1/index/pages.json"
PAGE_SOURCE_VERSION = "v1.1.1"
PAGE_LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
PAGE_SOURCE_SHA256 = "43d1d7ebaf009340d943a4d43bcbddfedd2c649a8410a37ee276cb7f7520d60c"
PAGE_DATA_SHA256 = "0122616bcfd941438344ea8cb46420f79ef32c75de53c921ecc269c07e10da3a"
PAGE_USAGE = (
    f"Page index by Quran.ws (Quran SVG Elements {PAGE_SOURCE_VERSION}), CC BY 4.0 "
    f"({PAGE_LICENSE_URL}). Normalized by HifzTrack to "
    "numbered inclusive Ayah ranges for the KFGQPC Madani 1441H Hafs edition. "
    "Retain source, license and modification credit when republishing the data."
)
PAGE_VERIFICATION = (
    "All 604 page ranges from the 1441H artwork-derived index compared against "
    "the archived KFGQPC developer data and the QUL 1441H range table. "
    "All 6,236 numbered Ayahs are covered once, including 54 cross-Surah ranges. "
    "The 25 different starts from the 1405H layout were confirmed."
)

Coordinate = tuple[int, int]


@dataclass(frozen=True)
class PageRange:
    page_number: int
    start: Coordinate
    end: Coordinate


def ranges_from_starts(
    starts: list[tuple[int, Coordinate]], coordinates: tuple[Coordinate, ...]
) -> list[PageRange]:
    if [number for number, _ in starts] != list(range(1, PAGE_COUNT + 1)):
        raise ValueError("Expected Mushaf pages 1 through 604 in order")
    rank = {coordinate: index for index, coordinate in enumerate(coordinates)}
    indexes = [rank.get(coordinate, -1) for _, coordinate in starts]
    if indexes[0] != 0 or indexes != sorted(set(indexes)):
        raise ValueError("Mushaf page starts must be valid and strictly increasing from 1:1")
    end_indexes = [index - 1 for index in indexes[1:]] + [len(coordinates) - 1]
    return [
        PageRange(number, start, coordinates[end_index])
        for (number, start), end_index in zip(starts, end_indexes, strict=True)
    ]


def load_page_ranges(
    coordinates: tuple[Coordinate, ...], path: Path = PAGE_PATH
) -> list[PageRange]:
    contents = path.read_text(encoding="utf-8")
    if sha256(contents.encode("utf-8")).hexdigest() != PAGE_DATA_SHA256:
        raise ValueError("Mushaf page file does not match the approved dataset checksum")
    data = json.loads(contents)
    if data["edition_id"] != EDITION_ID:
        raise ValueError("Mushaf page file uses an unexpected edition")
    ranges = [
        PageRange(
            row["page_number"],
            (row["start_surah_number"], row["start_ayah_number"]),
            (row["end_surah_number"], row["end_ayah_number"]),
        )
        for row in data["pages"]
    ]
    if ranges_from_starts([(page.page_number, page.start) for page in ranges], coordinates) != ranges:
        raise ValueError("Mushaf page ends must cover the canonical Ayahs without gaps or overlaps")
    return ranges


def page_starts(db: Session) -> list[tuple[int, Coordinate]]:
    rows = db.scalars(select(QuranPage).order_by(QuranPage.page_number)).all()
    return [
        (row.page_number, (row.start_surah_number, row.start_ayah_number)) for row in rows
    ]


def read_page_ranges(db: Session) -> list[PageRange] | None:
    source = db.get(QuranReferenceSource, PAGE_CATEGORY)
    if source is None or source.source_sha256 != PAGE_SOURCE_SHA256:
        return None

    surahs = db.scalars(select(QuranSurah).order_by(QuranSurah.surah_number)).all()
    coordinates = tuple(
        (surah.surah_number, ayah_number)
        for surah in surahs
        for ayah_number in range(1, surah.ayah_count + 1)
    )
    try:
        return ranges_from_starts(page_starts(db), coordinates)
    except ValueError:
        return None
