# **HifzTrack — Refined Product Requirements & MVP Technical Design**

Based on your decisions, I recommend positioning HifzTrack as a **multi-tenant Quran memorization management platform** that supports both informal Hifz communities and structured Quran learning institutions.

The key architectural principle should be:

> Each user maintains one personal Quran memorization record. They can share selected information with multiple groups, while groups independently manage their members, mentors, targets and assessments.

This avoids duplicate records, supports flexible privacy, and makes the system extensible for institutional use.

I would keep the first release as a modular monolith using FastAPI and PostgreSQL, with a responsive web frontend.

# **1. Product requirements document (PRD)**

## **1.1 Product vision**

**Product name:** HifzTrack

**Product category:** Quran memorization progress and community management platform.

**Problem statement**

Quran memorization communities often manage progress through spreadsheets, messaging groups or manual records. This creates several problems:

- No centralized record of individual memorization progress.
- Difficulty monitoring multiple members.
- No structured distinction between new memorization and revision.
- Limited visibility into individual and group progress.
- Difficulty maintaining accountability.
- No standardized way to verify memorization through mentors.

**Proposed solution**

HifzTrack provides a centralized platform where individuals can manage their Hifz journey, share progress with selected groups, receive mentor feedback, and participate in organized memorization programs.

## **1.2 Target users**

I would design the application around two operating environments.

**A. Informal communities**

Primary MVP use case

- Friends memorizing Quran together.
- University Quran memorization circles.
- Family memorization groups.
- Online Hifz accountability communities.

Their needs:

- Simple group creation.
- Easy member invitations.
- Shared progress.
- Daily accountability.
- Group statistics.

  **B. Structured institutions**

  Supported by the data model
- Madrasas.
- Quran learning centers.
- Hifz institutions.
- Teacher-led memorization programs.

Their needs:

- Mentor/student relationships.
- Structured memorization targets.
- Student assessments.
- Group administration.
- Institutional reporting.

Important scope decision: support both audiences in the architecture, but do not build a complicated institutional management system in the MVP.

## **1.3 User roles**

There are two concepts that should be kept separate:

1. Global user identity.
2. Role within a particular group.

A person may be an administrator in one group, a mentor in another, and a regular member in a third.

| Role           | Responsibilities                             |
| -------------- | -------------------------------------------- |
| User           | Manage personal profile and memorization     |
| Group Admin    | Manage a group, memberships and settings     |
| Mentor         | Assess assigned members and provide feedback |
| Platform Admin | Manage the entire application                |

A group can have multiple administrators and mentors.

## **1.4 Functional requirements**

I recommend assigning requirement IDs so you can use them later when writing issues, implementing APIs and testing functionality.

| ID    | Requirement                               | Priority |
| ----- | ----------------------------------------- | -------- |
| FR-01 | User registration and login               | P0       |
| FR-02 | Personal profile management               | P0       |
| FR-03 | Create, update and delete groups          | P0       |
| FR-04 | Join groups using invitations             | P0       |
| FR-05 | Multiple group memberships                | P0       |
| FR-06 | Quran Surah, Ayah, Juz and page reference | P0       |
| FR-07 | Record new memorization                   | P0       |
| FR-08 | Record revision sessions                  | P0       |
| FR-09 | Calculate individual progress             | P0       |
| FR-10 | Custom group data-sharing permissions     | P0       |
| FR-11 | View shared member progress               | P0       |
| FR-12 | Individual and group dashboards           | P0       |
| FR-13 | Set individual and group targets          | P1       |
| FR-14 | Mentor assessment and feedback            | P1       |
| FR-15 | Notifications and announcements           | P1       |
| FR-16 | Historical reports and analytics          | P1       |
| FR-17 | Export progress reports                   | P2       |

P0 is the initial MVP. P1 is the next functional release. P2 is a later enhancement.

## **1.5 Non-functional requirements**

These are particularly important because you are building a multi-user application.

- **Security:** Users must not access another group's private information.
- **Authorization:** Every protected API must validate user permissions.
- **Data integrity:** Memorization records must reference valid Quran locations.
- **Auditability:** Assessment changes and important administrative actions must be traceable.
- **Scalability:** The database should support multiple groups and growing membership.
- **Maintainability:** Business logic should be separated from API routes and database access.
- **Usability:** The web application must work comfortably on mobile browsers.
- **Reliability:** Progress calculations must be deterministic and consistent.

# **2. Core business logic and data rules**

