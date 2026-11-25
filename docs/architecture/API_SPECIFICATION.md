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
| GET/PATCH | `/groups/{group_id}/sharing/me` | Get or update the authenticated owner's active membership settings; target user and membership IDs are not accepted. Archived groups are read-only for settings changes. |
| GET | `/quran/surahs` | List Surah numbers and Ayah counts plus available `name_ar` and `name_latin` fields |
| GET | `/quran/surahs/{surah_number}/ayahs` | List canonical Ayah numbers for one Surah |
| GET | `/quran/ayahs/{surah_number}/{ayah_number}` | Resolve the stable Surah/Ayah coordinate |
| GET | `/quran/reference-source` | Read provenance, verification method and usage conditions for imported reference categories |
| GET | `/quran/metadata-availability` | Read Boolean availability for Arabic names, Latin names, Juz mappings and Mushaf pages |
| GET | `/quran/juzs` | List all 30 ordered Juz with inclusive canonical ranges in `{juzs}` |
| GET | `/quran/juzs/{juz_number}` | Resolve one Juz to its inclusive canonical range |
| GET | `/quran/ayahs/{surah_number}/{ayah_number}/juz` | Resolve a canonical Ayah to its Juz |
| GET | `/quran/pages` | List all 604 ordered pages with inclusive canonical ranges and edition |
| GET | `/quran/pages/{page_number}` | Resolve one page to its inclusive canonical range and edition |
| GET | `/quran/ayahs/{surah_number}/{ayah_number}/page` | Resolve a canonical Ayah to its page in the approved edition |
| GET | `/memorization/progress?surah_number=` | Read the authenticated user's saved Ayah statuses (omitted rows mean NOT_STARTED) |
| PUT | `/memorization/progress/{surah_number}/{ayah_number}` | Explicitly set one owned Ayah status; STRONG requires confirmation |
| POST/GET | `/memorization/submissions?limit=&offset=` | Submit Sabaq or read the authenticated user's paginated history |
| POST | `/memorization/submissions/{entry_id}/cancel` | Cancel an owned submitted entry while preserving history |
| POST | `/memorization/submissions/{entry_id}/correct` | Atomically cancel an owned entry and add its corrected replacement |
| GET/POST | `/revision/me`, `/revision` | List the authenticated user's revision history and submit a session; revision records are immutable after creation (ADR-017). |
| GET | `/dashboard/me?activity_limit=` | Current user's progress, recent Sabaq and revision, and active memberships |
| GET | `/groups/{group_id}/dashboard?limit=&offset=&activity_limit=` | Active roster, permitted progress and activity, and average completion with contributor count |
| GET | `/groups/{group_id}/members/{membership_id}/shared?limit=&offset=` | Read allowlisted fields for an ACTIVE membership, if the viewer is ACTIVE in the same group; notes are never returned. |
| POST | `/assessments` | Submit authorized mentor assessment |

## Planned resource groups

| Feature | Candidate operations | Scope rules |
|---|---|---|
| AUTH-01 / USER-01 | register, login, logout, current profile, update profile | Own account only; never expose credentials/secrets. |
| QURAN-01 | Surah/Ayah, metadata availability, Juz and Madani page lookup in both directions, and source provenance | Read-only. Categories are available only when their provenance and stored values match the approved version. |
| MEM-01 | read/update Ayah status; create/list/cancel/correct Sabaq submissions | Owner-only from the authenticated session; numeric canonical references only; activity and current status are independent; submission history is paginated and preserved. |
| REV-01 | `POST /revision`, `GET /revision/me?limit=&offset=` | Owner-only append and list operations. Group revision reads follow SHARE-01 settings. |
| GROUP-01 / GROUP-02 | create/update group, invite/join/leave, list members, change roles | Membership and role scoped; administrative actions checked server-side. Join requests are an extended proposal. |
| SHARE-01 | `GET/PATCH /groups/{group_id}/sharing/me`; `GET /groups/{group_id}/members/{membership_id}/shared` | Only the owner may change their own settings; ADMIN and MENTOR roles cannot change another member's settings. ACTIVE group members of any role can read only the fields enabled by the owner's settings. PENDING, SUSPENDED, and LEFT memberships cannot access shared data. Filter in backend before serialization; frontend hiding is not authorization. Shared activity accepts bounded `limit`/`offset` pagination. |
| DASH-01 / ANALYTICS-01 | `GET /dashboard/me`, `GET /groups/{group_id}/dashboard` | Read-only owner and group views under ADR-019. Group metrics and activity follow SHARE-01. |
| MENTOR-01/02 | assignment and assessment resources (Release 2) | Assigned scope, learner consent, and audit required. |

