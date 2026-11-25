# Decision log

Record approved decisions with ID, date, context, decision, consequences, and status. Proposed decisions must be labeled as proposals until approved.

## ADR-001: Modular monolith

**Status:** Accepted baseline. **Decision:** Use a modular monolith. **Reason:** The MVP does not require distributed services.

## ADR-002: Personal progress ownership

**Status:** Accepted. **Decision:** Each user owns one central personal memorization record. Current Ayah status is represented once per `(user, Ayah)`; Sabaq history is stored separately. Groups receive permission-filtered views of the same record and never own duplicate progress copies. **Reason:** A user can belong to multiple groups and share different views with each. Status transitions are defined in ADR-015; Sabaq cancellation/correction semantics are defined in ADR-016.

## ADR-003: Group-specific sharing

**Status:** Accepted baseline. **Decision:** Sharing is configured independently for each group membership and enforced server-side. **Reason:** A user may share different levels with different groups.

## ADR-004: Ayah-level memorization source

**Status:** Accepted baseline. **Decision:** Maintain memorization progress at Ayah level; derive Juz/page progress from canonical Quran data. **Reason:** Avoid competing progress truth and preserve precise tracking.

## ADR-005: Memorization and revision are separate

**Status:** Accepted baseline. **Decision:** Record Sabaq and Muraja'ah as separate activities; revision does not automatically alter memorization strength/status.

## ADR-006: No premature deferred work

**Status:** Accepted baseline. **Decision:** Preserve all planned features in the catalog, but implement only the approved release/milestone scope.

## ADR-007: Authentication and session baseline

**Status:** Accepted by the product owner for AUTH-01. **Decision:** Use email as the account identifier, Argon2id password hashing, server-side sessions persisted in PostgreSQL, Secure/HttpOnly/SameSite cookies, and server-side logout revocation. Use a signed double-submit CSRF token with exact configured-Origin validation for unsafe requests. Apply fixed 15-minute PostgreSQL counters using HMAC digests: 5 registrations per IP, 10 logins per IP/email pair, and 30 logins per IP; return generic 429 responses and do not lock accounts. Defer password recovery and MFA. Invitation rate limits remain to be designed with GROUP scope. **Consequences:** auth controls work across API workers; counters expire after a one-day retention period. Session lifetime defaults to 12 hours and is configuration, not a separately approved product policy.

## ADR-008: Membership episodes and leaving (DEC-007, DEC-017)

**Date:** 2026-11-23. **Status:** Approved for Phase 2. **Decision:** Leaving changes the current membership episode to LEFT and ends group access immediately; the episode and timestamps remain historical. A later invitation creates a new episode. PostgreSQL enforces one current PENDING/ACTIVE/SUSPENDED episode per `(group_id,user_id)` with a partial unique index that excludes LEFT. Personal progress is neither copied nor transferred on leave. **Consequences:** membership history remains queryable and database constraints enforce rejoin uniqueness.

## ADR-009: One group role per membership (DEC-008)

**Date:** 2026-11-23. **Status:** Approved for Phase 2. **Decision:** Each episode has exactly one ADMIN, MENTOR, or MEMBER role. A group may have multiple admins and mentors; a user's role is scoped to each group. No global or organization roles are introduced.

## ADR-010: Invitation policy (DEC-009)

**Date:** 2026-11-23. **Status:** Approved for Phase 2. **Decision:** Invitations default to seven-day expiry and one successful use; creation may explicitly set a positive cap up to 100. Return a random plaintext token once at creation and store only its HMAC digest. Revoke on admin departure/demotion/suspension and group archive. Use separate PostgreSQL HMAC rate counters: creation 10/user/hour, 30/group/hour, 20/IP/hour; acceptance 30/IP/15m, 10/token digest/15m. Respond with generic 429 and Retry-After; do not lock accounts or permanently invalidate an invitation for rate limiting. **Consequences:** rate-limit storage is isolated from AUTH-01 counters, with per-scope fixed windows.

## ADR-011: Group archive lifecycle (DEC-020)

**Date:** 2026-11-23. **Status:** Approved for Phase 2. **Decision:** Groups use ACTIVE/ARCHIVED. Archive is read-only, blocks invitations and membership changes, revokes outstanding invites, preserves group/membership history, and still permits current members to leave. Permanent deletion is not included.

## ADR-012: Minimal organization association (DEC-021)

**Date:** 2026-11-23. **Status:** Approved for Phase 2. **Decision:** Provide a minimal organizations table and nullable group foreign key. Organization association is metadata and grants no access. Organization membership, roles, administration, and hard tenant isolation are not implemented; group authorization remains based on ACTIVE group membership.

## ADR-013: Root-level API route convention

**Date:** 2026-11-23. **Status:** Approved implementation convention for Phase 2. **Decision:** Continue the existing AUTH-01 root-level route convention. `/api/v1` versioning remains a future architecture decision; no route retrofit is part of GROUP-01/GROUP-02.

## ADR-014: Canonical Quran dataset and Mushaf convention (DEC-002)

**Date:** 2026-11-23. **Status:** Conditionally approved; verification gates remain open.