Before designing the database, establish these rules. They will influence almost every part of the application.

## **2.1 Quran reference system**

The Quran reference system should be the canonical source of truth for progress.

I recommend supporting:

- 114 Surahs.
- Ayah-level references.
- 30 Juz.
- 604 Madani Mushaf pages (using a clearly specified page-reference convention).

Each Ayah should have a stable identifier.

For example:

**Quran reference**

# **2:1–5**

Surah Al-Baqarah, Ayahs 1–5

| Reference     | Value |
| ------------- | ----- |
| Surah         | 2     |
| Starting Ayah | 1     |
| Ending Ayah   | 5     |
| Juz           | 1     |
| Mushaf page   | 2     |

Do not independently maintain memorization progress in Surah, Juz and page tables.

Instead, store canonical ranges using Surah and Ayah coordinates, then calculate Juz/page coverage through the Quran reference data.

This prevents inconsistent progress calculations.

## **2.2 Memorization status model**

Use four states:

| Status      | Definition                      |
| ----------- | ------------------------------- |
| NOT_STARTED | No memorization recorded        |
| LEARNING    | Currently learning              |
| MEMORIZED   | Initial memorization completed  |
| STRONG      | Demonstrated reliable retention |

A status transition should be controlled by business logic.

For example:

```
NOT_STARTED
     |
     v
  LEARNING
     |
     v
  MEMORIZED
     |
     v
    STRONG
```

A member can also move backward from STRONG to MEMORIZED or LEARNING when a portion becomes weak.

**Important:** STRONG should not be assigned automatically merely because someone marks a portion as memorized. It should require an explicit assessment or a defined verification rule.

## **2.3 Individual progress versus group progress**

This is the most important data-ownership decision.

Imagine:

- Mr. A has memorized Surah Al-Baqarah, Ayahs 1–100.
- Mr. A belongs to Group X and Group Y.
- He shares detailed progress with Group X.
- He shares only summary progress with Group Y.

There should be only one underlying personal progress record.

**Mr. A — Personal progress**

**Memorization record**

Surah Al-Baqarah: 1–100

**Group X**

Detailed

Can see ranges, activity and status

**Group Y**

Summary

Can see overall progress only

The sharing layer determines what each group can see. It should never create a second copy of the memorization data.

## **2.4 Assessment is separate from memorization**

A mentor assessment should be an independent record.

For example:

```
Memorization Record
    |
    |-- Self-reported status: MEMORIZED
    |
    |-- Assessment 1: NEEDS_IMPROVEMENT
    |
    |-- Assessment 2: PASSED
```

This preserves the member's submission history and the mentor's assessment history.

Also, a member can be assessed by different mentors in different groups.

# **3. Database schema design**

I recommend PostgreSQL with SQLAlchemy 2.0 and UUID primary keys.

The schema should be relational and normalized, with a clear distinction between personal data, group data, Quran reference data and assessment data.

## **3.1 Entity relationship overview**

Here is the proposed logical data model.

\#chatgpt-mermaid-\_r_4b6\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r_4b6\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_4b6\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r_4b6\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_4b6\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_4b6\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r_4b6\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r_4b6\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r_4b6\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r_4b6\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r_4b6\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r_4b6\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_4b6\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r_4b6\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r_4b6\_ p{margin:0;}#chatgpt-mermaid-\_r_4b6\_ .entityBox{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_4b6\_ .relationshipLabelBox{fill:rgb(48, 48, 48);opacity:0.7;background-color:rgb(48, 48, 48);}#chatgpt-mermaid-\_r_4b6\_ .relationshipLabelBox rect{opacity:0.5;}#chatgpt-mermaid-\_r_4b6\_ .labelBkg{background-color:rgba(48, 48, 48, 0.5);}#chatgpt-mermaid-\_r_4b6\_ .edgeLabel{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_4b6\_ .edgeLabel .label rect{fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r_4b6\_ .edgeLabel .label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_4b6\_ .edgeLabel .label{fill:rgb(31, 78, 148);font-size:14px;}#chatgpt-mermaid-\_r_4b6\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r_4b6\_ .edge-pattern-dashed{stroke-dasharray:8,8;}#chatgpt-mermaid-\_r_4b6\_ .node rect,#chatgpt-mermaid-\_r_4b6\_ .node circle,#chatgpt-mermaid-\_r_4b6\_ .node ellipse,#chatgpt-mermaid-\_r_4b6\_ .node polygon{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r_4b6\_ .relationshipLine{stroke:rgb(175, 175, 175);stroke-width:1px;fill:none;}#chatgpt-mermaid-\_r_4b6\_ .marker{fill:none!important;stroke:rgb(175, 175, 175)!important;stroke-width:1;}#chatgpt-mermaid-\_r_4b6\_ [data-look=neo].labelBkg{background-color:rgba(48, 48, 48, 0.5);}#chatgpt-mermaid-\_r_4b6\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r_4b6\_ [data-look="neo"].node rect,#chatgpt-mermaid-\_r_4b6\_ [data-look="neo"].cluster rect,#chatgpt-mermaid-\_r_4b6\_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-\_r_4b6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_4b6\_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r_4b6\_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-\_r_4b6\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r_4b6\_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_4b6\_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r_4b6\_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-\_r_4b6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_4b6\_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r_4b6\_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r_4b6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_4b6\_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r_4b6\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r_4b6\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}USERSGROUP_MEMBERSHIPSGROUPSGROUP_INVITATIONSMEMORIZATION_ENTRIESREVISION_SESSIONSUSER_AYAH_PROGRESSQURAN_AYAHSGROUP_SHARING_SETTINGSASSESSMENTSGROUP_GOALSUSER_GOALSjoinscontainscreatessubmitsrecordsownsreferencesconfiguresreceivesassessesdefinesdefines

