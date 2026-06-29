# Functional Specification — Requirement Extraction

**Feature:** Requirement Extraction
**Module:** Core
**Version:** 1.0.0
**Phase:** Phase 2
**Last Updated:** 2026-06-29
**Status:** Planned

---

## 1. Summary

Requirement Extraction automates the identification of structured requirement artifacts from meeting transcripts using a configurable LLM. The extracted items (Functional Requirements, Non-Functional Requirements, Business Rules, Open Questions, Decisions, Action Items) are stored as `RequirementCandidate` records linked to evidence segments. A BA then reviews and curates these candidates in the Requirement Review workspace.

---

## 2. Goals

- Dramatically reduce the time a BA spends manually reading transcripts to extract requirements.
- Ensure full traceability: every extracted item is linked to its source transcript segments and verbatim evidence text.
- Support both local (privacy-first) and cloud LLM providers via a unified configuration interface.
- Produce consistently structured output regardless of LLM provider by using a strict JSON schema prompt.

---

## 3. Non-Goals

- This feature does **not** auto-approve candidates; all LLM output requires human review.
- This feature does **not** write to the Requirement table directly; it only creates `RequirementCandidate` records.
- This feature does **not** detect duplicate requirements across meetings or projects (future enhancement).
- This feature does **not** support custom extraction prompts through the UI in Phase 2 (admin-only via config).

---

## 4. Users

| Persona | Need |
|---|---|
| **BA (primary)** | Trigger extraction after reviewing transcript; receive a pre-populated candidates list |
| **Admin** | Configure LLM provider, model name, API keys, and system prompt template |

---

## 5. Functional Requirements

### FR-RE-001 — Trigger Extraction

**Description:** A BA can trigger LLM-based extraction for a specific meeting after the transcript has been reviewed.

**Acceptance Criteria:**
- AC-RE-001-1: The endpoint `POST /meetings/{id}/extract` initiates an extraction job and returns the job ID.
- AC-RE-001-2: The meeting must have status `transcribed`; otherwise the endpoint returns HTTP 422 with `TRANSCRIPT_NOT_READY`.
- AC-RE-001-3: Only one active extraction job per meeting is permitted; subsequent requests return HTTP 409 with `EXTRACTION_JOB_ACTIVE`.
- AC-RE-001-4: Re-extraction is allowed on completed/failed jobs; re-triggering clears previous `RequirementCandidate` records for the meeting (soft-delete) before creating new ones.
- AC-RE-001-5: The extraction job lifecycle uses statuses: `queued`, `running`, `done`, `failed`.

---

### FR-RE-002 — LLM Prompt Construction

**Description:** The system constructs a structured prompt combining system instructions and the full transcript before calling the LLM.

**Acceptance Criteria:**
- AC-RE-002-1: The system prompt instructs the LLM to extract items of type: `functional_requirement`, `non_functional_requirement`, `business_rule`, `open_question`, `decision`, `action_item`.
- AC-RE-002-2: The LLM is instructed to respond in a strict JSON format (see schema in Technical Contract).
- AC-RE-002-3: The transcript is included as the user message, formatted as `[HH:MM:SS] speaker: text` per segment (using `edited_text` if available, `original_text` as fallback).
- AC-RE-002-4: The system prompt template is configurable via `LLM_SYSTEM_PROMPT_PATH` env var; a default built-in template is used if not specified.
- AC-RE-002-5: If the transcript exceeds the LLM's context window, the system chunks the transcript into overlapping windows and merges results (deduplication by content hash).

---

### FR-RE-003 — LLM Provider Configuration

**Description:** The LLM provider is configurable without code changes.

**Acceptance Criteria:**
- AC-RE-003-1: Supported providers: `ollama` (local), `openai` (cloud), `anthropic` (cloud).
- AC-RE-003-2: Provider is set via `LLM_PROVIDER` env var; model via `LLM_MODEL`; API key via `LLM_API_KEY`.
- AC-RE-003-3: If `LLM_PROVIDER` is not set, extraction triggers return HTTP 503 with `LLM_NOT_CONFIGURED`.
- AC-RE-003-4: Connection to the LLM is validated at startup and logged as a warning if the provider is unreachable.

---

### FR-RE-004 — Candidate Storage

**Description:** Each extracted item is stored as a `RequirementCandidate` record linked to the meeting and source segments.

**Acceptance Criteria:**
- AC-RE-004-1: Each candidate record includes: `type`, `title`, `description`, `source_segment_ids` (array of UUIDs), `evidence_text` (verbatim quote from transcript), `confidence_score` (0.0–1.0, from LLM), `status` (`pending`).
- AC-RE-004-2: Candidates are stored in insertion order as returned by the LLM.
- AC-RE-004-3: `source_segment_ids` references valid `TranscriptSegment` IDs; invalid IDs are logged and skipped.
- AC-RE-004-4: On successful storage, the meeting status updates to `extraction_done`.

---

### FR-RE-005 — Extraction Failure Handling

**Description:** Failures during extraction are surfaced with actionable error information.

**Acceptance Criteria:**
- AC-RE-005-1: If the LLM returns malformed JSON, the job fails with `LLM_INVALID_RESPONSE` and includes the raw LLM output for debugging.
- AC-RE-005-2: If the LLM API returns a non-200 response, the job fails with `LLM_API_ERROR` and the HTTP status code is recorded.
- AC-RE-005-3: If the LLM call times out (configurable via `LLM_TIMEOUT_SECONDS`, default 120), the job fails with `LLM_TIMEOUT`.
- AC-RE-005-4: Failed jobs can be retried by re-triggering `POST /meetings/{id}/extract`.

---

### FR-RE-006 — Extraction Results Access

**Description:** The list of extracted candidates is accessible to feed into the Requirement Review workflow.

**Acceptance Criteria:**
- AC-RE-006-1: `GET /meetings/{id}/requirements/candidates` returns all `pending`, `approved`, and `rejected` candidates for the meeting.
- AC-RE-006-2: Results can be filtered by `type` and `status` via query parameters.
- AC-RE-006-3: Results are ordered by `sequence_index` (insertion order from LLM).
- AC-RE-006-4: Each candidate includes the referenced segment data (start/end/text) for display in the review workspace.

---

## 6. MVP vs Phase 2 Scope

| Capability | MVP | Phase 2 |
|---|---|---|
| LLM extraction trigger | ❌ | ✅ |
| FR / NFR / Business Rule extraction | ❌ | ✅ |
| Open Questions / Decisions / Action Items | ❌ | ✅ |
| Evidence linking to transcript segments | ❌ | ✅ |
| Confidence score from LLM | ❌ | ✅ |
| Local LLM support (Ollama) | ❌ | ✅ |
| Cloud LLM support (OpenAI, Anthropic) | ❌ | ✅ |
| Long transcript chunking | ❌ | ✅ |
| Extraction job status tracking | ❌ | ✅ |
| Glossary term extraction | ❌ | Future |
| Custom extraction prompts via UI | ❌ | Future |

---

## 7. Constraints & Assumptions

- LLM output quality depends on model capability; no guarantee of completeness or accuracy. Human review is mandatory.
- The default LLM timeout is 120 seconds; very long transcripts may require a higher value.
- Local Ollama models must be pre-installed and running; the tool does not manage Ollama installation.
- Transcripts are sent in plain text to the LLM; no audio is transmitted.
- All LLM API keys are server-side environment variables; they are never exposed to the frontend.
