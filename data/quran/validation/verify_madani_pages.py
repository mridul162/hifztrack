"""Check the shipped 1441H ranges against the pinned public evidence without writing files."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from compare_metadata import (
    HAFS_JSON,
    SOURCE,
    compare_ranges,
    from_ayah_assignments,
    from_page_table,
    require,
    validate_ranges,
)


SOURCE_SHA256 = "43d1d7ebaf009340d943a4d43bcbddfedd2c649a8410a37ee276cb7f7520d60c"
NORMALIZED_SHA256 = "0122616bcfd941438344ea8cb46420f79ef32c75de53c921ecc269c07e10da3a"
ARCHIVE_SHA256 = "a7b0e5591945712ec5e4d6142938ae4d1e9b49bdc89dff06222789bfebdfd72c"
NORMALIZED = SOURCE.parent / "derived/reference/madani-1441h-pages.json"
CHANGED_STARTS = [
    121, 122, 123, 145, 532, 533, 534, 565, 568, 570, 576, 584, 586,
    588, 589, 590, 592, 593, 594, 595, 596, 597, 598, 599, 600,
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_dir", type=Path)
    evidence = parser.parse_args().evidence_dir

    manifest = json.loads((evidence / "manifest.json").read_bytes())
    raw_index = (evidence / "pages.json").read_bytes()
    entry, = [item for item in manifest["files"] if item["name"] == "index/pages.json"]
    require(manifest["release"] == "v1.1.1", "Unexpected Quran SVG Elements release")
    require(
        len(raw_index) == entry["bytes"]
        and sha256(raw_index).hexdigest() == entry["sha256"] == SOURCE_SHA256,
        "Unexpected Quran SVG Elements index bytes",
    )
    index = json.loads(raw_index)
    require(index["edition"] == "hafs-kfgqpc" and index["license"] == "CC-BY-4.0", "Unexpected edition or license")
    indexed = [
        (row["page"], tuple(map(int, row["first_ayah"].split(":"))), tuple(map(int, row["last_ayah"].split(":"))))
        for row in index["pages"]
    ]
    normalized = NORMALIZED.read_text(encoding="utf-8")
    require(sha256(normalized.encode("utf-8")).hexdigest() == NORMALIZED_SHA256, "Unexpected normalized bytes")
    data = json.loads(normalized)
    require(data["edition_id"] == "madani-1441h-hafs", "Wrong HifzTrack edition")
    shipped = [
        (
            row["page_number"],
            (row["start_surah_number"], row["start_ayah_number"]),
            (row["end_surah_number"], row["end_ayah_number"]),
        )
        for row in data["pages"]
    ]
    require(shipped == indexed, "Normalized ranges disagree with the licensed index")

    coordinates = [
        (int(surah.get("index")), int(ayah.get("index")))
        for surah in ET.parse(SOURCE / "arabic/quran-uthmani.xml").getroot().findall("sura")
        for ayah in surah.findall("aya")
    ]
    rank = {coordinate: index for index, coordinate in enumerate(coordinates)}
    require(len(coordinates) == len(rank) == 6236, "Canonical Ayah count mismatch")
    validate_ranges("Normalized 1441H pages", shipped, 604, rank)
    for row, (_, start, end) in zip(index["pages"], indexed, strict=True):
        require(row["ayahs"] == rank[end] - rank[start] + 1, "Page Ayah count mismatch")

    archived = evidence / "kfgqpc-archive.zip"
    require(sha256(archived.read_bytes()).hexdigest() == ARCHIVE_SHA256, "Unexpected KFGQPC archive")
    with ZipFile(archived) as archive:
        publisher = from_ayah_assignments(json.loads(archive.read(HAFS_JSON)), "page")
    qul_1441 = from_page_table(evidence / "qul-v4.html")
    require(shipped == publisher == qul_1441, "1441H ranges disagree")
    compare_ranges("Normalized vs KFGQPC developer archive", shipped, publisher)
    compare_ranges("Normalized vs QUL 1441H", shipped, qul_1441)

    qul_1405 = from_page_table(evidence / "qul-v1.html")
    validate_ranges("QUL 1405H comparison", qul_1405, 604, rank)
    pairs = list(zip(shipped, qul_1405, strict=True))
    require(sum(current != old for current, old in pairs) == 36, "Unexpected number of different page ranges")
    require(
        [current[0] for current, old in pairs if current[1] != old[1]] == CHANGED_STARTS,
        "Unexpected list of different page starts",
    )
    compare_ranges("Normalized vs QUL 1405H", shipped, qul_1405)


if __name__ == "__main__":
    main()