I would organize the database into five logical domains:

1. Identity and access management.
2. Groups and memberships.
3. Quran reference and memorization.
4. Assessment and goals.
5. Notifications and reporting.

## **3.2 Table specifications**

### **A. Identity and group management**

**1.&#x20;**`users`

| Column        | Type         | Description                                        |
| ------------- | ------------ | -------------------------------------------------- |
| id            | UUID         | Primary key                                        |
| full_name     | VARCHAR(150) | User name                                          |
| email         | VARCHAR(255) | Unique, nullable if phone-based login is supported |
| phone         | VARCHAR(30)  | Unique, nullable                                   |
| password_hash | TEXT         | Hashed password                                    |
| is_active     | BOOLEAN      | Account status                                     |
| created_at    | TIMESTAMPTZ  | Registration date                                  |
| updated_at    | TIMESTAMPTZ  | Last update                                        |

Use either email or phone as a login identifier. Do not store plaintext passwords.

**2.&#x20;**`organizations`

This table provides a foundation for institutional use.

| Column      | Type         | Description      |
| ----------- | ------------ | ---------------- |
| id          | UUID         | Primary key      |
| name        | VARCHAR(200) | Institution name |
| description | TEXT         | Description      |
| created_by  | UUID         | FK → users       |
| created_at  | TIMESTAMPTZ  | Creation date    |

An informal community does not need an organization record.

**3.&#x20;**`groups`

| Column          | Type         | Description                  |
| --------------- | ------------ | ---------------------------- |
| id              | UUID         | Primary key                  |
| organization_id | UUID         | FK → organizations, nullable |
| name            | VARCHAR(200) | Group name                   |
| description     | TEXT         | Group description            |
| group_type      | ENUM         | COMMUNITY / CLASS / COHORT   |
| created_by      | UUID         | FK → users                   |
| is_active       | BOOLEAN      | Group status                 |
| created_at      | TIMESTAMPTZ  | Creation date                |

An organization can contain multiple groups.

**4.&#x20;**`group_memberships`

This is the central relationship table.

| Column    | Type        | Description                         |
| --------- | ----------- | ----------------------------------- |
| id        | UUID        | Primary key                         |
| group_id  | UUID        | FK → groups                         |
| user_id   | UUID        | FK → users                          |
| role      | ENUM        | ADMIN / MENTOR / MEMBER             |
| status    | ENUM        | PENDING / ACTIVE / SUSPENDED / LEFT |
| joined_at | TIMESTAMPTZ | Membership date                     |

Constraints:

- Unique `(group_id, user_id)`.
- Index `user_id`.
- Index `group_id`.
- Only ACTIVE memberships should grant group access.

**5.&#x20;**`group_sharing_settings`

This is where your custom sharing requirement is implemented.

| Column                  | Type        | Description                    |
| ----------------------- | ----------- | ------------------------------ |
| id                      | UUID        | Primary key                    |
| membership_id           | UUID        | Unique FK → group_memberships  |
| share_progress          | BOOLEAN     | Share overall progress         |
| share_memorization_logs | BOOLEAN     | Share new memorization records |
| share_revision_logs     | BOOLEAN     | Share revision history         |
| share_goals             | BOOLEAN     | Share personal goals           |
| share_assessments       | BOOLEAN     | Share assessment information   |
| updated_at              | TIMESTAMPTZ | Last settings update           |

