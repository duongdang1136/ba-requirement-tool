# Technical Contract — Meeting Processing

**Feature:** Meeting Processing
**Module:** Core
**Version:** 1.0.0
**Base URL:** `/api/v1`
**Last Updated:** 2026-06-29

---

## 1. Data Models

### MediaFile

```typescript
type MediaFile = {
  id: string;                   // UUID
  meeting_id: string;           // UUID — parent meeting
  original_filename: string;    // e.g. "standup-2026-06-29.mp3"
  mime_type: string;            // "audio/mpeg" | "audio/wav" | "audio/x-m4a" | "video/mp4"
  file_size_bytes: number;      // raw file size
  storage_path: string;         // server-side path (relative to data root)
  normalized_path: string | null; // path to WAV normalized copy; null until normalization done
  status: "uploaded" | "normalized" | "failed";
  uploaded_at: string;          // ISO 8601
  updated_at: string;           // ISO 8601
};
```

### ProcessingJob

```typescript
type ProcessingJobStatus =
  | "queued"
  | "normalizing"
  | "transcribing"
  | "done"
  | "failed";

type ProcessingJob = {
  id: string;                   // UUID
  meeting_id: string;           // UUID
  status: ProcessingJobStatus;
  error_code: string | null;    // e.g. "FFMPEG_ERROR", "MODEL_NOT_FOUND", "STT_TIMEOUT"
  error_message: string | null; // human-readable description
  queued_at: string;            // ISO 8601
  started_at: string | null;   // ISO 8601 — when processing began
  completed_at: string | null; // ISO 8601 — terminal state timestamp
};
```

### TranscriptSegment (produced by processing)

```typescript
type TranscriptSegment = {
  id: string;             // UUID
  meeting_id: string;     // UUID
  sequence_index: number; // 0-based ordering
  start: number;          // seconds (float, e.g. 12.34)
  end: number;            // seconds (float)
  speaker_id: string | null; // null in MVP (Phase 2: speaker diarization)
  original_text: string;  // raw STT output
  edited_text: string | null; // null = no user edits yet
  created_at: string;     // ISO 8601
  updated_at: string;     // ISO 8601
};
```

---

## 2. Endpoints

### 2.1 Upload Media File

**Upload a media file to a specific meeting.**

