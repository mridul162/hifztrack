# Feature catalog

Status convention: `NOT_STARTED`, `IN_PROGRESS`, `IMPLEMENTED`, `VERIFIED`. AUTH-01, USER-01, GROUP-01, GROUP-02, MEM-01, and REV-01 are `VERIFIED`; QURAN-01 remains `IN_PROGRESS`. QURAN-01 has numeric Surah/Ayah import, read-only APIs and a browser view, while Juz/page mappings and release evidence gates remain incomplete. MEM-01's personal Ayah status and separate Sabaq history APIs, schema, migration, learner page, SQLite tests, and PostgreSQL 18.6 integration tests are verified; see implementation status for migration and concurrency evidence. REV-01 provides owner-only append-and-list revision history; DEC-005 remains Sabaq-specific and revision records are immutable under ADR-017. Other feature statuses remain as listed. Original source priorities map to P0=MVP, P1=next functional release, P2=later enhancement. Features carried forward from the earlier initialization brief but absent as requirements in both originals are marked “Extended proposal.” Rows include dependencies and minimum acceptance criteria; required tests should include positive behavior, validation, and negative authorization cases where data access is involved.

| ID | Feature | Priority / release | Dependencies | Minimum acceptance criteria |
|---|---|---|---|---|
| AUTH-01 | Registration, login, logout, secure sessions | MVP / P0 / FR-01 | — | Valid users can authenticate; invalid credentials fail safely; sessions end on logout. |
| USER-01 | Profile and account settings | MVP / P0 / FR-02 | AUTH-01 | User can view/update allowed profile fields; private fields are not exposed to others. |
| USER-02 | Personal account data portability | Extended proposal; release TBD | AUTH-01 | If retained, authenticated user can export only their own account data; distinct from original FR-17 progress-report export. |
| QURAN-01 | Canonical Quran reference and navigation | MVP / P0 / FR-06 | — | Full feature: stable Surah/Ayah IDs resolve; validated data covers 114 Surahs, 6,236 Ayahs, 30 Juz and 604 Madani pages; Juz/page navigation derives from canonical mappings. Implemented first slice imports numeric Surah/Ayah coordinates and Ayah counts from the preserved Tanzil Arabic source, records source provenance, and provides read-only lookup and browsing. Juz/page and other metadata categories require their own documented sources and verification; Madani pages remain gated by exact-edition and boundary verification. The Tanzil metadata XML is not an application dependency. Full-text search is excluded. |
| QURAN-SEARCH-01 | Full Quran text or advanced search | Extended proposal; release TBD | QURAN-01 | Scope and release require owner approval; not part of P0 reference lookup/navigation. |
| MEM-01 | Sabaq activity and current Ayah status | MVP / P0 / FR-07, FR-09 | AUTH-01, QURAN-01 | One current row per user/Ayah; separate preserved historical submissions; ranges follow canonical order; repeated/overlapping submissions do not inflate unique Ayah progress; cancellation preserves history; correction cancels and replaces a submission; status changes are explicit learner actions under ADR-015/016. |
| REV-01 | Muraja'ah sessions | MVP / P0 / FR-08 | AUTH-01, QURAN-01 | Separate owner-only immutable revision session records range, type (`RECENT`, `OLD`, `FULL_JUZ`, `FULL_QURAN`), activity date, time, optional 1–5 self-rating and notes; revision never changes status automatically; no edit, correction, cancellation or delete operations (ADR-017). |
| GROUP-01 | Group creation and lifecycle | MVP / P0 / FR-03 | AUTH-01 | Authorized user creates, updates, and archives groups; creator receives ACTIVE ADMIN membership; optional organization association is metadata only. Groups use ACTIVE/ARCHIVED; archive is read-only, revokes invitations, preserves history, and permits member leave. |
| GROUP-02 | Membership, invitations, roles | MVP / P0 / FR-04, FR-05 | AUTH-01, GROUP-01 | Membership episodes use one ADMIN/MENTOR/MEMBER role and PENDING/ACTIVE/SUSPENDED/LEFT state; partial uniqueness covers current states and permits LEFT history/rejoin; invitations are one-time token delivery, HMAC-digested, expiring, revocable, capped, and throttled; only ACTIVE grants access. Join requests are an extended proposal. |
| SHARE-01 | Per-group progress sharing | MVP / P0 / FR-10, FR-11 | USER-01, GROUP-02, MEM-01, REV-01 | Per-membership settings: overall progress `PRIVATE`/`SUMMARY`/`DETAILED` (new episode defaults to `SUMMARY`); independent memorization-log, revision-log, goal, and assessment Booleans default false. Only the owner changes their own settings; group role does not override privacy. ACTIVE members of that group can see only approved fields; non-ACTIVE memberships cannot access shared data. Apply settings to eligible existing and future records and enforce changes on subsequent backend requests; leave/rejoin creates a fresh defaulted episode. Preserve user-owned source records, expose no private notes, and do not grant edit/delete rights over shared records (DEC-006/016/023; ADR-018). Goals and assessments remain P1; documenting their sharing controls does not implement those features. |
| DASH-01 | Personal and group dashboards/member views | MVP / P0 / FR-11, FR-12 | ANALYTICS-01, REV-01, GROUP-02, SHARE-01 | The owner-only dashboard shows current progress, bounded recent Sabaq and revision, and active group links. The group dashboard shows the ACTIVE roster and roles, permitted progress and recent activity, and mean completion with its contributor count. Both use the metric and privacy rules in DEC-018 / ADR-019. |
| ANALYTICS-01 | Basic individual statistics | MVP / P0 / FR-09, FR-12 | MEM-01 | Count all four statuses from current per-Ayah state, with missing rows counted as NOT_STARTED. Coverage counts MEMORIZED plus STRONG and uses 6,236 as the denominator. Activity cannot change the totals. A status regression is reflected on the next read. |
| GOAL-01 | Individual and collective group targets; schedules are an extended proposal | Release 2 / P1 / FR-13 | AUTH-01, MEM-01, GROUP-02, QURAN-01 | Individual goals cover new memorization or revision with target/unit/date range; group goals are collective, not copies of members' goals; group goal type and completion calculation remain DEC-024. |
| MENTOR-01 | Mentor assignment and learner monitoring | Release 2 / P1 / FR-14 | GROUP-02, SHARE-01 | Authorized parties establish/withdraw assignments; mentors assess only assigned members in their group; multiple mentors may assess a member in different groups; data relationships support this without changing personal record ownership. |
| MENTOR-02 | Assessments and feedback | Release 2 / P1 / FR-14 | MENTOR-01, MEM-01 | Assessment is a separate record associated with learner submission, mentor and group; result is PASSED or NEEDS_IMPROVEMENT; authorized group members only. It does not automatically change learner status; any future approved transition must be transactional (DEC-019). |
| NOTIFY-01 | Notifications | Release 2 / P1 / FR-15 | USER-01 | Notification delivery and preferences follow privacy policy; delivery channels and schedules remain to specify. |
| COMMUNITY-01 | Announcements | Release 2 / P1 / FR-15 | GROUP-02, SHARE-01 | Group announcements are visible within authorized scope and do not disclose unshared progress. |
| COMMUNITY-02 | Challenges and milestones | Extended proposal / Release 2 | GROUP-02, GOAL-01 | Earlier initialization brief addition; group challenge is opt-in and honors sharing. Not an original FR requirement. |
| ANALYTICS-02 | Historical reports and analytics | Release 2 / P1 / FR-16 | MEM-01, REV-01, SHARE-01 | SQL-derived, permission-filtered metrics distinguish total unique Ayahs, average individual completion, milestone counts, and participation rate. |
| NOTES-01 | Personal notes on difficult Ayahs/mistakes | Extended proposal / Release 2 | AUTH-01, QURAN-01 | Notes are Ayah-linked and private by default; sharing requires explicit policy. |
| RECOMMEND-01 | Weak/neglected portion revision recommendations | Extended proposal / Release 3 | REV-01, MEM-01 | Recommendations cite deterministic input signals and remain advisory. |
| AUDIO-01 | Recitation recording, sharing, mentor review | Extended proposal / Release 3 | AUTH-01, SHARE-01, MENTOR-01 | User controls recording access and deletion; review is permission-checked. |
| OFFLINE-01 | Offline activity capture and synchronization | Extended proposal / Release 3 | MEM-01, REV-01 | Offline entries sync without silent loss; duplicate/conflict behavior is documented. |
| WHATSAPP-01 | WhatsApp reminders and summaries | Extended proposal / Release 3 | NOTIFY-01 | Explicit opt-in, revocation, and privacy-safe content govern delivery. |
| REPORT-01 | Progress report export | Release 3 / P2 / FR-17 | DASH-01, SHARE-01, ANALYTICS-02 | Export scope follows caller access; fields/formats are documented. Source assigns P2/later; CSV/PDF formats came from the earlier initialization brief. |
| AI-01 | Optional AI-assisted recitation evaluation | Release 3 / experimental | AUDIO-01 | User opts in; output is clearly advisory, uncertainty is communicated, and data handling is disclosed. |
| ORG-01 | Organization data-model support | Data-model foundation; complex administration excluded from MVP | GROUP-01, GROUP-02 | Organization may contain groups; informal groups may have no organization; do not build complex institutional administration in MVP. |