This gives each member independent sharing settings for each group.

For example, the same user can enable detailed sharing in one group and disable revision-history sharing in another.

I recommend defaulting these settings to private or summary-level sharing, rather than exposing detailed information automatically.

**6.&#x20;**`group_invitations`

| Column           | Type        | Description             |
| ---------------- | ----------- | ----------------------- |
| id               | UUID        | Primary key             |
| group_id         | UUID        | FK → groups             |
| invite_code_hash | TEXT        | Hashed invitation token |
| created_by       | UUID        | FK → users              |
| expires_at       | TIMESTAMPTZ | Expiration              |
| max_uses         | INTEGER     | Optional usage limit    |
| used_count       | INTEGER     | Usage count             |
| is_active        | BOOLEAN     | Invitation status       |

Invitation codes should be random, expiring and revocable.

### **B. Quran reference and memorization**

**7.&#x20;**`quran_surahs`

| Column       | Type         | Description         |
| ------------ | ------------ | ------------------- |
| id           | SMALLINT     | Surah number, 1–114 |
| name_arabic  | VARCHAR(100) | Arabic name         |
| name_english | VARCHAR(100) | English name        |
| total_ayahs  | SMALLINT     | Number of verses    |

**8.&#x20;**`quran_ayahs`

| Column      | Type     | Description               |
| ----------- | -------- | ------------------------- |
| id          | INTEGER  | Stable Quran-wide ayah ID |
| surah_id    | SMALLINT | FK → quran_surahs         |
| ayah_number | SMALLINT | Local verse number        |
| juz_number  | SMALLINT | Juz reference             |
| page_number | SMALLINT | Mushaf page reference     |

Important constraints:

- Unique `(surah_id, ayah_number)`.
- Unique `id`.
- Validate the canonical Quran dataset during import.
- Use a documented Mushaf pagination convention.

**9.&#x20;**`memorization_entries`

This table stores what members actually submit.

| Column             | Type        | Description           |
| ------------------ | ----------- | --------------------- |
| id                 | UUID        | Primary key           |
| user_id            | UUID        | FK → users            |
| start_ayah_id      | INTEGER     | FK → quran_ayahs      |
| end_ayah_id        | INTEGER     | FK → quran_ayahs      |
| activity_date      | DATE        | Activity date         |
| notes              | TEXT        | Optional notes        |
| time_spent_minutes | INTEGER     | Time spent            |
| status             | ENUM        | SUBMITTED / CANCELLED |
| created_at         | TIMESTAMPTZ | Submission time       |

This represents a new memorization activity, not the current memorization status.

**10.&#x20;**`user_ayah_progress`

This is the current state of each user's memorization.

| Column              | Type        | Description                                 |
| ------------------- | ----------- | ------------------------------------------- |
| id                  | UUID        | Primary key                                 |
| user_id             | UUID        | FK → users                                  |
| ayah_id             | INTEGER     | FK → quran_ayahs                            |
| memorization_status | ENUM        | NOT_STARTED / LEARNING / MEMORIZED / STRONG |
| updated_at          | TIMESTAMPTZ | Last status update                          |

Constraint: unique `(user_id, ayah_id)`.

**Why have both&#x20;**`memorization_entries`**&#x20;and&#x20;**`user_ayah_progress`**?**

They serve different purposes:

- `memorization_entries` is the historical activity log.
- `user_ayah_progress` is the current state.

For example, a member may submit the same ayahs multiple times during learning. You should preserve all submissions but maintain only one current status per ayah.

A row-per-ayah approach is reasonable here: the Quran contains 6,236 ayahs, so even a user who has memorized the entire Quran has a manageable number of progress records.

**11.&#x20;**`revision_sessions`

| Column             | Type        | Description                          |
| ------------------ | ----------- | ------------------------------------ |
| id                 | UUID        | Primary key                          |
| user_id            | UUID        | FK → users                           |
| start_ayah_id      | INTEGER     | FK → quran_ayahs                     |
| end_ayah_id        | INTEGER     | FK → quran_ayahs                     |
| revision_type      | ENUM        | RECENT / OLD / FULL_JUZ / FULL_QURAN |
| activity_date      | DATE        | Revision date                        |
| time_spent_minutes | INTEGER     | Time spent                           |
| self_rating        | SMALLINT    | Optional rating, 1–5                 |
| notes              | TEXT        | Revision notes                       |
| created_at         | TIMESTAMPTZ | Creation time                        |

