# API specification

The API uses FastAPI and Pydantic schemas; enforce access in the backend. AUTH-01 currently implements the endpoints below directly at root (no `/api/v1` prefix); later route versioning remains an open contract choice.

The original source proposes the following REST paths as an initial contract, relative to `/api/v1`; retain them as candidates pending detailed request/response schemas:

| Method | Candidate path | Purpose |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | Register and authenticate |
| GET/POST | `/auth/csrf`, `/auth/logout` | Bootstrap CSRF token; revoke current session |
| GET/PATCH | `/users/me` | Read/update own profile |
| POST/GET | `/groups` | Create and list own groups |
| GET/PATCH | `/groups/{id}` | Group detail/update |
| POST | `/groups/{id}/invitations`, `/invitations/join` | Create invitation and join |
| GET | `/groups/{id}/members` | List authorized members |
| PATCH | `/groups/{id}/members/{user_id}/sharing` | Original path suggestion; actor/ownership ambiguity is tracked as DEC-016 |
| GET | `/quran/surahs`, `/quran/ayahs` | Browse Quran reference |
| POST | `/memorization` | Submit Sabaq |
| GET | `/memorization/me`, `/memorization/me/history` | Current progress and history |
| GET/POST | `/revision/me`, `/revision` | Read history and submit session |
| GET | `/groups/{id}/progress`, `/groups/{id}/analytics` | Permission-filtered group progress and analytics |
| POST | `/assessments` | Submit authorized mentor assessment |

## Planned resource groups

| Feature | Candidate operations | Scope rules |
|---|---|---|
| AUTH-01 / USER-01 | register, login, logout, current profile, update profile | Own account only; never expose credentials/secrets. |
| QURAN-01 | list Surahs, resolve Surah/Ayah references, browse Juz/page mappings | Read-only canonical data. Full text/advanced search is an extended proposal, not P0. |
| MEM-01 | create/list/update memorization entries; read progress | Owner-only for personal detail; preserve history. |
| REV-01 | create/list revision sessions | Owner-only unless group sharing permits. |
| GROUP-01 / GROUP-02 | create/update group, invite/join/leave, list members, change roles | Membership and role scoped; administrative actions checked server-side. Join requests are an extended proposal. |
| SHARE-01 | get/update sharing settings per group | Permission owner/actor is unresolved; changes apply to subsequent reads. Never allow group admin to override a learner's privacy setting absent explicit policy. |
| DASH-01 | personal dashboard, group dashboard, member summary | Group response filtered by member sharing and viewer permission. |
| MENTOR-01/02 | assignment and assessment resources (Release 2) | Assigned scope, learner consent, and audit required. |

## Contract requirements

- Validate all input and return consistent client-safe errors without leaking private resource existence.
- Apply authorization before retrieving or serializing sensitive fields.
- Paginate potentially unbounded activity and group member collections.
- Use stable identifiers and explicit timestamps/timezone semantics once selected.
- Avoid APIs that accept a group ID as ownership for personal progress.
- Personal progress endpoints operate on the authenticated user's one central record. Group APIs return permission-filtered views of that same record, never group-specific duplicates.
- Any group/mentor route resolves the caller's role for that particular membership; a user's role in one group grants no authority in another.
- Document idempotency and conflict behavior for activity updates and future offline sync.
- Support pagination for member lists and activity history, filters for dates/Surahs/statuses, consistent error responses, and response schemas that do not expose database models directly.

Detailed OpenAPI schemas and endpoint paths are deferred until the product decisions listed in the implementation status are resolved.

AUTH-01 contract: registration accepts email, full name and a 12–256 character password; registration and login establish opaque server-side sessions. `GET /auth/csrf` issues a signed double-submit token cookie and returns the same token for `X-CSRF-Token`. Every unsafe request requires that pair and an exact configured Origin. Session cookies are Secure, HttpOnly, SameSite=Lax, path `/`; they expire after configurable 12-hour default. `GET/PATCH /users/me` acts only on the current user; only `full_name` is patchable. Logout revokes the current database session. Authentication errors avoid revealing whether a login email exists.
