# Technical Contract — Export

**Feature:** Export
**Module:** Core
**Version:** 1.0.0
**Base URL:** `/api/v1`
**Last Updated:** 2026-06-29

---

## 1. Data Models

### ExportFormat

```typescript
type ExportFormat =
  | "markdown"
  | "txt"
  | "docx"
  | "csv"
  | "json"
  | "jira_csv";
```

### ExportScope

```typescript
type ExportScope = "transcript" | "requirements" | "action_items";
```

### ExportJobStatus

```typescript
type ExportJobStatus = "queued" | "generating" | "done" | "failed" | "expired";
```

### ExportJob

```typescript
type ExportJob = {
  id: string;                  // UUID
  project_id: string;          // UUID — null for meeting-level exports
  meeting_id: string | null;   // UUID — set for transcript exports
  format: ExportFormat;
  scope: ExportScope;
  status: ExportJobStatus;
  download_url: string | null; // signed URL; set on done
  expires_at: string | null;   // ISO 8601; 1 hour after generation
  file_size_bytes: number | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;          // ISO 8601
  completed_at: string | null; // ISO 8601
};
```

### ExportRequest

```typescript
type ExportRequest = {
  format: ExportFormat;
  scope: ExportScope;
  // Future: options for filtering, template selection, etc.
};
```

---

## 2. Endpoints

### 2.1 Export Project Requirements (Phase 2)

**Trigger a server-side export job for project requirements.**

```
POST /projects/{project_id}/exports/markdown
POST /projects/{project_id}/exports/docx
POST /projects/{project_id}/exports/csv
POST /projects/{project_id}/exports/json
POST /projects/{project_id}/exports/jira-csv
```

All project export endpoints share the same response shape. Example:

```
POST /projects/{project_id}/exports/markdown
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `project_id` | `string (UUID)` | Yes | Target project |

**Request Body:** _(empty)_

**Success Response — `202 Accepted`:**

```json
{
  "job": {
    "id": "x1y2z3a4-...",
    "project_id": "p9q0r1s2-...",
    "meeting_id": null,
    "format": "markdown",
    "scope": "requirements",
    "status": "queued",
    "download_url": null,
    "expires_at": null,
    "file_size_bytes": null,
    "error_code": null,
    "error_message": null,
    "created_at": "2026-06-29T15:00:00Z",
    "completed_at": null
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `PROJECT_NOT_FOUND` | `project_id` does not exist |
| `422 Unprocessable Entity` | `NO_APPROVED_REQUIREMENTS` | Project has no approved requirements |

---

### 2.2 Get Export Job Status

**Poll the status of an export job.**

```
GET /exports/{export_job_id}
```

**Success Response — `200 OK` (job done):**

```json
{
  "job": {
    "id": "x1y2z3a4-...",
    "project_id": "p9q0r1s2-...",
    "meeting_id": null,
    "format": "markdown",
    "scope": "requirements",
    "status": "done",
    "download_url": "https://files.example.com/exports/x1y2z3a4/requirements.md?token=abc123",
    "expires_at": "2026-06-29T16:00:00Z",
    "file_size_bytes": 24576,
    "error_code": null,
    "error_message": null,
    "created_at": "2026-06-29T15:00:00Z",
    "completed_at": "2026-06-29T15:00:04Z"
  }
}
```

**Success Response — `200 OK` (job failed):**

```json
{
  "job": {
    "id": "x1y2z3a4-...",
    "status": "failed",
    "error_code": "DOCX_GENERATION_ERROR",
    "error_message": "python-docx encountered an error: ...",
    "completed_at": "2026-06-29T15:00:06Z"
  }
}
```

---

### 2.3 List Export History (Phase 2)

**Get all export jobs for a project.**

```
GET /projects/{project_id}/exports
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | `integer` | No | `1` | |
| `page_size` | `integer` | No | `20` | |

**Success Response — `200 OK`:**

```json
{
  "exports": [
    {
      "id": "x1y2z3a4-...",
      "format": "markdown",
      "scope": "requirements",
      "status": "done",
      "download_url": "...",
      "expires_at": "2026-06-29T16:00:00Z",
      "file_size_bytes": 24576,
      "created_at": "2026-06-29T15:00:00Z",
      "completed_at": "2026-06-29T15:00:04Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 5,
    "total_pages": 1
  }
}
```

---

## 3. Client-Side Export (MVP — Transcript Only)

Transcript export in MVP is generated entirely in the browser using pre-fetched segment data. No API call is made for the export itself.

**Markdown template (generated in browser):**

```
# Meeting Transcript: {meeting.title}
**Date:** {YYYY-MM-DD}
**Duration:** {HH min SS sec}

---

**[{start_formatted} → {end_formatted}]**
{edited_text || original_text}

...
```

**Plain text template:**

```
Meeting Transcript: {meeting.title}
Date: {YYYY-MM-DD} | Duration: {HH min SS sec}
============================================================

[{start_formatted} → {end_formatted}]
{edited_text || original_text}

...
```

**Download trigger:** Uses the browser's `URL.createObjectURL` + `<a download>` pattern.

---

## 4. Error Response Schema

```typescript
type ErrorResponse = {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
};
```

---

## 5. Known Error Codes

| Code | HTTP | Description |
|---|---|---|
| `PROJECT_NOT_FOUND` | 404 | Referenced project does not exist |
| `NO_APPROVED_REQUIREMENTS` | 422 | Project has no approved requirements to export |
| `EXPORT_JOB_NOT_FOUND` | 404 | Referenced export job does not exist |
| `DOCX_GENERATION_ERROR` | — | python-docx failed (job-level) |
| `CSV_GENERATION_ERROR` | — | CSV serialization failed (job-level) |

---

## 6. Implementation Notes

- **File storage:** Server-generated export files are stored under `{DATA_ROOT}/exports/{project_id}/{job_id}/`. Files are deleted after `EXPORT_TTL_HOURS` (default 24h) via a cleanup cron job.
- **Download URL:** For MVP server exports, the download URL is a direct path on the FastAPI server protected by a short-lived token. Phase 2 should use object storage (S3/MinIO) for scalability.
- **Numbering:** Requirement IDs in exports (FR-001, NFR-001, etc.) are generated at export time based on `approved_at` order; they are not stored as persistent identifiers.
- **Jira CSV:** The Jira CSV format follows Jira's "CSV External System Import" format. Column names must match exactly: `Summary`, `Description`, `Issue Type`, `Priority`.