### **C. Assessment and goals**

**12.&#x20;**`assessments`

| Column                | Type        | Description                |
| --------------------- | ----------- | -------------------------- |
| id                    | UUID        | Primary key                |
| memorization_entry_id | UUID        | FK → memorization_entries  |
| mentor_user_id        | UUID        | FK → users                 |
| group_id              | UUID        | FK → groups                |
| result                | ENUM        | PASSED / NEEDS_IMPROVEMENT |
| feedback              | TEXT        | Mentor feedback            |
| assessed_at           | TIMESTAMPTZ | Assessment date            |

An assessment should only be accessible to authorized members of its associated group.

**13.&#x20;**`user_goals`

| Column       | Type    | Description                 |
| ------------ | ------- | --------------------------- |
| id           | UUID    | Primary key                 |
| user_id      | UUID    | FK → users                  |
| goal_type    | ENUM    | NEW_MEMORIZATION / REVISION |
| target_value | INTEGER | Target amount               |
| unit         | ENUM    | AYAHS / PAGES / JUZ         |
| start_date   | DATE    | Goal start                  |
| end_date     | DATE    | Goal end                    |
| is_active    | BOOLEAN | Goal status                 |

**14.&#x20;**`group_goals`

| Column       | Type         | Description         |
| ------------ | ------------ | ------------------- |
| id           | UUID         | Primary key         |
| group_id     | UUID         | FK → groups         |
| title        | VARCHAR(200) | Goal name           |
| target_value | INTEGER      | Collective target   |
| unit         | ENUM         | AYAHS / PAGES / JUZ |
| start_date   | DATE         | Start date          |
| end_date     | DATE         | End date            |

Group goals should represent collective targets, not a duplicate of each member's personal goal.

### **D. Later tables**

Add these when the corresponding functionality is implemented:

- `announcements`
- `notifications`
- `mentor_assignments`
- `audit_logs`
- `refresh_tokens`

For institutional use, `mentor_assignments` is particularly useful for explicitly defining which students a mentor can assess.

## **3.3 Important database design considerations**

There are four things I would handle carefully.

**1. Quran range validation**

A range must be valid in canonical Quran order.

For example, a range can span from the end of one Surah into the beginning of the next, but the start must precede the end.

Do not assume that `end_ayah_id - start_ayah_id + 1` is always a valid user input without checking the canonical reference data.

**2. Progress calculation**

Calculate progress from `user_ayah_progress`, not from the number of activity records.

For example:

\\[ \text{Memorized \\%} = \frac{\text{Memorized ayahs}}{6236}\times100 \\]

You can calculate separate percentages for MEMORIZED and STRONG.

**3. Revision does not change memorization status automatically.**

Completing a revision session means the user revised a portion. It does not prove that the portion is strong.

**4. Assessment and progress updates must be transactional.**

If a mentor's successful assessment changes a user's status, the assessment record and status update should be committed together.

For your first implementation, you can use a service-layer transaction rather than database triggers.

# **4. MVP architecture**

## **4.1 Recommended architecture**

I recommend a **modular monolith with a layered architecture**.

Do not start with microservices, message brokers, Kubernetes or complex distributed infrastructure. None of those are necessary for the initial application.

**Next.js Frontend**

Pages · Components · Forms · Dashboards

HTTPS / REST API

**FastAPI Application**

**Authentication**

Login and sessions

**Users**

Personal profiles

**Groups**

Membership and roles

**Quran**

Reference data

**Memorization**

Progress and logs

**Revision**

Revision history

**Assessments**

Mentor feedback

**Analytics**

Progress reports

**Shared application services**

Authorization · Validation · Business rules · Transactions

**PostgreSQL**

Relational data · Constraints · Indexes · Transactions

Supporting infrastructure:

- Redis: Not necessary initially.
- Background worker: Introduce when scheduled notifications become necessary.
- Object storage: Introduce when audio recordings are implemented.
- External Quran API: Not necessary; maintain your own validated reference dataset.

## **4.2 Backend project structure**

Since you are using FastAPI, SQLAlchemy and PostgreSQL, I would use the following structure:

