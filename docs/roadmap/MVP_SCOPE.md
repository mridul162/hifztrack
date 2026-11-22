# MVP scope

The MVP is the first usable release, not the full product. Deferred features remain in the feature catalog and roadmap.

## Included

- Registration, login, logout, secure sessions, profile/account basics.
- Canonical Quran reference with Surah/Ayah, Juz/page navigation, and search.
- Personal Ayah-level Sabaq memorization tracking and deterministic progress.
- One authoritative personal Ayah-progress record reused across all group memberships, with current state separated from preserved Sabaq history.
- Canonical Surah/Ayah references; Juz and Mushaf page references derived from Quran mappings.
- Separate Muraja'ah logs with type, notes, and self-assessment.
- Group creation, memberships, invitations, multiple memberships, and scoped roles. Join requests are an optional extension from the earlier initialization brief, not original FR-04.
- Per-group sharing preferences with backend-enforced privacy.
- Personal and group dashboards/member views filtered by sharing permissions.
- Basic individual statistics.
- Personal dashboard: total memorized, learning/strong portions, recent memorization/revision, memberships. Group dashboard: member count, permitted progress, recent activity, group statistics.
- Mentor assessment remains optional and P1 as a workflow. Keep the data model able to represent assessments and mentor assignments without implementing assessment UI in MVP. Organization-to-group data-model support is required; complex institutional administration is excluded from MVP.

## Excluded from MVP

P1/Release 2 exclusions: individual/group targets, full mentor assignment/assessment workflow, notifications, announcements, historical reports and analytics. Also deferred proposals: schedules, activity feed/challenges, personal notes, recommendations, audio, offline sync, WhatsApp, and AI evaluation. P2/later: progress-report export. Personal account-data export is an extended proposal, not in the originals. Complex institutional administration, real-time chat, complex gamification, native mobile apps, microservices, subscriptions and payments are excluded from MVP.

## MVP completion gate

Every included P0 feature meets catalog acceptance criteria; owner/group isolation and sharing behavior have automated positive and negative tests; Quran ranges validate against canonical order; repeated submissions do not inflate progress; transactions preserve activity/progress integrity; setup is documented. No feature is called verified without passing relevant tests. Production readiness is a later milestone.
