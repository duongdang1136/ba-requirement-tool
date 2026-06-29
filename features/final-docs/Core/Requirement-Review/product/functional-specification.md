# Functional Specification — Requirement Review

**Feature:** Requirement Review
**Module:** Core
**Version:** 1.0.0
**Phase:** Phase 2
**Last Updated:** 2026-06-29
**Status:** Planned

---

## 1. Summary

Requirement Review is the human-in-the-loop workspace where BAs evaluate AI-generated requirement candidates. Each candidate can be approved (converting it to a formal Requirement record), rejected, or edited inline before approval. The workspace provides contextual evidence from the transcript to support each decision.

---

## 2. Goals

- Make the review process fast: a BA should be able to review 20+ candidates in under 10 minutes.
- Provide full traceability: every approved requirement links back to its source transcript segments.
- Never discard information: rejected candidates remain in the system with a reason for auditability.
- Aggregate approved requirements at the project level across multiple meetings.

---

## 3. Non-Goals

- This feature does **not** run the LLM again; it only processes existing candidates.
- This feature does **not** create requirements without a source candidate in Phase 2 (manual FR creation is a future enhancement).
- This feature does **not** manage requirement versioning (future).
- This feature does **not** assign requirements to team members (future).

---

## 4. Users

| Persona | Need |
|---|---|
| **BA (primary)** | Review candidates quickly, edit if needed, build up the approved requirements list |
| **Tech Lead** | Read-only review of approved requirements; may also review and reject |
| **Project Manager** | View approved requirements and open questions at project level |

---

## 5. Functional Requirements

### FR-RR-001 — Candidate List

**Description:** The center panel displays all candidates for the current meeting, grouped or filtered by type.

**Acceptance Criteria:**
- AC-RR-001-1: The candidate list shows all candidates ordered by `sequence_index`.
- AC-RR-001-2: Each list item displays: type badge (color-coded), title, confidence score (e.g. "92%"), and status indicator (`pending` / `approved` / `rejected`).
- AC-RR-001-3: The list can be filtered by type (FR, NFR, Rule, Question, Decision, Action) and status (pending, approved, rejected) using tabs or filter chips.
- AC-RR-001-4: A progress bar shows `approved / total` count at the top of the list.
- AC-RR-001-5: Clicking a candidate selects it and loads its evidence in the right panel.

---

### FR-RR-002 — Candidate Detail (Evidence Panel)

**Description:** The right panel shows the full content of the selected candidate and its source evidence.

**Acceptance Criteria:**
- AC-RR-002-1: The evidence panel displays: candidate `type`, `title` (editable), `description` (editable), `confidence_score`, `evidence_text` (verbatim quote, read-only), and source segment timestamps.
- AC-RR-002-2: The `evidence_text` quote is shown in a distinct blockquote style.
- AC-RR-002-3: Clicking a source segment timestamp scrolls the left transcript panel to the corresponding segment.
- AC-RR-002-4: The `reviewer_note` field is editable as a plain text input; changes auto-save on blur.

---

### FR-RR-003 — Approve Candidate

**Description:** A BA approves a candidate, converting it into a formal Requirement record.

**Acceptance Criteria:**
- AC-RR-003-1: Clicking "Approve" on a `pending` candidate calls `POST /requirements/candidates/{id}/approve`.
- AC-RR-003-2: On success, the candidate `status` changes to `approved`, the card shows a green approved indicator, and a `Requirement` record is created in the database.
- AC-RR-003-3: The BA can edit `title` and `description` before approving; edits are included in the approve request payload.
- AC-RR-003-4: Previously `rejected` candidates can also be approved (status transitions from `rejected` → `approved`).
- AC-RR-003-5: Approving advances the candidate list automatically to the next `pending` candidate.

---

### FR-RR-004 — Reject Candidate

**Description:** A BA rejects a candidate with an optional reason.

**Acceptance Criteria:**
- AC-RR-004-1: Clicking "Reject" on a `pending` or `approved` candidate calls `POST /requirements/candidates/{id}/reject`.
- AC-RR-004-2: A rejection reason field is shown (optional text, max 500 chars).
- AC-RR-004-3: On success, the candidate `status` changes to `rejected` and the reviewer note is stored.
- AC-RR-004-4: Rejected candidates are retained in the system and visible in the "Rejected" filter view.
- AC-RR-004-5: If the candidate was `approved`, rejecting it also marks the linked `Requirement` record as `withdrawn`.

---

### FR-RR-005 — Edit Candidate Before Approving

**Description:** A BA can edit a candidate's title and description inline.

**Acceptance Criteria:**
- AC-RR-005-1: `title` is editable via a single-line text input; max 200 characters.
- AC-RR-005-2: `description` is editable via a multi-line textarea; max 5,000 characters.
- AC-RR-005-3: Edits to a `pending` candidate are saved immediately on blur via `PATCH /requirements/candidates/{id}`.
- AC-RR-005-4: The original LLM-generated values are preserved in a read-only "Original" collapsible section.
- AC-RR-005-5: `evidence_text` and `source_segment_ids` are not editable.

---

### FR-RR-006 — Project-Level Requirements View

**Description:** Approved requirements from all meetings within a project are aggregated into a project-level view.

**Acceptance Criteria:**
- AC-RR-006-1: `GET /projects/{id}/requirements` returns all approved Requirements across all meetings in the project.
- AC-RR-006-2: Requirements can be filtered by type.
- AC-RR-006-3: Each requirement shows: type, title, description, source meeting name, and approved date.
- AC-RR-006-4: `GET /projects/{id}/open-questions`, `GET /projects/{id}/decisions`, and `GET /projects/{id}/action-items` return the equivalent project-level aggregated views.

---

## 6. MVP vs Phase 2 Scope

| Capability | MVP | Phase 2 |
|---|---|---|
| Three-panel review workspace | ❌ | ✅ |
| Approve / reject candidates | ❌ | ✅ |
| Edit candidate before approving | ❌ | ✅ |
| Evidence panel with segment links | ❌ | ✅ |
| Filter by type / status | ❌ | ✅ |
| Project-level requirements view | ❌ | ✅ |
| Project-level open questions / decisions | ❌ | ✅ |
| Bulk approve/reject | ❌ | Future |
| Requirement priority scoring | ❌ | Future |
| Manual requirement creation (no LLM) | ❌ | Future |

---

## 7. Constraints & Assumptions

- A meeting must have at least one `RequirementCandidate` record before the review workspace is accessible.
- Approved Requirements are owned by the Project (not just the Meeting); this enables cross-meeting aggregation.
- The review workspace is read-write for BA role; read-only for PM/stakeholder roles (role management is a future feature; MVP assumes single user).
- `Requirement` records created by approval are immutable once created except through re-rejection (withdraw).
