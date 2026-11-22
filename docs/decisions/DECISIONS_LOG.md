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
