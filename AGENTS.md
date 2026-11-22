
# HifzTrack - Agent Instructions

## Documentation authority

The complete product vision and current specification live in `docs/`. Begin with `docs/README.md`, consult both preserved originals under `docs/source/`, then read the relevant requirements, feature, business-rule, architecture, and roadmap documents. The catalog includes original requirements and later proposals; presence in the catalog does not authorize a deferred feature.

If source material is incomplete, requirements conflict, or a decision is unresolved, document the gap and surface it. Do not silently invent or settle product commitments.

## Technology Stack

Backend:
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy 2.0
- Pydantic
- Alembic

Frontend:
- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

Infrastructure:
- Docker
- Docker Compose
- GitHub Actions (later)

## Architecture Rules

1. Use a modular monolithic architecture: Next.js + TypeScript frontend; FastAPI, Pydantic and SQLAlchemy 2.0 backend; PostgreSQL; Alembic migrations; Docker Compose.
2. Keep API, business logic, database access,
   and validation responsibilities separate.
3. Do not introduce microservices.
4. Do not introduce unnecessary abstractions.
5. Follow the documented database design.
6. Keep Quran reference data canonical.
7. Personal memorization data belongs to users,
   not groups.
8. A user can belong to multiple groups.
9. Sharing permissions are group-specific.
10. Enforce authorization on the backend.

## Development Rules

1. Work on one approved milestone at a time, following `docs/roadmap/DEVELOPMENT_ROADMAP.md` and `docs/roadmap/MVP_SCOPE.md`.
2. Inspect existing code before modifying it.
3. Do not rewrite working modules unnecessarily.
4. Avoid adding dependencies without justification.
5. Do not modify unrelated files.
6. Do not implement deferred features prematurely or remove them from the catalog.
7. Ask before changing documented architectural decisions.
8. Use database migrations for schema changes.
9. Never commit secrets or environment files.

## Testing Rules

1. Write tests for business logic.
2. Test authorization and access restrictions.
3. Test database constraints.
4. Run relevant tests after each change.
5. Fix failing tests before declaring completion.
6. Include negative authorization test cases.

## Codex Workflow

For each task:

1. Inspect relevant documentation and existing code.
2. Identify the feature IDs, release scope, dependencies, and acceptance criteria; explain the implementation plan.
3. Identify affected files.
4. Implement the smallest complete change.
5. Run relevant automated tests and review authorization and edge cases.
6. Update `docs/roadmap/IMPLEMENTATION_STATUS.md` and relevant specifications.
7. Report changed files, verification results, and unresolved issues.

Do not start implementing a later milestone without explicit user approval. Do not claim a feature is verified unless its acceptance criteria and tests pass.
Do not commit, push, or merge unless the user explicitly asks.

## Important Business Rules

- Memorization and revision are separate activities.
- Activity history must be preserved.
- Current progress is calculated from per-ayah status.
- Revision does not automatically make an ayah strong.
- Mentor assessments are optional.
- Group members can only access information
  permitted by the owner's sharing settings.
- Leaving a group revokes future group access.
