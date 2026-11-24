# Business rules

## Ownership and access

1. Personal memorization and revision records belong to the individual user, not to a group.
2. A user may belong to multiple groups; the same personal record may be shown in detailed form to one group and summary form to another.
3. Sharing is configured independently for each group and is enforced by backend queries and APIs.
4. Default sharing is privacy-conscious. Exact defaults require product approval. Source categories are overall progress, memorization logs, revision logs, goals, and assessments; sharing an assessment does not automatically grant access to private memorization notes. The five booleans do not yet define summary versus detailed overall-progress visibility; see DEC-023.
5. Leaving a group revokes future access to the user's group-scoped data.

## Quran and progress

6. Quran references use canonical identifiers and a selected, documented source.
7. Memorization progress is represented at Ayah level. Juz and page progress are derived from canonical mappings rather than maintained as competing truth.
8. Memorization (Sabaq) and revision (Muraja'ah) are separate activities with separate records.
9. Recording revision does not automatically mark an Ayah strong or alter memorization status.
10. Progress calculations must be deterministic and documented, including how repeated or overlapping ranges are handled.
11. The reference dataset covers 114 Surahs, 30 Juz, 6,236 Ayahs, and 604 Madani Mushaf pages under a documented convention. Each Ayah has a stable identifier and the dataset is validated at import.
   Under conditional DEC-002, HifzTrack maintains the application-facing metadata structure and validation rules. The Tanzil metadata XML is not an application dependency. Sources, provenance, verification method, and usage conditions must be documented per metadata category; proposed categories and evidence gates are recorded in ADR-014.
12. Validate ranges against canonical Quran order; ranges may cross Surah boundaries, and numeric IDs alone must not substitute for location validation.
13. Current progress comes from `user_ayah_progress`, not activity counts. MEMORIZED and STRONG coverage may be reported separately using the 6,236 Ayah denominator.
14. The Ayah statuses are NOT_STARTED (memorization has not started), LEARNING (currently being learned), MEMORIZED (learner considers the Ayah memorized), and STRONG (learner explicitly considers it strongly retained). The learner manually controls status per `(user, Ayah)` and may move between any defined statuses, including regression. STRONG requires explicit learner confirmation. Submission counts, mentor assessments, and revision activity do not automatically change status (DEC-004; ADR-015).

## History and assessment

15. Preserve every Sabaq submission as historical activity separately from one current status per user/Ayah. Repeated and overlapping submissions remain separate history and do not inflate unique Ayah progress. Cancellation changes SUBMITTED to CANCELLED without deleting history. Correct an erroneous submission by cancelling it and creating a corrected submission. Cancellation/correction does not change current Ayah status; current status and Sabaq history remain independently queryable (DEC-005; ADR-016).
   A missing saved progress row means NOT_STARTED. Progress writes are learner-controlled per Ayah; STRONG requires explicit confirmation, and transitions (including regressions) do not depend on Sabaq activity.
16. Revision sessions remain separate, user-owned history and do not change memorization status automatically. Once recorded, a revision session is immutable: users cannot edit, correct, cancel, or delete it. DEC-005/ADR-016 cancellation and correction rules apply to Sabaq submissions only; revision sessions use the separate immutable-history rule in ADR-017.
17. Mentor assessments are independent from learner self-reported status; a learner may be assessed by mentors in different groups. Access is restricted to authorized members of the associated group.
18. Source assessment results are PASSED or NEEDS_IMPROVEMENT. Assessment is a separate record and does not automatically change learner Ayah status. Any future status-transition workflow needs an explicit approved rule; if approved, assessment and status change commit in one transaction.
19. Group goals are collective targets and do not duplicate personal goals. Their type and completion calculation remain open under DEC-024.
20. Distinguish group metrics: total unique Ayahs memorized, average individual completion, milestone count, and participation rate.
21. Group roles and membership changes are authorized and auditable; only ACTIVE memberships grant group access.
22. Derived analytics and reports must honor the same permissions as source records.
23. Source invitation tokens are random, stored hashed, expiring, revocable, and may have a maximum-use count.
24. Source membership roles are ADMIN, MENTOR, MEMBER; states are PENDING, ACTIVE, SUSPENDED, LEFT. Only ACTIVE grants access. Phase 2 resolves rejoin history and current-row uniqueness as documented below.

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

DEC-002 remains conditionally approved. Verify local Arabic-file provenance and applicable license/attribution before public release; the implemented local numeric-reference slice records the preserved source notice and conditions but does not settle redistribution rights. Establish documented sources and usage conditions before integrating each further HifzTrack-owned metadata category, and identify the exact authoritative Madani edition plus independently verify all 604 page boundaries before adding page mappings. The Tanzil metadata XML is not an application dependency. Other unresolved details include the sharing field matrix/defaults, deletion/export behavior, mentor consent and assessment vocabulary, timezone boundaries, and broader audit retention.