```
hifztrack/
│
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── group.py
│   │   ├── membership.py
│   │   ├── quran.py
│   │   ├── memorization.py
│   │   ├── revision.py
│   │   └── assessment.py
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   ├── group.py
│   │   ├── memorization.py
│   │   └── assessment.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── groups.py
│   │       ├── memberships.py
│   │       ├── memorization.py
│   │       ├── revision.py
│   │       └── assessments.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── group_service.py
│   │   ├── sharing_service.py
│   │   ├── memorization_service.py
│   │   ├── revision_service.py
│   │   └── assessment_service.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── group_repository.py
│   │   └── memorization_repository.py
│   │
│   └── dependencies/
│       ├── authentication.py
│       └── permissions.py
│
├── migrations/
├── tests/
├── scripts/
│   └── seed_quran.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

This structure is a target structure, not something you need to create entirely on day one.

### **Responsibilities of the layers**

| Layer        | Responsibility                   |
| ------------ | -------------------------------- |
| API          | HTTP requests and responses      |
| Schemas      | Input/output validation          |
| Services     | Business rules and orchestration |
| Repositories | Database queries                 |
| Models       | Database structure               |
| Dependencies | Authentication and permissions   |
| Core         | Configuration and infrastructure |

For example, when a member submits new memorization:

```
POST /api/v1/memorization
          |
          v
   API Endpoint
          |
          v
   Pydantic Validation
          |
          v
   Memorization Service
          |
          |-- Validate Quran range
          |-- Validate ownership
          |-- Create activity entry
          |-- Update ayah progress
          |
          v
   Repository / SQLAlchemy
          |
          v
      PostgreSQL
