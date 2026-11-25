# HifzTrack

HifzTrack is a Quran memorization tracking and community management platform. The repository contains the product specification, technical design, development foundation, and governance for the complete product vision.

Start with [the documentation index](docs/README.md). The repository has the verified F0-A foundation and AUTH-01 authentication/profile milestone. QURAN-01 provides numeric Surah/Ayah references and navigation for the Madani 1441H Hafs edition. [Implementation status](docs/roadmap/IMPLEMENTATION_STATUS.md)

## Local development

Prerequisites: Python 3.13 for local backend development, Node.js 20.9 or newer and npm for local frontend development, or Docker Desktop with Compose v2 to run the complete stack. Create a local environment file by copying `.env.example` to `.env`, then start the services from the repository root:

```powershell
Copy-Item .env.example .env
docker compose -f infrastructure/docker/compose.yaml up --build
```

After Compose starts, create the tables and load the local numeric references with Madani 1441H Hafs page mappings:

```powershell
docker compose -f infrastructure/docker/compose.yaml exec backend alembic upgrade head
docker compose -f infrastructure/docker/compose.yaml exec backend python -m app.quran.import_reference --with-pages
```

The local Compose service mounts the preserved Arabic source and the normalized page dataset read-only. Omit `--with-pages` for a numeric-only import. Open the frontend at <http://localhost:3000>, including `/quran` for Surah/Ayah and page browsing. The API liveness check is at <http://localhost:8000/health/live> and database readiness is at <http://localhost:8000/health/ready>. [Page data attribution](data/quran/derived/reference/NOTICE.md)

The Compose database credentials and security key are development-only placeholders. Replace `SECURITY_SECRET_KEY` with a random value of at least 32 bytes for local use; do not use development values in production. The environment file is ignored by Git. The session cookie is Secure by default.
PostgreSQL data persists in the dedicated Docker volume `hifztrack_f0a_postgres_data`.

## Backend commands

From `backend/`, create and activate a Python 3.13 virtual environment, then install development dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
pytest
alembic upgrade head
```

Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL before running Alembic or the backend outside Compose. For example, the local default in `.env.example` points to `localhost:5432`.

## Frontend commands

From `frontend/`:

```powershell
npm ci
npm run dev
npm run build
```

Set `NEXT_PUBLIC_API_URL` to the browser-accessible API origin when it differs from `http://localhost:8000`. `CORS_ORIGINS` configures the backend's allowed frontend origins.

## Database migrations

Alembic is configured in `backend/alembic.ini`; migration scripts live in `backend/migrations/versions/`. The initial migration establishes Alembic tracking only. The AUTH-01 migration adds users, opaque server sessions, and authentication rate-limit counters. After starting PostgreSQL, run `alembic upgrade head` from `backend/`. Do not add later domain tables until their milestone is approved.
