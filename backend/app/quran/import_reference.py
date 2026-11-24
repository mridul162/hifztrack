from app.db.session import SessionLocal
from app.quran.importer import import_reference
from app.quran.reference import SOURCE_PATH, load_reference_file


def main() -> None:
    data = load_reference_file(SOURCE_PATH)
    with SessionLocal.begin() as db:
        result = import_reference(db, data)
    action = "already current" if result.already_loaded else "imported"
    print(f"Quran references {action}: {result.surah_count} Surahs, {result.ayah_count} Ayahs")
    print(f"Source SHA-256: {data.source_sha256}")


if __name__ == "__main__":
    main()