## Feature specification and traceability standard

For each feature implementation, expand the row into objective, user stories, functional requirements, business rules, dependencies, acceptance criteria, required tests, priority, status, and links to schema/API/UI/test artifacts. Keep the mapping current across `architecture/DATABASE_DESIGN.md`, `architecture/API_SPECIFICATION.md`, UI requirements, and implementation status.

## Requirement traceability

| Feature IDs | Requirement IDs | Priority | Status |
|---|---|---|---|
| AUTH-01, USER-01 | PR-AUTH-01, PR-SEC-01 | P0 | VERIFIED |
| USER-02 | PR-USER-EXPORT-01 | Extended proposal | NOT_STARTED |
| REPORT-01 | PR-REPORT-01 | P2 / later | NOT_STARTED |
| QURAN-01 | PR-QURAN-01 | P0 | IN_PROGRESS (numeric Surah/Ayah slice implemented; Juz/page and release gates remain) |
| QURAN-SEARCH-01 | No original P0 requirement; extended proposal | TBD | NOT_STARTED |
| MEM-01 | PR-MEM-01, PR-HIST-01, PR-SEC-01 | P0 | VERIFIED (see implementation status) |
| REV-01 | PR-REV-01, PR-HIST-01 | P0 | VERIFIED (see implementation status) |
| GROUP-01, GROUP-02 | PR-GROUP-01 | P0 | VERIFIED (see implementation status) |
| SHARE-01 | PR-SHARE-01, PR-SEC-01 | P0 | VERIFIED (see implementation status) |
| DASH-01 | PR-DASH-01, PR-SEC-01 | P0 | VERIFIED (see implementation status) |
| ANALYTICS-01 | PR-ANALYTICS-01 | P0 | VERIFIED (see implementation status) |
| GOAL-01 | PR-GOAL-01 | P1 | NOT_STARTED |
| MENTOR-01, MENTOR-02 | PR-MENTOR-01 | P1 | NOT_STARTED |
| NOTIFY-01, COMMUNITY-01 | PR-COMM-01 | P1 | NOT_STARTED |
| COMMUNITY-02 | PR-COMM-02 | Extended proposal | NOT_STARTED |
| ANALYTICS-02 | PR-ANALYTICS-02 | P1 | NOT_STARTED |
| NOTES-01 | PR-NOTES-01 | Extended proposal | NOT_STARTED |
| RECOMMEND-01 | PR-RECOMMEND-01 | Extended proposal | NOT_STARTED |
| AUDIO-01 | PR-AUDIO-01 | Extended proposal | NOT_STARTED |
| OFFLINE-01 | PR-OFFLINE-01 | Extended proposal | NOT_STARTED |
| WHATSAPP-01 | PR-WHATSAPP-01 | Extended proposal | NOT_STARTED |
| AI-01 | PR-AI-01 | Excluded MVP; extended experimental proposal | NOT_STARTED |
| ORG-01 | PR-ORG-01 | Data-model support is original; complex administration excluded from MVP | NOT_STARTED |

