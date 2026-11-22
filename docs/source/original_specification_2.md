For HifzTrack, I recommend using **Codex as your primary implementation agent, GitHub as your source-control platform, and a milestone-based development workflow.**

The most important thing is not to ask Codex to build the entire application in one prompt.

Instead, set up a repository that gives Codex:

- A clear understanding of the product.
- Explicit architectural decisions.
- Database and business rules.
- Coding conventions.
- A sequence of implementation milestones.
- Automated tests to verify its work.

You should act as the technical lead: define requirements, review architecture, inspect code, run tests, and approve changes. Codex should handle much of the implementation.

# **1. Recommended development workflow**

**You — Product & Technical Lead**

Requirements · Architecture · Code review · Decisions

**Codex — Coding Agent**

Implementation · Testing · Debugging · Refactoring

**GitHub Repository**

Source code · Documentation · Issues · Version history

**Development Environment**

Docker · PostgreSQL · Automated tests · Local application

The development cycle should be:

1. Give Codex one clearly defined task.
2. Ask it to inspect the existing architecture.
3. Let it implement the task.
4. Ask it to run relevant tests.
5. Review the changes.
6. Commit the completed milestone.
7. Move to the next task.

This is much safer than allowing an agent to make large, uncontrolled changes across the entire repository.

# **2. Create the GitHub repository**

Create a new repository:

[Oakstone & Github | Executive Search for GTM SaaS](https://images.openai.com/static-rsc-4/HQnzkeZepdcbz6yki5F911xaI7qZFrq-EjoAnoh5focKQlZBBR_xVRxmdszYIh8CF9ZImt1zDUWQIDbeJm9vx6gJmTSUYpEpChiHmY_gLt1gXp9uq4lq-oxfEEM9g7FJhQpCYi7WHrUwBF9vcV_4-kwArSHYrPmmA6I2uBI6wFE?purpose=inline)

**hifztrack**

Suggested repository name

[Create GitHub repository](https://github.com/new?utm_source=chatgpt.com)

Recommended settings:

| Setting         | Value                        |
| --------------- | ---------------------------- |
| Repository name | `hifztrack`                  |
| Visibility      | Private initially            |
| README          | Yes                          |
| `.gitignore`    | Python                       |
| License         | Decide before public release |
| Default branch  | `main`                       |

I recommend keeping it private while you are developing and handling real community data.

## **2.1 Clone the repository**

On your Windows machine:

```
git clone https://github.com/YOUR_USERNAME/hifztrack.git

cd hifztrack
```

Create your development branch:

```
git checkout -b develop
```

Use `develop` for integration and feature branches for individual tasks.

# **3. Set up the repository structure**

I recommend a **monorepo** rather than separate frontend and backend repositories.

Why?

- One repository contains the complete application.
- Codex can understand frontend/backend dependencies together.
- Easier local development with Docker Compose.
- Easier to manage API contracts and database migrations.
- One place for project documentation and architectural decisions.

Create this initial structure:

```
hifztrack/
│
├── AGENTS.md
├── README.md
├── .gitignore
├── .env.example
│
├── docs/
│   ├── PRD.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── DATABASE_DESIGN.md
│   ├── API_SPECIFICATION.md
│   ├── BUSINESS_RULES.md
│   └── DEVELOPMENT_ROADMAP.md
│
├── backend/
│
├── frontend/
│
├── infrastructure/
│   └── docker/
│
├── scripts/
│
└── tests/
```

Don't create every backend and frontend module manually. Let Codex establish those structures during the relevant implementation phases.

## **3.1 What each documentation file should contain**

These documents are the project's source of truth.

| File                     | Responsibility                                       |
| ------------------------ | ---------------------------------------------------- |
| `PRD.md`                 | Product vision, target users, requirements           |
| `SYSTEM_ARCHITECTURE.md` | System components and architecture                   |
| `DATABASE_DESIGN.md`     | ERD, tables, constraints, relationships              |
| `API_SPECIFICATION.md`   | API endpoints and request/response contracts         |
| `BUSINESS_RULES.md`      | Memorization, revision, sharing and assessment rules |
| `DEVELOPMENT_ROADMAP.md` | Milestones and acceptance criteria                   |

I would also add:

`DECISIONS_LOG.md` — records important architectural decisions and why they were made.

For example:

```
# Architecture Decision Records

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
```

## **3.2 Create&#x20;**`AGENTS.md`

Most important file for Codex

Codex reads `AGENTS.md` to understand repository-specific instructions. It is the appropriate place for persistent coding conventions, architectural boundaries, testing expectations and project rules.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.chatgpt.com\&sz=32)

ChatGPT Learn+1



I recommend starting with this:

```

# HifzTrack - Agent Instructions

## Project Overview

HifzTrack is a Quran memorization tracking and
community management platform.

It supports:
- Individual Quran memorization tracking.
- Revision tracking (Muraja'ah).
- Multiple memorization groups.
- Custom group-level data sharing.
- Optional mentor verification.
- Community and institutional use cases.

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

1. Use a modular monolithic architecture.
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

1. Work on one milestone at a time.
2. Inspect existing code before modifying it.
3. Do not rewrite working modules unnecessarily.
4. Avoid adding dependencies without justification.
5. Do not modify unrelated files.
6. Do not introduce features outside the current task.
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
2. Explain the implementation plan.
3. Identify affected files.
4. Implement the smallest complete change.
5. Run relevant tests.
6. Report changed files and test results.
7. Document important decisions.

Do not start implementing the next milestone
without explicit user approval.

## Important Business Rules

- Memorization and revision are separate activities.
- Activity history must be preserved.
- Current progress is calculated from per-ayah status.
- Revision does not automatically make an ayah strong.
- Mentor assessments are optional.
- Group members can only access information
  permitted by the owner's sharing settings.
- Leaving a group revokes future group access.

```

Keep `AGENTS.md` concise. Detailed requirements belong in `docs/`, which Codex should consult when working on the relevant features.

# **4. How to initialize Codex**

You have two practical approaches:

**Option A — Codex desktop application**

1. Open Codex.
2. Connect your GitHub account if you want repository integration.
3. Open your local `hifztrack` repository.
4. Allow access to the project workspace.
5. Start with the repository-planning prompt below.

**Option B — Codex CLI**

From the repository root:

```
codex
```

Sign in when prompted.

Codex CLI can inspect files, edit the local repository and run development commands. You can review its changes as it works.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.chatgpt.com\&sz=32)

