# Implementation status and open questions

## Status

F0-A (minimum application foundation) is VERIFIED: Next.js frontend, FastAPI backend, PostgreSQL Compose service, health endpoints, and its initial empty Alembic baseline. AUTH-01 / USER-01 are also VERIFIED as a separate milestone below. The broader Phase 0 checklist remains NOT AUTHORIZED and must not be inferred from either milestone.

Status meanings: `NOT_STARTED` = no implementation; `IN_PROGRESS` = actively being built; `IMPLEMENTED` = code exists, verification pending; `VERIFIED` = acceptance criteria and relevant tests pass.

Quran source data was inspected and comment-only well-formed derivative translation XML files were created under `data/quran/derived/translations/`; see [`data/quran/validation/VALIDATION_REPORT.md`](../../data/quran/validation/VALIDATION_REPORT.md) and rerunnable [`validate_datasets.py`](../../data/quran/validation/validate_datasets.py). All three original translation files still fail strict XML parsing and remain unchanged. Derivatives pass structural and content-preservation checks. This does not implement or verify QURAN-01 and does not resolve DEC-002: translation/metadata licensing evidence remains incomplete. The broader Phase 0 checklist remains NOT AUTHORIZED.

F0-A verification at completion: backend tests, local liveness/readiness behavior, Next.js production build, dependency audit, Compose configuration, healthy PostgreSQL/FastAPI/Next.js containers, frontend-to-backend networking, CORS, and `alembic upgrade head` against fresh PostgreSQL 17 passed. At that point the database contained only `alembic_version`. AUTH-01 is a subsequent milestone and adds separate user/session/rate-limit tables; it does not alter the F0-A verification record. No Quran reference integration is authorized by this work.

AUTH-01 / USER-01 status: VERIFIED. Thirteen backend tests pass, including registration/duplicate handling, password hashing, valid/invalid login, session persistence/expiry/revocation, current-user profile access/update, cross-account session isolation, CSRF validation, and registration/login throttles. The AUTH-01 migration applied to local PostgreSQL, `alembic check` reports no schema drift, and a PostgreSQL-backed registration/login/profile/revocation smoke flow passed with its temporary account removed. Next.js production build passes; Compose rebuild/start produced healthy PostgreSQL, API, and frontend services; API liveness and `/login` return 200. Compose configuration and `git diff --check` pass. No Quran data was ingested or integrated. The broader Phase 0 remains NOT AUTHORIZED.

GROUP-01 / GROUP-02 status: VERIFIED. The implementation was verified against PostgreSQL 17.12 using a disposable container with tmpfs database storage and no persistent volume. Alembic upgraded to `0003_groups`, downgraded to base (leaving only `alembic_version`), upgraded again, and `alembic check` found no drift. PostgreSQL schema inspection confirmed the required tables, check constraints, foreign keys, and `uq_group_memberships_current` partial index for PENDING/ACTIVE/SUSPENDED (excluding LEFT). Thirty backend SQLite tests and 19 PostgreSQL integration tests pass. PostgreSQL tests cover single/multi-use invitation races, last-admin and membership uniqueness races, expiry while waiting for a lock, invite revocation racing with acceptance, exact boundaries for all invitation rate-limit scopes, HMAC storage, and counter cleanup. Explicit-null role/state requests return 422; acceptance refreshes the locked invitation row and checks expiry with a fresh timestamp. Frontend TypeScript and production build pass. No frontend test script or Ruff executable is available. No persistent development database volume was used. This work does not implement sharing, dashboards, Quran tracking, or mentor workflows.

## Source coverage and reconciliation

Reviewed `docs/source/original_specification.md` and `docs/source/original_specification_2.md`; they remain preserved unchanged. The first contains PRD, FR-01..FR-17, business/data rules, schema, architecture, REST candidates, UI and eight-phase plan. The second contains repository and development workflow guidance. Requirements now map original FR IDs to current feature IDs and coverage.

## Reconciliation against original specifications

