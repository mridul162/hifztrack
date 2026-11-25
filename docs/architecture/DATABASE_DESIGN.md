# Database design

This documents the implemented baseline and remaining conceptual entities. The project uses PostgreSQL, SQLAlchemy 2.0, UUID primary keys, and Alembic migrations. AUTH-01 is in migration `0002_auth`; GROUP-01/GROUP-02 schema is in `0003_groups`; Quran reference schema extends in `0004_quran_reference` and `0005_quran_reference_sources`; personal memorization tables are added in `0006_memorization`; membership-scoped sharing settings are added in `0008_group_sharing`. DEC-002 remains conditional: verify Arabic provenance/license/attribution before public release; document sources and usage conditions for each further metadata category; verify the exact Madani edition and all page boundaries before adding page mappings. The Tanzil metadata XML is not an application dependency.

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
| group_sharing_settings | Implemented in `0008_group_sharing`: one settings record per membership episode, linked by a unique membership FK; overall progress visibility is `PRIVATE`/`SUMMARY`/`DETAILED` (defaults `SUMMARY`), plus independent Boolean controls for memorization logs, revision logs, goals, and assessments (all default false), and creation/update timestamps. Settings are owner-controlled and episode-specific; the migration backfills existing episodes and each new membership flow creates its settings in the same transaction. Rejoining creates a new row with defaults. (DEC-006/016/023; ADR-018). |
| quran_surahs / quran_ayahs | Created by `0004_quran_reference`; `0005_quran_reference_sources` adds each Surah's Ayah count. Surah number is the Surah key; `(surah_number, ayah_number)` is the stable Ayah key. The importer stores numeric coordinates/counts only, never Arabic text or Surah names. |
| quran_reference_sources | One provenance record per imported metadata category: source name/version/path/hash/link, usage conditions and structural verification method. The first supported category is `SURAH_AYAH_ORDER`; it is read from the Tanzil Arabic source file, never the Tanzil metadata XML. |
| quran_juzs / quran_pages | Empty mapping tables hold each Juz/page number and its start `(surah_number, ayah_number)` coordinate; composite FKs require an existing canonical Ayah. Mapping rows remain unpopulated until each source is established; Madani pages additionally require exact-edition identification and independent boundary verification under DEC-002. |
| memorization_entries | User-owned Sabaq submission: UUID, canonical start/end Surah/Ayah coordinates with composite Quran FKs, activity date, optional notes/time spent, SUBMITTED/CANCELLED status, created timestamp. Every submission is preserved as history; corrections cancel the incorrect entry and add a corrected one without changing current Ayah status (DEC-005 / ADR-016). |
| user_ayah_progress | At most one current row per `(user_id, surah_number, ayah_number)` with NOT_STARTED/LEARNING/MEMORIZED/STRONG status and update timestamp. An absent row is interpreted as NOT_STARTED; writes are explicit learner actions. |
| ayah_progress_events | Recommended later history of status changes, including actor/reason; source says add eventually, so not an MVP requirement unless required for audit policy. |
| revision_sessions | Immutable user-owned range/type (RECENT/OLD/FULL_JUZ/FULL_QURAN), activity date, time spent, optional 1–5 self-rating and notes, created timestamp. Composite Quran FKs and checks validate endpoints, canonical range order, type, duration and rating. No cancellation, replacement, or soft-delete fields; DEC-005 applies to Sabaq only (ADR-017). |
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
- Authorization and response filtering follow the field-by-field rules in `docs/04_BUSINESS_RULES.md`; no personal notes or group-owned copies are exposed by sharing.
- Sharing permissions are evaluated per membership episode. Only the data owner changes that episode's settings; group roles do not override them. All ACTIVE group members are eligible audiences for enabled fields, while PENDING, SUSPENDED, and LEFT memberships are excluded. Backend queries filter existing and future eligible records according to the approved field matrix; never duplicate personal records into group-owned copies.
- A new episode's settings use the approved defaults; historical settings are retained with the prior episode and are not restored on rejoin. The settings model does not grant edit/delete access to shared personal records.
- Ayah-level progress is the source for derived Surah/Juz/page progress.
- Revision history does not mutate memorization status. Revision sessions are append-only and cannot be edited, corrected, cancelled, or deleted by users (ADR-017).
- Assessment records identify assessor, learner, referenced activity/range, and timestamp without replacing learner entries.
- Assessment does not automatically mutate learner status. Any approved future status transition is atomic with its assessment (DEC-019).
- Each membership episode carries one role, allowing the same user to have different roles in different groups. Multiple admins and mentors per group are allowed.
- Surah/Ayah are canonical reference coordinates. Juz and Mushaf page references are derived through versioned canonical mappings; they are not separate progress stores.
- Current Ayah state and preserved historical Sabaq activity are separate concepts and tables. Cancellation/correction rules are defined by DEC-005 / ADR-016; status changes are explicit learner actions defined by DEC-004 / ADR-015.
- Sabaq submission, cancellation, and correction never change `user_ayah_progress`. Correcting a Sabaq entry cancels the old row and creates a replacement in one transaction. Status updates are independent explicit learner actions. Any approved assessment-triggered progress update is atomic with the assessment.
- Validate Quran ranges through canonical ordering; numeric ID arithmetic alone is not sufficient validation.
- Current-state progress is counted per Ayah, not by the number of activity submissions.
- Dashboards read existing tables without a schema change. Personal statistics group current Ayah statuses in SQL. Group queries join ACTIVE membership episodes to their sharing settings and aggregate eligible coverage in SQL for the roster and whole-group mean. Personal histories and shared activity remain user-owned and are read separately.
- Group analytics keep unique Ayah totals, mean individual completion, milestone counts, and participation rate as distinct labeled metrics.
- Invitation tokens are random, HMAC-digested, expiring, revocable, and use-limited. Acceptance and last-admin protection serialize on the group row; invitation consumption also locks the invitation and increments use count in the same transaction.

## Open schema decisions

Open schema details include date/time policy, range representation, group goal type/completion (DEC-024), and broader audit retention. Sharing visibility, owner-only control, and default semantics are resolved in DEC-006/016/023; the conceptual settings model above does not prescribe implementation details. DEC-002 conditionally approves the Quran source/convention; release and further-category evidence gates remain as recorded in ADR-014. Organization inheritance is not used for authorization. Membership episode, group lifecycle, invitation policy, and minimal organization support are resolved in DEC-007/008/009/017/020/021.