ChatGPT Learn+1



Official resources:

- [Codex CLI documentation](https://learn.chatgpt.com/docs/cli?utm_source=chatgpt.com)
- [AGENTS.md configuration guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md?utm_source=chatgpt.com)
- [OpenAI Codex development workflow](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex?utm_source=chatgpt.com)

For Windows, use the supported Codex desktop workflow or a compatible CLI environment. WSL2 is an option if you want a Linux-based development environment.

# **5. Your first Codex task: repository initialization**

This is where I would start.

**Do not ask Codex to implement authentication, database models or frontend pages yet.**

First, give it the product requirements and ask it to prepare the repository.

Use this prompt:

# Task: Initialize HifzTrack Repository

You are working as a senior software architect on HifzTrack.

HifzTrack is a Quran memorization tracking and community management platform.

## Product Context

The platform supports:

- Individual Quran memorization tracking.
- Revision (Muraja'ah) tracking.
- Multiple groups per user.
- Custom progress-sharing permissions per group.
- Optional mentor verification.
- Informal Quran communities and structured institutions.

## Technology Stack

Backend:

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

- Docker Compose

Architecture:

- Modular monolith
- REST API
- Layered backend architecture

## Task

Initialize the repository documentation and development foundation.

1. Inspect the existing repository.
2. Read the existing AGENTS.md if present.
3. Create or refine the following documentation:
   - docs/PRD.md
   - docs/SYSTEM_ARCHITECTURE.md
   - docs/DATABASE_DESIGN.md
   - docs/API_SPECIFICATION.md
   - docs/BUSINESS_RULES.md
   - docs/DEVELOPMENT_ROADMAP.md
   - docs/DECISIONS_LOG.md
4. Use the established HifzTrack requirements and architectural decisions.
5. Identify contradictions, missing requirements and unresolved technical decisions.
6. Do not silently invent business rules. Document assumptions separately.
7. Ensure all documentation is consistent with one another.
8. Update README.md with the project overview and documentation index.

## Constraints

- Do not implement application features.
- Do not create unnecessary application modules.
- Do not install dependencies.
- Do not introduce microservices.
- Do not change the agreed technology stack.
- Do not overwrite existing work without reviewing it.

## Expected Output

Provide:

1. Repository documentation structure.
2. Completed documentation files.
3. List of unresolved decisions.
4. Proposed implementation milestones.
5. Recommended next development task.

Stop after completing repository initialization. Wait for approval before implementation.

**Why this first task matters:** You want Codex to turn the product concept into consistent, maintainable engineering documentation before it starts generating code.

Review all seven documents yourself. Pay particular attention to the database design and sharing rules.

# **6. Implement the project milestone by milestone**

Once repository documentation is ready, use this implementation sequence.

**Phase 0 — Development foundation**

Start here

Deliverables:

- Backend and frontend scaffolding.
- Docker Compose.
- PostgreSQL connection.
- SQLAlchemy configuration.
- Alembic migrations.
- Health-check endpoint.
- Basic frontend layout.
- Development environment documentation.

  Acceptance: frontend and backend run locally, database connection works, migrations execute.

  **Phase 1 — Authentication**
- User registration.
- Login and logout.
- Secure session management.
- Profile management.
- Authentication tests.

  **Phase 2 — Group management**
- Group creation.
- Invitations.
- Multiple memberships.
- Membership roles.
- Group administration.

  **Phase 3 — Quran and memorization**
- Quran reference dataset.
- Surah and Ayah selection.
- Memorization submissions.
- Per-Ayah progress.
- Progress calculations.

  **Phase 4 — Revision**
- Revision sessions.
- Revision history.
- Revision analytics.

  **Phase 5 — Sharing and authorization**
- Per-group sharing preferences.
- Shared progress API.
- Permission enforcement.
- Security tests.

  **Phase 6 — Mentor and dashboards**
- Optional mentor assessment.
- Personal dashboard.
- Group dashboard.
- Basic analytics.

  **Phase 7 — Production readiness**
- CI/CD.
- Logging.
- Backups.
- Deployment.
- Security review.

## **6.1 Prompt for Phase 0**

Once Codex has completed repository initialization and you approve its documentation, give it this task:

# Task: Implement HifzTrack Development Foundation

Read:

- AGENTS.md
- docs/SYSTEM_ARCHITECTURE.md
- docs/DEVELOPMENT_ROADMAP.md

Implement Phase 0 only.

## Backend

Set up:

- FastAPI application.
- SQLAlchemy 2.0.
- PostgreSQL connection.
- Alembic migrations.
- Pydantic settings.
- Environment variable configuration.
- Health-check endpoint.

## Frontend

Set up:

- Next.js with TypeScript.
- Tailwind CSS.
- shadcn/ui.
- Basic responsive application layout.
- Basic API client configuration.

## Infrastructure

Set up:

- Backend Dockerfile.
- Frontend Dockerfile.
- Docker Compose.
- PostgreSQL service.
- Environment example file.

## Quality Requirements

- Keep the implementation minimal.
- Follow the documented architecture.
- Do not implement authentication yet.
- Do not create future feature modules prematurely.
- Add basic tests.
- Add setup instructions to README.md.
- Never commit secrets.

## Acceptance Criteria

1. Docker Compose starts the application.
2. FastAPI health endpoint responds successfully.
3. FastAPI connects to PostgreSQL.
4. Alembic migrations can run.
5. Next.js application starts.
6. Frontend can communicate with the backend.
7. Relevant tests pass.

Before implementation, explain your proposed file structure and implementation plan.

After implementation, report:

- Files created or modified.
- Commands executed.
- Tests executed and results.
- Any unresolved issues.

Do not begin Phase 1.

# **7. How to manage Git branches and commits**

I recommend a simple branching strategy.

```
main
  |
  └── develop
        |
        ├── feature/authentication
        ├── feature/group-management
        ├── feature/memorization
        ├── feature/revision
        └── feature/group-sharing
```

Example workflow:

```
git checkout develop

git checkout -b feature/authentication

# Let Codex implement the feature.

# Review the changes
git diff

# Run tests
# Commit only after verification

git add backend frontend tests
git commit -m "feat: implement authentication"

git checkout develop
git merge feature/authentication
```

For each milestone, create a Git checkpoint before asking Codex to make significant changes.

**Important:** Do not let Codex automatically commit or merge everything. Review the diff before accepting changes.

# **8. How to get better results from agentic coding**

These are the practices I would follow throughout HifzTrack development.

| Practice       | What to do                              |
| -------------- | --------------------------------------- |
| Small tasks    | One feature or cohesive change per task |
| Planning first | Ask Codex for an implementation plan    |
| Context        | Tell it which documentation to read     |
| Testing        | Require tests for business logic        |
| Code review    | Inspect diffs and edge cases            |
| Architecture   | Ask before architectural changes        |
| Git            | Commit after verified milestones        |
| Documentation  | Update docs when decisions change       |

### **Use three types of Codex prompts**

**Type 1: Planning**

```
Read the relevant documentation.

Analyze how this feature should be implemented.

Identify:
- Business rules
- Database changes
- API changes
- Affected modules
- Edge cases
- Tests required

Do not write code yet.
```

**Type 2: Implementation**

```
Implement the approved plan.

Keep changes limited to this feature.

Follow AGENTS.md and existing architecture.

Write tests and run them.

Do not modify unrelated modules.
```

**Type 3: Review**

```
Review the implementation as a senior backend engineer.

Focus on:
- Incorrect business logic
- Database integrity
- Authorization vulnerabilities
- Race conditions
- Missing test cases
- Unnecessary complexity

Do not modify files yet.

Report findings by severity.
```

You can also use Codex's `/review` command for reviewing changes.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://learn.chatgpt.com\&sz=32)

ChatGPT Learn+1



# **9. My recommended starting stack**

[The Python Programming Logo: A Symbol Of Innovation And Community  – peerdh.com](https://images.openai.com/static-rsc-4/1zm_3HI-h3J8YwI9BIJr_3cQRhZqv3nAVxTSYEFHBJkjSZE4ABRzo8wZ3VHRJ0xYzlJj-HsPlG1t0ez3XKA3zp9-HPjmrZLu71xu89CSAyI4qZ2oiF-h3K7Dpe_McEqmEJqZO687jfbyrWNRcHm01XpVLZyU1sBreCaiovQeybw?purpose=inline)

**Backend: Python + FastAPI**

[Making a custom 404 page in Next.js - DEV Community](https://images.openai.com/static-rsc-4/bLlalbNp6jrlR_MDbXrZboKQVewUYbl540tPaxrKHfeYhkUuIbcY24EuZwqdvoz2T6syE51AVhW2nzEAnbXMhFU1S9FS9hfRUHcmE0rqe4-MftFGYbc3hxELPbunRQ4RO1h7brQUYFBkCbuY4CGkHzzUDPnQR728ILI1Y17qp2M?purpose=inline)

**Frontend: Next.js + TypeScript**

[Postgresql Logo PNG Transparent With Clear Background ID 473068 |  TOPpng](https://images.openai.com/static-rsc-4/x6sDZ8oKI9URixQ5E82vqCQV1aR38qK7E8n0HKggx6_cD8G7QtlPuHlyO99GalHPJOycjs41bPgfrRTqdHFqayPWJl57hxNttQynREzHXSUSsui_zVAB_ssyc1xdm_msJ5GiDzf23C9Z2RuuoyVCc6J0AbuAqX5Aul_x1J78q2I?purpose=inline)

**Database: PostgreSQL**

[Docker Logo PNG, AI, EPS, CDR, PDF, SVG - iconLogoVector](https://images.openai.com/static-rsc-4/x_Ge8Om-lmdDyESi_E1do4drGQT9DSkX52vTn2ewhosAAWrXUQb75wMc1ir1acbib9ghrUC265cv3GoWGy3jQpD5Eo8uaFw2K4vVUP6L8ro7xoeh077PcgfTkj0A9dAagm-ASFMY2S_Q_IAVAVpZCEojLDWXxsXMojeGIp5mFLE?purpose=inline)

**Infrastructure: Docker Compose**

[Yazılım Lisans Tipleri ve Repository’e Lisans Ekleme - DEV Community](https://images.openai.com/static-rsc-4/vRwy1RGUwiPPYZ2MIClOm4RNqWId6-r6fWZm8GbDuWkGTL66NwCxAqx_1qm-HBd-yJmibunsfFWAEl4nB-Hhcm7275D-jwikK3I-xgv8XD2OUh3ovbsSN0ejWc_R1pNr7Wj3-0faPtdDWX6NwCWRrIvYy2Em0L6zfV_qbMzxVkk?purpose=inline)

**Version control: GitHub**

I would avoid adding Redis, Celery, Kubernetes, LangChain or any AI framework at this stage.

You can introduce additional infrastructure when an actual requirement justifies it.

# **10. What you should do today**

Here is the exact order I recommend:

1. Create the private GitHub repository `hifztrack`.
2. Clone it to your local machine.
3. Create the initial repository structure.
4. Add `AGENTS.md`.
5. Open the repository in Codex.
6. Submit the repository initialization prompt.
7. Review and approve the generated documentation.
8. Start Phase 0.

**One important piece of advice:** Don't measure progress by how many files Codex generates. Measure it by how many working, tested features you have.

Your first milestone should be a clean development environment with a running Next.js frontend, FastAPI backend and PostgreSQL database. Once that foundation works, the rest of HifzTrack can be developed incrementally.

My recommendation is to keep the first Codex session dedicated entirely to repository initialization and documentation. That will give you a much more controlled starting point.