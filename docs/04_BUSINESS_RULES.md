# Business rules

## Ownership and access

1. Personal memorization and revision records belong to the individual user, not to a group.
2. A user may belong to multiple groups; the same personal record may be shown in detailed form to one group and summary form to another.
3. Sharing is configured independently for each group and is enforced by backend queries and APIs.
4. Sharing settings belong to one membership episode and are independent across groups. A new episode defaults to overall progress `SUMMARY`; memorization logs, revision logs, goals, and assessments are disabled. These defaults apply to every new episode, including rejoin episodes (DEC-006; ADR-018).
5. Only the data owner may change their own settings for a membership. ADMIN and MENTOR roles do not override the owner's choices. All ACTIVE members of that group may read information the owner shares with that group, regardless of role; PENDING, SUSPENDED, and LEFT memberships cannot access shared information. Leaving or otherwise losing ACTIVE status revokes future access through that membership. Authorization and field filtering are enforced by backend requests, not frontend visibility (DEC-016; ADR-018).
6. Overall-progress visibility is `PRIVATE`, `SUMMARY`, or `DETAILED` (DEC-023; ADR-018):
   - `PRIVATE` exposes no overall-progress information.
   - `SUMMARY` exposes total memorized Ayahs and completion percentage using the canonical 6,236-Ayah total. It exposes no per-Surah breakdown or individual Ayah status.
   - `DETAILED` exposes Surah/Ayah identifiers and each Ayah's current memorization status. It exposes no memorization logs, revision logs, notes, activity dates, or historical status changes.
7. Memorization logs, revision logs, goals, and assessments each have independent Boolean settings. Enabling one never enables another:
   - **Memorization logs:** Surah/Ayah range, submission date/time, and current record status where relevant. Exclude private notes and correction details.
   - **Revision logs:** Surah/Ayah range, revision type, activity date, duration, and self-rating if provided. Exclude private notes. Revision records remain immutable; sharing grants no edit or delete permission.
   - **Goals:** title or description, target Surah/Ayah range, start date and target completion date if provided, current status, and completion progress. Exclude private notes and unrelated activity. Goals are P1; this setting does not bring goal functionality into SHARE-01.
   - **Assessments:** assessment date, assessed Surah/Ayah range, result or rating, assessor identity where applicable, and feedback explicitly recorded as part of the assessment. Exclude private memorization/revision notes and unrelated personal records. Mentor assessment workflow remains P1.
8. Settings apply to both existing and future eligible records. Enabling a category makes eligible historical records available to ACTIVE members of that group subject to the field restrictions above. Disabling it prevents subsequent HifzTrack API requests from retrieving that category. Changes apply immediately to subsequent backend requests; reducing `DETAILED` to `SUMMARY` limits subsequent responses to summary fields. Information already viewed, downloaded, or copied cannot be retroactively withdrawn.
9. Leaving revokes future access through the old membership episode. Rejoining creates a new episode with the defaults above; prior settings are not restored. Preserve the prior episode and its historical records under the membership lifecycle rules (DEC-007/017; ADR-008, ADR-018).

## Quran and progress

