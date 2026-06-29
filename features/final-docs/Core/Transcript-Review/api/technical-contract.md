# Technical Contract — Transcript Review

**Feature:** Transcript Review
**Module:** Core
**Version:** 1.0.0
**Base URL:** `/api/v1`
**Last Updated:** 2026-06-29

---

## 1. Data Models

### TranscriptSegment

```typescript
type TranscriptSegment = {
  id: string;              // UUID
  meeting_id: string;      // UUID
  sequence_index: number;  // 0-based, determines display order
  start: number;           // float seconds, e.g. 12.34
  end: number;             // float seconds
  speaker_id: string | null; // null in MVP
  original_text: string;   // immutable STT output
  edited_text: string | null; // null = not yet edited by user
  created_at: string;      // ISO 8601
  updated_at: string;      // ISO 8601
};
```

### TranscriptPage (paginated response)

```typescript
type TranscriptPage = {
  segments: TranscriptSegment[];
  pagination: {
    page: number;         // 1-based current page
    page_size: number;    // items per page (default 100)
    total_count: number;  // total segments in meeting
    total_pages: number;
  };
  meeting: {
    id: string;
    title: string;
    status: string;       // should be "transcribed"
    total_duration: number; // seconds
  };
};
```

### SegmentPatchRequest

```typescript
type SegmentPatchRequest = {
  edited_text: string | null; // string = save edit; null = revert to original
};
```

### SegmentPatchResponse

```typescript
type SegmentPatchResponse = {
  segment: TranscriptSegment;
};
```

---

## 2. Endpoints

### 2.1 Get Transcript Segments

**Retrieve all transcript segments for a meeting, paginated.**

```
GET /meetings/{meeting_id}/transcript
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `meeting_id` | `string (UUID)` | Yes | Target meeting |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `page` | `integer` | No | `1` | Page number (1-based) |
| `page_size` | `integer` | No | `100` | Items per page (max 500) |

**Success Response — `200 OK`:**

```json
{
  "meeting": {
    "id": "b2e1a3c4-...",
    "title": "Sprint Review 2026-06-29",
    "status": "transcribed",
    "total_duration": 2580.5
  },
  "segments": [
    {
      "id": "c9d4e5f6-...",
      "meeting_id": "b2e1a3c4-...",
      "sequence_index": 0,
      "start": 0.0,
      "end": 8.42,
      "speaker_id": null,
      "original_text": "okay so let's start the sprint review for this cycle",
      "edited_text": "Okay, so let's start the sprint review for this cycle.",
      "created_at": "2026-06-29T10:04:00Z",
      "updated_at": "2026-06-29T11:20:00Z"
    },
    {
      "id": "d1e2f3a4-...",
      "meeting_id": "b2e1a3c4-...",
      "sequence_index": 1,
      "start": 8.42,
      "end": 15.10,
      "speaker_id": null,
      "original_text": "we completed the login module and the dashboard",
      "edited_text": null,
      "created_at": "2026-06-29T10:04:00Z",
      "updated_at": "2026-06-29T10:04:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 100,
    "total_count": 47,
    "total_pages": 1
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `MEETING_NOT_FOUND` | `meeting_id` does not exist |
| `422 Unprocessable Entity` | `TRANSCRIPT_NOT_READY` | Meeting status is not `transcribed` |

---

### 2.2 Update Transcript Segment

**Save an edited transcript segment, or revert to original.**

```
PATCH /transcript-segments/{segment_id}
Content-Type: application/json
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `segment_id` | `string (UUID)` | Yes | Target segment |

**Request Body:**

```json
{
  "edited_text": "Okay, so let's start the sprint review for this cycle."
}
```

To revert:

```json
{
  "edited_text": null
}
```

**Validation Rules:**
- `edited_text` must be either `null` or a non-empty string (trim whitespace before check).
- `edited_text` must not exceed 10,000 characters.

**Success Response — `200 OK`:**

```json
{
  "segment": {
    "id": "c9d4e5f6-...",
    "meeting_id": "b2e1a3c4-...",
    "sequence_index": 0,
    "start": 0.0,
    "end": 8.42,
    "speaker_id": null,
    "original_text": "okay so let's start the sprint review for this cycle",
    "edited_text": "Okay, so let's start the sprint review for this cycle.",
    "created_at": "2026-06-29T10:04:00Z",
    "updated_at": "2026-06-29T11:22:00Z"
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `SEGMENT_NOT_FOUND` | `segment_id` does not exist |
| `422 Unprocessable Entity` | `EMPTY_EDITED_TEXT` | `edited_text` is empty string or whitespace-only |
| `422 Unprocessable Entity` | `TEXT_TOO_LONG` | `edited_text` exceeds 10,000 characters |

---

## 3. Error Response Schema

```typescript
type ErrorResponse = {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
};
```

**Example:**

```json
{
  "error": {
    "code": "EMPTY_EDITED_TEXT",
    "message": "edited_text cannot be an empty string. Use null to revert to the original transcription.",
    "details": {
      "segment_id": "c9d4e5f6-..."
    }
  }
}
```

---

## 4. Known Error Codes

| Code | HTTP | Description |
|---|---|---|
| `MEETING_NOT_FOUND` | 404 | Referenced meeting does not exist |
| `TRANSCRIPT_NOT_READY` | 422 | Meeting has not completed transcription |
| `SEGMENT_NOT_FOUND` | 404 | Referenced segment does not exist |
| `EMPTY_EDITED_TEXT` | 422 | `edited_text` is empty or whitespace-only |
| `TEXT_TOO_LONG` | 422 | `edited_text` exceeds character limit |

---

## 5. Implementation Notes

- **Immutability:** `original_text`, `start`, `end`, and `sequence_index` are read-only after creation. The `PATCH` endpoint ignores any attempt to modify them.
- **Soft-delete protection:** Segments with `deleted_at` set are excluded from all `GET` responses and cannot be PATCHed (return `404`).
- **Optimistic locking (Phase 2):** If concurrent edits become a concern, add an `ETag` header to `GET /transcript` and require `If-Match` on `PATCH`.
- **Caching:** The `GET /transcript` response may be cached per `meeting_id`. Cache must be invalidated on any `PATCH` to a segment belonging to that meeting.
