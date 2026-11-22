# Security design

## Baseline controls

- Authenticate protected operations and enforce authorization on the backend for every resource and action.
- Apply least privilege to approved group roles. Organization-to-group data-model support does not establish an organization role or permission policy.
- Treat each user's per-group sharing settings as mandatory data access controls, not UI preferences.
- Use secure session handling, password hashing, input validation, and transport protection appropriate to deployment; select exact mechanisms during implementation design.
- The original source recommends Argon2id password hashing, secure HTTP-only cookies, CSRF protection for cookie sessions, and rate limits on authentication/invitation endpoints. These remain implementation selections to confirm under DEC-009; never store long-lived JWTs in browser localStorage.
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

Password hash/session recommendations are in the source, but the owner has not yet approved the exact policy. Password recovery, MFA, account deletion, retention, encryption/key management, audit access, breach response, and any future organization-role boundary are also not yet specified.
