# System architecture

## Baseline

Use a modular monolith with a layered REST API: Next.js + TypeScript responsive frontend, FastAPI backend, Pydantic validation, SQLAlchemy 2.0 persistence, PostgreSQL, Alembic migrations, and Docker Compose. Do not introduce microservices, message brokers, Kubernetes, or complex distributed infrastructure for the MVP.

The original describes the product as multi-tenant. Use a global user identity with group-scoped membership/roles and optional organization-to-group metadata. DEC-021 resolves that an organization association grants no access; no organization-level roles, membership, or authorization are implemented. Personal progress remains owned centrally by the user.

## Logical boundaries

- **Frontend:** authentication/session experience, Quran navigation, personal trackers, group/member views, settings, and later modules.
- **API:** root-level HTTP endpoints following AUTH-01; authentication, validation, authorization, and stable response contracts. API versioning remains a future architectural decision; do not imply a `/api/v1` prefix is implemented.
- **Application/domain modules:** identity, Quran reference, memorization, revision, groups/sharing, dashboards; later goals, mentorship, notification, and analytics modules.
- **Persistence:** relational entities and repositories; migrations are the only schema evolution mechanism.
- **Background work:** defer selection of a job mechanism until scheduled notifications or exports require it.

Backend responsibilities remain distinct: API handles HTTP, schemas validate input/output, services orchestrate business rules and transactions, repositories query data, models represent persistence, dependencies provide authentication/permissions, and core holds configuration/infrastructure. This is a logical target; do not scaffold all feature modules before their milestones.

## Request flow

Browser -> Next.js UI -> FastAPI endpoint -> authenticated principal and scoped authorization -> domain operation -> SQLAlchemy/PostgreSQL -> response filtered for caller permissions. Group data must be privacy-filtered in the backend before serialization.

## Deployment and operations

Docker Compose is the development baseline. Production hosting, object storage, email delivery, observability, backup/restore targets, and CI provider are unresolved. Keep secrets in environment-specific secret stores; `.env.example` contains names/placeholders only.

No Redis is needed initially. Add a background worker only when scheduled notifications require it, object storage when audio recording is implemented, and maintain a validated internal Quran reference dataset rather than depending on an external Quran API.

## Architecture constraints

- Personal progress ownership and group-specific sharing are foundational.
- A single user-owned memorization record is the source for all group views; group membership creates scoped access, not duplicate progress data.
- Group view authorization is backend-enforced per membership episode. Only the owner changes that episode's sharing settings; ADMIN/MENTOR role does not override privacy. All ACTIVE members are eligible readers of enabled fields, and other membership states are denied. A rejoin creates fresh settings with approved defaults; personal records remain user-owned and are never copied into groups (DEC-006/016/023; ADR-018).
- Surah/Ayah are canonical; Juz and Mushaf page references are derived from canonical mappings.
- Separate current progress state from historical memorization and revision activity.
- Canonical Quran reference data is separate from user activity.
- Memorization and revision are distinct domains.
- Mentor verification remains optional.
- Prefer explicit module boundaries and ordinary relational modeling over premature abstraction.
