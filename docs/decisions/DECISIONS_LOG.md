# Decision log

Record approved decisions with ID, date, context, decision, consequences, and status. Proposed decisions must be labeled as proposals until approved.

## ADR-001: Modular monolith

**Status:** Accepted baseline. **Decision:** Use a modular monolith. **Reason:** The MVP does not require distributed services.

## ADR-002: Personal progress ownership

**Status:** Accepted baseline. **Decision:** Memorization and revision records belong to individual users, not groups. **Reason:** A user can belong to multiple groups.

## ADR-003: Group-specific sharing

**Status:** Accepted baseline. **Decision:** Sharing is configured independently for each group membership and enforced server-side. **Reason:** A user may share different levels with different groups.

## ADR-004: Ayah-level memorization source

**Status:** Accepted baseline. **Decision:** Maintain memorization progress at Ayah level; derive Juz/page progress from canonical Quran data. **Reason:** Avoid competing progress truth and preserve precise tracking.

## ADR-005: Memorization and revision are separate

**Status:** Accepted baseline. **Decision:** Record Sabaq and Muraja'ah as separate activities; revision does not automatically alter memorization strength/status.

## ADR-006: No premature deferred work

**Status:** Accepted baseline. **Decision:** Preserve all planned features in the catalog, but implement only the approved release/milestone scope.
