# User roles and permissions

Global user identity and group-scoped role are separate. A person may be an administrator in one group, mentor in another, and member in a third; a group may have multiple administrators and mentors. Detailed role assignment, moderation, and age-related rules remain open decisions. The original source includes a Platform Admin responsible for the whole application; its exceptional access boundary still needs policy.

| Role | Own profile/progress | Group membership | Group data |
|---|---|---|---|
| Learner/member | Read and manage own records | Join/leave groups through approved invitation flow; manage own sharing settings | Read group content and member data only as permitted by each owner and role |
| Group admin | Same as any learner | Create/manage group and membership subject to policy; multiple admins allowed | Manage group configuration; cannot override another member's private sharing choices |
| Mentor | Same as any learner | Assigned by an authorized group process | View assigned learner data only within consent and sharing policy; submit optional assessments/feedback |
| Organization administrator (proposed future role) | Not approved | No organization-level permissions or workflows are defined | Original sources support organization-to-group data-model foundation, but do not define this role or its permissions |
| Platform admin | Platform operations | Platform-level operations | Original source says manage the entire application; extent of access to private progress and break-glass process remain unresolved |

## Authorization requirements

- Authenticate every protected request and authorize it server-side.
- Apply least privilege and validate both role and resource scope.
- Treat sharing preferences as per-user, per-group controls, with privacy-conscious defaults.
- Filter or reject group reads that exceed the viewer's scope; never rely on frontend hiding.
- A membership ending revokes future group access. Retention of already-created group artifacts is an open policy question.
- Mentorship does not itself imply access beyond the learner's chosen sharing settings.
- Record sensitive role and access changes in an audit trail.
