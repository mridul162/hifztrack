# API specification

The API uses FastAPI and Pydantic schemas; enforce access in the backend. AUTH-01 and Phase 2 use root-level routes without an `/api/v1` prefix. API versioning remains a future architectural decision. The original source proposed `/api/v1` routes; Phase 2 does not retrofit that prefix.

| Method | Candidate path | Purpose |
|---|---|---|
| POST | `/auth/register`, `/auth/login` | Register and authenticate |
| GET/POST | `/auth/csrf`, `/auth/logout` | Bootstrap CSRF token; revoke current session |
| GET/PATCH | `/users/me` | Read/update own profile |
| POST/GET | `/groups` | Create group (creator becomes ACTIVE ADMIN atomically); list ACTIVE memberships |
| GET/PATCH | `/groups/{id}` | Read/update group metadata for ACTIVE members/admins |
| POST | `/groups/{id}/archive` | Archive group; revoke invitations; preserve history |
| GET | `/groups/{id}/members?limit=&offset=` | Paginated roster for ACTIVE members, minimal display fields |
| POST/GET | `/groups/{id}/invitations` | Admin create (one-time plaintext token response) and list (digest never exposed) |
| POST | `/groups/{id}/invitations/{invitation_id}/revoke` | Revoke an invitation as ACTIVE ADMIN |
| POST | `/invitations/accept` | Accept a valid invitation as authenticated user; create ACTIVE MEMBER episode |
| PATCH | `/groups/{id}/members/{membership_id}` | Admin update a member's role/state; last-active-admin invariant enforced |
| POST | `/groups/{id}/leave` | Leave own active membership; preserve LEFT episode |
| PATCH | `/groups/{id}/members/{user_id}/sharing` | Original path suggestion; actor/ownership ambiguity is tracked as DEC-016 |
| GET | `/quran/surahs` | List Surah numbers and Ayah counts; returns 503 until a complete reference import is available |
| GET | `/quran/surahs/{surah_number}/ayahs` | List canonical Ayah numbers for one Surah |
| GET | `/quran/ayahs/{surah_number}/{ayah_number}` | Resolve the stable Surah/Ayah coordinate |
| GET | `/quran/reference-source` | Read provenance, verification method and usage conditions for imported reference categories |
| POST | `/memorization` | Submit Sabaq |
| GET | `/memorization/me`, `/memorization/me/history` | Current progress and history |
| GET/POST | `/revision/me`, `/revision` | Read history and submit session |
| GET | `/groups/{id}/progress`, `/groups/{id}/analytics` | Permission-filtered group progress and analytics |
| POST | `/assessments` | Submit authorized mentor assessment |

## Planned resource groups

| Feature | Candidate operations | Scope rules |
|---|---|---|
| AUTH-01 / USER-01 | register, login, logout, current profile, update profile | Own account only; never expose credentials/secrets. |
| QURAN-01 | list Surahs/counts, list Ayah numbers, resolve Surah/Ayah references, read source provenance | Read-only numeric references. Juz/page mappings remain gated under DEC-002. No Quran text, translations or full-text search are provided in this slice. |
| MEM-01 | create/list/update memorization entries; read progress | Owner-only for personal detail; preserve history. |
| REV-01 | create/list revision sessions | Owner-only unless group sharing permits. |
| GROUP-01 / GROUP-02 | create/update group, invite/join/leave, list members, change roles | Membership and role scoped; administrative actions checked server-side. Join requests are an extended proposal. |
| SHARE-01 | get/update sharing settings per group | Permission owner/actor is unresolved; changes apply to subsequent reads. Never allow group admin to override a learner's privacy setting absent explicit policy. |
| DASH-01 | personal dashboard, group dashboard, member summary | Group response filtered by member sharing and viewer permission. |
| MENTOR-01/02 | assignment and assessment resources (Release 2) | Assigned scope, learner consent, and audit required. |

## Group authorization and invitation contract

- Every operation derives the actor from the existing AUTH-01 session and uses the existing CSRF middleware for unsafe requests.
- Only ACTIVE memberships grant access. MEMBER and MENTOR can read group details/roster and leave; only ADMIN manages metadata, invitations, and other members. Roles are group-scoped.
- Group creation and initial ADMIN membership are one transaction. Group/member reads are not granted by organization association.
- Invitation role is always MEMBER; plaintext token is returned only at creation, stored as HMAC digest, expires after seven days by default, and defaults to one successful use (API supports an explicit cap up to 100). Counters are atomic under locks.
- Invitation throttles use separate PostgreSQL HMAC counters: 10/user/hour, 30/group/hour, 20/IP/hour creation; 30/IP/15m and 10/token digest/15m acceptance. Responses are generic 429 with Retry-After.
- Roster exposes display name, membership role/state and timestamps only; no email or authentication fields.

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
