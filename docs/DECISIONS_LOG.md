# Legacy decision log

The consolidated, current decision register is [decisions/DECISIONS_LOG.md](decisions/DECISIONS_LOG.md).

## ADR-001: Modular Monolith

Decision:
Use a modular monolithic backend.

Reason:
The MVP does not require distributed services.

## ADR-002: Personal Progress Ownership

Decision:
Memorization progress belongs to individual users,
not to groups.

Reason:
A user can belong to multiple groups.

## ADR-003: Group-Specific Sharing

Decision:
Sharing permissions are configured independently
for each group membership.

Reason:
A user may share different levels of information
with different groups.
