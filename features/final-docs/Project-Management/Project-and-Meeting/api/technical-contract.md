# Technical Contract — Project & Meeting Management

**Feature:** Project & Meeting Management
**Module:** Project Management
**Version:** 1.0.0
**Base URL:** `/api/v1`
**Last Updated:** 2026-06-29

---

## 1. Data Models

### ProjectStatus

```typescript
type ProjectStatus = "active" | "archived";
```

### Project

```typescript
type Project = {
  id: string;              // UUID
  name: string;            // max 200 chars
  description: string | null; // max 2000 chars
  status: ProjectStatus;
  meeting_count: number;   // total (including archived)
  active_meeting_count: number; // non-archived meetings
  created_at: string;      // ISO 8601
  updated_at: string;      // ISO 8601
};
```

### MeetingStatus

```typescript
type MeetingStatus =
  | "draft"
  | "uploaded"
  | "processing"
  | "transcribed"
  | "extracting"
  | "extraction_done"
  | "reviewed"
  | "failed"
  | "archived";
```

### Meeting

```typescript
type Meeting = {
  id: string;              // UUID
  project_id: string;      // UUID
  title: string;           // max 200 chars
  description: string | null; // max 2000 chars
  status: MeetingStatus;
  meeting_date: string;    // ISO 8601 date, e.g. "2026-06-29"
  has_media: boolean;      // true if a MediaFile is attached
  segment_count: number;   // 0 until transcribed
  candidate_count: number; // 0 until extraction done
  approved_count: number;  // approved RequirementCandidates
  created_at: string;      // ISO 8601
  updated_at: string;      // ISO 8601
};
```

### ProjectCreateRequest

```typescript
type ProjectCreateRequest = {
  name: string;            // required, max 200 chars
  description?: string;   // optional, max 2000 chars
};
```

### MeetingCreateRequest

```typescript
type MeetingCreateRequest = {
  title: string;           // required, max 200 chars
  description?: string;   // optional, max 2000 chars
  meeting_date?: string;  // optional ISO 8601 date; defaults to today
};
```

### PatchRequest (generic status patch)

```typescript
type StatusPatchRequest = {
  status: "active" | "archived";
};
```

---

## 2. Endpoints

### 2.1 Create Project

```
POST /projects
Content-Type: application/json
```

**Request Body:**

```json
{
  "name": "E-commerce Redesign 2026",
  "description": "Full redesign of the storefront for the 2026 Q3 launch."
}
```

**Success Response — `201 Created`:**

```json
{
  "project": {
    "id": "p9q0r1s2-...",
    "name": "E-commerce Redesign 2026",
    "description": "Full redesign of the storefront for the 2026 Q3 launch.",
    "status": "active",
    "meeting_count": 0,
    "active_meeting_count": 0,
    "created_at": "2026-06-29T09:00:00Z",
    "updated_at": "2026-06-29T09:00:00Z"
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `422 Unprocessable Entity` | `NAME_REQUIRED` | `name` is empty or missing |
| `422 Unprocessable Entity` | `NAME_TOO_LONG` | `name` exceeds 200 characters |
| `409 Conflict` | `PROJECT_NAME_TAKEN` | A project with this name already exists |

---

### 2.2 List Projects

```
GET /projects
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `q` | `string` | No | — | Case-insensitive name filter |
| `status` | `string` | No | `active` | `active` or `archived` |
| `page` | `integer` | No | `1` | |
| `page_size` | `integer` | No | `20` | Max 100 |

**Success Response — `200 OK`:**

```json
{
  "projects": [
    {
      "id": "p9q0r1s2-...",
      "name": "E-commerce Redesign 2026",
      "description": "...",
      "status": "active",
      "meeting_count": 5,
      "active_meeting_count": 4,
      "created_at": "2026-06-29T09:00:00Z",
      "updated_at": "2026-06-29T14:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 3,
    "total_pages": 1
  }
}
```

---

### 2.3 Get Project

```
GET /projects/{project_id}
```

**Success Response — `200 OK`:**

