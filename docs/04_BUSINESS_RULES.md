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
12. Validate ranges against canonical Quran order; ranges may cross Surah boundaries, and numeric IDs alone must not substitute for location validation.
13. Current progress comes from `user_ayah_progress`, not activity counts. MEMORIZED and STRONG coverage may be reported separately using the 6,236 Ayah denominator.
14. The established Ayah statuses are NOT_STARTED, LEARNING, MEMORIZED, and STRONG. Allowed transitions, regression criteria, and STRONG verification rules remain unresolved under DEC-004.

## History and assessment

15. Preserve Sabaq submissions as historical activity separately from one current status per user/Ayah. Repeated submissions do not inflate progress. The candidate activity state is SUBMITTED/CANCELLED, but cancellation semantics remain unresolved.
16. Revision sessions remain separate history and do not change memorization status automatically.
17. Mentor assessments are independent from learner self-reported status; a learner may be assessed by mentors in different groups. Access is restricted to authorized members of the associated group.
18. Source assessment results are PASSED or NEEDS_IMPROVEMENT. Assessment is a separate record and does not automatically change learner Ayah status. Any future status-transition workflow needs an explicit approved rule; if approved, assessment and status change commit in one transaction.
19. Group goals are collective targets and do not duplicate personal goals. Their type and completion calculation remain open under DEC-024.
20. Distinguish group metrics: total unique Ayahs memorized, average individual completion, milestone count, and participation rate.
21. Group roles and membership changes are authorized and auditable; only ACTIVE memberships grant group access.
22. Derived analytics and reports must honor the same permissions as source records.
23. Source invitation tokens are random, stored hashed, expiring, revocable, and may have a maximum-use count.
24. Source membership roles are ADMIN, MENTOR, MEMBER; states are PENDING, ACTIVE, SUSPENDED, LEFT. Only ACTIVE grants access. The source's unique `(group_id,user_id)` constraint leaves rejoin history to DEC-017.

## Unresolved policy details

The canonical Quran dataset/license, Ayah status transitions and verification criteria (DEC-004), overlap/correction semantics, sharing field matrix/defaults, retention after leaving a group, deletion/export behavior, mentor consent and assessment vocabulary, timezone boundaries, and audit retention need decisions before affected features are implemented.
