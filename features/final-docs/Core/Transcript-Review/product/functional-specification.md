# Functional Specification — Transcript Review

**Feature:** Transcript Review
**Module:** Core
**Version:** 1.0.0
**Phase:** MVP
**Last Updated:** 2026-06-29
**Status:** In Review

---

## 1. Summary

Transcript Review provides a structured editing interface for BAs to verify and correct the raw speech-to-text output produced by Meeting Processing. Edits are stored non-destructively as `edited_text` alongside the immutable `original_text`, enabling full auditability. The finalized transcript feeds downstream into the Requirement Extraction pipeline.

---

## 2. Goals

- Allow BAs to fix STT errors quickly without losing the original machine output.
- Provide enough context (timestamps, original text) to make corrections confidently.
- Auto-save edits to prevent data loss during long review sessions.
- Export the finalized transcript in human-readable formats (Markdown, TXT) for sharing.

---

## 3. Non-Goals

- This feature does **not** play back audio (deferred to Phase 2 with synchronized playback).
- This feature does **not** assign speaker labels (Phase 2 diarization feature).
- This feature does **not** merge or split segments (Phase 2).
- This feature does **not** perform find-and-replace across all segments simultaneously (Phase 2).

---

## 4. Users

| Persona | Need |
|---|---|
| **BA (primary)** | Read STT output, fix transcription errors, save a clean transcript for extraction |
| **Project Manager** | Read the transcript for meeting summary; may export it |

---

## 5. Functional Requirements

### FR-TR-001 — Load Transcript

**Description:** The transcript view loads all segments for a meeting in sequential order.

**Acceptance Criteria:**
- AC-TR-001-1: The endpoint `GET /meetings/{id}/transcript` returns all non-deleted segments ordered by `sequence_index` ascending.
- AC-TR-001-2: Each segment in the response includes: `id`, `sequence_index`, `start`, `end`, `original_text`, `edited_text`, `speaker_id` (null in MVP).
- AC-TR-001-3: If the meeting status is not `transcribed`, the endpoint returns HTTP 422 with error code `TRANSCRIPT_NOT_READY`.
- AC-TR-001-4: Segments are paginated server-side in sets of 100. The response includes `total_count` and pagination metadata.
- AC-TR-001-5: The frontend displays the meeting title, total segment count, and total duration at the top of the view.

---

### FR-TR-002 — Display Segment with Timestamp

**Description:** Each segment is rendered with its time range and both original and edited text.

**Acceptance Criteria:**
- AC-TR-002-1: The timestamp is displayed as `[HH:MM:SS → HH:MM:SS]` format.
- AC-TR-002-2: `original_text` is always shown (read-only) in a muted/secondary style.
- AC-TR-002-3: If `edited_text` is null, the editable field shows `original_text` as the placeholder/initial value.
- AC-TR-002-4: If `edited_text` is not null, a visual indicator (e.g. ✏ icon, distinct background) signals the segment has been edited.
- AC-TR-002-5: Segments are displayed in a scrollable list; the viewport can accommodate at least 20 segments without horizontal scrolling.

---

### FR-TR-003 — Inline Edit Segment

**Description:** A BA can click on any segment to edit its `edited_text`.

**Acceptance Criteria:**
- AC-TR-003-1: Clicking a segment's text area activates inline editing mode (contenteditable or textarea).
- AC-TR-003-2: The user can type freely; the edit area supports multi-line text.
- AC-TR-003-3: Pressing `Escape` cancels the edit and reverts to the last saved `edited_text` (or `original_text` if never edited).
- AC-TR-003-4: Pressing `Ctrl+Enter` saves the current edit immediately.
- AC-TR-003-5: Only one segment can be in edit mode at a time; clicking a different segment commits the previous edit (auto-save on blur).

---

### FR-TR-004 — Save Segment Edit

**Description:** Edited text is persisted to the server.

**Acceptance Criteria:**
- AC-TR-004-1: Saving calls `PATCH /transcript-segments/{id}` with the updated `edited_text`.
- AC-TR-004-2: A saving indicator (spinner or "Saving…" text) appears during the API call.
- AC-TR-004-3: On success, the indicator transitions to "Saved ✓" for 2 seconds, then disappears.
- AC-TR-004-4: On API failure, an inline error is shown: "Could not save. Retry?" with a retry button; the segment remains in edit mode.
- AC-TR-004-5: Saving an `edited_text` that is identical to `original_text` is allowed (the server stores it as-is).
- AC-TR-004-6: Setting `edited_text` to empty string (`""`) is **not** allowed; the UI prevents submission and shows an inline validation error.

---

### FR-TR-005 — Revert Segment to Original

**Description:** A user can discard their edit and restore the original STT text.

**Acceptance Criteria:**
- AC-TR-005-1: Each edited segment (where `edited_text != null`) shows a "Revert" action.
- AC-TR-005-2: Clicking "Revert" shows a confirmation: *"This will discard your edit and restore the original transcription. Continue?"*
- AC-TR-005-3: Confirming calls `PATCH /transcript-segments/{id}` with `edited_text: null`.
- AC-TR-005-4: After revert, the edited indicator disappears and the segment shows `original_text`.

---

### FR-TR-006 — Timestamp Navigation

**Description:** Clicking a segment's timestamp jumps to that position in the audio (Phase 2 only via audio player; MVP: no-op or scrolls to top of segment).

**Acceptance Criteria (MVP):**
- AC-TR-006-1: Timestamps are displayed but not interactive in MVP (non-clickable or styled as plain text).

---

### FR-TR-007 — Export Transcript (MVP)

**Description:** A BA can export the finalized transcript as Markdown or plain TXT.

**Acceptance Criteria:**
- AC-TR-007-1: An "Export" button is present in the transcript view toolbar.
- AC-TR-007-2: Clicking opens a format picker: **Markdown** | **Plain Text**.
- AC-TR-007-3: The exported content uses `edited_text` when available; falls back to `original_text` per segment.
- AC-TR-007-4: Each segment in the Markdown export is formatted as:
  ```
  **[00:01:23 → 00:01:45]**
  This is the transcript text for this segment.
  ```
- AC-TR-007-5: The download filename is `{meeting_title}_{YYYY-MM-DD}.md` or `.txt`.
- AC-TR-007-6: Export is client-side (no server round-trip for transcript-only export in MVP).

---

## 6. MVP vs Phase 2 Scope

| Capability | MVP | Phase 2 |
|---|---|---|
| View all transcript segments with timestamps | ✅ | ✅ |
| Inline segment editing | ✅ | ✅ |
| original_text preserved immutably | ✅ | ✅ |
| Auto-save on blur | ✅ | ✅ |
| Revert to original | ✅ | ✅ |
| Export Markdown / TXT | ✅ | ✅ |
| Audio playback + synchronized highlight | ❌ | ✅ |
| Speaker label assignment | ❌ | ✅ |
| Merge / split segments | ❌ | ✅ |
| Find & replace | ❌ | ✅ |
| Confidence score display (from STT) | ❌ | ✅ |

---

## 7. Constraints & Assumptions

- Segments are immutable in terms of `start`/`end` timestamps and `original_text`; only `edited_text` is writable.
- A meeting must be in `transcribed` status before the Transcript Review page is accessible.
- The frontend fetches all segments on page load (paginated); no real-time WebSocket updates in MVP.
- Transcript export in MVP is a client-side operation using pre-fetched segment data.