```json
{
  "project": {
    "id": "p9q0r1s2-...",
    "name": "E-commerce Redesign 2026",
    "description": "...",
    "status": "active",
    "meeting_count": 5,
    "active_meeting_count": 4,
    "created_at": "2026-06-29T09:00:00Z",
    "updated_at": "2026-06-29T14:00:00Z"
  },
  "meeting_status_summary": {
    "draft": 1,
    "uploaded": 0,
    "processing": 0,
    "transcribed": 2,
    "extraction_done": 1,
    "reviewed": 0,
    "failed": 0,
    "archived": 1
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `PROJECT_NOT_FOUND` | Project does not exist |

---

### 2.4 Patch Project (archive / restore)

```
PATCH /projects/{project_id}
Content-Type: application/json
```

**Request Body:**

```json
{ "status": "archived" }
```

**Success Response — `200 OK`:**

```json
{
  "project": { "id": "p9q0r1s2-...", "status": "archived", "updated_at": "..." }
}
```

---

### 2.5 Create Meeting

```
POST /projects/{project_id}/meetings
Content-Type: application/json
```

**Request Body:**

```json
{
  "title": "Sprint Review 2026-06-29",
  "description": "End of Sprint 12 review with product and engineering.",
  "meeting_date": "2026-06-29"
}
```

**Success Response — `201 Created`:**

```json
{
  "meeting": {
    "id": "b2e1a3c4-...",
    "project_id": "p9q0r1s2-...",
    "title": "Sprint Review 2026-06-29",
    "description": "End of Sprint 12 review with product and engineering.",
    "status": "draft",
    "meeting_date": "2026-06-29",
    "has_media": false,
    "segment_count": 0,
    "candidate_count": 0,
    "approved_count": 0,
    "created_at": "2026-06-29T09:05:00Z",
    "updated_at": "2026-06-29T09:05:00Z"
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `PROJECT_NOT_FOUND` | Parent project does not exist |
| `422 Unprocessable Entity` | `PROJECT_ARCHIVED` | Cannot add meetings to an archived project |
| `422 Unprocessable Entity` | `TITLE_REQUIRED` | `title` is missing or empty |
| `422 Unprocessable Entity` | `INVALID_DATE` | `meeting_date` is not a valid ISO 8601 date |

---

### 2.6 List Meetings in Project

```
GET /projects/{project_id}/meetings
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `q` | `string` | No | — | Title filter |
| `status` | `string` | No | — | Filter by `MeetingStatus` |
| `page` | `integer` | No | `1` | |
| `page_size` | `integer` | No | `20` | Max 100 |

**Success Response — `200 OK`:**

```json
{
  "meetings": [
    {
      "id": "b2e1a3c4-...",
      "project_id": "p9q0r1s2-...",
      "title": "Sprint Review 2026-06-29",
      "status": "transcribed",
      "meeting_date": "2026-06-29",
      "has_media": true,
      "segment_count": 47,
      "candidate_count": 0,
      "approved_count": 0,
      "created_at": "2026-06-29T09:05:00Z",
      "updated_at": "2026-06-29T10:04:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 4,
    "total_pages": 1
  }
}
```

---

### 2.7 Patch Meeting

```
PATCH /meetings/{meeting_id}
Content-Type: application/json
```

Supports updating `title`, `description`, `meeting_date`, or `status` (to `archived` only).

**Request Body examples:**

```json
{ "title": "Sprint Review — June 2026" }
```

```json
{ "status": "archived" }
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `MEETING_NOT_FOUND` | Meeting does not exist |
| `422 Unprocessable Entity` | `JOB_STILL_ACTIVE` | Cannot archive a meeting with an active job |

---

## 3. Known Error Codes

| Code | HTTP | Description |
|---|---|---|
| `PROJECT_NOT_FOUND` | 404 | Referenced project does not exist |
| `PROJECT_NAME_TAKEN` | 409 | Project name is already in use |
| `PROJECT_ARCHIVED` | 422 | Cannot add meetings to an archived project |
| `NAME_REQUIRED` | 422 | `name` is empty or missing |
| `NAME_TOO_LONG` | 422 | `name` exceeds 200 characters |
| `MEETING_NOT_FOUND` | 404 | Referenced meeting does not exist |
| `TITLE_REQUIRED` | 422 | Meeting `title` is empty or missing |
| `INVALID_DATE` | 422 | `meeting_date` is not a valid date |
| `JOB_STILL_ACTIVE` | 422 | Cannot archive a meeting with an active processing job |

---

## 4. Implementation Notes

- **meeting_count vs active_meeting_count:** `meeting_count` includes archived meetings; `active_meeting_count` excludes them. Useful for displaying "5 meetings (1 archived)".
- **Status is server-controlled:** `MeetingStatus` is set by the backend based on job outcomes; the only client-writable status value is `archived`.
- **Soft archive:** Both `Project` and `Meeting` use an `archived_at` timestamp column (null = not archived) rather than a status enum for the archive state, allowing clean filtering with `WHERE archived_at IS NULL`.
- **Pagination defaults:** `page_size` defaults to 20 for both projects and meetings. Maximum is 100 for lists and 500 for transcript segments.
