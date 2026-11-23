# Implementation status and open questions

## Status

F0-A (minimum application foundation) is authorized and implemented: Next.js frontend, FastAPI backend, PostgreSQL Compose service, health endpoints, and an empty Alembic baseline. Foundation verification is recorded below. No product feature is implemented or verified. The broader Phase 0 checklist remains NOT AUTHORIZED and must not be inferred from F0-A approval.

Status meanings: `NOT_STARTED` = no implementation; `IN_PROGRESS` = actively being built; `IMPLEMENTED` = code exists, verification pending; `VERIFIED` = acceptance criteria and relevant tests pass.

Quran source data was inspected and comment-only well-formed derivative translation XML files were created under `data/quran/derived/translations/`; see [`data/quran/validation/VALIDATION_REPORT.md`](../../data/quran/validation/VALIDATION_REPORT.md) and rerunnable [`validate_datasets.py`](../../data/quran/validation/validate_datasets.py). All three original translation files still fail strict XML parsing and remain unchanged. Derivatives pass structural and content-preservation checks. This does not implement or verify QURAN-01 and does not resolve DEC-002: translation/metadata licensing evidence remains incomplete. Phase 0 remains NOT AUTHORIZED.

F0-A status: VERIFIED. Backend development dependencies installed; all four backend tests pass; local liveness returns 200 and readiness returns 503 without PostgreSQL; Next.js production build passes; `npm audit` reports zero vulnerabilities; Compose configuration validates; PostgreSQL, FastAPI, and Next.js containers start healthy; frontend-to-backend networking and local-origin CORS work; and `alembic upgrade head` succeeds against a fresh PostgreSQL 17 database. The database contains only `alembic_version`; no business tables exist. This milestone does not include AUTH-01, domain models, or Quran reference integration. See the README for setup.

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
- Membership uniqueness `(group_id,user_id)` plus LEFT status leaves rejoin/history behavior unspecified.
- Assessments are separate records and do not automatically change learner status. Whether an explicit status-transition workflow may ever be permitted remains DEC-019; if approved, it must be transactional.
- Sharing booleans do not specify how summary and detailed overall-progress views are encoded; DEC-023 keeps the representation open.
- `group_goals` lacks the `goal_type` available in `user_goals`; type and completion calculations remain open under DEC-024.
- Full Quran text/advanced search is not in the original P0 reference-navigation requirement; it remains an extended proposal.
- P2 progress-report export is original. Personal account-data export and exact CSV/PDF details are extended proposals.
- API, DB, and UX documents remain design baselines, not final implementation contracts.

## Open decisions

See [OPEN_DECISIONS.md](OPEN_DECISIONS.md) for IDs, questions, rationale, options/consequences, provisional recommendations, and approval requirements. Source recovery is resolved. Remaining key decisions include status transitions, sharing actor/default, membership history, assessment effects, and Quran dataset/license.

## Foundation milestone

F0-A (minimum application foundation) was separately approved. It is limited to application scaffolding, health checks, database connectivity, migrations with no business tables, local Compose services, and setup documentation. Approval of F0-A does not authorize the broader Phase 0 checklist or AUTH-01.