Each Juz has `juz_number`, `start` and `end`. The page list returns `{edition, pages}`. Single page and inverse page lookups return `{edition, page}`. Each page has `page_number`, `start` and `end`. Both endpoints of each range carry `surah_number` and `ayah_number`. The edition contains `id: "madani-1441h-hafs"`, its display `name`, `source_url`, `license_url` and `attribution`.

Missing, incomplete or inconsistent mappings return 503. Invalid page and Juz numbers and unknown canonical Ayahs return 404 after the applicable checks. If a name category is unavailable, `/quran/surahs` omits that field across the response and continues serving numeric coordinates. The Boolean availability endpoint reports each category independently. Name and Juz responses link to attribution at `/quran/reference-source`; the available source records use `SURAH_AYAH_ORDER`, `SURAH_NAMES_AR`, `SURAH_NAMES_LATIN`, `JUZ_BOUNDARIES` and `MUSHAF_PAGES`.

## Dashboard response contracts

- `GET /dashboard/me` uses the authenticated session without a target-user parameter. Returns `progress` with `total_memorized_ayahs`, `completion_percentage`, and `status_counts` (`not_started`, `learning`, `memorized`, `strong`). `recent_sabaq` and `recent_revision` use the existing owner history response fields. `memberships` lists active episodes with `group_id`, `group_name`, `role`, and `lifecycle`, including archived groups that can still be opened.
- `GET /groups/{group_id}/dashboard` requires an ACTIVE membership in that group. An unauthenticated request returns HTTP 401. A non-active viewer or inaccessible group returns HTTP 404. Archived groups remain readable by ACTIVE members.
- Group response fields are `active_member_count`, `members`, `member_limit`, `member_offset`, `average_completion_percentage`, `contributor_count`, `recent_sabaq`, and `recent_revision`. `members` contains `membership_id`, `display_name`, `role`, and `progress`. Progress includes only `total_memorized_ayahs` and `completion_percentage` when `SUMMARY` or `DETAILED` is permitted. It is `null` for private or unavailable progress. The group average is `null` when the contributor count is zero.
- The roster defaults to `limit=50` and `offset=0` with a maximum limit of 100. It is ordered by membership creation time and ID ascending. Counts, average, and recent shared histories cover the whole group regardless of roster page.
- A group activity item contains `membership_id`, `display_name`, and `log`. Sabaq log fields are Surah/Ayah range, `created_at`, and record `status`. Revision log fields are range, `revision_type`, `activity_date`, `time_spent_minutes`, and `self_rating`. The lists include eligible records only, with the same independent sharing controls as SHARE-01.
- Each activity list defaults to 5 entries and allows `activity_limit` from 1 to 20. Personal histories and group revision sort by activity date, creation timestamp, then record ID descending. Group Sabaq sorts by submission creation timestamp and record ID descending, like the shared-member view. Preserved cancelled Sabaq entries retain their record status. Empty histories are empty arrays.
- Dashboard reads that calculate progress return HTTP 503 if the canonical Ayah reference set is incomplete. A group with zero eligible contributors can still return the roster and permitted activity. Successful responses include `Cache-Control: private, no-store`.

## Group authorization and invitation contract

