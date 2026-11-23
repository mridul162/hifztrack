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

**Context:** QURAN-01 requires a canonical Quran reference, stable Surah/Ayah coordinates, and derived Juz/page navigation. The repository contains Tanzil Quran Text Uthmani v1.1 and Tanzil metadata, but local provenance, metadata-license evidence, and independent verification of page boundaries are incomplete.

**Approved decision:** Use Tanzil Quran Text Uthmani v1.1 in Uthmani script, with the Madani Mushaf and 604-page convention. Canonical Ayah identity is `(surah_number, ayah_number)`; Juz and page references are derived. Exclude translations from the initial release and preserve the Arabic source text verbatim. Defer additional Mushaf editions.

**Consequences:** QURAN-01 may use this direction only after the applicable evidence gates below are satisfied. Translation files remain outside initial-release import, API, and distribution scope and require a separate licensing decision.

**Outstanding conditions before import/use:** Establish provenance of the local Arabic file and preserve the applicable Tanzil notice; resolve the notice discrepancy from authoritative evidence; establish the provenance and licensing basis for metadata's `cc-by-3.0` declaration and record attribution/redistribution requirements; identify the exact authoritative Madani edition and independently verify all 604 page boundaries, recording source, method, discrepancies, and result.

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
