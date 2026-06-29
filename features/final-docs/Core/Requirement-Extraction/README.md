# Feature: Requirement Extraction

## Overview

Requirement Extraction uses a configured LLM to analyze the finalized meeting transcript and automatically identify structured requirement artifacts: Functional Requirements, Non-Functional Requirements, Business Rules, Open Questions, Decisions, and Action Items. All extracted items are stored as `RequirementCandidate` records pending human review.

---

## Artifacts

| Artifact | Path | Description |
|---|---|---|
| Functional Specification | `product/functional-specification.md` | User-facing behavior, acceptance criteria, MVP vs Phase 2 scope |
| Technical Contract | `api/technical-contract.md` | REST API endpoints, request/response schemas, error codes |
| Design Contract | `design/design-contract.md` | UI screens, states, layout, UX rules |

---

## Scope

### In Scope (Phase 2)
- LLM-powered extraction from meeting transcript
- Extraction artifact types: Functional Requirements (FR), Non-Functional Requirements (NFR), Business Rules, Open Questions, Decisions, Action Items
- Evidence linking: each candidate includes the source segment IDs and verbatim quote
- Configurable LLM provider (local Ollama or cloud API)
- Extraction job lifecycle tracking
- Candidate storage for downstream review

### Out of Scope
- Manual requirement creation (not LLM-powered; covered in Requirement Review)
- Duplicate detection across projects (future enhancement)
- Glossary term extraction (future enhancement)
- Auto-approval without human review

---

## Dependencies

| System | Role |
|---|---|
| Transcript Review | Provides the source segments; must be in `transcribed` status |
| Requirement Review | Consumes candidates produced here |
| LLM Provider | External or local; configurable via env vars |

---

## Related Features

- [Transcript Review](../Transcript-Review/README.md)
- [Requirement Review](../Requirement-Review/README.md)