- Every operation derives the actor from the existing AUTH-01 session and uses the existing CSRF middleware for unsafe requests.
- Only ACTIVE memberships grant access. MEMBER and MENTOR can read group details/roster and leave; only ADMIN manages metadata, invitations, and other members. Roles are group-scoped.
- Group creation and initial ADMIN membership are one transaction. Group/member reads are not granted by organization association.
- Invitation role is always MEMBER; plaintext token is returned only at creation, stored as HMAC digest, expires after seven days by default, and defaults to one successful use (API supports an explicit cap up to 100). Counters are atomic under locks.
- Invitation throttles use separate PostgreSQL HMAC counters: 10/user/hour, 30/group/hour, 20/IP/hour creation; 30/IP/15m and 10/token digest/15m acceptance. Responses are generic 429 with Retry-After.
- Roster exposes display name, membership role/state and timestamps only; no email or authentication fields.

## Contract requirements

- Validate all input and return consistent client-safe errors without leaking private resource existence.
- A concurrent first-time write to the same user's Ayah status is protected by the composite primary key; the losing request receives 409 and may retry. Concurrent updates to an existing row serialize on its row lock. Only one concurrent cancellation/correction of a submission succeeds; later attempts receive 409.
- Apply authorization before retrieving or serializing sensitive fields.
- Paginate potentially unbounded activity and group member collections.
- Use stable identifiers and explicit timestamps/timezone semantics once selected.
- Avoid APIs that accept a group ID as ownership for personal progress.
- Personal progress endpoints operate on the authenticated user's one central record. Group APIs return permission-filtered views of that same record, never group-specific duplicates.
- Any group/mentor route resolves the caller's role for that particular membership; a user's role in one group grants no authority in another.
- Sharing settings are resolved for the specific membership episode. Overall progress is `PRIVATE`, `SUMMARY` (total memorized Ayahs and percentage of 6,236 only), or `DETAILED` (Surah/Ayah identifiers and current Ayah status only). Independent Boolean controls govern memorization logs, revision logs, goals, and assessments. All default false; overall progress defaults `SUMMARY` for each new episode.
- Only the owner may update their own settings. Active membership, not role, determines audience: all ACTIVE members can access enabled fields; PENDING, SUSPENDED, and LEFT members cannot. Changes govern eligible historical and future records and apply to subsequent requests. An old episode's settings are not restored on rejoin.
- Sharing response fields follow `docs/04_BUSINESS_RULES.md`; private notes are excluded. Sharing does not grant edit/delete permission over personal records. Already viewed, downloaded, or copied data cannot be withdrawn retroactively.
- The shared-member response omits disabled categories. `PRIVATE` omits progress fields; `SUMMARY` returns only total memorized Ayahs and percentage; `DETAILED` returns current status per canonical Ayah, including implicit `NOT_STARTED`. Detailed progress returns 503 until all 6,236 canonical Quran Ayah references are loaded. Memorization logs expose only range, submission timestamp, and record status; revision logs expose only range, type, activity date, duration, and optional self-rating. Goals and assessments are stored as preferences only; their P1 records/workflows are not implemented.
- Document idempotency and conflict behavior for activity updates and future offline sync.
- Support pagination for member lists and activity history, filters for dates/Surahs/statuses, consistent error responses, and response schemas that do not expose database models directly.

FastAPI publishes the response schemas for implemented endpoints in OpenAPI. Planned endpoints remain subject to the open product decisions.

AUTH-01 contract: registration accepts email, full name and a 12–256 character password; registration and login establish opaque server-side sessions. `GET /auth/csrf` issues a signed double-submit token cookie and returns the same token for `X-CSRF-Token`. Every unsafe request requires that pair and an exact configured Origin. Session cookies are Secure, HttpOnly, SameSite=Lax, path `/`; they expire after configurable 12-hour default. `GET/PATCH /users/me` acts only on the current user; only `full_name` is patchable. Logout revokes the current database session. Authentication errors avoid revealing whether a login email exists.
