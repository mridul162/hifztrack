# HifzTrack

HifzTrack is a Quran memorization tracking and community management platform. The repository contains the product specification, technical design, development foundation, and governance for the complete product vision.

Start with [the documentation index](docs/README.md). The current foundation provides a Next.js frontend, FastAPI backend, PostgreSQL development service, and empty Alembic baseline. Product features have not yet been implemented.

## Local development

Prerequisites: Python 3.13 for local backend development, Node.js 20.9 or newer and npm for local frontend development, or Docker Desktop with Compose v2 to run the complete stack. Create a local environment file by copying `.env.example` to `.env`, then start the services from the repository root:

```powershell
Copy-Item .env.example .env
docker compose -f infrastructure/docker/compose.yaml up --build
```

Open the frontend at <http://localhost:3000>. The development page reports whether it can reach the API. The API liveness check is at <http://localhost:8000/health/live>; database readiness is at <http://localhost:8000/health/ready>.

The Compose database credentials are development-only placeholders. Do not use them in a production environment. The environment file is ignored by Git.
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

Alembic is configured in `backend/alembic.ini`; migration scripts live in `backend/migrations/versions/`. The initial migration establishes Alembic tracking only and creates no application tables. After starting PostgreSQL, run `alembic upgrade head` from `backend/`. Do not add domain tables until their milestone is approved.