| Source requirement area | Reconciliation result |
|---|---|
| FR-01/02/05/11 | Covered in requirements and feature catalog. |
| FR-03/04 | Features present; invitation token behavior captured; group deletion/archival and rejoin details remain partial. |
| FR-06/07/08/09 | Counts, status vocabulary, session fields, range validation and progress denominator captured; exact dataset/license and status transitions remain open. Full-text search is separate extended scope. |
| FR-10 | Five sharing categories and private/summary default recommendation captured; API actor/ownership ambiguity remains. |
| FR-12 | P0 dashboard screen content captured; group statistics are limited to current-state/basic summaries. Goals/announcements are conditional because they are P1. |
| FR-13/14/15 | Corrected to P1/Release 2; target types/units, assessment result model and notification/announcement lifecycle captured; schedule cadence, status effects, delivery preferences remain open. |
| FR-16/17 | Historical reports/analytics mapped to P1 with distinct group metrics; progress-report export mapped to P2. Exact date windows, export fields and format remain incomplete. |
| Non-functional requirements | Security, authorization, integrity, auditability, scalability, maintainability, mobile usability and deterministic calculations are explicit. |
| Architecture/schema/API/UI/workflow | Stack, layered monolith, source entities/constraints, REST candidates, six screen types, Phase 0-7 sequence, and Git/Codex governance incorporated. Detailed contracts, Quran dataset/license and deployment choices remain open. |
| Features absent from originals | Marked as extended proposals in feature catalog; none are authorized for MVP by inclusion in the catalog. |

Extended proposals beyond original functional requirements include personal account-data portability, activity feed/challenges/milestones, personal notes, revision recommendations, offline sync, WhatsApp integration, AI evaluation, and detailed audio recording/sharing. CSV/PDF as exact report formats are also an expansion. Accessibility conformance targets and exceptional platform-admin access are quality/security elaborations, not explicit FRs. Features explicitly excluded from MVP in the source remain future proposals only.

## Source ambiguities and documentation corrections

- Source PATCH path targets another member's sharing settings although product intent gives each owner control. Do not grant group-admin override without explicit approval.
- Source P0 dashboards mention personal goals and announcements although FR-13/FR-15 are P1. The UI docs make those panels conditional; do not imply P1 functionality exists in MVP.
- `memorization_entries` are preserved historical activity but have SUBMITTED/CANCELLED state; cancellation/correction semantics remain open under DEC-005.
- Phase 2 resolves membership episodes: at most one PENDING/ACTIVE/SUSPENDED row per `(group_id,user_id)` using a partial unique index; LEFT rows are retained and excluded so rejoin creates a new episode.
- Assessments are separate records and do not automatically change learner status. Whether an explicit status-transition workflow may ever be permitted remains DEC-019; if approved, it must be transactional.
- Sharing booleans do not specify how summary and detailed overall-progress views are encoded; DEC-023 keeps the representation open.
- `group_goals` lacks the `goal_type` available in `user_goals`; type and completion calculations remain open under DEC-024.
- Full Quran text/advanced search is not in the original P0 reference-navigation requirement; it remains an extended proposal.
- P2 progress-report export is original. Personal account-data export and exact CSV/PDF details are extended proposals.
- API, DB, and UX documents remain design baselines, not final implementation contracts.

## Open decisions

See [OPEN_DECISIONS.md](OPEN_DECISIONS.md) for IDs, questions, rationale, options/consequences, and approval status. DEC-007/008/009 (group invitations)/017/020/021 were approved for Phase 2 on 2026-11-23. Remaining key decisions include status transitions, sharing actor/default, assessment effects, and Quran dataset/license.

## Foundation milestone

F0-A (minimum application foundation) was separately approved and is VERIFIED. The broader Phase 0 checklist remains NOT AUTHORIZED. AUTH-01 / USER-01 remains VERIFIED as recorded above. Phase 2 was explicitly authorized; GROUP-01 / GROUP-02 are IMPLEMENTED pending verification evidence.
