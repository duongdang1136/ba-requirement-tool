# Feature: Meeting Processing

## Overview

Meeting Processing is the entry point of the BA Requirement Tool pipeline. It handles audio/video file upload, validates media integrity, normalizes audio to a standardized format using ffmpeg, runs offline speech-to-text transcription via sherpa-onnx, and tracks the processing job lifecycle through to completion.

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
- Upload audio/video files (`.mp3`, `.wav`, `.m4a`, `.mp4`)
- Server-side file validation (format, size)
- Audio normalization: ffmpeg → WAV, mono, 16 kHz
- Offline STT: sherpa-onnx, no speaker diarization
- Processing job status tracking (queued → processing → done / failed)
- Transcript output with timestamps (per-segment)

### Out of Scope (MVP — deferred to Phase 2)
- Speaker diarization
- Voice Activity Detection (VAD)
- Speech enhancement / noise reduction
- Real-time streaming transcription
- Cloud-based STT providers

---

## Dependencies

| System | Role |
|---|---|
| Project & Meeting Management | Meeting must exist before media upload |
| Transcript Review | Consumes the transcript segments produced here |
| ffmpeg | Audio normalization |
| sherpa-onnx | Offline speech-to-text engine |

---

## Related Features

- [Transcript Review](../Transcript-Review/README.md)
- [Project & Meeting Management](../../Project-Management/Project-and-Meeting/README.md)