**Context:** QURAN-01 requires a canonical Quran reference, stable Surah/Ayah coordinates, and derived Juz/page navigation. The repository contains Tanzil Quran Text Uthmani v1.1 and a Tanzil metadata XML file. The local Arabic text's provenance and applicable conditions, the basis for each independently sourced metadata category, and independent verification of page boundaries remain incomplete. The Tanzil metadata XML is not intended to be an application dependency.

**Approved direction (conditional):** Retain Tanzil Quran Text Uthmani v1.1 in Uthmani script verbatim, with applicable copyright and attribution notices preserved, and intend to use the Madani Mushaf 604-page convention. Canonical Ayah identity is `(surah_number, ayah_number)`; Surah and Ayah numbers remain separate and Juz/page references are derived. Exclude translations from the initial release. Defer additional Mushaf editions. This refinement records the proposed approach and does not close DEC-002 or create a new final approval.

**HifzTrack-owned metadata approach:** HifzTrack will own its application-facing metadata structure and validation rules and maintain a structured metadata dataset. `data/quran/source/metadata/quran-data.xml` will not be an application dependency. Proposed metadata categories are Surah information/order, Ayah counts/canonical ordering, Juz boundaries, Hizb and quarter-Hizb boundaries, Ruku boundaries, Sajdah locations/types, and Madani Mushaf page boundaries. These are proposed categories, not verified values. For every category, document its source, provenance, verification method, and applicable usage conditions. An independently maintained structure does not by itself remove restrictions on externally sourced values; do not copy values from the Tanzil metadata file without a separately established basis.

**Consequences:** The local numeric Surah/Ayah implementation may proceed with the source-recording limits above. Public release and integration of additional metadata remain subject to the outstanding conditions below. Translation files remain outside initial-release import, API, and distribution scope; translation licensing is outside the initial-release scope.

**Outstanding conditions:** (1) Before public release, verify provenance of the local Arabic file and applicable license, copyright, and attribution requirements, including resolving the notice discrepancy from authoritative evidence. The local development slice reads only numeric coordinates/counts from the unchanged file and records its notice, hash, and validation method; this limited use does not close the condition or establish redistribution rights. (2) Before integrating each further HifzTrack-owned metadata category, establish and document its source, provenance, verification method, and applicable usage conditions. This replaces the former proposed requirement to establish a licensing basis for using Tanzil's metadata XML as an application dependency; it does not eliminate licensing questions for independently sourced metadata values. (3) Before integrating Madani page mappings, identify the exact authoritative edition and independently verify all 604 page boundaries with a reproducible method, recording source, edition identity, discrepancies, and result. The existing XML's 604 ordered page markers alone do not establish verification.

## ADR-015: Ayah status transitions (DEC-004)

**Date:** 2026-11-23. **Status:** Resolved / approved.

**Context:** Current progress needs an explicit status model and transition rule that does not infer learner state from activity or assessment.

**Approved decision:** Per `(user, Ayah)`, statuses are NOT_STARTED (memorization has not started), LEARNING (currently being learned), MEMORIZED (learner considers it memorized), and STRONG (learner explicitly considers it strongly retained). The learner manually controls transitions among these statuses; regression is permitted. STRONG requires explicit learner confirmation. Sabaq submissions, mentor assessments, and revision activity do not automatically change current status.

**Consequences:** Current status is independent of activity counts and mentor/revision events. No automatic STRONG promotion or assessment-driven transition is allowed.

## ADR-016: Sabaq submission history and corrections (DEC-005)

**Date:** 2026-11-23. **Status:** Resolved / approved.

**Context:** Sabaq activity must remain auditable without becoming a competing source of current Ayah progress.

**Approved decision:** Each Sabaq submission creates a historical record. Repeated and overlapping submissions remain separate records and never create duplicate current progress rows or inflate unique Ayah counts. Cancellation preserves the record and changes its activity state from SUBMITTED to CANCELLED. A correction cancels the incorrect submission and creates a new submission with corrected information. Cancellation and correction do not change current Ayah status; only an explicit learner status update under ADR-015 changes it. Current status and Sabaq history remain independently queryable.

**Consequences:** Never derive current status from the latest Sabaq submission or automatically reverse progress after cancellation. Personal progress remains centrally user-owned as established by ADR-002.

## ADR-017: Immutable revision session history (REV-01)

**Date:** 2026-11-24. **Status:** Resolved / approved.

**Context:** REV-01 stores a learner's separate Muraja'ah history. DEC-005 and ADR-016 define cancellation and correction for Sabaq submissions only; revision should not inherit those transitions by assumption.

**Approved decision:** Each revision session is a user-owned historical record and becomes immutable after creation. Users cannot edit, correct, cancel, or delete revision sessions. Do not add cancellation status, replacement references, or correction-specific fields to the revision model. Revision activity never changes current Ayah status. DEC-005 remains limited to Sabaq submission records.

**Consequences:** REV-01 provides authenticated create/list operations only. Repeated or overlapping revision ranges are preserved as separate records. Revision-session analytics remain deferred under DEC-022.

