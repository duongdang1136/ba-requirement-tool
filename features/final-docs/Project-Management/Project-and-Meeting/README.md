# Feature: Project & Meeting Management

## Overview

Project & Meeting Management provides the organizational scaffolding for the BA Requirement Tool. BAs create Projects to group related meetings, then create Meeting records within a project before uploading audio files. This feature handles the full lifecycle of both entities: creation, listing, viewing, and archiving.

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
- Create, list, and view Projects
- Create, list, and view Meetings within a project
- Meeting status lifecycle: draft → uploaded → transcribed → extraction_done → reviewed
- Archive / soft-delete projects and meetings
- Project and meeting search (basic title filter)

### Out of Scope (MVP — deferred)
- User accounts and authentication (single-user MVP)
- Project sharing / team collaboration
- Meeting tags and custom metadata
- Project templates
- Calendar integration

---

## Dependencies

| System | Role |
|---|---|
| Meeting Processing | Meetings must exist before media upload |
| All Core features | Project is the root entity for all BA artifacts |

---

## Related Features

- [Meeting Processing](../../Core/Meeting-Processing/README.md)
- [Export](../../Core/Export/README.md)