10. Quran references use canonical identifiers and a selected, documented source.
11. Memorization progress is represented at Ayah level. Juz and page progress are derived from canonical mappings rather than maintained as competing truth.
12. Memorization (Sabaq) and revision (Muraja'ah) are separate activities with separate records.
13. Recording revision does not automatically mark an Ayah strong or alter memorization status.
14. Progress calculations must be deterministic and documented, including how repeated or overlapping ranges are handled.
15. The reference dataset covers 114 Surahs, 30 Juz, 6,236 Ayahs, and 604 Madani Mushaf pages under a documented convention. Each Ayah has a stable identifier and the dataset is validated at import.
   Under conditional DEC-002, HifzTrack maintains the application-facing metadata structure and validation rules. The Tanzil metadata XML is not an application dependency. Sources, provenance, verification method, and usage conditions must be documented per metadata category; proposed categories and evidence gates are recorded in ADR-014.
16. Validate ranges against canonical Quran order; ranges may cross Surah boundaries, and numeric IDs alone must not substitute for location validation.
17. Current progress comes from `user_ayah_progress`, not activity counts. MEMORIZED and STRONG coverage may be reported separately using the 6,236 Ayah denominator.
18. The Ayah statuses are NOT_STARTED (memorization has not started), LEARNING (currently being learned), MEMORIZED (learner considers the Ayah memorized), and STRONG (learner explicitly considers it strongly retained). The learner manually controls status per `(user, Ayah)` and may move between any defined statuses, including regression. STRONG requires explicit learner confirmation. Submission counts, mentor assessments, and revision activity do not automatically change status (DEC-004; ADR-015).

## History and assessment

19. Preserve every Sabaq submission as historical activity separately from one current status per user/Ayah. Repeated and overlapping submissions remain separate history and do not inflate unique Ayah progress. Cancellation changes SUBMITTED to CANCELLED without deleting history. Correct an erroneous submission by cancelling it and creating a corrected submission. Cancellation/correction does not change current Ayah status; current status and Sabaq history remain independently queryable (DEC-005; ADR-016).
   A missing saved progress row means NOT_STARTED. Progress writes are learner-controlled per Ayah; STRONG requires explicit confirmation, and transitions (including regressions) do not depend on Sabaq activity.
20. Revision sessions remain separate, user-owned history and do not change memorization status automatically. Once recorded, a revision session is immutable: users cannot edit, correct, cancel, or delete it. DEC-005/ADR-016 cancellation and correction rules apply to Sabaq submissions only; revision sessions use the separate immutable-history rule in ADR-017.
21. Mentor assessments are independent from learner self-reported status; a learner may be assessed by mentors in different groups. Access is restricted to authorized members of the associated group.
22. Source assessment results are PASSED or NEEDS_IMPROVEMENT. Assessment is a separate record and does not automatically change learner Ayah status. Any future status-transition workflow needs an explicit approved rule; if approved, assessment and status change commit in one transaction.
23. Group goals are collective targets and do not duplicate personal goals. Their type and completion calculation remain open under DEC-024.
24. Distinguish group metrics: total unique Ayahs memorized, average individual completion, milestone count, and participation rate.
25. Group roles and membership changes are authorized and auditable; only ACTIVE memberships grant group access.
26. Derived analytics and reports must honor the same permissions as source records.
27. Source invitation tokens are random, stored hashed, expiring, revocable, and may have a maximum-use count.
28. Source membership roles are ADMIN, MENTOR, MEMBER; states are PENDING, ACTIVE, SUSPENDED, LEFT. Only ACTIVE grants access. Phase 2 resolves rejoin history and current-row uniqueness as documented below.

## MVP dashboard metrics (DEC-018 / ADR-019)

- Personal statistics count current `MEMORIZED` plus `STRONG` Ayahs as memorized coverage and divide by 6,236 for the percentage. Display all four status counts separately. Subtract the saved `LEARNING`, `MEMORIZED`, and `STRONG` counts from 6,236 to get `NOT_STARTED`, which includes both missing and explicit rows. Sabaq and revision histories are independent of this calculation.
- An ACTIVE group member can see coverage and percentage for ACTIVE targets sharing `SUMMARY` or `DETAILED`. Detailed member views may show their separately permitted per-Ayah statuses. The dashboard displays no additional status breakdown. `PRIVATE` contributes neither a per-member summary nor a value in the group mean.
- Group mean completion is `100 × sum(eligible memorized counts) / (6,236 × contributor count)`. The same denominator for every member makes this the arithmetic mean of the unrounded individual percentages. Round displayed percentages to two decimal places. A genuine zero is eligible, while no contributors yields an unavailable average.
- Activity categories use independent membership sharing flags and the SHARE-01 field allowlists. Archived groups stay readable for ACTIVE members and retain their existing write restrictions. Changes to status, sharing, and membership are reflected on subsequent requests.

## Approved Phase 2 group rules

- A group starts ACTIVE. ARCHIVED groups are read-only: no invitations or membership changes, all outstanding invitations are revoked, existing members may leave, and history is retained. Permanent deletion is not implemented.
- A nullable organization link is metadata only and does not grant group access. Organization roles, membership, and authorization are out of scope.
- A membership episode has exactly one ADMIN, MENTOR, or MEMBER role. Multiple users may hold ADMIN or MENTOR in one group; a user can hold different roles across groups.
- Current membership uniqueness is enforced by a PostgreSQL partial unique index for `(group_id,user_id)` where state is PENDING, ACTIVE, or SUSPENDED. LEFT episodes remain historical; rejoining creates a new episode.
- Group creator receives ACTIVE ADMIN membership atomically with group creation. Only ACTIVE ADMIN manages group metadata, invitations, and other memberships. At least one ACTIVE ADMIN must remain; group-row locking serializes changes.
- Invitation acceptance creates ACTIVE MEMBER membership. Invitations expire after seven days by default, default to one successful use, can be explicitly capped up to 100 uses, are revocable, and store only an HMAC digest. Plaintext appears only in the creation response. Leaving or losing active ADMIN membership revokes invitations created by that user; archiving revokes all outstanding invitations.
- Invitation throttles use PostgreSQL HMAC counters: creation 10/user/hour, 30/group/hour, 20/IP/hour; acceptance attempts 30/IP/15 minutes and 10/token digest/15 minutes. Rate limiting returns generic 429 with Retry-After and does not invalidate invitations or lock accounts.
- Group roster exposes display name, role, state, and membership timestamps only; it does not expose email or authentication/session data.

The canonical source invitation and membership rules above replace the earlier unresolved notes for these decisions.

## Remaining unresolved policy details

DEC-002 remains conditionally approved. Verify local Arabic-file provenance and applicable license/attribution before public release; the implemented local numeric-reference slice records the preserved source notice and conditions but does not settle redistribution rights. Establish documented sources and usage conditions before integrating each further HifzTrack-owned metadata category, and identify the exact authoritative Madani edition plus independently verify all 604 page boundaries before adding page mappings. The Tanzil metadata XML is not an application dependency. Other unresolved details include deletion/export behavior, mentor consent and assessment vocabulary, timezone boundaries, and broader audit retention. Sharing policy defaults, field matrix, and owner-only control are resolved by DEC-006/016/023 and ADR-018.
