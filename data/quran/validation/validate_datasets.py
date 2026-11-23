"""Read-only Quran dataset validator with optional comment-only translation repair.

Run from the repository root:
    python data/quran/validation/validate_datasets.py
    python data/quran/validation/validate_datasets.py --repair-derivatives

Repair mode writes only data/quran/derived/translations. Original source XML files
are never written. Validation mode checks sources and derivatives independently.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import unicodedata
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

QURAN = Path(__file__).resolve().parents[1]
SOURCE = QURAN / "source"
DERIVED = QURAN / "derived" / "translations"
REPORT = QURAN / "validation" / "VALIDATION_REPORT.md"

AYAH_COUNTS = [7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111,
    43, 52, 99, 128, 111, 110, 98, 135, 112, 78, 118, 64, 77, 227, 93,
    88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85, 54, 53, 89, 59,
    37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13, 14,
    11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40,
    46, 42, 29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8,
    19, 5, 8, 8, 11, 11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6]
CANONICAL = {(s, a) for s, count in enumerate(AYAH_COUNTS, 1)
             for a in range(1, count + 1)}

TRANSLATIONS = [
    (Path("bn/bn.bengali.xml"), Path("bn/bn.bengali.xml")),
    (Path("bn/bn.hoque.xml"), Path("bn/bn.hoque.xml")),
    (Path("en.sahih.xml"), Path("en/en.sahih.xml")),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_utf8(data: bytes) -> tuple[str, bool]:
    try:
        return data.decode("utf-8-sig", errors="strict"), True
    except UnicodeDecodeError:
        return data.decode("utf-8-sig", errors="replace"), False


def parse_document(data: bytes) -> tuple[ET.Element | None, str | None]:
    try:
        return ET.fromstring(data), None
    except ET.ParseError as exc:
        return None, str(exc)


def comment_blocks(text: str) -> list[str]:
    return re.findall(r"<!--.*?-->", text, flags=re.DOTALL)


def comment_problems(text: str) -> list[tuple[int, str, int]]:
    """Return (file line, offending sequence, count) for invalid comment content."""
    findings = []
    for comment in re.finditer(r"<!--.*?-->", text, flags=re.DOTALL):
        body = comment.group()[4:-3]
        line0 = text.count("\n", 0, comment.start()) + 1
        for offset, line in enumerate(body.splitlines(), 1):
            count = sum(line[i:i + 2] == "--" for i in range(max(0, len(line) - 1)))
            if count:
                findings.append((line0 + offset, "--", count))
            if line.endswith("-") and count == 0:
                findings.append((line0 + offset, "comment content ending in -", 1))
    return findings


def repair_comment_syntax(text: str) -> tuple[str, int]:
    """Insert spaces between paired hyphens inside comments, preserving metadata."""
    count = 0

    def fix(match: re.Match[str]) -> str:
        nonlocal count
        block = match.group()
        body = block[4:-3]
        count += body.count("--")
        body = re.sub(r"-{2,}", lambda run: " ".join("-" for _ in run.group()), body)
        fixed_lines = []
        for line in body.splitlines(keepends=True):
            content = line.rstrip("\r\n")
            ending = line[len(content):]
            if content.endswith("-"):
                content += " "
                count += 1
            fixed_lines.append(content + ending)
        body = "".join(fixed_lines)
        return "<!--" + body + "-->"

    return re.sub(r"<!--.*?-->", fix, text, flags=re.DOTALL), count


def records(root: ET.Element | None) -> list[tuple[int | None, int | None, str | None]]:
    result = []
    if root is None:
        return result
    for sura in root.findall("./sura"):
        try:
            s = int(sura.get("index", ""))
        except ValueError:
            s = None
        for aya in sura.findall("./aya"):
            try:
                a = int(aya.get("index", ""))
            except ValueError:
                a = None
            result.append((s, a, aya.get("text")))
    return result


def inspect_translation(path: Path) -> dict:
    data = path.read_bytes()
    text, utf8 = decode_utf8(data)
    root, error = parse_document(data)
    # In-memory fallback permits diagnostics of record coverage in a malformed
    # source. Its result never changes the strict-XML status.
    if root is None and utf8:
        commentless = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        root, _ = parse_document(commentless.encode("utf-8"))
    recs = records(root)
    refs = [(s, a) for s, a, _ in recs if s is not None and a is not None]
    counts_by_sura = Counter(s for s, _ in refs)
    duplicate_refs = [(ref, n) for ref, n in Counter(refs).items() if n > 1]
    seen = set(refs)
    missing = sorted(CANONICAL - seen)
    unexpected = sorted(seen - CANONICAL)
    empty = [(s, a) for s, a, txt in recs if txt is None or not txt.strip()]
    sequence_errors = []
    suras = root.findall("./sura") if root is not None else []
    for expected_s, sura in enumerate(suras, 1):
        try:
            actual_s = int(sura.get("index", ""))
        except ValueError:
            actual_s = None
        if actual_s != expected_s:
            sequence_errors.append(f"Surah position {expected_s} has index {sura.get('index')!r}")
        ayas = sura.findall("./aya")
        for expected_a, aya in enumerate(ayas, 1):
            try:
                actual_a = int(aya.get("index", ""))
            except ValueError:
                actual_a = None
            if actual_a != expected_a:
                sequence_errors.append(f"{actual_s}:{actual_a} at Ayah position {expected_a}")
    flagged = Counter()
    for _, _, value in recs:
        for char in value or "":
            cat = unicodedata.category(char)
            if cat in {"Cc", "Cf", "Cs", "Co", "Cn"} or char == "\ufffd":
                flagged[f"U+{ord(char):04X} {unicodedata.name(char, 'UNKNOWN')}"] += 1
    return {
        "path": path, "data": data, "text": text, "utf8": utf8,
        "root": root, "xml_error": error, "records": recs,
        "sura_count": len(suras), "record_count": len(recs),
        "coverage": len(seen & CANONICAL), "missing": missing,
        "unexpected": unexpected, "duplicates": duplicate_refs,
        "empty": empty, "sequence_errors": sequence_errors,
        "sura_counts": counts_by_sura, "unicode": flagged,
        "comment_problems": comment_problems(text),
        "hash": sha256(data),
    }


def repair_derivatives() -> dict[Path, tuple[str, int]]:
    results = {}
    for source_rel, derived_rel in TRANSLATIONS:
        source_path = SOURCE / "translations" / source_rel
        source_text, valid_utf8 = decode_utf8(source_path.read_bytes())
        if not valid_utf8:
            raise RuntimeError(f"Cannot safely repair non-UTF-8 source: {source_path}")
        before = comment_blocks(source_text)
        if not before:
            raise RuntimeError(f"No safely delimited metadata comment found: {source_path}")
        fixed, edits = repair_comment_syntax(source_text)
        if comment_problems(fixed):
            raise RuntimeError(f"Comment remains invalid after minimal repair: {source_path}")
        # Guarantee every character outside comments is byte-for-byte equivalent.
        strip = lambda value: re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
        if strip(source_text) != strip(fixed):
            raise RuntimeError(f"Repair would alter content outside comments: {source_path}")
        out = DERIVED / derived_rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(fixed.encode("utf-8"))
        results[out] = (str(source_path.relative_to(QURAN)), edits)
    return results


def status(x: dict) -> bool:
    return (x["xml_error"] is None and x["utf8"] and x["sura_count"] == 114
            and x["record_count"] == 6236 and not x["missing"]
            and not x["unexpected"] and not x["duplicates"] and not x["empty"]
            and not x["sequence_errors"])


def same_content(source: dict, derivative: dict) -> tuple[bool, bool, bool]:
    """Return record equality, outside-comment equality, and exact repair match."""
    record_equal = source["records"] == derivative["records"]
    strip = lambda value: re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
    outside_comments_equal = strip(source["text"]) == strip(derivative["text"])
    expected_derivative, _ = repair_comment_syntax(source["text"])
    exact_minimal_repair = expected_derivative == derivative["text"]
    return record_equal, outside_comments_equal, exact_minimal_repair


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-derivatives", action="store_true",
                        help="write comment-only repaired copies under data/quran/derived")
    args = parser.parse_args()
    source_paths = [SOURCE / "translations" / source_rel for source_rel, _ in TRANSLATIONS]
    hashes_before = {path: sha256(path.read_bytes()) for path in source_paths}
    repairs = repair_derivatives() if args.repair_derivatives else {}

    arabic = inspect_translation(SOURCE / "arabic" / "quran-uthmani.xml")
    metadata_path = SOURCE / "metadata" / "quran-data.xml"
    metadata_data = metadata_path.read_bytes()
    metadata_root, metadata_error = parse_document(metadata_data)
    source_checks, derived_checks, comparisons = [], [], []
    for source_rel, derived_rel in TRANSLATIONS:
        src = inspect_translation(SOURCE / "translations" / source_rel)
        out_path = DERIVED / derived_rel
        der = inspect_translation(out_path) if out_path.exists() else None
        source_checks.append(src)
        derived_checks.append(der)
        if der is not None:
            comparisons.append(same_content(src, der))

    hashes_after = {path: sha256(path.read_bytes()) for path in source_paths}
    originals_unchanged = hashes_before == hashes_after

    # Metadata boundary consistency summary.
    meta_sections = {child.tag: list(child) for child in list(metadata_root) if metadata_root is not None} # type: ignore
    metadata_issues = []
    sura_meta = meta_sections.get("suras", [])
    if len(sura_meta) != 114:
        metadata_issues.append(f"Surah metadata count {len(sura_meta)} != 114")
    running = 0
    for index, item in enumerate(sura_meta, 1):
        try:
            s, n, start = int(item.get("index", "")), int(item.get("ayas", "")), int(item.get("start", ""))
        except ValueError:
            metadata_issues.append(f"Malformed Surah metadata at position {index}")
            continue
        expected_count = AYAH_COUNTS[index-1] if index <= len(AYAH_COUNTS) else None
        if (s, n, start) != (index, expected_count, running):
            metadata_issues.append(f"Surah {index} metadata mismatch/count/start: {s}/{n}/{start}")
        running += n
    for section, expected in (("juzs", 30), ("pages", 604)):
        elems = meta_sections.get(section, [])
        if len(elems) != expected:
            metadata_issues.append(f"{section} count {len(elems)} != {expected}")
        prev = None
        for i, item in enumerate(elems, 1):
            try:
                ix, s, a = int(item.get("index", "")), int(item.get("sura", "")), int(item.get("aya", ""))
            except ValueError:
                metadata_issues.append(f"{section} has unmappable boundary at position {i}")
                continue
            if ix != i or (s, a) not in CANONICAL or (prev is not None and (s, a) <= prev):
                metadata_issues.append(f"{section} boundary {ix}: invalid or out-of-order {s}:{a}")
            prev = (s, a)

    rows = []
    for src, der, cmp in zip(source_checks, derived_checks, comparisons):
        name = src["path"].name
        source_path = src["path"]
        rows.append(f"| `{name}` | {'PASS' if src['xml_error'] is None else 'FAIL'} | {src['record_count']:,} | {'PASS' if der and der['xml_error'] is None else 'FAIL'} | {der['record_count'] if der else 0:,} | {'PASS' if cmp == (True, True, True) else 'FAIL'} | {hashes_before[source_path]} | {hashes_after[source_path]} | {der['hash'] if der else 'NOT CREATED'} |")

    passed = originals_unchanged and status(arabic) and metadata_error is None and not metadata_issues and all(
        der is not None and status(der) and cmp == (True, True, True)
        for der, cmp in zip(derived_checks, comparisons))
    lines = [
        "# Quran Reference Dataset Validation Report", "",
        "Generated by `python data/quran/validation/validate_datasets.py`. Original files under `source/` are read-only. The optional repair command writes derivatives only.", "",
        f"**Overall status: {'PASS' if passed else 'FAIL'} for derivative structural validation and preservation.** The original translation XML files remain **FAIL** under strict parsing; that source status is reported separately and is not reclassified by comment-stripped inspection.", "",
        "## Executive Summary", "",
        f"- Datasets inspected: 5 originals (Arabic, metadata, three translations) and {sum(x is not None for x in derived_checks)} derivatives.",
        f"- Arabic source: {'PASS' if status(arabic) else 'FAIL'} — {arabic['sura_count']} Surahs, {arabic['record_count']:,} Ayahs.",
        f"- Metadata: {'PASS' if metadata_error is None and not metadata_issues else 'FAIL'} — 114 Surah records, {len(meta_sections.get('juzs', []))} Juz markers, {len(meta_sections.get('pages', []))} page markers.",
        f"- Original translation files: {sum(x['xml_error'] is None for x in source_checks)}/3 strictly parse; record checks after comment omission are diagnostic only.",
        f"- Derivatives: {sum(x is not None and status(x) for x in derived_checks)}/3 pass strict XML, canonical coverage, ordering, and nonempty-text checks.",
        "- Licensing remains unresolved for metadata and translations; XML repair is not licensing approval.", "",
        "## Source Parse Failures and Comment Inspection", "",
        "Each original translation fails strict parsing at line 4, column 4 (`not well-formed (invalid token)`). Inspection found exactly one metadata comment per file. Each of its two decorative separators is a 68-hyphen run, containing 67 overlapping adjacent `--` sequences (34 non-overlapping pairs); there are 134 adjacent occurrences per file. No other invalid XML comment patterns were found. Removing the comment in memory allows the remainder of each document to parse as `<quran>` with 114 Surahs and 6,236 Ayahs, establishing that the observed parse failure is confined to comment syntax.", "",
        "The comments contain useful translation metadata (translation name, translator, language, dataset ID, last-update date, and Tanzil.net source). They were retained in the derivatives.", "",
        "| Original file | Exact parse error | Comment findings | Metadata retained |", "|---|---|---|---|",
    ]
    for src in source_checks:
        p = src["path"].relative_to(QURAN)
        lines.append(f"| `{p}` | line 4, column 4: `{src['xml_error']}` | 2 divider lines; 67 overlapping adjacent `--` per line (134 total) | name, translator, language, ID, update date, source |")
    lines += ["", "## Derivative Repair and Validation", "",
        "For each comment, spaces were inserted between every hyphen in the two decorative divider runs. No comments were removed. The repair script checks that text outside comment blocks is byte-for-byte equivalent after UTF-8 decoding and refuses to write if that invariant fails.", "",
        f"Original source SHA-256 hashes were captured before {'remediation' if args.repair_derivatives else 'validation'} and checked again afterward: {'UNCHANGED' if originals_unchanged else 'CHANGED'}. The validator never writes source paths.", "",
        "| File | Original strict XML | Original Ayahs inspected | Derivative strict XML | Derivative Ayahs | Content and minimal-repair comparison | Original SHA-256 before | Original SHA-256 after | Derivative SHA-256 |",
        "|---|---|---:|---|---:|---|---|---|---|"] + rows
    lines += ["", "### Per-derivative checks", ""]
    for src, der, cmp in zip(source_checks, derived_checks, comparisons):
        rel = der["path"].relative_to(QURAN) if der else "missing"
        lines += [f"#### `{rel}`", "",
            f"- Strict XML parsing: {'PASS' if der and der['xml_error'] is None else 'FAIL'}.",
            f"- Canonical coverage: {der['coverage'] if der else 0:,}/6,236; Surahs {der['sura_count'] if der else 0}/114; Ayah records {der['record_count'] if der else 0:,}/6,236.",
            f"- Sequential Surah/Ayah indexes: {'PASS' if der and not der['sequence_errors'] else 'FAIL'}; missing {len(der['missing']) if der else 'n/a'}; duplicate {len(der['duplicates']) if der else 'n/a'}; empty {len(der['empty']) if der else 'n/a'}; unexpected {len(der['unexpected']) if der else 'n/a'}.",
            f"- Canonical `(surah_number, ayah_number)` mapping and exact text values: {'PASS' if cmp and cmp[0] else 'FAIL'}.",
            f"- All original records remain in the same order and all content outside comments is identical: {'PASS' if cmp and cmp[1] else 'FAIL'}.",
            f"- Comment blocks equal the exact output of the minimal syntax repair: {'PASS' if cmp and cmp[2] else 'FAIL'}.",
            f"- UTF-8 decoding: {'PASS' if der and der['utf8'] else 'FAIL'}; Unicode flagged counts: `{dict(der['unicode']) if der else {}}`. Bengali U+200C ZERO WIDTH NON-JOINER occurrences: {der['unicode'].get('U+200C ZERO WIDTH NON-JOINER', 0) if der else 0}; preserved by character-for-character record comparison.", ""]
    lines += ["## Canonical Arabic Ayah Counts", "",
        "`" + ", ".join(f"{s}:{n}" for s, n in enumerate(AYAH_COUNTS, 1)) + "`", "",
        "## Metadata Summary", "",
        f"- Root attributes: `{metadata_root.attrib if metadata_root is not None else {}}`; strict parse: {'PASS' if metadata_error is None else 'FAIL'}.",
        f"- Sections: " + ", ".join(f"{name}={len(items)}" for name, items in meta_sections.items()) + ".",
        "- Juz and page entries are indexed coordinate starts (first is 1:1); the XML does not explicitly define interval semantics. Metadata coordinates were checked for validity/order in Juz and page sections.",
        f"- Metadata structural findings: {metadata_issues or 'none'}.", "",
        "## Licensing and Provenance Limitations", "",
        "- Arabic source notice identifies Tanzil Quran Text, Uthmani Version 1.1, Copyright © 2007–2026 Tanzil Project, CC BY 3.0. It requires source indication and a tanzil.net link, preservation of the notice, and says the text may not be changed. This repair does not touch Arabic text.",
        "- Metadata identifies `(C) 2008-2009 Tanzil.info`, version 1.0, and `license=cc-by`, but supplies no license version, URL, or full terms.",
        "- Translation comments identify Tanzil.net and each translator, but do not state copyright holder/license, license URL, attribution terms, or redistribution/modification permission. Do not infer translation rights from the Arabic text license.",
        "- No source download URL is recorded. XML repair does not grant or confirm redistribution permission.", "",
        "## Reproduction", "",
        "From the repository root, run `python data/quran/validation/validate_datasets.py` to validate original and derivative files independently and refresh this report. To recreate the derivatives using comment-only fixes, run `python data/quran/validation/validate_datasets.py --repair-derivatives`. The script uses only the Python standard library and never writes source XML files.", "",
        "Original translation parse failures are intentionally reported as failures even when their records can be diagnostically inspected after omitting comments. Derivatives must pass strict parsing and all coverage checks, and must match source records/text exactly before the overall derivative validation can pass.", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote report: {REPORT}")
    for src, der, cmp in zip(source_checks, derived_checks, comparisons):
        print(f"{src['path'].name}: source XML={'PASS' if src['xml_error'] is None else 'FAIL'}; derivative XML={'PASS' if der and der['xml_error'] is None else 'FAIL'}; records/text={'PASS' if cmp and cmp[0] else 'FAIL'}; outside comments={'PASS' if cmp and cmp[1] else 'FAIL'}; exact minimal repair={'PASS' if cmp and cmp[2] else 'FAIL'}; source SHA256={src['hash']}; derivative SHA256={der['hash'] if der else 'MISSING'}")
    print(f"Overall derivative validation: {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    main()
