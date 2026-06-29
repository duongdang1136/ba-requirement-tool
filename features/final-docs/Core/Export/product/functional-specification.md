# Functional Specification — Export

**Feature:** Export
**Module:** Core
**Version:** 1.0.0
**Phase:** MVP (transcript export) + Phase 2 (full requirement export)
**Last Updated:** 2026-06-29
**Status:** In Review (MVP) / Planned (Phase 2)

---

## 1. Summary

Export converts the structured data produced by Meeting Processing, Transcript Review, and Requirement Review into downloadable documents in multiple formats. The exported documents are intended to be shared with stakeholders, added to project wikis, or imported into tools like Jira.

---

## 2. Goals

- Allow BAs to distribute finalized meeting transcripts and requirement documents without requiring recipients to have access to the BA Requirement Tool.
- Support multiple output formats to match downstream tool requirements (Word documents for managers, CSV for Jira import, JSON for developers).
- Keep MVP export simple and client-side to minimize infrastructure complexity.

---

## 3. Non-Goals

- This feature does **not** push directly to Jira, Confluence, or any external API (file download only).
- This feature does **not** support real-time collaborative export (export is a point-in-time snapshot).
- This feature does **not** provide custom document templates through the UI in Phase 2 (admin-configured only).
- This feature does **not** support incremental exports (each export is a full snapshot).

---

## 4. Users

| Persona | Need |
|---|---|
| **BA (primary)** | Export final requirement documents to share with team / client |
| **Project Manager** | Download meeting minutes (transcript) for records |
| **Developer** | Download requirements as JSON or CSV for backlog tooling |
| **Admin** | Download Jira CSV to bulk-import action items |

---

## 5. Functional Requirements

### FR-EX-001 — Export Transcript as Markdown (MVP)

**Description:** A BA can download the meeting transcript as a Markdown file.

**Acceptance Criteria:**
- AC-EX-001-1: The export includes all transcript segments in `sequence_index` order.
- AC-EX-001-2: Each segment uses `edited_text` if available; falls back to `original_text`.
- AC-EX-001-3: The Markdown format is:
  ```markdown
  # Meeting Transcript: Sprint Review 2026-06-29
  **Date:** 2026-06-29
  **Duration:** 43 minutes

  ---

  **[00:00:00 → 00:00:08]**
  Okay, so let's start the sprint review for this cycle.

  **[00:00:08 → 00:00:15]**
  We completed the login module and the dashboard.
  ```
- AC-EX-001-4: The download filename is `{meeting_title}_{YYYY-MM-DD}_transcript.md` (spaces replaced with hyphens).
- AC-EX-001-5: Export is client-side (no server call); uses pre-fetched segment data.

---

### FR-EX-002 — Export Transcript as Plain Text (MVP)

**Description:** A BA can download the meeting transcript as a plain `.txt` file.

**Acceptance Criteria:**
- AC-EX-002-1: Plain text format:
  ```
  Meeting Transcript: Sprint Review 2026-06-29
  Date: 2026-06-29 | Duration: 43 minutes
  ============================================

  [00:00:00 → 00:00:08]
  Okay, so let's start the sprint review for this cycle.

  [00:00:08 → 00:00:15]
  We completed the login module and the dashboard.
  ```
- AC-EX-002-2: Filename: `{meeting_title}_{YYYY-MM-DD}_transcript.txt`.
- AC-EX-002-3: Client-side generation using pre-fetched segments.

---

### FR-EX-003 — Export Project Requirements as Markdown (Phase 2)

**Description:** A BA can export all approved requirements for a project as a structured Markdown document.

**Acceptance Criteria:**
- AC-EX-003-1: Calling `POST /projects/{id}/exports/markdown` creates an `ExportJob` and returns a job ID.
- AC-EX-003-2: The generated document includes sections: Functional Requirements, Non-Functional Requirements, Business Rules, Open Questions, Decisions, Action Items.
- AC-EX-003-3: Each requirement is formatted as:
  ```markdown
  ### FR-001 — User login with email and password
  **Source:** Sprint Review 2026-06-29
  **Approved:** 2026-06-29

  The system must allow users to authenticate using their registered email address and a password.

  > **Evidence:** "we need users to be able to log in with their email and a password"
  ```
