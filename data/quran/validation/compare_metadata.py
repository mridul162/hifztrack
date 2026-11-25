"""Compare QURAN-01B source snapshots without writing data or opening a database."""

import argparse
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
from itertools import groupby
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import ZipFile


SOURCE = Path(__file__).resolve().parents[1] / "source"
HAFS_JSON = "UthmanicHafs_v2-0 data/hafsData_v2-0.json"
PAGE_RANGE = re.compile(r"(\d+):(\d+)\s*-\s*(\d+):(\d+)")


class Table(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
        self.feed(path.read_text(encoding="utf-8"))
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag == "td" and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def metadata(path):
    root = ET.parse(path).getroot()
    print(f"{path.name}: metadata {root.attrib['version']}; license={root.attrib['license']}")
    groups = []
    for section, item in (("suras", "sura"), ("juzs", "juz"), ("pages", "page")):
        groups.append([row.attrib for row in root.findall(f"./{{*}}{section}/{{*}}{item}")])
    return groups


def from_starts(rows, coordinates, rank):
    starts = [(int(row["sura"]), int(row["aya"])) for row in rows]
    return [
        (int(row["index"]), start, coordinates[rank[starts[index + 1]] - 1] if index + 1 < len(starts) else coordinates[-1])
        for index, (row, start) in enumerate(zip(rows, starts, strict=True))
    ]


def from_ayah_assignments(rows, field):
    result = []
    for number, group in groupby(rows, key=lambda row: int(row[field])):
        coordinates = [(int(row["sura_no"]), int(row["aya_no"])) for row in group]
        result.append((number, coordinates[0], coordinates[-1]))
    return result


def from_page_table(path):
    ranges = []
    for row in Table(path).rows:
        if len(row) < 2 or not row[0].isdigit():
            continue
        match = PAGE_RANGE.fullmatch(row[1])
        require(match is not None, f"{path.name}: invalid or missing range on page {row[0]}")
        start_surah, start_ayah, end_surah, end_ayah = map(int, match.groups())
        ranges.append((int(row[0]), (start_surah, start_ayah), (end_surah, end_ayah)))
    return ranges


def validate_ranges(label, ranges, expected_count, rank):
    require([number for number, _, _ in ranges] == list(range(1, expected_count + 1)), f"{label}: wrong numbering")
    next_start = 0
    for number, start, end in ranges:
        require(start in rank and end in rank, f"{label}: {number} has an unknown coordinate")
        require(rank[start] == next_start and rank[end] >= next_start, f"{label}: gap, overlap or reversed range at {number}")
        next_start = rank[end] + 1
    require(next_start == len(rank), f"{label}: incomplete coverage")
    cross_surah = sum(start[0] != end[0] for _, start, end in ranges)
    print(f"{label}: {expected_count} ranges, {next_start} Ayahs, {cross_surah} cross-Surah ranges")


def compare_ranges(label, first, second):
    pairs = list(zip(first, second, strict=True))
    different_ranges = [left[0] for left, right in pairs if left != right]
    different_starts = [left[0] for left, right in pairs if left[1] != right[1]]
    print(f"{label}: {len(pairs) - len(different_ranges)}/{len(pairs)} exact ranges")
    if different_ranges:
        print(f"  Ranges that differ: {different_ranges}")
        print(f"  Starts that differ: {different_starts}")


def arabic_for_comparison(name):
    text = "".join(
        char for char in unicodedata.normalize("NFKC", name)
        if not unicodedata.category(char).startswith(("M", "C")) and char not in " ـ"
    )
    return text.translate(str.maketrans("آأإٱىؤئي", "اااايويي"))


def latin_for_comparison(name):
    return "".join(char.lower() for char in unicodedata.normalize("NFKD", name) if char.isascii() and char.isalpha())


def compare_names(tanzil, qpc, qul, counts):
    qpc_names = {}
    for number, rows in groupby(qpc, key=lambda row: int(row["sura_no"])):
        names = {(row["sura_name_ar"], row["sura_name_en"]) for row in rows}
        require(len(names) == 1, f"KFGQPC: inconsistent names on Surah {number}")
        qpc_names[number] = names.pop()
    qul_rows = [row for row in Table(qul).rows if len(row) == 8 and row[0].isdigit()]
    require([int(row[0]) for row in qul_rows] == list(range(1, 115)), "QUL names: wrong Surah numbering")
    require(all(int(row[6]) == counts[int(row[0])] for row in qul_rows), "QUL names: Ayah counts disagree")
    for language, from_xml, qul_column, qpc_column, fold in (
        ("Arabic", "name", 3, 0, arabic_for_comparison),
        ("Latin", "tname", 2, 1, latin_for_comparison),
    ):
        qpc_values = [qpc_names[number][qpc_column] for number in range(1, 115)]
        qul_values = [row[qul_column] for row in qul_rows]
        xml_values = [row[from_xml] for row in tanzil]
        expected_script = language.upper()
        for name in [*qpc_values, *qul_values, *xml_values]:
            require(
                any(char.isalpha() and expected_script in unicodedata.name(char, "") for char in name),
                f"Missing {language} letters in a Surah name",
            )
        for label, other in (("KFGQPC", qpc_values), ("QUL", qul_values)):
            pairs = list(zip(xml_values, other, strict=True))
            exact = sum(left == right for left, right in pairs)
            matching = sum(fold(left) == fold(right) for left, right in pairs)
            print(f"Tanzil vs {label}, {language}: {exact}/114 literal, {matching}/114 with comparison folding")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_dir", type=Path)
    args = parser.parse_args()
    evidence = args.evidence_dir
    coordinates = [
        (int(surah.attrib["index"]), int(ayah.attrib["index"]))
        for surah in ET.parse(SOURCE / "arabic/quran-uthmani.xml").getroot().findall("sura")
        for ayah in surah.findall("aya")
    ]
    counts = Counter(surah for surah, _ in coordinates)
    canonical = [(surah, ayah) for surah in range(1, 115) for ayah in range(1, counts[surah] + 1)]
    require(coordinates == canonical and len(coordinates) == 6236 and len(counts) == 114, "Canonical coordinates disagree")
    rank = {coordinate: index for index, coordinate in enumerate(coordinates)}

    upstream = evidence / "tanzil.xml"
    package = evidence / "kfgqpc-archive.zip"
    for path in (upstream, package, *(evidence / f"qul-{name}.html" for name in ("names", "v1", "v2", "v4"))):
        print(f"{path.name}: SHA-256 {sha256(path.read_bytes()).hexdigest()}")
    tanzil_names, tanzil_juzs, tanzil_pages = metadata(upstream)
    require(metadata(SOURCE / "metadata/quran-data.xml") == [tanzil_names, tanzil_juzs, tanzil_pages], "Local metadata records differ from Tanzil")
    require([int(row["index"]) for row in tanzil_names] == list(range(1, 115)), "Tanzil: wrong Surah numbering")
    for row in tanzil_names:
        number = int(row["index"])
        require(int(row["start"]) == rank[number, 1] and int(row["ayas"]) == counts[number], f"Tanzil: invalid Surah {number}")

    with ZipFile(package) as archive:
        raw_hafs = archive.read(HAFS_JSON)
    print(f"KFGQPC JSON: SHA-256 {sha256(raw_hafs).hexdigest()}")
    hafs = json.loads(raw_hafs)
    hafs_coordinates = [(int(row["sura_no"]), int(row["aya_no"])) for row in hafs]
    require(hafs_coordinates == coordinates, "KFGQPC: canonical coordinates disagree")
    compare_names(tanzil_names, hafs, evidence / "qul-names.html", counts)

    tanzil_juz_ranges = from_starts(tanzil_juzs, coordinates, rank)
    hafs_juz_ranges = from_ayah_assignments(hafs, "jozz")
    tanzil_page_ranges = from_starts(tanzil_pages, coordinates, rank)
    hafs_page_ranges = from_ayah_assignments(hafs, "page")
    for label, juzs, pages in (("Tanzil", tanzil_juz_ranges, tanzil_page_ranges), ("KFGQPC", hafs_juz_ranges, hafs_page_ranges)):
        validate_ranges(f"{label} Juz", juzs, 30, rank)
        validate_ranges(f"{label} pages", pages, 604, rank)
    compare_ranges("Tanzil vs KFGQPC Juz", tanzil_juz_ranges, hafs_juz_ranges)
    compare_ranges("Tanzil vs KFGQPC pages", tanzil_page_ranges, hafs_page_ranges)
    for version in ("v1", "v2", "v4"):
        ranges = from_page_table(evidence / f"qul-{version}.html")
        validate_ranges(f"QUL {version}", ranges, 604, rank)
        compare_ranges(f"QUL {version} vs Tanzil pages", ranges, tanzil_page_ranges)
        compare_ranges(f"QUL {version} vs KFGQPC pages", ranges, hafs_page_ranges)

    for first, second in zip(tanzil_juz_ranges, hafs_juz_ranges, strict=True):
        if first[1] != second[1]:
            first_chapter, first_ayah = first[1]
            second_chapter, second_ayah = second[1]
            tanzil_marked = "\u06de" in hafs[rank[first[1]]]["aya_text"]
            hafs_marked = "\u06de" in hafs[rank[second[1]]]["aya_text"]
            print(f"Juz {first[0]}: Tanzil {first_chapter}:{first_ayah} (marker={tanzil_marked}), "
                  f"KFGQPC numeric {second_chapter}:{second_ayah} (marker={hafs_marked})")


if __name__ == "__main__":
    main()
