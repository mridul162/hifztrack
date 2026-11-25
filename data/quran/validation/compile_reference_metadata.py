"""Compile or check the HifzTrack name and Juz files using pinned source evidence."""

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from compare_metadata import HAFS_JSON, SOURCE, require, validate_ranges


VERSION = "1.0.0"
OUTPUT = SOURCE.parent / "derived/reference"
HASHES = {
    "surahs.tsv": "f869b38aea4dfd05f8d1adaba681127ead07183e478f0138ea85d8db314d690e",
    "registry-LICENSE": "89235c188005b4909b764a7a2ea97987586f1a2fec9b69d5c770ff5d4c301068",
    "division-source.json": "799ea25b484fc3ca1073427d17a031686727e576e40d7a173e3ff0f62b0ad038",
    "publisher.zip": "a7b0e5591945712ec5e4d6142938ae4d1e9b49bdc89dff06222789bfebdfd72c",
}
SUN_LETTERS = dict(zip("تثدذرزسشصضطظلن", (
    "t", "th", "d", "dh", "r", "z", "s", "sh", "s", "d", "t", "z", "l", "n",
), strict=True))
LATIN_EDITS = {
    5: "Ma'idah", 6: "An'am", 7: "A'raf", 13: "Ra'd", 23: "Mu'minun",
    26: "Shu'ara", 36: "Ya-Sin", 38: "Sad", 50: "Qaf", 56: "Waqi'ah",
    62: "Jumu'ah", 70: "Ma'arij", 79: "Nazi'at", 80: "Abasa", 87: "A'la",
    101: "Qari'ah", 107: "Ma'un",
}
PUBLISHER_LATIN_VARIANTS = {3, 9, 60, 92, 106, 108}


def checked_input(evidence, name):
    raw = (evidence / name).read_bytes()
    require(sha256(raw).hexdigest() == HASHES[name], f"Unexpected bytes in {name}")
    return raw


def plain_arabic(heading):
    return "".join(
        char for char in unicodedata.normalize("NFC", heading)
        if not unicodedata.category(char).startswith("M") and char != "ـ"
    )


def name_for_comparison(heading):
    plain = plain_arabic(heading).translate(str.maketrans("يیٱإ", "ىىاأ"))
    return "".join(char for char in plain if not char.isspace())


def compile_names(raw, publisher):
    headings = {int(row["sura_no"]): row["sura_name_ar"] for row in publisher}
    publisher_spellings = {int(row["sura_no"]): row["sura_name_en"] for row in publisher}
    names = []
    variants = set()
    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        number, _, heading, display, *_ = line.split("\t")
        number = int(number)
        arabic = plain_arabic(heading)
        latin = LATIN_EDITS.get(number, display)
        if arabic.startswith("ال"):
            article = SUN_LETTERS.get(arabic[2], "l")
            # Double the consonant across the hyphen for sun-letter assimilation.
            latin = f"A{article}-{latin}"
        require(name_for_comparison(arabic) == name_for_comparison(headings[number]),
                f"Registry and publisher headings differ at Surah {number}")
        if latin_for_comparison(latin) != latin_for_comparison(publisher_spellings[number]):
            variants.add(number)
        names.append({"surah_number": number, "name_ar": arabic, "name_latin": latin})

    require([row["surah_number"] for row in names] == list(range(1, 115)), "Wrong Surah numbering")
    require(variants == PUBLISHER_LATIN_VARIANTS, "Unexpected publisher Latin spelling differences")
    print("Arabic headings: 114/114 agree after comparison-only spelling folds.")
    print(f"Latin headings: 108/114 agree after comparison-only folds. Documented variants: {sorted(variants)}.")
    return names


def latin_for_comparison(heading):
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", heading.lower()))


def compile_juz(raw, publisher, coordinates):
    index = json.loads(raw)
    require(index["edition"] == "hafs-kfgqpc" and index["license"] == "CC-BY-4.0",
            "Unexpected division source or license")
    marks = {(int(row["sura_no"]), int(row["aya_no"])) for row in publisher
             if row["aya_text"].startswith("\u06de")}
    printed = {tuple(map(int, row["ayah_key"].split(":"))) for row in index["division_marks"]}
    require(len(marks) == 199 and printed == marks, "Publisher rosette locations disagree")

    declared = {}
    for row in publisher:
        declared.setdefault(int(row["jozz"]), (int(row["sura_no"]), int(row["aya_no"])))
    starts = [(row["juz"], tuple(map(int, row["ayah_key"].split(":")))) for row in index["juz"]]
    require([number for number, _ in starts] == list(range(1, 31)), "Wrong Juz numbering")
    require({number: start for number, start in starts if start != declared[number]}
            == {4: (3, 93), 11: (9, 93)}, "Unexpected publisher assignment differences")
    require(all(start[1] == 1 or start in marks for _, start in starts),
            "A Juz beginning within a Surah has no rosette")

    rank = {coordinate: position for position, coordinate in enumerate(coordinates)}
    ends = [coordinates[rank[start] - 1] for _, start in starts[1:]] + [coordinates[-1]]
    validate_ranges("HifzTrack Juz", [(number, start, end)
                                      for (number, start), end in zip(starts, ends, strict=True)], 30, rank)
    print("Publisher evidence: 28 numeric starts agree, 21 internal starts carry rosettes, "
          "and all 199 rosette coordinates agree at source level.")
    return [
        {"juz_number": number, "start_surah_number": start[0], "start_ayah_number": start[1],
         "end_surah_number": end[0], "end_ayah_number": end[1]}
        for (number, start), end in zip(starts, ends, strict=True)
    ]


def record(category, rows, write):
    contents = ('{\n  "version": "' + VERSION + '",\n  "' + category + '": [\n    '
                + ",\n    ".join(json.dumps(row, ensure_ascii=False) for row in rows)
                + "\n  ]\n}\n")
    path = OUTPUT / f"{category}-v1.json"
    if write:
        path.write_bytes(contents.encode("utf-8"))
    else:
        require(path.read_text(encoding="utf-8") == contents, f"{path.name} differs from compiled data")
    print(f"{path.name} SHA-256 {sha256(contents.encode('utf-8')).hexdigest()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    checked_input(args.evidence_dir, "registry-LICENSE")
    division_data = checked_input(args.evidence_dir, "division-source.json")
    manifest = json.loads((args.evidence_dir / "elements-manifest.json").read_bytes())
    entry, = [entry for entry in manifest["files"] if entry["name"] == "index/divisions.json"]
    require(manifest["release"] == "v1.1.1" and entry["bytes"] == len(division_data)
            and entry["sha256"] == HASHES["division-source.json"], "Division index differs from release manifest")
    with ZipFile(BytesIO(checked_input(args.evidence_dir, "publisher.zip"))) as archive:
        publisher = json.loads(archive.read(HAFS_JSON))
    coordinates = [
        (int(surah.get("index")), int(ayah.get("index")))
        for surah in ET.parse(SOURCE / "arabic/quran-uthmani.xml").getroot().findall("sura")
        for ayah in surah.findall("aya")
    ]
    require(len(coordinates) == 6236 and coordinates ==
            [(int(row["sura_no"]), int(row["aya_no"])) for row in publisher],
            "Publisher and canonical Ayah coordinates disagree")
    record("surahs", compile_names(checked_input(args.evidence_dir, "surahs.tsv"), publisher), args.write)
    record("juzs", compile_juz(division_data, publisher, coordinates), args.write)


if __name__ == "__main__":
    main()