```
POST /meetings/{meeting_id}/media
Content-Type: multipart/form-data
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `meeting_id` | `string (UUID)` | Yes | Target meeting |

**Request Body (multipart/form-data):**

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | `binary` | Yes | The audio/video file |

**Supported MIME Types:** `audio/mpeg`, `audio/wav`, `audio/x-m4a`, `video/mp4`
**Max File Size:** 500 MB (configurable via `MAX_UPLOAD_SIZE_MB` env var)

**Success Response — `201 Created`:**

```json
{
  "media_file": {
    "id": "d4f8c2a1-...",
    "meeting_id": "b2e1a3c4-...",
    "original_filename": "meeting-recording.mp3",
    "mime_type": "audio/mpeg",
    "file_size_bytes": 24576000,
    "storage_path": "uploads/b2e1a3c4/meeting-recording.mp3",
    "normalized_path": null,
    "status": "uploaded",
    "uploaded_at": "2026-06-29T10:00:00Z",
    "updated_at": "2026-06-29T10:00:00Z"
  },
  "meeting_status": "uploaded"
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `MEETING_NOT_FOUND` | `meeting_id` does not exist |
| `413 Payload Too Large` | `FILE_TOO_LARGE` | File exceeds size limit |
| `422 Unprocessable Entity` | `UNSUPPORTED_MEDIA_TYPE` | MIME type not in allowed list |

---

### 2.2 Trigger Processing

**Start the audio normalization + STT pipeline for a meeting.**

```
POST /meetings/{meeting_id}/process
Content-Type: application/json
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `meeting_id` | `string (UUID)` | Yes | Target meeting |

**Request Body:** _(empty)_

**Success Response — `202 Accepted`:**

```json
{
  "job": {
    "id": "9a3b7c1d-...",
    "meeting_id": "b2e1a3c4-...",
    "status": "queued",
    "error_code": null,
    "error_message": null,
    "queued_at": "2026-06-29T10:01:00Z",
    "started_at": null,
    "completed_at": null
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `MEETING_NOT_FOUND` | `meeting_id` does not exist |
| `409 Conflict` | `JOB_ALREADY_ACTIVE` | A non-terminal job already exists for this meeting |
| `422 Unprocessable Entity` | `NO_MEDIA_FILE` | Meeting has no uploaded media file |

---

### 2.3 Get Processing Status

**Poll the current state of a meeting's processing job.**

```
GET /meetings/{meeting_id}/status
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `meeting_id` | `string (UUID)` | Yes | Target meeting |

**Success Response — `200 OK`:**

```json
{
  "meeting_id": "b2e1a3c4-...",
  "meeting_status": "transcribing",
  "job": {
    "id": "9a3b7c1d-...",
    "meeting_id": "b2e1a3c4-...",
    "status": "transcribing",
    "error_code": null,
    "error_message": null,
    "queued_at": "2026-06-29T10:01:00Z",
    "started_at": "2026-06-29T10:01:05Z",
    "completed_at": null
  }
}
```

**When job is `done`:**

```json
{
  "meeting_id": "b2e1a3c4-...",
  "meeting_status": "transcribed",
  "job": {
    "id": "9a3b7c1d-...",
    "status": "done",
    "queued_at": "2026-06-29T10:01:00Z",
    "started_at": "2026-06-29T10:01:05Z",
    "completed_at": "2026-06-29T10:03:44Z",
    "error_code": null,
    "error_message": null
  },
  "segment_count": 47
}
```

**When job is `failed`:**

```json
{
  "meeting_id": "b2e1a3c4-...",
  "meeting_status": "failed",
  "job": {
    "id": "9a3b7c1d-...",
    "status": "failed",
    "error_code": "FFMPEG_ERROR",
    "error_message": "ffmpeg exited with code 1: Invalid data found when processing input",
    "queued_at": "2026-06-29T10:01:00Z",
    "started_at": "2026-06-29T10:01:05Z",
    "completed_at": "2026-06-29T10:01:08Z"
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `MEETING_NOT_FOUND` | `meeting_id` does not exist |

---

## 3. Error Response Schema

All errors follow this envelope:

```typescript
type ErrorResponse = {
  error: {
    code: string;       // machine-readable snake_case
    message: string;    // human-readable description
    details?: unknown;  // optional extra context
  };
};
```

**Example:**

```json
{
  "error": {
    "code": "UNSUPPORTED_MEDIA_TYPE",
    "message": "File type 'video/quicktime' is not supported. Accepted types: audio/mpeg, audio/wav, audio/x-m4a, video/mp4.",
    "details": {
      "provided_mime_type": "video/quicktime",
      "accepted_types": ["audio/mpeg", "audio/wav", "audio/x-m4a", "video/mp4"]
    }
  }
}
```

---

## 4. Known Error Codes

| Code | HTTP | Description |
|---|---|---|
| `MEETING_NOT_FOUND` | 404 | Referenced meeting does not exist |
| `FILE_TOO_LARGE` | 413 | Uploaded file exceeds configured max size |
| `UNSUPPORTED_MEDIA_TYPE` | 422 | File MIME type not in allowed list |
| `NO_MEDIA_FILE` | 422 | Process triggered with no media file attached |
| `JOB_ALREADY_ACTIVE` | 409 | A non-terminal job is already running for this meeting |
| `FFMPEG_ERROR` | — | ffmpeg failed during normalization (job-level, not HTTP) |
| `MODEL_NOT_FOUND` | — | sherpa-onnx model file missing (job-level, not HTTP) |
| `STT_TIMEOUT` | — | Transcription exceeded configured timeout (Phase 2) |

---

## 5. Implementation Notes

- **File Storage:** Uploaded files are stored under `{DATA_ROOT}/uploads/{meeting_id}/`. Normalized files go to `{DATA_ROOT}/normalized/{meeting_id}/`. Both paths are configurable via env vars.
- **Job Queue:** MVP uses a Python `asyncio` background task. Phase 2 should migrate to Celery + Redis for resilience.
- **Polling Strategy:** Frontend should poll `GET /meetings/{id}/status` every 3 seconds during active jobs. Exponential back-off recommended after 60 seconds.
- **Re-processing:** Re-triggering a failed job is allowed. It soft-deletes existing `TranscriptSegment` rows (sets `deleted_at`) before creating new ones.
