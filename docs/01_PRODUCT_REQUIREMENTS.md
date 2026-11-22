# Product requirements

This document describes the intended complete product. Release assignments are maintained in [the feature catalog](02_FEATURE_CATALOG.md) and [MVP scope](roadmap/MVP_SCOPE.md).

## Product capabilities

Requirement IDs below are repository traceability anchors. Original source IDs FR-01 through FR-17 from `docs/source/original_specification.md` are mapped below. Source priority mapping is P0=MVP, P1=next functional release, P2=later enhancement. The second source is a development workflow guide rather than a separate functional requirements list.

| Requirement | Requirement statement | Release |
|---|---|---|
| PR-AUTH-01 | Users can register, authenticate, log out, and manage profiles/settings. | MVP |
| PR-GROUP-01 | Users can create groups, join by invitation, hold multiple memberships, and have group-scoped roles. | MVP |
| PR-QURAN-01 | Quran references resolve canonically by Surah and Ayah, with Juz/page navigation and search. | MVP |
| PR-MEM-01 | Users record Sabaq at Ayah/range level; current progress is distinct from preserved historical activity. | MVP |
| PR-REV-01 | Users record Muraja'ah separately with revision type, notes, and self-assessment. | MVP |
| PR-SHARE-01 | Users configure sharing independently for each group; backend APIs enforce settings. | MVP |
| PR-DASH-01 | Personal and group dashboards show appropriate progress/member summaries. | MVP |
| PR-ANALYTICS-01 | Basic individual statistics are available and derived deterministically. | MVP |
| PR-GOAL-01 | Users set personal targets and groups set collective targets for new memorization or revision. | Release 2 / P1 |
| PR-MENTOR-01 | Optional mentors are assigned, monitor learners, assess progress, and provide feedback. | Release 2 |
| PR-COMM-01 | Groups can use notifications and announcements. | Release 2 / P1 |
| PR-ANALYTICS-02 | Learners/groups can use advanced progress, consistency, participation, and revision analytics. | Release 2 |
| PR-USER-EXPORT-01 | Personal account data portability. | Extended proposal; not in original FRs |
| PR-NOTES-01 | Personal notes about difficult Ayahs/mistakes. | Extended proposal |
| PR-COMM-02 | Activity feed, challenges, and milestones. | Extended proposal |
| PR-REPORT-01 | Export progress reports. | Later / P2 (FR-17); CSV/PDF are proposed format details |
| PR-RECOMMEND-01 | Identify weak/neglected portions and recommend revision. | Future proposal; advanced recommendations excluded from MVP |
| PR-AUDIO-01 | Record/share recitation and enable mentor review. | Future proposal; recording/playback excluded from MVP |
| PR-OFFLINE-01 | Record activities offline and synchronize later. | Extended proposal |
| PR-WHATSAPP-01 | WhatsApp reminders and summaries. | Future proposal; integration excluded from MVP |
| PR-AI-01 | Optional AI-assisted recitation evaluation and feedback. | Experimental proposal; AI evaluation excluded from MVP |
| PR-ORG-01 | Support informal and institutional contexts in product architecture/data model. | Data-model foundation; complex administration excluded from MVP |
| PR-SEC-01 | Protected data is authorized server-side; personal records remain user-owned and group access obeys each user's settings. | All releases |
| PR-HIST-01 | Historical activity is preserved while current progress is represented separately. | MVP foundation |

## Original functional requirement traceability

| Original source ID | Original requirement / priority | Current feature mapping | Coverage |
|---|---|---|---|
| FR-01 | Registration and login / P0 | AUTH-01 | Complete |
| FR-02 | Personal profile / P0 | USER-01 | Complete |
| FR-03 | Create, update, delete groups / P0 | GROUP-01 | Partial: delete/archival policy unspecified |
| FR-04 | Join by invitation / P0 | GROUP-02 | Partial: invitation lifecycle details need acceptance criteria |
| FR-05 | Multiple group memberships / P0 | GROUP-02 | Complete |
| FR-06 | Surah, Ayah, Juz, page references / P0 | QURAN-01 | Partial: 114/30/604 Madani page convention and dataset validation need explicit acceptance |
| FR-07 | Record new memorization / P0 | MEM-01 | Partial: source fields and submission/cancellation state need acceptance criteria |
| FR-08 | Record revision sessions / P0 | REV-01 | Partial: source revision types and rating range need acceptance criteria |
| FR-09 | Calculate individual progress / P0 | MEM-01, ANALYTICS-01 | Partial: formulas and 6,236 Ayah denominator need explicit definitions |
| FR-10 | Custom group sharing / P0 | SHARE-01 | Partial: exact fields are known; API actor/ownership ambiguity remains |
| FR-11 | View shared member progress / P0 | DASH-01, SHARE-01 | Complete in principle; all fields remain permission-filtered |
| FR-12 | Individual and group dashboards / P0 | DASH-01 | Partial: source screen contents are not fully specified in UI requirements |
| FR-13 | Individual and group targets / P1 | GOAL-01 | Partial: group collective goal semantics and schedules need criteria |
| FR-14 | Mentor assessment and feedback / P1 | MENTOR-01, MENTOR-02 | Partial: assessment history is separate; effects on status need decision |
| FR-15 | Notifications and announcements / P1 | NOTIFY-01, COMMUNITY-01 | Partial: delivery/preferences and announcement lifecycle unspecified |
| FR-16 | Historical reports and analytics / P1 | ANALYTICS-02, REPORT-01 | Partial: source metric definitions need inclusion |
| FR-17 | Export progress reports / P2 | REPORT-01 | Partial: data scope and formats unspecified; later release |

