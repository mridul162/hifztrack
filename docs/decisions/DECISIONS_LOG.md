# Decision log

Record approved decisions with ID, date, context, decision, consequences, and status. Proposed decisions must be labeled as proposals until approved.

## ADR-001: Modular monolith

**Status:** Accepted baseline. **Decision:** Use a modular monolith. **Reason:** The MVP does not require distributed services.

## ADR-002: Personal progress ownership

**Status:** Accepted. **Decision:** Each user owns one central personal memorization record. Current Ayah status is represented once per `(user, Ayah)`; Sabaq history is stored separately. Groups receive permission-filtered views of the same record and never own duplicate progress copies. **Reason:** A user can belong to multiple groups and share different views with each. Correction, cancellation, and status-history semantics remain open under DEC-005.

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
