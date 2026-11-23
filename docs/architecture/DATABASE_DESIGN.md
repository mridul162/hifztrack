# Database design

This documents the implemented baseline and remaining conceptual entities. The project uses PostgreSQL, SQLAlchemy 2.0, UUID primary keys, and Alembic migrations. AUTH-01 is in migration `0002_auth`; GROUP-01/GROUP-02 schema is in `0003_groups`. DEC-002 conditionally approves the Quran source/convention; its provenance, notice, metadata-license, and page-boundary verification gates remain required before Quran reference integration.

## Candidate entities

| Entity | Purpose and key relationships |
|---|---|
| users | UUID identity/profile, email or phone login identifier, password hash, active state and timestamps; owns personal progress/settings. Never store plaintext passwords. |
| user_sessions | Opaque token SHA-256 hash, owning user, creation/expiry/revocation timestamps; session token itself is only in an HttpOnly cookie. |
| auth_rate_limits | Fixed-window scope, HMAC key digest, UTC window start, attempt count and expiry; used for AUTH-01 registration/login throttles. |
| groups | UUID community/class/cohort, nullable organization FK, name/description/creator, ACTIVE/ARCHIVED lifecycle, timestamps. Archive is read-only, blocks invitations and membership changes, revokes outstanding invitations, and preserves history; members may leave. Hard deletion is not implemented. |
| organizations | Minimal UUID/name/timestamps table. The optional group association grants no access; organization membership, roles, administration, and authorization are out of scope. |
| group_memberships | Membership episode with role ADMIN/MENTOR/MEMBER, state PENDING/ACTIVE/SUSPENDED/LEFT, join/leave and audit timestamps. PostgreSQL partial unique index on `(group_id,user_id)` covers PENDING/ACTIVE/SUSPENDED only; LEFT episodes remain as history and rejoining creates a new row. Only ACTIVE grants access. |
| group_invitations | Group, creator, unique HMAC token digest, expiry, capped use count, used count, revocation and created timestamps. Default expiry is 7 days and max uses 1; plaintext is returned only at creation. |
| group_membership_events | Append-only role/state/join/leave event record with membership/group/actor, prior/new value and timestamp; no unrelated personal fields. |
| group_rate_limits | PostgreSQL fixed-window counters with HMAC digests, UTC window start, attempts and expiry; separate from AUTH-01 counters. |
| group_sharing_settings | Unique membership FK; five controls for overall progress, memorization logs, revision logs, goals, assessments; updated timestamp; privacy-conscious default. How summary versus detailed overall progress maps to these controls is unresolved (DEC-023); no visibility-level schema is selected. |
| quran_surahs / quran_ayahs | 114 Surahs; stable Quran-wide ID for 6,236 Ayahs, Surah/local Ayah number, Juz and Madani page number; unique `(surah_id,ayah_number)` and validated canonical import. |
| quran_juz / quran_pages / mappings | Canonical mappings from references to Ayahs; data import provenance required. |
| memorization_entries | User-owned Sabaq submission: UUID, start/end Ayah IDs, activity date, optional notes/time spent, SUBMITTED/CANCELLED status, created timestamp. Every submission is preserved as history; corrections cancel the incorrect entry and add a corrected one without changing current Ayah status (DEC-005 / ADR-016). |
| user_ayah_progress | Exactly one current row per `(user_id, ayah_id)` with NOT_STARTED/LEARNING/MEMORIZED/STRONG status and update timestamp. |
| ayah_progress_events | Recommended later history of status changes, including actor/reason; source says add eventually, so not an MVP requirement unless required for audit policy. |
| revision_sessions | User-owned range/type (RECENT/OLD/FULL_JUZ/FULL_QURAN), activity date, time spent, optional 1–5 self-rating, notes, created timestamp. |
| mentor_assignments / assessments | Optional learner/mentor/group assignment; assessment references memorization entry, mentor, group, PASSED/NEEDS_IMPROVEMENT, feedback and assessed timestamp. |
| user_goals / group_goals | Personal new-memorization/revision target with value, AYAHS/PAGES/JUZ, date range/active flag; collective group target, not duplicated member goals. Candidate `group_goals` lacks the `goal_type` present in `user_goals`; resolve type/completion semantics under DEC-024 before final schema. |
| personal_notes | Private-by-default Ayah-linked notes. |
| notifications / announcements / activity | Later communication and engagement records with explicit visibility scope. |
| audit_events | Sensitive changes and access/role events according to retention policy. |

Original later-stage entities also include announcements, notifications, mentor assignments, audit logs, and refresh tokens. Their implementation and exact schemas are deferred to relevant milestones; refresh-token storage depends on the approved session design. The source's analytics recommendation is SQL aggregation, not AI.

## Relationships and invariants

- Users have many groups through memberships; groups have many users.
- Memorization and revision records reference a user, never a group as owner. Group dashboards query the same central user record through membership and sharing policy; they must not create group-owned copies.
- Group views join a user's allowed sharing settings and active membership before returning details.
- Ayah-level progress is the source for derived Surah/Juz/page progress.
- Revision history does not mutate memorization status.
- Assessment records identify assessor, learner, referenced activity/range, and timestamp without replacing learner entries.
- Assessment does not automatically mutate learner status. Any approved future status transition is atomic with its assessment (DEC-019).
- Each membership episode carries one role, allowing the same user to have different roles in different groups. Multiple admins and mentors per group are allowed.
- Surah/Ayah are canonical reference coordinates. Juz and Mushaf page references are derived through versioned canonical mappings; they are not separate progress stores.
- Current Ayah state and preserved historical Sabaq activity are separate concepts and tables. Cancellation/correction rules are defined by DEC-005 / ADR-016; status changes are explicit learner actions defined by DEC-004 / ADR-015.
- Memorization submission and resulting current-state updates occur in one service-layer transaction. Any approved assessment-triggered progress update is atomic with the assessment.
- Validate Quran ranges through canonical ordering; numeric ID arithmetic alone is not sufficient validation.
- Current-state progress is counted per Ayah, not by the number of activity submissions.
- Group analytics keep unique Ayah totals, mean individual completion, milestone counts, and participation rate as distinct labeled metrics.
- Invitation tokens are random, HMAC-digested, expiring, revocable, and use-limited. Acceptance and last-admin protection serialize on the group row; invitation consumption also locks the invitation and increments use count in the same transaction.

## Open schema decisions

Open schema details include date/time policy, Quran dataset/version/license, range representation, sharing visibility representation (DEC-023) and API actor, group goal type/completion (DEC-024), and broader audit retention. Organization inheritance is not used for authorization. Membership episode, group lifecycle, invitation policy, and minimal organization support are resolved in DEC-007/008/009/017/020/021.