## ADR-018: Group sharing policy (DEC-006, DEC-016, DEC-023)

**Date:** 2026-11-24. **Status:** Resolved / approved by the product owner for SHARE-01 documentation.

**Context:** Each user owns one personal memorization/revision history but may share different permitted views with different groups. Group roles and membership episodes must not widen that user's privacy choices.

**Approved decision:** Each new membership episode has its own sharing settings. Defaults are overall progress `SUMMARY`, with memorization logs, revision logs, goals, and assessments disabled. Only the data owner may change the settings for their own membership; ADMIN and MENTOR roles do not grant an override. Overall progress is represented as `PRIVATE`, `SUMMARY`, or `DETAILED`; the other four categories have independent Boolean controls. Each category is independent and enabling one does not enable another. Permitted fields, audience, and effective behavior are specified in the business rules and API specification.

**Consequences:** Backend authorization and response filtering must enforce the settings on every subsequent request. Shared data remains user-owned and is queried through the relevant membership; no group-owned copies are created. Leaving ends future access through that episode. Rejoining creates a new episode with defaults rather than restoring prior settings; historical membership records remain preserved. This decision records policy only and does not mark SHARE-01 implemented.

## ADR-019: MVP dashboard metrics (DEC-018)

**Date:** 2026-11-25. **Status:** Owner-approved for P0 DASH-01 and ANALYTICS-01.

**Decision.** The personal dashboard reports memorized coverage, completion percentage, counts for all four current Ayah statuses, separate recent Sabaq and revision histories, and active group memberships. `MEMORIZED` and `STRONG` each count toward coverage. Missing progress rows count as `NOT_STARTED` and the four counts sum to 6,236. Personal data is session-owner scoped.

The group dashboard reports the active member count and roster with roles, permitted per-member coverage summaries, separate recent shared activity lists, and average completion with its contributor count. Each ACTIVE membership sharing `SUMMARY` or `DETAILED` contributes equally, including members with zero completion. Apply rounding once to the mean of unrounded percentages. The average is unavailable when no members qualify. `PRIVATE` and inactive episodes contribute no progress, and activity permissions remain independent under ADR-018.

**Consequences.** Dashboards are read-only, derive totals from current Ayah status, preserve archive and membership rules, and use bounded recent histories without reporting windows. Historical reports, date-based reports, participation, advanced group metrics, and revision analytics remain deferred. Goals, assessments, and announcements follow their separate release scope. DEC-010 and DEC-022 retain their existing scope.

## ADR-020: QURAN-01 metadata conventions (DEC-002)

**Date:** 2026-11-25. **Status:** Owner-approved conventions. DEC-002 remains CONDITIONALLY APPROVED.

ADR-021 supersedes the supplier choices for Surah names and Juz mappings. The original decision is recorded below.

- Use Tanzil plain Arabic Surah names.
- Use Quran.com-style simplified Latin Surah names. QUL `name_simple` is the candidate.
- Use the Tanzil Juz convention, including Juz 4 from `3:93` and Juz 11 from `9:93`.
- Use the King Fahd Glorious Qur'an Printing Complex Madani Mushaf, 1441H, Hafs, 604 numbered pages. The application edition ID is `madani-1441h-hafs`.
- Keep Surah/Ayah canonical and maintain HifzTrack's normalized metadata. Display names cannot change identifiers or personal records. Alternative name conventions and additional Mushaf editions are deferred.

Each category needs versioned provenance, applicable usage and redistribution terms, attribution, structural checks, and independent accuracy evidence before import. The Quran.ws numeric page index passed those gates for the selected 1441H edition. Arabic names, Latin names, and Juz mappings still need metadata-specific evidence. ADR-014 continues to govern the separate local Arabic verse-text release gate and initial exclusion of translations. [Category clearance](../../data/quran/validation/METADATA_CLEARANCE.md)

## ADR-021: HifzTrack-maintained Quran reference metadata (DEC-002)

**Date:** 2026-11-25. **Status:** Owner-approved. DEC-002 remains CONDITIONALLY APPROVED for the separate Arabic verse-text release gate.

HifzTrack independently maintains versioned plain Arabic and simplified Latin Surah names and canonical Juz ranges. The names are display metadata. Surah/Ayah coordinates remain the stable identity for references and personal records. Juz 4 starts at `3:93` and Juz 11 at `9:93`. The single approved Mushaf edition remains the 604-page KFGQPC Madani 1441H Hafs, identified as `madani-1441h-hafs`.

Tanzil, QUL and Quran.com are optional reference sources under applicable terms. Provider-specific permission is unnecessary when existing terms already cover the intended use. Every compiled category requires lawful sources, versioned provenance, attribution as applicable, structural validation and independent accuracy evidence. Previously cleared material remains usable under its existing terms. The application runs using its imported database references and local versioned import files, with no external Quran API dependency.

ADR-014 continues to govern Arabic verse-text release evidence. Verse-text display, translations and additional Mushaf editions remain outside this work. [Compilation and verification](../../data/quran/validation/INDEPENDENT_METADATA.md)
