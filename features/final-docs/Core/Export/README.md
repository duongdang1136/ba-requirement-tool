# Feature: Export

## Overview

Export allows BAs to generate structured documentation artifacts from approved project requirements and meeting transcripts. Supported formats in Phase 2 include Markdown, DOCX, CSV, JSON, and Jira CSV. MVP supports Markdown and plain TXT transcript export only.

---

## Artifacts

| Artifact | Path | Description |
|---|---|---|
| Functional Specification | `product/functional-specification.md` | User-facing behavior, acceptance criteria, MVP vs Phase 2 scope |
| Technical Contract | `api/technical-contract.md` | REST API endpoints, request/response schemas, error codes |
| Design Contract | `design/design-contract.md` | UI screens, states, layout, UX rules |

---

## Scope

### In Scope (MVP)
- Export meeting transcript as Markdown (`.md`)
- Export meeting transcript as plain text (`.txt`)
- Client-side generation (no server round-trip for transcript export)

### In Scope (Phase 2)
- Export project requirements as Markdown document
- Export project requirements as DOCX (Word)
- Export project requirements as CSV (spreadsheet-compatible)
- Export project requirements as JSON (machine-readable)
- Export action items / open questions as Jira-compatible CSV
- Server-side export job with download link
- Export history per project

### Out of Scope
- Direct Jira API push (future integration)
- Confluence page publish (future)
- Custom document templates via UI (future)

---

## Dependencies

| System | Role |
|---|---|
| Transcript Review | Source of transcript segments for export |
| Requirement Review | Source of approved Requirements / Questions / Decisions / Action Items |
| Project & Meeting Management | Project metadata included in export headers |

---

## Related Features

- [Transcript Review](../Transcript-Review/README.md)
- [Requirement Review](../Requirement-Review/README.md)
