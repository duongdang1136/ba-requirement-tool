# Feature: Transcript Review

## Overview

Transcript Review is the editing interface that allows BAs to read, correct, and finalize the raw speech-to-text output before it is used for requirement extraction. The UI presents time-stamped segments side-by-side with an inline editor, and persists edits as `edited_text` without overwriting the original STT output.

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
- Display all transcript segments with start/end timestamps
- Inline editing of individual segments (edited_text)
- Visual diff: original_text vs edited_text
- Auto-save on blur / manual save button
- Segment-level read/write state
- Export transcript as Markdown or plain TXT
- Jump to segment by timestamp click

### Out of Scope (MVP — deferred to Phase 2)
- Speaker label assignment per segment
- Merge / split segments
- Audio playback synchronized with highlighted segment
- Find & replace across all segments
- Bulk segment edits

---

## Dependencies

| System | Role |
|---|---|
| Meeting Processing | Produces the `TranscriptSegment` records consumed here |
| Requirement Extraction | Consumes the finalized (edited) transcript |
| Export | Exports transcript as part of meeting document |

---

## Related Features

- [Meeting Processing](../Meeting-Processing/README.md)
- [Requirement Extraction](../Requirement-Extraction/README.md)
