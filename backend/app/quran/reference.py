from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import xml.etree.ElementTree as ET


EXPECTED_SURAH_COUNT = 114
EXPECTED_AYAH_COUNT = 6236
SOURCE_CATEGORY = "SURAH_AYAH_ORDER"
SOURCE_NAME = "Tanzil Quran Text (Uthmani)"
SOURCE_VERSION = "1.1"
SOURCE_URL = "https://tanzil.net"
SOURCE_RELATIVE_PATH = "data/quran/source/arabic/quran-uthmani.xml"


def reference_file_path(relative_path: str) -> Path:
    module_path = Path(__file__).resolve()
    candidate_roots = (module_path.parents[3], module_path.parents[2])
    for root in candidate_roots:
        candidate = root / relative_path
        if candidate.is_file():
            return candidate
    return candidate_roots[0] / relative_path


SOURCE_PATH = reference_file_path(SOURCE_RELATIVE_PATH)

NOTICE_REQUIREMENTS = (
    "Tanzil Quran Text (Uthmani, Version 1.1)",
    "License: Creative Commons Attribution 3.0",
    "Permission is granted to copy and distribute verbatim copies",
    "CHANGING IT IS NOT ALLOWED.",
    "source (Tanzil Project) is clearly indicated",
    "tanzil.net",
    "copyright notice shall be included in all verbatim copies",
)

USAGE_CONDITIONS = (
    "The preserved source notice states CC BY 3.0; it permits verbatim copies, "
    "prohibits changing the Quran text, requires identifying Tanzil Project and linking "
    "to tanzil.net, and requires preserving the notice with verbatim text copies. "
    "This reference category stores only Surah/Ayah coordinates and counts, not Quran text. "
    "DEC-002 remains conditional; public release still requires its outstanding evidence gates."
)


@dataclass(frozen=True)
class SurahReference:
    surah_number: int
    ayah_count: int


@dataclass(frozen=True)
class QuranReferenceData:
    surahs: tuple[SurahReference, ...]
    ayahs: tuple[tuple[int, int], ...]
    source_sha256: str


def _positive_index(value: str | None, label: str) -> int:
    try:
        number = int(value or "")
    except ValueError as exc:
        raise ValueError(f"Invalid {label}: expected a positive integer") from exc
    if number < 1:
        raise ValueError(f"Invalid {label}: expected a positive integer")
    return number


def parse_coordinate_xml(
    contents: bytes,
) -> tuple[tuple[SurahReference, ...], tuple[tuple[int, int], ...]]:
    """Parse only numeric coordinates; Quran text and names are never retained."""
    try:
        root = ET.fromstring(contents)
    except ET.ParseError as exc:
        raise ValueError("Quran reference source is not well-formed XML") from exc
    if root.tag != "quran":
        raise ValueError("Quran reference source must have a quran root element")

    sura_elements = root.findall("sura")
    if len(sura_elements) != EXPECTED_SURAH_COUNT:
        raise ValueError(f"Expected {EXPECTED_SURAH_COUNT} Surahs, found {len(sura_elements)}")

    surahs: list[SurahReference] = []
    ayahs: list[tuple[int, int]] = []
    for expected_surah, sura in enumerate(sura_elements, start=1):
        surah_number = _positive_index(sura.get("index"), "Surah index")
        if surah_number != expected_surah:
            raise ValueError("Surah indexes must be sequential and in canonical order")

        aya_elements = sura.findall("aya")
        if not aya_elements:
            raise ValueError(f"Surah {surah_number} has no Ayah records")
        for expected_ayah, aya in enumerate(aya_elements, start=1):
            ayah_number = _positive_index(aya.get("index"), "Ayah index")
            if ayah_number != expected_ayah:
                raise ValueError(f"Ayah indexes in Surah {surah_number} must be sequential")
            ayahs.append((surah_number, ayah_number))
        surahs.append(SurahReference(surah_number, len(aya_elements)))

    if len(ayahs) != EXPECTED_AYAH_COUNT:
        raise ValueError(f"Expected {EXPECTED_AYAH_COUNT} Ayahs, found {len(ayahs)}")
    return tuple(surahs), tuple(ayahs)


def load_reference_file(path: Path = SOURCE_PATH) -> QuranReferenceData:
    raw = path.read_bytes()
    try:
        notice = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Quran reference source must be valid UTF-8") from exc
    missing = [required for required in NOTICE_REQUIREMENTS if required not in notice]
    if missing:
        raise ValueError("Quran reference source is missing required Tanzil notice terms")
    surahs, ayahs = parse_coordinate_xml(raw)
    return QuranReferenceData(surahs, ayahs, sha256(raw).hexdigest())
