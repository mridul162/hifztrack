import argparse

from app.db.session import SessionLocal
from app.quran.importer import import_reference
from app.quran.pages import EDITION_NAME, PAGE_COUNT
from app.quran.reference import SOURCE_PATH, load_reference_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Import canonical Quran references.")
    parser.add_argument("--with-pages", action="store_true", help=f"also load {EDITION_NAME}")
    args = parser.parse_args()
    data = load_reference_file(SOURCE_PATH)
    with SessionLocal.begin() as db:
        result = import_reference(db, data, with_pages=args.with_pages)
    action = "already current" if result.already_loaded else "imported"
    print(f"Quran references {action}: {result.surah_count} Surahs, {result.ayah_count} Ayahs")
    print(f"Source SHA-256: {data.source_sha256}")
    if args.with_pages:
        print(f"Mushaf page mappings current: {PAGE_COUNT} pages for {EDITION_NAME}")


if __name__ == "__main__":
    main()
