# Development roadmap

Implement one approved milestone at a time. The complete product inventory is in `docs/02_FEATURE_CATALOG.md`; this roadmap controls sequencing, not whether future features remain part of the vision.

## Source-aligned milestone sequence

The original specification proposes the following sequence. Phase 0 is documented for traceability only; this reconciliation task does not start it.

| Phase | Deliverable | Main focus |
|---|---|---|
| 0 | Development foundation: backend/frontend scaffolding, Compose/PostgreSQL, SQLAlchemy/Alembic, health check, basic UI and environment docs | Local foundation acceptance only; not authorized by this task |
| 1 | Authentication and profile | Sessions, privacy and auth tests |
| 2 | Groups and memberships | Group CRUD, invitation, many-to-many roles/admins |
| 3 | Quran reference and memorization | Canonical data, submissions, Ayah status and calculations |
| 4 | Revision tracking | Separate sessions, history and revision analytics |
| 5 | Sharing and authorization | Per-membership visibility and negative security tests |
| 6 | Mentor and dashboards | Optional assessment, personal/group dashboards and basic analytics |
| 7 | Production readiness | CI/CD, logging, backups, deployment and security review |

Detailed milestone acceptance criteria from the source are retained in the feature catalog and corresponding requirements. Before any phase begins, the owner approves scope, review gates, and open decisions. Git guidance from the source is to use GitHub, keep `main` as default and `develop` as integration branch, use feature branches for work, inspect diffs, and commit only after verification; do not auto-commit or merge.

Repository guidance from the source: begin private during development; choose the license before public release; `.gitignore` should follow the Python/backend setup; never commit secrets. Review one task/milestone at a time, run relevant tests, and have the project owner review and approve changes.

| Phase | Acceptance summary from source |
|---|---|
| 0 | Frontend/backend run locally, database connects, migrations execute. This phase has not started. |
| 1 | Register/login, update own profile, deny access to another user's private profile. |
| 2 | Create multiple groups, join multiple groups, admins manage membership, invitations expire or can be revoked. |
| 3 | Record Quran ranges; calculate progress correctly; derive Juz/page coverage; repeated submissions do not inflate progress. |
| 4 | Record revision sessions; preserve revision history; keep revision independent of new memorization. |
| 5 | Configure sharing per group; group APIs do not expose private information; leaving revokes future access. |
| 6 | Individual progress is accurate; group statistics include only authorized shared data; date-based reports are available. |
| 7 | Automated tests cover critical services and negative authorization; migrations and Docker deployment work; backups and error monitoring are configured. |

## Release 2: accountability and management

P1 scope from source: individual and collective targets, mentor assessment/feedback, notifications and announcements, historical reports and analytics. The earlier initialization brief additionally proposed notes, challenges, and expanded activity/community features; these are labeled extended proposals, not source FR commitments.

## Release 3: advanced platform

P2 scope from source: progress report export. The earlier initialization brief proposed CSV/PDF reporting details, revision recommendations, audio, offline sync, WhatsApp, and experimental AI evaluation; retain as future proposals, not MVP requirements.

## Gate for each milestone

Confirm dependencies and acceptance criteria, implement only the approved scope, run relevant automated tests including access-control negatives, update specification/status, and review unresolved risks before moving to the next milestone.
