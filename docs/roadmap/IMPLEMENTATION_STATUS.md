# Implementation status and open questions

## Status

Repository currently contains documentation only. Application features: `NOT_STARTED`. No feature is `IMPLEMENTED` or `VERIFIED`.

Status meanings: `NOT_STARTED` = no implementation; `IN_PROGRESS` = actively being built; `IMPLEMENTED` = code exists, verification pending; `VERIFIED` = acceptance criteria and relevant tests pass.

## Source coverage and reconciliation

Reviewed `docs/source/original_specification.md` and `docs/source/original_specification_2.md`; they remain preserved unchanged. The first contains PRD, FR-01..FR-17, business/data rules, schema, architecture, REST candidates, UI and eight-phase plan. The second contains repository and development workflow guidance. Requirements now map original FR IDs to current feature IDs and coverage.

## Reconciliation against original specifications

| Source requirement area | Reconciliation result |
|---|---|
| FR-01/02/05/11 | Covered in requirements and feature catalog. |
| FR-03/04 | Features present; invitation token behavior captured; group deletion/archival and rejoin details remain partial. |
| FR-06/07/08/09 | Counts, status vocabulary, session fields, range validation and progress denominator captured; exact dataset/license and status transitions remain open. |
| FR-10 | Five sharing categories and private/summary default recommendation captured; API actor/ownership ambiguity remains. |
| FR-12 | P0 dashboard screen content captured; goals/announcements are conditional because they are P1. |
| FR-13/14/15 | Corrected to P1/Release 2; target types/units, assessment result model and notification/announcement lifecycle captured; schedule cadence, status effects, delivery preferences remain open. |
| FR-16/17 | Historical reports/analytics mapped to P1 with distinct group metrics; progress-report export mapped to P2. Exact date windows, export fields and format remain incomplete. |
| Non-functional requirements | Security, authorization, integrity, auditability, scalability, maintainability, mobile usability and deterministic calculations are explicit. |
| Architecture/schema/API/UI/workflow | Stack, layered monolith, source entities/constraints, REST candidates, six screen types, Phase 0-7 sequence, and Git/Codex governance incorporated. Detailed contracts, Quran dataset/license and deployment choices remain open. |
| Features absent from originals | Marked as extended proposals in feature catalog; none are authorized for MVP by inclusion in the catalog. |

Extended proposals beyond original functional requirements include personal account-data portability, activity feed/challenges/milestones, personal notes, revision recommendations, offline sync, WhatsApp integration, AI evaluation, and detailed audio recording/sharing. CSV/PDF as exact report formats are also an expansion. Accessibility conformance targets and exceptional platform-admin access are quality/security elaborations, not explicit FRs. Features explicitly excluded from MVP in the source remain future proposals only.

## Source ambiguities and documentation corrections

- Source PATCH path targets another member's sharing settings although product intent gives each owner control. Do not grant group-admin override without explicit approval.
- Source P0 dashboards mention personal goals and announcements although FR-13/FR-15 are P1. The UI docs make those panels conditional; do not imply P1 functionality exists in MVP.
- `memorization_entries` are called immutable history but also have SUBMITTED/CANCELLED state; cancellation/correction semantics remain open.
- Membership uniqueness `(group_id,user_id)` plus LEFT status leaves rejoin/history behavior unspecified.
- Assessments are independent history, while a successful assessment may transactionally update status. Trigger, actor and authority remain unspecified.
- P2 progress-report export is original. Personal account-data export and exact CSV/PDF details are extended proposals.
- API, DB, and UX documents remain design baselines, not final implementation contracts.

## Open decisions

See [OPEN_DECISIONS.md](OPEN_DECISIONS.md) for IDs, questions, rationale, options/consequences, provisional recommendations, and approval requirements. Source recovery is resolved. Remaining key decisions include status transitions, sharing actor/default, membership history, assessment effects, and Quran dataset/license.

## Recommended first implementation milestone

Before application code, review this reconciliation and obtain approval for product decisions affecting schema/privacy. Then separately approve a roadmap phase. No application milestone has started; this task does not start Phase 0.
