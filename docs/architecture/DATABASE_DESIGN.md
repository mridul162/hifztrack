# Database design

This is a source-reconciled conceptual baseline, not a finalized migration specification. The original recommends PostgreSQL, SQLAlchemy 2.0, UUID primary keys and a normalized relational schema. Exact migration DDL, indexes/constraints beyond those listed, deletion policy, and Quran dataset/license must be reviewed before migrations.

## Candidate entities

| Entity | Purpose and key relationships |
|---|---|
| users | UUID identity/profile, email or phone login identifier, password hash, active state and timestamps; owns personal progress/settings. Never store plaintext passwords. |
| groups | UUID community/class/cohort, optional organization FK, name/description/creator/active state/time. |
| organizations | Future institutional container for groups; role scope requires design. |
| memberships | User-to-group association; role ADMIN/MENTOR/MEMBER, status PENDING/ACTIVE/SUSPENDED/LEFT; unique `(group_id,user_id)` per source; index both FKs; only ACTIVE grants access. Rejoin/history semantics remain open. |
| group_invitations | Group, random hashed invite code, creator, expiry, optional max uses, used count, active/revoked status. |
| group_sharing_settings | Unique membership FK; controls overall progress, memorization logs, revision logs, goals, assessments; updated timestamp; private or summary-level default. |
| quran_surahs / quran_ayahs | 114 Surahs; stable Quran-wide ID for 6,236 Ayahs, Surah/local Ayah number, Juz and Madani page number; unique `(surah_id,ayah_number)` and validated canonical import. |
| quran_juz / quran_pages / mappings | Canonical mappings from references to Ayahs; data import provenance required. |
| memorization_entries | User-owned Sabaq submission: UUID, start/end Ayah IDs, activity date, optional notes/time spent, SUBMITTED/CANCELLED status, created timestamp. Historical activity, not current state. |
| user_ayah_progress | Exactly one current row per `(user_id, ayah_id)` with NOT_STARTED/LEARNING/MEMORIZED/STRONG status and update timestamp. |
| ayah_progress_events | Recommended later history of status changes, including actor/reason; source says add eventually, so not an MVP requirement unless required for audit policy. |
| revision_sessions | User-owned range/type (RECENT/OLD/FULL_JUZ/FULL_QURAN), activity date, time spent, optional 1–5 self-rating, notes, created timestamp. |
| mentor_assignments / assessments | Optional learner/mentor/group assignment; assessment references memorization entry, mentor, group, PASSED/NEEDS_IMPROVEMENT, feedback and assessed timestamp. |
| user_goals / group_goals | Personal new-memorization/revision target with value, AYAHS/PAGES/JUZ, date range/active flag; collective group target, not duplicated member goals. |
| personal_notes | Private-by-default Ayah-linked notes. |
| notifications / announcements / activity | Later communication and engagement records with explicit visibility scope. |
| audit_events | Sensitive changes and access/role events according to retention policy. |

Original later-stage entities also include announcements, notifications, mentor assignments, audit logs, and refresh tokens. Their implementation and exact schemas are deferred to relevant milestones; refresh-token storage depends on the approved session design. The source's analytics recommendation is SQL aggregation, not AI.

## Relationships and invariants

- Users have many groups through memberships; groups have many users.
- Memorization and revision records reference a user, never a group as owner. Group dashboards query the same central user record through membership and sharing policy; they must not create group-owned copies.
- Group views join a user's allowed sharing settings and active membership before returning details.
- Ayah-level progress is the source for derived Surah/Juz/page progress.
- Revision history does not mutate memorization status implicitly.
- Assessment records identify assessor, learner, referenced activity/range, and timestamp without replacing learner entries.
- Each membership carries its own role scope, allowing the same user to have different roles in different groups.
- Surah/Ayah are canonical reference coordinates. Juz and Mushaf page references are derived through versioned canonical mappings; they are not separate progress stores.
- Current Ayah state and historical Sabaq events are separate concepts and tables; exact source-of-truth transition/correction behavior remains undecided.
- Memorization submission and resulting current-state updates occur in one service-layer transaction. Any approved assessment-triggered progress update is atomic with the assessment.
- Validate Quran ranges through canonical ordering; numeric ID arithmetic alone is not sufficient validation.
- Current-state progress is counted per Ayah, not by the number of activity submissions.
- Group analytics keep unique Ayah totals, mean individual completion, milestone counts, and participation rate as distinct labeled metrics.
- Invitation tokens are random, hashed, expiring, revocable, and may have use limits.

## Open schema decisions

Open schema details include correction/rejoin semantics, date/time and timezone representation, exact Quran dataset/version/license, range representation, sharing configuration and API actor, audit scope, and organization inheritance. The source recommends one current progress row per user/Ayah plus separate immutable activity history; it does not specify the complete status event log or every correction workflow.
