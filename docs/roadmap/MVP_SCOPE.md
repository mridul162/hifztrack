# MVP scope

The MVP is the first usable release, not the full product. Deferred features remain in the feature catalog and roadmap.

## Included

- Registration, login, logout, secure sessions, profile/account basics.
- Canonical Quran reference with Surah/Ayah lookup and Juz/Mushaf-page navigation. Full text or advanced search is an extended proposal, not MVP scope.
- Personal Ayah-level Sabaq memorization tracking and deterministic progress.
- One authoritative personal Ayah-progress record reused across all group memberships, with current state separated from preserved Sabaq history.
- Canonical Surah/Ayah references; Juz and Mushaf page references derived from Quran mappings.
- Separate Muraja'ah logs with type, notes, and self-assessment.
- Group creation, memberships, invitations, multiple memberships, and scoped roles. Join requests are an optional extension from the earlier initialization brief, not original FR-04.
- Per-group sharing preferences with backend-enforced privacy.
- Personal and group dashboards/member views filtered by sharing permissions.
- Basic individual and current-state group summaries; historical reports, participation analytics and advanced group metrics are P1.
- Personal dashboard: total memorized, learning/strong portions, recent memorization/revision, memberships. Group dashboard: member count, permitted current-state progress, recent activity, and basic current-state summaries; the exact P0 group-statistic set remains DEC-018.
- Mentor assessment remains optional and P1 as a workflow. Keep the data model able to represent assessments and mentor assignments without implementing assessment UI in MVP. Organization-to-group data-model support is required; complex institutional administration is excluded from MVP.

Phase 2 organization support is a minimal `organizations` table and nullable `groups.organization_id`. This association is metadata only: organization membership, roles, administration, and access grants are out of scope. Group access always requires an ACTIVE membership in that group.

Phase 2 organization support is a minimal `organizations` table and nullable `groups.organization_id`. This association is metadata only: organization membership, roles, administration, and access grants are out of scope. Group access always requires an ACTIVE membership in that group.

## Excluded from MVP

P1/Release 2 exclusions: individual/group targets, full mentor assignment/assessment workflow, notifications, announcements, historical reports and analytics. Also deferred proposals: schedules, activity feed/challenges, personal notes, recommendations, audio, offline sync, WhatsApp, and AI evaluation. P2/later: progress-report export. Personal account-data export is an extended proposal, not in the originals. Complex institutional administration, real-time chat, complex gamification, native mobile apps, microservices, subscriptions and payments are excluded from MVP.

## MVP completion gate

Every included P0 feature meets catalog acceptance criteria; owner/group isolation and sharing behavior have automated positive and negative tests; Quran ranges validate against canonical order; repeated submissions do not inflate progress; transactions preserve activity/progress integrity; setup is documented. No feature is called verified without passing relevant tests. Production readiness is a later milestone.
