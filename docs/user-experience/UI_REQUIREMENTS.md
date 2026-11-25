# UI requirements

## Baseline

- Responsive web experience for desktop and mobile widths.
- Clear distinction between memorization and revision actions and histories.
- Quran navigation exposes stable Surah/Ayah references and derived Juz/page context.
- Show users which group they are configuring when they edit sharing preferences.
- Explain whether a view is private, group-shared, or mentor-visible.
- Provide loading, empty, validation, success, and failure states for all forms and lists.
- Use accessible labels, keyboard navigation, visible focus, and sufficient contrast.

Current QURAN-01 browser slice lists Surah numbers/counts, Ayah numbers and the selected coordinate. It displays no Quran text or translations; Juz/page context is omitted until its source and verification gates are satisfied.

Current MEM-01 page (`/memorization`) is personal and requires an authenticated session. It shows numeric Ayah references and current status, supports explicit status changes (with confirmation before STRONG), records canonical Sabaq start/end references, and shows paginated activity history with cancellation and correction actions. Missing progress rows display as NOT_STARTED. Sabaq actions never mutate current Ayah status. Juz/page navigation is deferred until the Quran mappings meet their verification gates.

REV-01 page (`/revision`) requires an authenticated session. It records the canonical numeric range, revision type, activity date, time, optional 1–5 self-rating and notes, and shows paginated owner-only history with loading, empty, validation, success, and failure states. Saved revision records are immutable and have no edit, correction, cancellation, or delete actions. Revision never changes current Ayah status.

SHARE-01 provides an owner-facing settings page at `/groups/{group_id}/sharing` with overall visibility and four independent category controls. The page heading identifies the group being configured. It explains what each category exposes, loads and saves the authenticated owner's settings, and shows loading, error, and save-success states. Group details link to shared information for ACTIVE members. Shared views display only fields allowed by the backend response; disabled categories and private notes are not rendered. Goal and assessment toggles are stored preferences only while their P1 workflows remain unavailable.

## MVP screen inventory

Authentication; profile/settings; personal dashboard; Quran Surah/Ayah reference navigation and lookup; Juz/page navigation; memorization tracker/history; revision tracker/history; group list/create/detail; invitations; group membership management; per-group sharing settings; group dashboard and permitted member summary. Full Quran text/advanced search is an extended proposal, not P0.

Source screen details:

- `/dashboard` shows the signed-in learner's memorized count, completion percentage, and four status counts in a compact dark card. A segmented bar shows the relative size of each status. Expandable rows show recent Sabaq, recent revision, and active group links, with shortcuts to the full lists. The page shows a sign-in link when access requires authentication and describes empty histories or memberships.
- Memorization tracker: Surah selection, start/end Ayah, current status, activity history, Juz/page navigation.
- The group detail page at `/groups/{id}` shows the group dashboard with an active count, paginated active roster and roles, links to existing shared-member views, eligible member progress, and separate recent shared activity lists. It labels an unavailable average or member progress distinctly from zero completion and shows the number of contributors. Group administration remains on the same page.
- The personal and group dashboard sections provide loading, empty, error, and denied-access states. Shared-member detail continues to show only information permitted by the selected member's sharing settings.
- Revision tracker: range, type, time, self-assessment.
- Settings/administration: memberships, roles, sharing preferences, invitations, group configuration.

Use a persistent desktop sidebar and compact mobile navigation; keep daily memorization entry low-friction. The product requirement is responsive mobile-browser support.

## Future UI

Goals, mentor dashboard and feedback, notifications, announcements, and advanced analytics/reports are deferred according to release scope. Schedules, activity/challenges, personal Ayah notes, audio capture/review, offline conflict resolution, and AI evaluation are extended proposals.

Detailed visual system, supported languages/script/transliteration, RTL requirements, chart definitions, and accessibility conformance target remain open.
