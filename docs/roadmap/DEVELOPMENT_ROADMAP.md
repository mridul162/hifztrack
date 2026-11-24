# Development roadmap

Implement one approved milestone at a time. The complete product inventory is in `docs/02_FEATURE_CATALOG.md`; this roadmap controls sequencing, not whether future features remain part of the vision.

## Source-aligned milestone sequence

The original specification proposes the following sequence. F0-A is an owner-approved, limited foundation task; it does not authorize the remaining Phase 0 checklist.

| Phase | Deliverable | Main focus |
|---|---|---|
| 0 | Development foundation: backend/frontend scaffolding, Compose/PostgreSQL, SQLAlchemy/Alembic, health check, basic UI and environment docs | F0-A approved as a limited foundation slice; broader Phase 0 acceptance remains unauthorized |
| 1 | Authentication and profile | Sessions, privacy and auth tests; VERIFIED |
| 2 | Groups and memberships | Group CRUD, invitation, many-to-many roles/admins |
| 3 | Quran reference and memorization | QURAN-01 numeric references are IN_PROGRESS; MEM-01 personal Ayah status and Sabaq activity are VERIFIED. REV-01 remains in Phase 4. |
| 4 | Revision tracking | P0 recording and history; detailed revision analytics are P1 / Release 2 (FR-16, DEC-022) |
| 5 | Sharing and authorization | Per-membership visibility and negative security tests |
| 6 | Mentor and dashboards | Optional assessment, personal/group dashboards and basic analytics |
| 7 | Production readiness | CI/CD, logging, backups, deployment and security review |

GROUP-01 and GROUP-02 are VERIFIED. PostgreSQL migration upgrade/downgrade, schema inspection, rate-limit boundaries, and concurrency coverage are recorded in the implementation status.

Detailed milestone acceptance criteria from the source are retained in the feature catalog and corresponding requirements. Before any phase begins, the owner approves scope, review gates, and open decisions. Git guidance from the source is to use GitHub, keep `main` as default and `develop` as integration branch, use feature branches for work, inspect diffs, and commit only after verification; do not auto-commit or merge.

Repository guidance from the source: begin private during development; choose the license before public release; `.gitignore` should follow the Python/backend setup; never commit secrets. Review one task/milestone at a time, run relevant tests, and have the project owner review and approve changes.

| Phase | Acceptance summary from source |
|---|---|
| 0 | F0-A foundation is verified; broader Phase 0 remains NOT AUTHORIZED. |
| 1 | Register/login, update own profile, deny access to another user's private profile. AUTH-01 / USER-01 are VERIFIED; see implementation status for evidence. |
| 2 | Create multiple groups, join multiple groups, admins manage membership, invitations expire or can be revoked. |
| 3 | Record Quran ranges; calculate progress correctly; derive Juz/page coverage; repeated submissions do not inflate progress. |
| 4 | Record revision sessions and preserve revision history in P0; keep revision independent of new memorization. Detailed revision analytics are P1 / Release 2 under FR-16 and DEC-022. |
| 5 | Configure sharing per group; group APIs do not expose private information; leaving revokes future access. |
| 6 | Dashboard progress is accurate and group statistics include only authorized shared data (P0). The source also asks for date-based reports in this phase; FR-16 classifies historical reports/analytics as P1, so those reports belong to Release 2 unless the owner approves a scope change. |
| 7 | Automated tests cover critical services and negative authorization; migrations and Docker deployment work; backups and error monitoring are configured. |

### Phase 0 acceptance checklist (broader work not authorized)

The broader Phase 0 remains **NOT AUTHORIZED**. F0-A approval does not authorize completing this checklist. When separately approved, its acceptance requires:

1. Docker Compose starts the application services.
2. FastAPI starts and its health endpoint responds.
3. FastAPI connects to PostgreSQL.
4. Alembic migrations execute successfully.
5. Next.js starts successfully.
6. The frontend can communicate with the backend.
7. Relevant basic tests pass.
8. README and environment setup instructions are documented.

This checklist records broader Phase 0 criteria only; the limited F0-A work and its verification are recorded separately above. The remaining checklist work is not authorized.

## Release 2: accountability and management

P1 scope from source: individual and collective targets, mentor assessment/feedback, notifications and announcements, historical reports and analytics. The earlier initialization brief additionally proposed notes, challenges, and expanded activity/community features; these are labeled extended proposals, not source FR commitments.

## Release 3: advanced platform

P2 scope from source: progress report export. The earlier initialization brief proposed CSV/PDF reporting details, revision recommendations, audio, offline sync, WhatsApp, and experimental AI evaluation; retain as future proposals, not MVP requirements.

## Gate for each milestone

Confirm dependencies and acceptance criteria, implement only the approved scope, run relevant automated tests including access-control negatives, update specification/status, and review unresolved risks before moving to the next milestone.
