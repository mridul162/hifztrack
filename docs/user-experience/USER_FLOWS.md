# User flows

These are initial flows for product discussion; exact screens and edge cases are specified in `UI_REQUIREMENTS.md`.

## Learner setup and practice (MVP)

1. Register or sign in, then review profile and privacy settings.
2. Select a Surah/Ayah or look up a reference using canonical navigation. Full-text/advanced search is an extended proposal, not MVP scope.
3. Record a Sabaq range and its memorization status; review personal progress.
4. Record Muraja'ah separately with revision type, notes, and self-assessment.
5. Review personal dashboard and basic statistics.

The source MVP dashboard includes total Quran memorized, learning and strong portions, recent memorization/revision activity, and group memberships. Personal goals appear in the suggested dashboard, but goal creation is P1/Release 2; showing goals is conditional on that feature being released.

## Group participation (MVP)

1. Create a group or accept an invitation to join. Join requests are a proposed extension, not original P0 scope.
2. Review group role and configure sharing for that specific group.
3. Browse group dashboard/member views; see only information each member allows.
4. Update sharing or leave; subsequent group requests respect the change immediately.

The source group dashboard includes member count, shared member progress, recent activities, and group statistics. Announcements were P1/Release 2, so the dashboard must not imply they are available in MVP.

## Future flows

Release 2 adds personal/group targets, mentor assignment/assessment, notifications, announcements, and expanded analytics. Schedules, challenges and notes are extended proposals. Release 3 explores report export, recommendations, audio review, offline sync, WhatsApp and AI evaluation. Each deferred flow needs explicit consent, error, and privacy states before implementation.
