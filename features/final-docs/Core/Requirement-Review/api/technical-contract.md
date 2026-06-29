# Technical Contract — Requirement Review

**Feature:** Requirement Review
**Module:** Core
**Version:** 1.0.0
**Base URL:** `/api/v1`
**Last Updated:** 2026-06-29

---

## 1. Data Models

### Requirement

```typescript
type RequirementStatus = "active" | "withdrawn";

type Requirement = {
  id: string;                        // UUID
  project_id: string;                // UUID
  meeting_id: string;                // UUID — source meeting
  candidate_id: string;              // UUID — source RequirementCandidate
  type: RequirementCandidateType;    // same type enum as candidate
  title: string;                     // approved title (may differ from candidate)
  description: string;               // approved description
  evidence_text: string;             // verbatim quote (from candidate)
  source_segment_ids: string[];      // UUIDs of TranscriptSegment records
  confidence_score: number;          // inherited from LLM output
  status: RequirementStatus;
  reviewer_note: string | null;
  approved_at: string;               // ISO 8601
  withdrawn_at: string | null;       // ISO 8601; set on rejection of approved candidate
  created_at: string;                // ISO 8601
  updated_at: string;                // ISO 8601
};
```

### ApproveRequest

```typescript
type ApproveRequest = {
  title?: string;       // override candidate title; falls back to candidate.title
  description?: string; // override candidate description
  reviewer_note?: string;
};
```

### RejectRequest

```typescript
type RejectRequest = {
  reviewer_note?: string; // rejection reason; optional, max 500 chars
};
```

### CandidatePatchRequest

```typescript
type CandidatePatchRequest = {
  title?: string;         // max 200 chars
  description?: string;  // max 5000 chars
  reviewer_note?: string; // max 500 chars
};
```

---

## 2. Endpoints

### 2.1 Approve Candidate

**Approve a requirement candidate, promoting it to a Requirement record.**

```
POST /requirements/candidates/{candidate_id}/approve
Content-Type: application/json
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `candidate_id` | `string (UUID)` | Yes | Target candidate |

**Request Body:**

```json
{
  "title": "User login with email and password",
  "description": "The system must allow users to authenticate using their registered email address and a password. Failed attempts must be tracked.",
  "reviewer_note": "Confirmed with product owner — includes lockout after 5 failures."
}
```

All fields are optional. If omitted, the candidate's current `title` / `description` / `reviewer_note` are used.

**Success Response — `200 OK`:**

```json
{
  "candidate": {
    "id": "a1b2c3d4-...",
    "status": "approved",
    "updated_at": "2026-06-29T14:00:00Z"
  },
  "requirement": {
    "id": "e5f6a7b8-...",
    "project_id": "p9q0r1s2-...",
    "meeting_id": "b2e1a3c4-...",
    "candidate_id": "a1b2c3d4-...",
    "type": "functional_requirement",
    "title": "User login with email and password",
    "description": "The system must allow users to authenticate using their registered email address and a password. Failed attempts must be tracked.",
    "evidence_text": "we need users to be able to log in with their email and a password",
    "source_segment_ids": ["c9d4e5f6-...", "d1e2f3a4-..."],
    "confidence_score": 0.92,
    "status": "active",
    "reviewer_note": "Confirmed with product owner — includes lockout after 5 failures.",
    "approved_at": "2026-06-29T14:00:00Z",
    "withdrawn_at": null,
    "created_at": "2026-06-29T14:00:00Z",
    "updated_at": "2026-06-29T14:00:00Z"
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `CANDIDATE_NOT_FOUND` | `candidate_id` does not exist |
| `422 Unprocessable Entity` | `TITLE_TOO_LONG` | Provided title exceeds 200 characters |

---

### 2.2 Reject Candidate

**Reject a requirement candidate (marks it as rejected; withdraws any linked Requirement).**

```
POST /requirements/candidates/{candidate_id}/reject
Content-Type: application/json
```

**Request Body:**

```json
{
  "reviewer_note": "Out of scope for this release. Discussed and deferred."
}
```

**Success Response — `200 OK`:**

```json
{
  "candidate": {
    "id": "a1b2c3d4-...",
    "status": "rejected",
    "reviewer_note": "Out of scope for this release. Discussed and deferred.",
    "updated_at": "2026-06-29T14:05:00Z"
  }
}
```

**Error Responses:**

| HTTP | Error Code | Condition |
|---|---|---|
| `404 Not Found` | `CANDIDATE_NOT_FOUND` | `candidate_id` does not exist |

---

### 2.3 Patch Candidate

**Edit a candidate's title, description, or reviewer note.**

```
PATCH /requirements/candidates/{candidate_id}
Content-Type: application/json
```

**Request Body:**

```json
{
  "description": "Updated description with more detail from the meeting discussion."
}
```

**Success Response — `200 OK`:**

```json
{
  "candidate": {
    "id": "a1b2c3d4-...",
    "title": "User login with email and password",
    "description": "Updated description with more detail from the meeting discussion.",
    "reviewer_note": null,
    "status": "pending",
    "updated_at": "2026-06-29T14:02:00Z"
  }
}
```

---

### 2.4 Get Project Requirements

**Get all approved Requirements for a project.**

```
GET /projects/{project_id}/requirements
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `type` | `string` | No | (all) | Filter by requirement type |
| `status` | `string` | No | `active` | Filter by `active` or `withdrawn` |
| `page` | `integer` | No | `1` | |
| `page_size` | `integer` | No | `50` | |

**Success Response — `200 OK`:**

```json
{
  "requirements": [
    {
      "id": "e5f6a7b8-...",
      "type": "functional_requirement",
      "title": "User login with email and password",
      "description": "...",
      "source_meeting": {
        "id": "b2e1a3c4-...",
        "title": "Sprint Review 2026-06-29"
      },
      "approved_at": "2026-06-29T14:00:00Z",
      "status": "active"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_count": 8,
    "total_pages": 1
  }
}
```

---

### 2.5 Get Project Open Questions / Decisions / Action Items

```
GET /projects/{project_id}/open-questions
GET /projects/{project_id}/decisions
GET /projects/{project_id}/action-items
```

These endpoints follow the same shape as `GET /projects/{id}/requirements` but filter by the respective `type` value. All three support the same pagination query parameters.

---

## 3. Known Error Codes

| Code | HTTP | Description |
|---|---|---|
| `CANDIDATE_NOT_FOUND` | 404 | Referenced candidate does not exist |
| `TITLE_TOO_LONG` | 422 | Provided title exceeds 200 characters |
| `DESCRIPTION_TOO_LONG` | 422 | Provided description exceeds 5,000 characters |
| `NOTE_TOO_LONG` | 422 | Reviewer note exceeds 500 characters |
| `PROJECT_NOT_FOUND` | 404 | Referenced project does not exist |

---

## 4. Implementation Notes

- **Approve idempotency:** Approving an already-approved candidate is a no-op (returns `200` with existing requirement data).
- **Reject of approved:** Sets `Requirement.status = "withdrawn"` and `withdrawn_at = now()`. The candidate `status` becomes `rejected`.
- **Candidate original values:** The `original_title` and `original_description` (LLM output before user edits) are stored in separate columns on `RequirementCandidate` for audit purposes; they are never overwritten.
- **Project aggregation:** The `GET /projects/{id}/requirements` query joins `Requirement` → `Meeting` → `Project` and filters by `project_id`. Ensure this query is indexed on `(project_id, type, status)`.
