# Technical Contract — Requirement Extraction

**Feature:** Requirement Extraction
**Module:** Core
**Version:** 1.0.0
**Base URL:** `/api/v1`
**Last Updated:** 2026-06-29

---

## 1. Data Models

### RequirementCandidateType

```typescript
type RequirementCandidateType =
  | "functional_requirement"
  | "non_functional_requirement"
  | "business_rule"
  | "open_question"
  | "decision"
  | "action_item";
```

### RequirementCandidateStatus

```typescript
type RequirementCandidateStatus = "pending" | "approved" | "rejected";
```

### RequirementCandidate

```typescript
type RequirementCandidate = {
  id: string;                        // UUID
  meeting_id: string;                // UUID
  type: RequirementCandidateType;
  title: string;                     // short label, max 200 chars
  description: string;               // full extracted text
  evidence_text: string;             // verbatim quote from transcript
  source_segment_ids: string[];      // UUIDs of TranscriptSegment records
  confidence_score: number;          // 0.0 – 1.0, LLM-provided
  sequence_index: number;            // insertion order from LLM output
  status: RequirementCandidateStatus;
  reviewer_note: string | null;      // added during Requirement Review
  created_at: string;                // ISO 8601
  updated_at: string;                // ISO 8601
};
```

### ExtractionJob

```typescript
type ExtractionJobStatus = "queued" | "running" | "done" | "failed";

type ExtractionJob = {
  id: string;                   // UUID
  meeting_id: string;           // UUID
  status: ExtractionJobStatus;
  candidate_count: number | null; // populated on done
  error_code: string | null;
  error_message: string | null;
  queued_at: string;            // ISO 8601
  started_at: string | null;   // ISO 8601
  completed_at: string | null; // ISO 8601
};
```

### LLM Expected Output Schema

The LLM is instructed to produce the following JSON (used in prompt engineering, not as an API schema):

```json
{
  "candidates": [
    {
      "type": "functional_requirement",
      "title": "User login with email and password",
      "description": "The system must allow users to authenticate using their email address and a password.",
      "evidence_text": "we need users to be able to log in with their email and a password",
      "source_segment_indices": [3, 4],
      "confidence": 0.92
    }
  ]
}
```

> Note: `source_segment_indices` are 0-based `sequence_index` values. The server maps these to `TranscriptSegment.id` values when storing candidates.

---

## 2. Endpoints

### 2.1 Trigger Extraction

**Initiate LLM-based extraction for a meeting.**

```
POST /meetings/{meeting_id}/extract
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
    "id": "f7a1b2c3-...",
    "meeting_id": "b2e1a3c4-...",
    "status": "queued",
    "candidate_count": null,
    "error_code": null,
    "error_message": null,
    "queued_at": "2026-06-29T12:00:00Z",
    "started_at": null,
    "completed_at": null
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `MEETING_NOT_FOUND` | `meeting_id` does not exist |
| `409 Conflict` | `EXTRACTION_JOB_ACTIVE` | An active extraction job already exists |
| `422 Unprocessable Entity` | `TRANSCRIPT_NOT_READY` | Meeting status is not `transcribed` |
| `503 Service Unavailable` | `LLM_NOT_CONFIGURED` | No LLM provider is configured |

---

### 2.2 Get Extraction Status

**Poll the current state of the extraction job for a meeting.**

```
GET /meetings/{meeting_id}/extract/status
```

**Success Response — `200 OK`:**

```json
{
  "meeting_id": "b2e1a3c4-...",
  "meeting_status": "extraction_done",
  "job": {
    "id": "f7a1b2c3-...",
    "status": "done",
    "candidate_count": 23,
    "error_code": null,
    "error_message": null,
    "queued_at": "2026-06-29T12:00:00Z",
    "started_at": "2026-06-29T12:00:03Z",
    "completed_at": "2026-06-29T12:01:45Z"
  }
}
```

---

### 2.3 Get Requirement Candidates

**Retrieve extracted candidates for a meeting.**

```
GET /meetings/{meeting_id}/requirements/candidates
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `type` | `string` | No | (all) | Filter by candidate type |
| `status` | `string` | No | (all) | Filter by `pending`, `approved`, `rejected` |
| `page` | `integer` | No | `1` | Page number |
| `page_size` | `integer` | No | `50` | Items per page (max 200) |

**Success Response — `200 OK`:**

```json
{
  "candidates": [
    {
      "id": "a1b2c3d4-...",
      "meeting_id": "b2e1a3c4-...",
      "type": "functional_requirement",
      "title": "User login with email and password",
      "description": "The system must allow users to authenticate using their email address and a password.",
      "evidence_text": "we need users to be able to log in with their email and a password",
      "source_segment_ids": ["c9d4e5f6-...", "d1e2f3a4-..."],
      "confidence_score": 0.92,
      "sequence_index": 0,
      "status": "pending",
      "reviewer_note": null,
      "created_at": "2026-06-29T12:01:45Z",
      "updated_at": "2026-06-29T12:01:45Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 23,
    "total_pages": 1
  },
  "summary": {
    "pending": 18,
    "approved": 4,
    "rejected": 1,
    "by_type": {
      "functional_requirement": 12,
      "non_functional_requirement": 3,
      "business_rule": 2,
      "open_question": 4,
      "decision": 1,
      "action_item": 1
    }
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `MEETING_NOT_FOUND` | `meeting_id` does not exist |

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

---

## 4. Known Error Codes

| Code | HTTP | Description |
|---|---|---|
| `MEETING_NOT_FOUND` | 404 | Referenced meeting does not exist |
| `TRANSCRIPT_NOT_READY` | 422 | Meeting has not completed transcription |
| `EXTRACTION_JOB_ACTIVE` | 409 | An active extraction job is already running |
| `LLM_NOT_CONFIGURED` | 503 | `LLM_PROVIDER` env var is not set |
| `LLM_API_ERROR` | — | LLM provider returned a non-2xx response (job-level) |
| `LLM_INVALID_RESPONSE` | — | LLM returned non-JSON or schema-incompatible output (job-level) |
| `LLM_TIMEOUT` | — | LLM call exceeded `LLM_TIMEOUT_SECONDS` (job-level) |

---

## 5. Implementation Notes

- **Prompt Template:** System prompt is loaded from `LLM_SYSTEM_PROMPT_PATH`. The default prompt instructs the LLM to: extract candidates in JSON, assign a confidence score, include verbatim evidence, and reference segment indices.
- **Context Window Handling:** If the transcript token count exceeds `LLM_MAX_CONTEXT_TOKENS`, it is split into overlapping chunks (500-token overlap). Candidates from all chunks are merged; duplicates detected by content hash (SHA-256 of title+description) are discarded.
- **Re-extraction:** Previous candidates are soft-deleted (sets `deleted_at`) before new ones are created. Approved candidates that exist in a re-extraction run are re-created as `pending` (users must re-review).
- **Polling:** Frontend should poll `GET /meetings/{id}/extract/status` every 5 seconds while job is `queued` or `running`.