- AC-EX-003-4: Requirements within each section are numbered sequentially (FR-001, FR-002, ...; NFR-001, ...).
- AC-EX-003-5: On job completion, a signed download URL is returned (valid for 1 hour).
- AC-EX-003-6: Filename: `{project_name}_{YYYY-MM-DD}_requirements.md`.

---

### FR-EX-004 — Export Project Requirements as DOCX (Phase 2)

**Description:** Generate a Word-compatible `.docx` file from the same data as the Markdown export.

**Acceptance Criteria:**
- AC-EX-004-1: The DOCX uses the same section structure as the Markdown export.
- AC-EX-004-2: Heading styles are applied: H1 = document title, H2 = section, H3 = requirement title.
- AC-EX-004-3: Evidence quotes use the "Intense Quote" Word style.
- AC-EX-004-4: Generation uses `python-docx` library server-side.
- AC-EX-004-5: Filename: `{project_name}_{YYYY-MM-DD}_requirements.docx`.

---

### FR-EX-005 — Export Requirements as CSV (Phase 2)

**Description:** Generate a CSV for spreadsheet import.

**Acceptance Criteria:**
- AC-EX-005-1: CSV columns: `id`, `type`, `title`, `description`, `source_meeting`, `approved_date`, `status`.
- AC-EX-005-2: UTF-8 with BOM encoding to ensure Excel compatibility.
- AC-EX-005-3: Filename: `{project_name}_{YYYY-MM-DD}_requirements.csv`.

---

### FR-EX-006 — Export Requirements as JSON (Phase 2)

**Description:** Generate a structured JSON file for programmatic consumption.

**Acceptance Criteria:**
- AC-EX-006-1: JSON structure matches the `Requirement` data model schema exactly.
- AC-EX-006-2: Includes a top-level `meta` object with: `project_name`, `export_date`, `requirement_count`.
- AC-EX-006-3: Filename: `{project_name}_{YYYY-MM-DD}_requirements.json`.

---

### FR-EX-007 — Export Action Items as Jira CSV (Phase 2)

**Description:** Generate a Jira-compatible CSV for bulk issue import.

**Acceptance Criteria:**
- AC-EX-007-1: Jira CSV columns: `Summary`, `Description`, `Issue Type`, `Priority`, `Reporter`.
- AC-EX-007-2: Only `action_item` type requirements are included.
- AC-EX-007-3: `Issue Type` defaults to `Task`; `Priority` defaults to `Medium`.
- AC-EX-007-4: Filename: `{project_name}_{YYYY-MM-DD}_jira_action_items.csv`.

---

### FR-EX-008 — Export History (Phase 2)

**Description:** Track all export jobs per project.

**Acceptance Criteria:**
- AC-EX-008-1: Each export creates an `ExportJob` record with: `format`, `status`, `created_at`, `download_url`, `expires_at`.
- AC-EX-008-2: Export history is visible per project in a "Exports" tab.
- AC-EX-008-3: Expired download URLs return `410 Gone`; user can re-export.

---

## 6. MVP vs Phase 2 Scope

| Capability | MVP | Phase 2 |
|---|---|---|
| Transcript export (Markdown) | ✅ | ✅ |
| Transcript export (Plain Text) | ✅ | ✅ |
| Requirements export (Markdown) | ❌ | ✅ |
| Requirements export (DOCX) | ❌ | ✅ |
| Requirements export (CSV) | ❌ | ✅ |
| Requirements export (JSON) | ❌ | ✅ |
| Action items as Jira CSV | ❌ | ✅ |
| Export history | ❌ | ✅ |
| Server-side export job | ❌ | ✅ |
| Custom templates via UI | ❌ | Future |

---

## 7. Constraints & Assumptions

- MVP transcript export is client-side only; no data leaves the machine via the export feature itself.
- Phase 2 DOCX generation requires `python-docx` to be installed in the backend environment.
- Download URLs for server-generated exports are time-limited (1 hour default) and stored as signed paths.
- The system does not email exports; users download files manually.
