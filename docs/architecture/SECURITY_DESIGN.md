# Security design

## Baseline controls

- Authenticate protected operations and enforce authorization on the backend for every resource and action.
- Apply least privilege to approved group roles. Organization-to-group data-model support does not establish an organization role or permission policy.
- Treat each user's per-group sharing settings as mandatory data access controls, not UI preferences.
- Use secure session handling, password hashing, input validation, and transport protection appropriate to deployment; select exact mechanisms during implementation design.
- AUTH-01 owner-approved controls: email identifier; Argon2id; opaque PostgreSQL-backed server sessions; Secure, HttpOnly, SameSite session cookie; server-side logout revocation; password recovery and MFA deferred. The session lifetime defaults to 12 hours and is configurable. Never store browser authentication tokens in localStorage.
- Unsafe requests require a signed double-submit CSRF cookie/header pair and an exact Origin matching configured CORS origins. The CSRF cookie is JavaScript-readable; the session cookie remains HttpOnly. Missing/invalid Origin or token is rejected; Referer alone is not accepted.
- Authentication rate limits use atomic fixed 15-minute PostgreSQL counters keyed by HMAC digests of client IP and normalized email: 5 registrations/IP, 10 logins/IP+email, and 30 logins/IP. Responses are generic 429 with Retry-After; accounts are not locked. Expired counters are cleaned during auth attempts. Invitation throttling remains for the group milestone.
- Apply both role-based and resource-level authorization. Important state changes (including session-sensitive assessment/status operations) should run transactionally.
- Keep secrets out of source control and logs. Provide placeholders only in `.env.example`.
- Avoid returning private details in errors, group APIs, analytics, exports, notifications, or audit views.
- Audit membership, role, sharing, assessment, and other sensitive changes; define retention and access policy.

## Privacy requirements

- Personal progress remains user-owned.
- Sharing uses the owner-approved membership-specific defaults and field matrix in DEC-006/016/023 and ADR-018. The backend enforces the owner's settings for every request; group roles cannot override them, and only ACTIVE memberships can access enabled shared fields.
- SHARE-01 uses the self-scoped settings route `/groups/{group_id}/sharing/me`; it cannot target another owner's settings. Shared-member reads validate both the viewer's ACTIVE membership and the target's ACTIVE membership in the same group before filtering allowed fields. Settings changes lock the group and the owner's membership to serialize with archive/leave operations.
- Leaving a group revokes subsequent access.
- Mentor assignment does not override learner sharing/consent.
- AI, audio, messaging integrations, and exports require explicit data-use and retention decisions before release.

## Threat areas to address

Cross-group data leakage, insecure direct object references, role escalation, session theft, account enumeration, abuse of invitation/join flows, export leakage, and overbroad administrator access. Add negative authorization tests for each relevant feature.

## Open security decisions

Password hashing and session policy for AUTH-01 is approved as recorded in ADR-007. Password recovery, MFA, account deletion, retention, encryption/key management, audit access, breach response, and any future organization-role boundary are not yet specified.