### Identity and community

- A person can register, authenticate, manage a profile, and securely end a session.
- A person can create groups, join by invitation, and hold multiple group memberships with distinct roles. Join requests remain an extension from the earlier brief, not an original FR.
- Group membership has a role and lifecycle; authorized group operators manage membership.
- Institutional data-model support permits optional organizations to contain groups; informal groups need no organization record. Complex institutional management is deferred.
- Intended audiences include informal communities (friends, university circles, families, online accountability groups) and structured institutions (madrasas, Quran learning centers, Hifz institutions, teacher-led programs). Informal communities are the primary MVP use case; institutional workflows should not make the MVP complex.
- Groups may be informal or associated with an organization; source group types include `COMMUNITY`, `CLASS`, and `COHORT`.

### Quran and personal practice

- The application provides 114 Surahs, 30 Juz, Ayah-level references, and 604 Madani Mushaf pages under a documented page convention; each Ayah has a stable identifier, and the dataset is validated at import.
- A learner has one authoritative personal memorization record across memberships; groups receive permission-filtered views and do not own duplicate progress records.
- Current Ayah-level progress is distinct from the historical Sabaq activity log. Changes preserve history; exact correction semantics remain unresolved.
- A learner records revision (Muraja'ah) separately, including revision type, notes, and self-assessment.
- Surah/Ayah are canonical references. Juz and Mushaf page context/progress are derived from canonical Quran mappings rather than duplicated as independent progress truth.
- Original FR-13 requires personal and group targets; schedules are an extended proposal. Notes, advanced recommendations and audio details are not original functional requirements.

## Memorization status model

The source proposes `NOT_STARTED`, `LEARNING`, `MEMORIZED`, and `STRONG`. `STRONG` requires explicit assessment or a defined verification rule; it must not result merely from self-marking a portion memorized. A portion can regress from `STRONG` to `MEMORIZED` or `LEARNING`. Exact transitions and the effect of mentor assessment remain open in [the decision register](roadmap/OPEN_DECISIONS.md).

### Sharing, mentorship, and insight

- Sharing settings are configurable independently for each group.
- A group dashboard and member views expose only data permitted by the learner's settings and the viewer's role. Overall progress, memorization logs, revision logs, personal goals and assessment information are separate sharing categories.
- Optional mentorship supports assignments, assessments, feedback, and learner monitoring.
- Historical reports/analytics, notifications, and announcements are original P1 requirements. Activity feeds and challenges are extended proposals.

### Portability and advanced capabilities

- Progress-report export is original P2/later (FR-17). CSV/PDF formats and personal account-data portability are additions from the earlier initialization brief, not requirements in the original specifications.
- Release 3 or later proposals include offline activity capture/sync, WhatsApp integration, detailed audio sharing/review, and optional AI-assisted recitation evaluation. These are not original FRs; audio, WhatsApp and AI evaluation are explicitly out of MVP.

## Quality requirements

- Enforce authentication and authorization on the server for every protected operation.
- Preserve activity history; corrections should be traceable rather than erasing history without policy.
- Apply group-specific privacy on every group-facing query and response.
- Keep calculations deterministic and testable.
- Use migrations for schema changes and validate inputs at API boundaries.
- Provide accessible, responsive interfaces; detailed UI acceptance criteria remain to be refined.
- Security: users cannot access another group's private information; every protected API validates permission.
- Integrity: memorization references must resolve to valid Quran locations and ranges.
- Auditability: assessment changes and important administrative actions are traceable.
- Scalability: support many groups and growing membership without duplicating personal progress.
- Maintainability: separate business rules from API routes and database access.
- Usability: work comfortably on mobile browsers.
- Reliability: calculations are deterministic and consistent.

## Out of scope for initial baseline

MVP exclusions explicitly named in the original source include AI recitation evaluation, audio recording/playback, WhatsApp integration, real-time chat, complex gamification, advanced recommendation algorithms, native mobile apps, microservices, and subscription/payment systems. Product-wide licensing and formal institutional compliance requirements remain unspecified. Features from the earlier initialization brief that are not functional requirements in either original specification are tagged as extended proposals in the feature catalog, not silently treated as source requirements.
