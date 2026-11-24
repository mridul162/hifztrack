# User flows

These are initial flows for product discussion; exact screens and edge cases are specified in `UI_REQUIREMENTS.md`.

## Learner setup and practice (MVP)

1. Register or sign in, then review profile and privacy settings.
2. Select a Surah/Ayah or look up a reference using canonical navigation. Full-text/advanced search is an extended proposal, not MVP scope.
3. Record a Sabaq range and review personal progress. Set each Ayah's current status separately; Sabaq activity does not change it.
4. Record Muraja'ah separately with revision type, notes, and self-assessment.
5. Review personal dashboard and basic statistics.

The current reference browser selects a numeric Surah, then an Ayah number, and shows the selected `surah:ayah` coordinate. It does not display Quran text, translations, Juz or page mappings.

The current `/memorization` workflow requires sign-in, lists numeric Ayahs for the selected Surah with saved status (missing rows display as NOT_STARTED), allows learner status changes with explicit confirmation for STRONG, and records/list/cancels/corrects Sabaq ranges. Activity history is owner-only and paginated. Juz/page navigation is not included in this slice.

The source MVP dashboard includes total Quran memorized, learning and strong portions, recent memorization/revision activity, and group memberships. Personal goals appear in the suggested dashboard, but goal creation is P1/Release 2; showing goals is conditional on that feature being released.

## Group participation (MVP)

1. Create an ACTIVE group; the creator receives an ACTIVE ADMIN membership in the same transaction, or accept a valid invitation as an ACTIVE MEMBER. Join requests are a proposed extension, not original P0 scope.
2. Review group role and roster. Only ACTIVE memberships grant access; MEMBER and MENTOR read group information and may leave. ADMIN manages group metadata, invitations and other members' role/state.
3. Admins create seven-day invitations (one successful use by default), distribute the one-time token link, and may revoke outstanding invitations. The roster shows display name, role, state and membership timestamps, never email.
4. A member leaves; the LEFT membership episode remains in history and later rejoining creates a new episode. Admins may archive a group; archive revokes invitations and makes the group read-only, while existing members may still leave.

The source group dashboard includes member count, shared member progress, recent activities, and group statistics. Announcements were P1/Release 2, so the dashboard must not imply they are available in MVP.

## Future flows

Release 2 adds personal/group targets, mentor assignment/assessment, notifications, announcements, and expanded analytics. Schedules, challenges and notes are extended proposals. Release 3 explores report export, recommendations, audio review, offline sync, WhatsApp and AI evaluation. Each deferred flow needs explicit consent, error, and privacy states before implementation.
