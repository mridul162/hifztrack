from hashlib import sha256
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import QuranSurah


Coordinate = tuple[int, int]
Range = tuple[int, Coordinate, Coordinate]


def ordered_digest(rows: list[tuple]) -> str:
    contents = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return sha256(contents.encode("utf-8")).hexdigest()


def range_boundaries(
    starts: list[tuple[int, Coordinate]],
    coordinates: tuple[Coordinate, ...],
    *,
    count: int,
    label: str,
) -> list[Range]:
    if [number for number, _ in starts] != list(range(1, count + 1)):
        raise ValueError(f"Expected {label} numbers 1 through {count} in order")
    rank = {coordinate: index for index, coordinate in enumerate(coordinates)}
    indexes = [rank.get(coordinate, -1) for _, coordinate in starts]
    if indexes[0] != 0 or indexes != sorted(set(indexes)):
        raise ValueError(f"{label} starts must be valid and strictly increasing from 1:1")
    end_indexes = [index - 1 for index in indexes[1:]] + [len(coordinates) - 1]
    return [
        (number, start, coordinates[end_index])
        for (number, start), end_index in zip(starts, end_indexes, strict=True)
    ]


def checked_stored_ranges(
    db: Session, starts: list[tuple[int, Coordinate]], *, count: int, label: str, digest: str
) -> list[Range] | None:
    if len(starts) != count:
        return None
    surahs = db.execute(
        select(QuranSurah.surah_number, QuranSurah.ayah_count).order_by(QuranSurah.surah_number)
    )
    coordinates = tuple(
        (surah_number, ayah_number)
        for surah_number, ayah_count in surahs
        for ayah_number in range(1, ayah_count + 1)
    )
    try:
        ranges = range_boundaries(starts, coordinates, count=count, label=label)
    except ValueError:
        return None
    return ranges if ordered_digest(ranges) == digest else None
