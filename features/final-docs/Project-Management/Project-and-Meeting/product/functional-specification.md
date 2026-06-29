# Functional Specification — Project & Meeting Management

**Feature:** Project & Meeting Management
**Module:** Project Management
**Version:** 1.0.0
**Phase:** MVP
**Last Updated:** 2026-06-29
**Status:** In Review

---

## 1. Summary

Project & Meeting Management is the organizational layer of the BA Requirement Tool. A **Project** represents a product, engagement, or initiative (e.g. "E-commerce Redesign 2026"). A **Meeting** represents a single recorded session within that project. All other features — media upload, transcription, extraction, review, and export — operate within the context of a meeting and its parent project.

---

## 2. Goals

- Provide a clear, navigable hierarchy: Project → Meeting → Transcript → Requirements.
- Allow BAs to manage multiple projects and meetings without confusion.
- Track the status of each meeting through its full processing lifecycle so the BA always knows what step comes next.

---

## 3. Non-Goals

- This feature does **not** manage user accounts or permissions (single-user MVP).
- This feature does **not** integrate with external project management tools (future Jira/Linear integration).
- This feature does **not** support bulk import of meetings from a calendar feed (future).
- This feature does **not** provide analytics or reporting on project-level metrics (future).

---

## 4. Users

| Persona | Need |
|---|---|
| **BA (primary)** | Create projects per engagement, create meeting records per session, navigate between them |
| **Project Manager** | View project list and meeting statuses to understand BA progress |

---

## 5. Functional Requirements

### FR-PM-001 — Create Project

**Description:** A BA can create a new project with a name and optional description.

**Acceptance Criteria:**
- AC-PM-001-1: A project requires a `name` (non-empty string, max 200 chars).
- AC-PM-001-2: `description` is optional (max 2,000 chars).
- AC-PM-001-3: Project `name` must be unique per user (case-insensitive in MVP single-user context).
- AC-PM-001-4: On creation, the project `status` is set to `active` and `created_at` is recorded.
- AC-PM-001-5: The response includes the full `Project` object with the generated `id`.

---

### FR-PM-002 — List Projects

**Description:** A BA can view all their projects in a list.

**Acceptance Criteria:**
- AC-PM-002-1: `GET /projects` returns all non-archived projects ordered by `updated_at` descending.
- AC-PM-002-2: Each project in the list includes: `id`, `name`, `description`, `status`, `meeting_count`, `created_at`, `updated_at`.
- AC-PM-002-3: An optional `q` query parameter filters projects by name (case-insensitive substring match).
- AC-PM-002-4: An optional `status` query parameter filters by `active` or `archived`.
- AC-PM-002-5: Results are paginated with a default `page_size` of 20.

---

### FR-PM-003 — View Project

**Description:** A BA can view the detail of a single project including its meeting list.

**Acceptance Criteria:**
- AC-PM-003-1: `GET /projects/{id}` returns the full `Project` object.
- AC-PM-003-2: The project detail includes a summary of meetings: `meeting_count`, and counts by status (`draft`, `uploaded`, `transcribed`, etc.).
- AC-PM-003-3: If the project does not exist or is hard-deleted, return HTTP 404 with `PROJECT_NOT_FOUND`.

---

### FR-PM-004 — Archive Project

**Description:** A BA can archive a project to remove it from the active list.

**Acceptance Criteria:**
- AC-PM-004-1: `PATCH /projects/{id}` with `{"status": "archived"}` sets the project `status` to `archived`.
- AC-PM-004-2: Archived projects do not appear in the default `GET /projects` list (unless `status=archived` filter is applied).
- AC-PM-004-3: Archiving a project does not delete its meetings or requirements.
- AC-PM-004-4: An archived project can be restored by patching `{"status": "active"}`.

---

### FR-PM-005 — Create Meeting

**Description:** A BA creates a meeting record within a project.

**Acceptance Criteria:**
- AC-PM-005-1: `POST /projects/{id}/meetings` requires a `title` (non-empty string, max 200 chars).
- AC-PM-005-2: Optional fields: `description` (max 2,000 chars), `meeting_date` (ISO 8601 date string, defaults to `created_at` date if omitted).
- AC-PM-005-3: The meeting `status` is initialized to `draft`.
- AC-PM-005-4: If the parent project is `archived`, creating a meeting within it returns HTTP 422 with `PROJECT_ARCHIVED`.
- AC-PM-005-5: The response includes the full `Meeting` object.

---

### FR-PM-006 — List Meetings in Project

**Description:** A BA can list all meetings within a project.

**Acceptance Criteria:**
- AC-PM-006-1: `GET /projects/{id}/meetings` returns all non-archived meetings ordered by `meeting_date` descending (most recent first).
- AC-PM-006-2: Each meeting includes: `id`, `title`, `description`, `status`, `meeting_date`, `created_at`, `updated_at`, and whether a media file exists (`has_media: boolean`).
- AC-PM-006-3: An optional `q` query parameter filters by meeting title.
- AC-PM-006-4: An optional `status` query parameter filters by meeting status.
- AC-PM-006-5: Results are paginated with a default `page_size` of 20.

---

### FR-PM-007 — Meeting Status Lifecycle

**Description:** Meeting status transitions through well-defined states driven by downstream actions.

**Valid statuses and transitions:**

| Status | Meaning | Transition trigger |
|---|---|---|
| `draft` | Meeting created, no media | Initial state on creation |
| `uploaded` | Media file attached | Media upload success |
| `processing` | STT job active | Process job starts |
| `transcribed` | Transcript available | Process job completes successfully |
| `extracting` | LLM extraction running | Extraction job starts |
| `extraction_done` | Candidates available | Extraction job completes |
| `reviewed` | All candidates reviewed | All candidates have `approved` or `rejected` status |
| `failed` | Processing or extraction error | Job failure |

**Acceptance Criteria:**
- AC-PM-007-1: Status transitions are driven by backend processes; the status is not directly writable by the client.
- AC-PM-007-2: The meeting status is included in all list and detail responses.
- AC-PM-007-3: The UI uses the meeting status to determine which actions are available (e.g. "Process" button only shown when status is `uploaded`).

---

### FR-PM-008 — Archive Meeting

**Description:** A BA can archive a meeting to hide it from the default list.

**Acceptance Criteria:**
- AC-PM-008-1: `PATCH /meetings/{id}` with `{"status": "archived"}` sets the meeting status.
- AC-PM-008-2: Only meetings in terminal states (`transcribed`, `extraction_done`, `reviewed`, `failed`) can be archived.
- AC-PM-008-3: Archiving a meeting that is in `processing` or `extracting` state returns HTTP 422 with `JOB_STILL_ACTIVE`.

---

## 6. MVP vs Phase 2 Scope

| Capability | MVP | Phase 2 |
|---|---|---|
| Create / list / view projects | ✅ | ✅ |
| Create / list / view meetings | ✅ | ✅ |
| Meeting status lifecycle | ✅ | ✅ |
| Archive / restore project & meeting | ✅ | ✅ |
| Search by name | ✅ | ✅ |
| User accounts & authentication | ❌ | ✅ |
| Team / collaborator access | ❌ | ✅ |
| Meeting tags / custom metadata | ❌ | ✅ |
| Calendar integration | ❌ | Future |
| Project templates | ❌ | Future |

---

## 7. Constraints & Assumptions

- MVP is single-user; no authentication or authorization layer. All data is accessible without a login token.
- Project names are unique globally (single user context); Phase 2 will scope uniqueness per user.
- Meeting dates default to the day the meeting record is created if not provided.
- Hard deletion is not supported in MVP; archive is the only "removal" mechanism.
