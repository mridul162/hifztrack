# UI requirements

## Baseline

- Responsive web experience for desktop and mobile widths.
- Clear distinction between memorization and revision actions and histories.
- Quran navigation exposes stable Surah/Ayah references and derived Juz/page context.
- Show users which group they are configuring when they edit sharing preferences.
- Explain whether a view is private, group-shared, or mentor-visible.
- Provide loading, empty, validation, success, and failure states for all forms and lists.
- Use accessible labels, keyboard navigation, visible focus, and sufficient contrast.

## MVP screen inventory

Authentication; profile/settings; personal dashboard; Quran Surah/Ayah reference navigation and lookup; Juz/page navigation; memorization tracker/history; revision tracker/history; group list/create/detail; invitations; group membership management; per-group sharing settings; group dashboard and permitted member summary. Full Quran text/advanced search is an extended proposal, not P0.

Source screen details:

- Personal dashboard: total memorized Quran progress, learning/strong portions, recent Sabaq and revision activity, group memberships. Goal summary is conditional on Release 2 goals.
- Memorization tracker: Surah selection, start/end Ayah, current status, activity history, Juz/page navigation.
- Group dashboard: member count, permitted member progress, recent activities, group statistics. Announcements are Release 2.
- Member profile: only progress/activity/information allowed by that member's sharing settings.
- Revision tracker: range, type, time, self-assessment.
- Settings/administration: memberships, roles, sharing preferences, invitations, group configuration.

Use a persistent desktop sidebar and compact mobile navigation; keep daily memorization entry low-friction. The product requirement is responsive mobile-browser support.

## Future UI

Goals, mentor dashboard and feedback, notifications, announcements, and advanced analytics/reports are deferred according to release scope. Schedules, activity/challenges, personal Ayah notes, audio capture/review, offline conflict resolution, and AI evaluation are extended proposals.

Detailed visual system, supported languages/script/transliteration, RTL requirements, chart definitions, and accessibility conformance target remain open.
