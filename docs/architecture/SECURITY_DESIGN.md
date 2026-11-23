# Security design

## Baseline controls

- Authenticate protected operations and enforce authorization on the backend for every resource and action.
- Apply least privilege to approved group roles. Organization-to-group data-model support does not establish an organization role or permission policy.
- Treat each user's per-group sharing settings as mandatory data access controls, not UI preferences.
- Use secure session handling, password hashing, input validation, and transport protection appropriate to deployment; select exact mechanisms during implementation design.
- Approved for the future AUTH-01 milestone: email account identifier, Argon2id password hashing, server-side sessions stored in PostgreSQL, Secure/HttpOnly/SameSite cookies, and server-side logout revocation. Password recovery and MFA are deferred; preserve future extensibility. Cookie-session CSRF protection and authentication/invitation rate limits remain required security design items to specify before their affected endpoints ship. Never store long-lived JWTs in browser localStorage.
- Apply both role-based and resource-level authorization. Important state changes (including session-sensitive assessment/status operations) should run transactionally.
- Keep secrets out of source control and logs. Provide placeholders only in `.env.example`.
- Avoid returning private details in errors, group APIs, analytics, exports, notifications, or audit views.
- Audit membership, role, sharing, assessment, and other sensitive changes; define retention and access policy.

## Privacy requirements

- Personal progress remains user-owned.
- Sharing defaults to private/limited until the exact default matrix is approved.
- Leaving a group revokes subsequent access.
- Mentor assignment does not override learner sharing/consent.
- AI, audio, messaging integrations, and exports require explicit data-use and retention decisions before release.

## Threat areas to address

Cross-group data leakage, insecure direct object references, role escalation, session theft, account enumeration, abuse of invitation/join flows, export leakage, and overbroad administrator access. Add negative authorization tests for each relevant feature.

## Open security decisions

Password hashing and session policy for AUTH-01 is approved as recorded in ADR-007. Password recovery, MFA, account deletion, retention, encryption/key management, audit access, breach response, and any future organization-role boundary are not yet specified.
