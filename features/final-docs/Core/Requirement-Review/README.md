# Feature: Requirement Review

## Overview

Requirement Review is a three-panel workspace where BAs evaluate LLM-generated requirement candidates. The left panel shows the transcript for evidence lookup, the center panel lists candidates for approve/reject/edit actions, and the right panel displays the evidence quote and source segments for the selected candidate.

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
- Three-panel review workspace: transcript / candidates / evidence
- Approve a candidate (promotes to Requirement)
- Reject a candidate (with optional reason)
- Edit a candidate's title and description before approving
- Add reviewer notes
- Filter candidates by type and status
- View approved requirements per project

### Out of Scope
- Bulk approve/reject (future enhancement)
- Requirement priority / effort scoring (future enhancement)
- Linking requirements to backlog items / Jira (handled in Export)
- Custom requirement fields / templates (future)

---

## Dependencies

| System | Role |
|---|---|
| Requirement Extraction | Produces `RequirementCandidate` records consumed here |
| Export | Consumes approved `Requirement` records for document generation |
| Project & Meeting Management | Requirements belong to a project context |

---

## Related Features

- [Requirement Extraction](../Requirement-Extraction/README.md)
- [Export](../Export/README.md)