## Minimum verification coverage

| Feature group | Required automated evidence before `VERIFIED` |
|---|---|
| AUTH-01, USER-01 | Valid/invalid authentication, session termination, ownership and private-field tests. |
| QURAN-01 | Canonical Surah/Ayah lookup and Juz/Mushaf-page navigation/mapping integrity tests. |
| QURAN-SEARCH-01 | If approved later, search relevance, text normalization and privacy tests. |
| MEM-01, REV-01 | User ownership, history preservation, current-state calculation, range boundary, and no implicit cross-activity mutation tests. |
| GROUP-01, GROUP-02 | Role-scoped membership lifecycle, multiple memberships, and cross-group role isolation tests. |
| SHARE-01, DASH-01 | Per-group preference matrix, live permission changes, revoked membership, denied access, and cross-group leakage tests. |
| ANALYTICS-01/02, REPORT-01 | Deterministic aggregates, time-window boundaries, permission-filtered outputs, and export scope tests. |
| MENTOR-01/02, AUDIO-01 | Consent/assignment scope, assessor attribution, revocation, and unauthorized access tests. |
| GOAL-01, NOTIFY-01, COMMUNITY-01/02, NOTES-01 | Ownership/role checks, privacy-safe delivery/feed behavior, opt-in settings, and boundary tests. |
| RECOMMEND-01, OFFLINE-01, WHATSAPP-01, AI-01 | Defined algorithm/conflict behavior, opt-in/revocation, privacy handling, and failure/uncertainty tests. |
| ORG-01 | Verify optional organization-to-group association does not bypass user sharing; any organization role requires separately approved scope. |

## Module coverage

The inventory includes authentication/user management, Quran reference, memorization, revision, groups, sharing, dashboards, goals, mentoring/assessment, analytics, notifications, community, notes, recommendations, audio, offline, WhatsApp, AI evaluation, reporting/export, and organizational support.

## Source provenance and added proposals

Original specification 1 is the source for FR-01 through FR-17, core model, roles, Quran reference, database concepts, REST API candidates, MVP UI and roadmap. Original specification 2 is the source for repository/Codex workflow and guardrails. The added proposal items retained from the earlier initialization brief, but not specified as functional requirements by the two originals, are personal account export (distinct from progress-report export), challenges/milestones, personal notes, revision recommendations, offline sync, WhatsApp integration, and AI evaluation. Audio was explicitly excluded from the MVP in the original; detailed recitation recording/sharing is retained as a future proposal, not a source requirement. No listed proposal enters the MVP by virtue of appearing here.