```

The service should execute the activity insertion and progress update in a single database transaction.

## **4.3 Frontend structure**

For Next.js, I recommend organizing the application around user-facing features.

```
frontend/
│
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   └── register/
│   │   │
│   │   ├── dashboard/
│   │   ├── groups/
│   │   ├── memorization/
│   │   ├── revision/
│   │   ├── assessments/
│   │   └── settings/
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── dashboard/
│   │   ├── groups/
│   │   └── quran/
│   │
│   ├── features/
│   │   ├── auth/
│   │   ├── memorization/
│   │   ├── revision/
│   │   └── groups/
│   │
│   ├── lib/
│   │   ├── api-client.ts
│   │   └── utils.ts
│   │
│   └── types/
│
└── package.json
```

# **5. API design**

Design the API around business resources rather than individual database tables.

Here is the initial API contract I recommend.

| Method | Endpoint                                 | Purpose                   |
| ------ | ---------------------------------------- | ------------------------- |
| POST   | `/auth/register`                         | Register user             |
| POST   | `/auth/login`                            | Authenticate              |
| GET    | `/users/me`                              | Get personal profile      |
| PATCH  | `/users/me`                              | Update profile            |
| POST   | `/groups`                                | Create group              |
| GET    | `/groups`                                | List user's groups        |
| GET    | `/groups/{id}`                           | Group details             |
| PATCH  | `/groups/{id}`                           | Update group              |
| POST   | `/groups/{id}/invitations`               | Create invitation         |
| POST   | `/invitations/join`                      | Join group                |
| GET    | `/groups/{id}/members`                   | List members              |
| PATCH  | `/groups/{id}/members/{user_id}/sharing` | Update sharing settings   |
| GET    | `/quran/surahs`                          | List Surahs               |
| GET    | `/quran/ayahs`                           | Get Ayahs                 |
| POST   | `/memorization`                          | Submit memorization       |
| GET    | `/memorization/me`                       | Get personal progress     |
| GET    | `/memorization/me/history`               | Get activity history      |
| GET    | `/revision/me`                           | Get revision history      |
| POST   | `/revision`                              | Submit revision           |
| GET    | `/groups/{id}/progress`                  | Get shared group progress |
| POST   | `/assessments`                           | Submit mentor assessment  |
| GET    | `/groups/{id}/analytics`                 | Group analytics           |

A few API design rules:

- Use pagination for member lists and activity history.
- Use filters for dates, Surahs and statuses.
- Return consistent error responses.
- Validate resource ownership and permissions in the service layer.
- Do not expose database models directly as API responses.

## **5.1 Custom sharing authorization**

This deserves special attention.

Imagine a user requests:

```
GET /api/v1/groups/{group_id}/progress
```

The backend should:

1. Authenticate the requester.
2. Verify active membership in the group.
3. Retrieve group members.
4. Retrieve each member's sharing settings for that group.
5. Filter fields based on those settings.
6. Return only authorized information.

Example:

```
if sharing.share_progress:    response["progress"] = progress_summaryif sharing.share_memorization_logs:    response["memorization_logs"] = logsif sharing.share_revision_logs:    response["revision_logs"] = revisions
```

This is illustrative service logic, not a complete authorization implementation.

**Never rely on the frontend to hide private information.** The backend must enforce every sharing permission.

Also, sharing a mentor assessment should not automatically grant access to all private memorization notes.

## **5.2 Authentication and security**

For this application, I recommend:

- Password hashing using Argon2id.
- Secure, HTTP-only cookies for browser authentication.
- CSRF protection if using cookie-based sessions.
- Role-based authorization.
- Resource-level authorization.
- Rate limiting on authentication and invitation endpoints.
- Database transactions for important state changes.
- Audit logs for role changes, assessments and sharing changes.

If you use JWT, do not store long-lived authentication tokens in browser localStorage. A secure cookie-based approach is preferable for a browser-first product.

# **6. MVP user interface**

I would build six primary pages.

**1. Personal dashboard**

P0

[Dashboard Interface Package by Irvilani | Dribbble](https://images.openai.com/static-rsc-4/H_1jgXSFJnjAZWa_sh8woxzLldmamaR3scUO3acrTPb0h3kt-JGvSyzBAsN6vx3OsgtMn1moEW1_FLtv8dqcuXmDxpQYXGSFwXlLL65ISi3-nP_7xZY88vdpjeE0uHhhe5ZpHU5lgx5WI5a1GCY03Ky76hKpU6gZJvnWwnPIl2o?purpose=inline)

[dribbble.com](https://dribbble.com/services/60956-Dashboard-Interface-Package?utm_source=chatgpt.com)

Shows:

- Total memorized Quran progress.
- Learning and strong portions.
- Recent memorization activity.
- Recent revision activity.
- Group memberships.
- Personal goals.

  **2. Memorization tracker**

  P0

  [Quran Academy](https://images.openai.com/static-rsc-4/tTi3zdreWCAlO1EiQSY9cSrUvtWRjPiHPXW97qSQfgm_KbyTtAvBujuvO-paaaKr71NPUCKyM0eK6LwCjJqUsijOaC_skUxy5vuV0mHAtIR7DSwMCkm_LRw1JML072SrDxIxmKYW50ngL0v6UpU6h9WxjOM_if-pQekL_Tkcj3A?purpose=inline)

  [tr.quranacademy.org](https://tr.quranacademy.org/?utm_source=chatgpt.com)

  Shows:
- Surah selection.
- Starting and ending Ayah.
- Current memorization status.
- Memorization history.
- Page and Juz navigation.

  **3. Group dashboard**

  P0

  [Communeo - Dashboard Community Management System Animation by Vektora UIUX for Vektora on Dribbble](https://images.openai.com/static-rsc-4/8MXXH5Cszzm5R9ZLVr3eFCV-Efdhgb9JO1ia8l-JlDPEajIUygD6v9_jA00HIGk8q2aSec0T44gvdPPn91y-T13QeMFcKpI5IvXHz_Rvda9sKBDcZ-9I1V9nQAB0c58Eq2Hf_AogS88ZNgvKZGyVVe1XmkY08qQ-oVoCnzWOueA?purpose=inline)

  [dribbble.com](https://dribbble.com/shots/24955588-Communeo-Dashboard-Community-Management-System-Animation?utm_source=chatgpt.com)

  Shows:
- Group member count.
- Member progress.
- Recent activities.
- Group statistics.
- Announcements.

  **4. Member profile**

Displays a member's shared memorization progress, activity and other information permitted by their sharing settings.

**5. Revision tracker**

Allows members to record revision ranges, revision types, time and self-assessment.

**6. Settings and administration**

Manages memberships, roles, sharing preferences, invitations and group configuration.

One UI recommendation: use a persistent sidebar on desktop, but switch to a compact mobile navigation. The daily memorization entry workflow should take as few interactions as possible.

# **7. Development roadmap**

I would develop this in seven controlled milestones.

| Milestone | Deliverable                           | Main engineering focus           |
| --------- | ------------------------------------- | -------------------------------- |
| 1         | Authentication and user management    | Security and sessions            |
| 2         | Group creation and membership         | Relational modeling              |
| 3         | Quran reference and progress tracking | Data modeling and business logic |
| 4         | Revision tracking                     | Historical records               |
| 5         | Custom sharing and authorization      | Access control                   |
| 6         | Dashboards and analytics              | Aggregation and queries          |
| 7         | Testing and deployment                | Reliability and operations       |

### **Milestone acceptance criteria**

**Milestone 1 — Authentication**

- A user can register and log in.
- A user can update their profile.
- Users cannot access another user's private profile.

**Milestone 2 — Groups**

- A user can create multiple groups.
- A user can join multiple groups.
- Group admins can manage memberships.
- Group invitations can expire or be revoked.

**Milestone 3 — Memorization**

- A user can record a Quran range.
- Progress is calculated correctly.
- Juz and page coverage can be derived.
- Repeated submissions do not inflate progress.

**Milestone 4 — Revision**

- A user can record a revision session.
- Revision history is retained.
- Revision activity is independent of new memorization.

**Milestone 5 — Sharing**

- A user can configure sharing separately for each group.
- Private information is not exposed through group APIs.
- Leaving a group removes its access to the member's shared information.

**Milestone 6 — Analytics**

- Individual progress is accurate.
- Group statistics only include authorized shared data.
- Date-based reports are available.

**Milestone 7 — Production readiness**

- Critical services have automated tests.
- Authorization has negative test cases.
- Database migrations work.
- Docker deployment works.
- Backups and error monitoring are configured.

# **8. Critical technical decisions**

Before implementation, I would finalize these decisions.

| Decision            | Recommendation                      | Reason                                 |
| ------------------- | ----------------------------------- | -------------------------------------- |
| Architecture        | Modular monolith                    | Simpler development and deployment     |
| Progress storage    | One row per user per Ayah           | Accurate status and range calculations |
| Activity history    | Separate immutable activity records | Historical tracking                    |
| Group relationships | Many-to-many                        | Multiple groups per user               |
| Sharing             | Per-membership permissions          | Custom visibility                      |
| Verification        | Optional mentor assessments         | Supports informal and formal groups    |
| Quran references    | Internal canonical dataset          | Reliable calculations                  |
| Analytics           | SQL aggregation                     | No need for AI                         |
| Authentication      | Secure cookie-based sessions        | Browser security                       |
| Deployment          | Docker + PostgreSQL                 | Reproducible deployment                |

Three additional recommendations:

**1. Add an explicit mentor assignment relationship.**

For institutional environments, a mentor should not automatically assess every member of a group. Introduce `mentor_assignments` to define which students they supervise.

**2. Preserve progress history.**

The current `user_ayah_progress` table tells you the current status, but you should eventually add `ayah_progress_events` to preserve status changes, including who made them and why.

**3. Do not implement group-level progress by summing every member's ayah count.**

Group progress should have clearly defined metrics, such as:

- Total unique ayahs memorized across members.
- Average individual completion percentage.
- Number of members reaching specific milestones.
- Group participation rate.

These measure different things and should not be presented as interchangeable.

# **9. What I would deliberately exclude from the MVP**

To prevent scope creep, I would not initially build:

- AI recitation evaluation.
- Audio recording and playback.
- WhatsApp integration.
- Real-time chat.
- Complex gamification.
- Advanced recommendation algorithms.
- Mobile applications.
- Microservices.
- Subscription and payment systems.

None of these is necessary to validate the core product.

# **10. Immediate implementation plan**

My recommendation is to start with the database and business rules rather than designing every frontend page first.

**Initial engineering checklist**

0 of 8 completed

0%

Finalize the PRD and functional requirements

Finalize database ERD and relationships

Define Quran reference data format and source

Define memorization status transition rules

Define group sharing and authorization rules

Create FastAPI project structure

Set up PostgreSQL and Alembic migrations

Implement authentication and group membership

## **My suggested next step: finalize the database design**

I would split the next phase into three concrete deliverables:

1. `SYSTEM_REQUIREMENTS.md` — Final product requirements, user stories, functional requirements and business rules.
2. `DATABASE_DESIGN.md` — Complete ERD, table definitions, constraints, indexes and relationships.
3. `SYSTEM_ARCHITECTURE.md` — Backend architecture, frontend architecture, API boundaries, authorization and deployment design.

These documents should become the source of truth for development.

**One final architectural observation:** HifzTrack's most challenging engineering problem isn't Quran progress calculation. It's ensuring that personal progress, group membership, custom sharing permissions and mentor verification work together without exposing data incorrectly or creating inconsistent records.

I would make that the central engineering focus of this project. It will also make HifzTrack a considerably stronger demonstration of your backend and system-design capabilities.