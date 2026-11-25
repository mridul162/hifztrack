# QURAN-01D metadata compilation and verification

Reviewed on 2026-11-25 against `develop` at `d0546dd`. ADR-021 makes HifzTrack the maintainer of its own versioned display names and Juz mappings. Source licenses and credits continue to apply. QURAN-01 is **IN_PROGRESS** while independent human review is outstanding. DEC-002 remains **CONDITIONALLY APPROVED** for the separate Arabic verse-text release gate. [ADR-021](../../../docs/decisions/DECISIONS_LOG.md#adr-021-hifztrack-maintained-quran-reference-metadata-dec-002) · [Attribution](../derived/reference/NOTICE.md)

## Sources and compilation

| Shipped category | Source, terms and transformations |
|---|---|
| Arabic names | Quran.ws Surah registry at git revision `d1d6be33be9d`, which references al-Suyuti's *al-Itqan*. The pinned project license specifically covers the `standards/` directory under CC BY 4.0. Normalize to Unicode NFC and strip combining vocalization and tatweel while retaining letters, spaces, precomposed hamza and madda. Match keys to canonical Surah numbers. [Registry](https://github.com/quran-ws/docs/blob/d1d6be33be9d/standards/terminology/registries/surahs.tsv) · [Pinned license](https://github.com/quran-ws/docs/blob/d1d6be33be9d/LICENSE) |
| Simplified Latin names | Use the same registry's licensed display stems. Restore the Arabic definite article where present, assimilating it before sun letters (for example `Ar-Rahman` and `An-Nas`). Use ordinary ASCII, initial capitalization, retained doubled consonants, spaces for multiword names, and a hyphen after the article. Keep selected internal hamza/ayn distinctions with a straight apostrophe. The compiler records the 17 explicit spelling edits, including `Ya-Sin`, `Sad`, `Qaf` and `Ma'un`. Surah 21 is `Al-Anbiya`. Surah 3 uses `Aal Imran`, where `Aal` is part of the name. Surah 60 follows the recognized `Mumtahinah` reading. [Compiler](compile_reference_metadata.py) · [Ibn Ashur on Surah 60 variants](https://islamweb.com/ar/library/content/61/4029/%D8%B3%D9%88%D8%B1%D8%A9-%D8%A7%D9%84%D9%85%D9%85%D8%AA%D8%AD%D9%86%D8%A9) |
| Juz ranges | Source the numbered starts from the Quran.ws Quran SVG Elements v1.1.1 division index. This exact index identifies its labels and indexes as CC BY 4.0. Build each inclusive end from the preceding numbered Ayah before the next start. The final end is `114:6`. The output contains only Juz numbers and coordinates. [Division index](https://cdn.quran.ws/svg/elements/v1.1.1/index/divisions.json) · [Source methodology](https://quran.ws/docs/reference/quran-svg-elements/) · [License coverage](https://quran.ws/docs/reference/licensing/) |
| Madani 1441H Hafs pages | Retain the existing 604 ranges, dataset bytes, edition ID, provenance and CC BY 4.0 attribution from Quran.ws Quran SVG Elements v1.1.1. [QURAN-01C verification](METADATA_CLEARANCE.md) |

The two new files are HifzTrack-maintained adaptations of openly licensed reference material. Their compilation inputs are the Quran.ws registry and division index. KFGQPC's archived developer data is comparison evidence. The existing verse XML supplies canonical coordinate attributes for structural validation. The historical Tanzil, QUL and Quran.com metadata candidates supply no values to these files. The application uses local files for import and the database for lookups.

| Version 1.0.0 normalized file | SHA-256 after LF normalization |
|---|---|
| `surahs-v1.json` | `ffa2bb94cc21f98b45f95e6939d9cb3941ab218169caed4a4e393c1cac9c8438` |
| `juzs-v1.json` | `abc8c423b6b12f0b20499019192c49b7781d3acf5c8602a4cc32562a47ab9798` |

## Structural and independent accuracy checks

- **Structure.** The compiler validates 114 ordered Surah IDs, exact agreement on the canonical 6,236 coordinate order, and 30 Juz ranges covering every numbered Ayah exactly once. Twenty-eight Juz ranges cross Surah boundaries. The importer validates the normalized hashes and inclusive endpoints. Read APIs verify ordered value digests in addition to provenance, so even an in-bounds edit that leaves all ranges contiguous makes the affected data unavailable.
- **Names.** All 114 Arabic entries agree with the KFGQPC developer archive after comparison-only folding of vocalization, spacing, terminal yeh variants and hamza position. The Latin comparison ignores case, accent and punctuation. It matched 108 of 114. The remaining six are recognized pronunciation or spelling variants for Surahs 3, 9, 60, 92, 106 and 108. The checked-in spellings are `Aal Imran`, `At-Tawbah`, `Al-Mumtahinah`, `Al-Layl`, `Quraysh` and `Al-Kawthar`. A human editorial read-through of the simplified list is still pending.
- **Juz.** All 30 starts were checked against the KFGQPC developer archive's numbered assignments and the 1441H edition's indexed marks. The archive's `jozz` field agrees on 28 starts. For Juz 4 and 11 it labels the transitions `3:92` and `9:94` respectively. The archive places an inline `U+06DE` marker at each approved start (`3:93`, `9:93`) and at all 21 Juz starts that fall inside a Surah. The other nine starts are Surah openings. The two sources agree on all 199 printed division-mark coordinates. These are source-level checks. A separate print review of the Juz designations remains pending. [Archived publisher package record](https://github.com/quran-ws/kfgqpc-resources/blob/main/metadata/quran-dev.json) · [Publisher printing master](https://qurancomplex.gov.sa/mushaf-printing)

Save the pinned [registry](https://raw.githubusercontent.com/quran-ws/docs/d1d6be33be9d/standards/terminology/registries/surahs.tsv) as `surahs.tsv`, the [registry license](https://raw.githubusercontent.com/quran-ws/docs/d1d6be33be9d/LICENSE) as `registry-LICENSE`, the [division index](https://cdn.quran.ws/svg/elements/v1.1.1/index/divisions.json) as `division-source.json`, its [manifest](https://cdn.quran.ws/svg/elements/v1.1.1/manifest.json) as `elements-manifest.json`, and the [publisher archive v2.0, update 13.0](https://cdn.quran.ws/KFGQPC/resources/quran-dev/uthmanic-hafs/UthmanicHafs_v2-0.zip) as `publisher.zip`. The compiler pins the checksums and compares the committed outputs by default.

```powershell
python -B data/quran/validation/compile_reference_metadata.py <evidence-directory>
```

## Implementation and verification runs

- Migration `0009_quran_surah_names` adds nullable `name_ar` and `name_latin` columns. Juz and pages use the existing start-coordinate tables. The importer uses one transaction for the requested categories and refuses partial or conflicting stored data. Existing numeric and page-only imports and the page API payloads remain compatible. [Database design](../../../docs/architecture/DATABASE_DESIGN.md) · [API contracts](../../../docs/architecture/API_SPECIFICATION.md)
- `python -m app.quran.import_reference --with-metadata --with-pages` extended a page-seeded database and reran successfully. The new Surah fields are optional, Juz endpoints resolve in both directions, and missing or corrupted data is unavailable by category. `/quran`, `/memorization` and `/revision` support named Surah choices, Juz and page ranges, and numeric fallback.
- Guarded PostgreSQL 18.6 `python -m pytest -q -p no:cacheprovider --basetemp <qa-directory>` passed **113 tests, zero skips**. Coverage includes all stored reference coordinates, range gaps and overlaps, valid-coordinate page and Juz corruption, name corruption, conflict rollback, idempotence, and preserved learner history, sharing settings, and personal and group dashboard responses. `python -m alembic upgrade head`, `python -m alembic downgrade 0008_group_sharing`, re-upgrade and `python -m alembic check` passed. PostgreSQL 17 was unavailable on this run because the Docker daemon was down and the installed server was 18.6.
- `python -B -m pytest -q -p no:cacheprovider data/quran/validation/test_validate_datasets.py` passed both tests. The independent metadata compiler passed pinned-input and shipped-output checks. `node node_modules/typescript/bin/tsc --noEmit -p tsconfig.json`, `node node_modules/next/dist/bin/next build --webpack` and `docker compose --env-file .env.example -f infrastructure/docker/compose.yaml config --quiet` passed.
- Headless Chrome against the production build and live disposable PostgreSQL verified numeric browsing with partial metadata, both displayed names, 30 Juz and 604 page options, both exceptional Juz starts, Juz selection and Sabaq save, page-based Sabaq correction with the original preserved, Juz selection and revision save, and a Juz API error with page selection still usable.

## Changed files

- Backend and tests. `backend/app/quran/{import_reference,importer,metadata,pages,ranges}.py`, `backend/app/{api,models,schemas}/quran.py`, `backend/migrations/versions/0009_quran_surah_names.py` and `backend/tests/postgres/{conftest,test_quran_reference_postgres}.py`.
- Frontend. `frontend/src/app/{quran,memorization,revision}/page.tsx` and `frontend/src/components/{mushaf-page-picker,surah-select}.tsx`.
- Data and evidence. `data/quran/derived/reference/{juzs-v1.json,surahs-v1.json,NOTICE.md}` and `data/quran/validation/{compile_reference_metadata.py,INDEPENDENT_METADATA.md}`.
- Setup and canonical documentation. `README.md`, `docs/{01_PRODUCT_REQUIREMENTS,02_FEATURE_CATALOG,04_BUSINESS_RULES}.md`, `docs/architecture/{API_SPECIFICATION,DATABASE_DESIGN}.md`, `docs/decisions/DECISIONS_LOG.md`, `docs/roadmap/{DEVELOPMENT_ROADMAP,IMPLEMENTATION_STATUS,OPEN_DECISIONS}.md` and `docs/user-experience/UI_REQUIREMENTS.md`.

## Independent human review still pending

1. Compare all 114 Arabic names by Surah number against an authoritative Hafs Mushaf index. Confirm the plain spelling treatment for Surahs 34, 42 and 78, where publisher orthography differs.
2. Read through the 114 Latin display names with the Arabic headings. Confirm the six documented spelling variants and the compiler's explicit editorial spellings.
3. Compare each of the 30 starts against the numbered Juz designation in an authoritative Hafs Mushaf. Explicitly confirm `3:93` and `9:93` in the 1441H edition, then record the reviewer, edition, date and any corrections before changing QURAN-01 status.
