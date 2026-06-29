# Functional Specification — Meeting Processing

**Feature:** Meeting Processing
**Module:** Core
**Version:** 1.0.0
**Phase:** MVP
**Last Updated:** 2026-06-29
**Status:** In Review

---

## 1. Summary

Meeting Processing is the pipeline that converts raw audio/video files into time-stamped transcript segments. A user uploads a media file attached to a meeting, the system normalizes the audio, runs offline speech-to-text, and makes the resulting transcript available for review.

---

## 2. Goals

- Enable BAs to upload any common meeting recording format and receive a readable transcript with minimal setup.
- Keep all processing offline by default (no data leaves the machine) to satisfy enterprise data-privacy requirements.
- Provide clear, real-time feedback on processing state so users are never left wondering whether the job is running.

---

## 3. Non-Goals

- This feature does **not** identify individual speakers (deferred to Phase 2 speaker diarization).
- This feature does **not** perform requirement extraction (handled by Requirement Extraction module).
- This feature does **not** support streaming/live recording from a microphone.
- This feature does **not** support batch upload of multiple files in a single request.

---

## 4. Users

| Persona | Need |
|---|---|
| **BA (primary)** | Upload meeting recordings, monitor transcription progress, proceed to transcript review |
| **Tech Lead / Admin** | Configure STT model path; monitor job queue health |

---

## 5. Functional Requirements

### FR-MP-001 — File Upload

**Description:** A user can upload a single media file (.mp3, .wav, .m4a, .mp4) to a specific meeting.

**Acceptance Criteria:**
- AC-MP-001-1: The upload endpoint accepts files with MIME types: `audio/mpeg`, `audio/wav`, `audio/x-m4a`, `video/mp4`.
- AC-MP-001-2: Files larger than 500 MB are rejected with HTTP 413 and a descriptive error message.
- AC-MP-001-3: Files with unsupported MIME types are rejected with HTTP 422 and a list of supported types.
- AC-MP-001-4: On successful upload, the file is persisted to disk and a `MediaFile` record is created in the database with status `uploaded`.
- AC-MP-001-5: The upload endpoint returns the `MediaFile` ID and the meeting's updated status.
- AC-MP-001-6: If a meeting already has a media file, re-uploading replaces the existing file and resets the transcript (previous segments are soft-deleted).

---

### FR-MP-002 — Audio Normalization

**Description:** After upload, the system normalizes the audio to WAV, mono, 16 kHz for downstream STT compatibility.

**Acceptance Criteria:**
- AC-MP-002-1: Normalization is triggered automatically when a processing job is started (not at upload time).
- AC-MP-002-2: The system invokes ffmpeg with flags: `-ac 1 -ar 16000 -f wav`.
- AC-MP-002-3: If ffmpeg is not installed or fails, the `ProcessingJob` transitions to `failed` with error code `FFMPEG_ERROR` and a human-readable message.
- AC-MP-002-4: The normalized file is stored in a configurable working directory (default: `./data/normalized/`).
- AC-MP-002-5: The original uploaded file is preserved; only the normalized copy is used for STT.

---

### FR-MP-003 — Processing Job Lifecycle

**Description:** A user explicitly triggers processing. The system creates a job and tracks its lifecycle.

**Acceptance Criteria:**
- AC-MP-003-1: Calling `POST /meetings/{id}/process` creates a `ProcessingJob` with status `queued` and returns the job ID.
- AC-MP-003-2: Valid job statuses are: `queued`, `normalizing`, `transcribing`, `done`, `failed`.
- AC-MP-003-3: Only one active job (not `done`/`failed`) may exist per meeting at a time; additional trigger requests return HTTP 409.
- AC-MP-003-4: The job status is queryable via `GET /meetings/{id}/status`.
- AC-MP-003-5: On terminal state (`done` or `failed`), the response includes `completed_at` timestamp and, if failed, an `error` object.
- AC-MP-003-6: If the meeting has no media file when process is triggered, the API returns HTTP 422 with error code `NO_MEDIA_FILE`.

---

### FR-MP-004 — Offline Speech-to-Text

**Description:** The system transcribes the normalized audio using a locally configured sherpa-onnx model.

**Acceptance Criteria:**
- AC-MP-004-1: STT runs entirely on-device; no network calls are made during transcription.
- AC-MP-004-2: The model path is configurable via environment variable `SHERPA_ONNX_MODEL_PATH`.
- AC-MP-004-3: If the model file is missing at startup, the server logs a critical error and STT jobs return `failed` with `MODEL_NOT_FOUND`.
- AC-MP-004-4: Each spoken utterance is stored as a `TranscriptSegment` with `start` (seconds), `end` (seconds), and `original_text`.
- AC-MP-004-5: `edited_text` is initialized to `null` (indicating no edits have been made yet).
- AC-MP-004-6: Segments are stored in chronological order and indexed by `sequence_index`.
- AC-MP-004-7: On completion, the meeting status updates to `transcribed` and the job transitions to `done`.

---

### FR-MP-005 — Error Handling & Recovery

**Description:** The system surfaces processing errors clearly and allows re-triggering.

**Acceptance Criteria:**
- AC-MP-005-1: If a job fails at any stage, the `ProcessingJob.status` is set to `failed` and `error_code` + `error_message` are populated.
- AC-MP-005-2: A failed meeting can have a new process job triggered (re-processing is allowed).
- AC-MP-005-3: Re-processing clears any previously created `TranscriptSegment` records for that meeting before re-running.
- AC-MP-005-4: Error codes are machine-readable strings (e.g. `FFMPEG_ERROR`, `MODEL_NOT_FOUND`, `STT_TIMEOUT`).

---

## 6. MVP vs Phase 2 Scope

| Capability | MVP | Phase 2 |
|---|---|---|
| Upload .mp3/.wav/.m4a/.mp4 | ✅ | ✅ |
| ffmpeg normalization | ✅ | ✅ |
| sherpa-onnx offline STT | ✅ | ✅ |
| Per-segment timestamps | ✅ | ✅ |
| Processing job lifecycle | ✅ | ✅ |
| Speaker diarization | ❌ | ✅ |
| VAD + speech enhancement | ❌ | ✅ |
| Cloud STT providers | ❌ | ✅ (configurable) |
| Progress percentage / ETA | ❌ | ✅ |
| Batch file upload | ❌ | ✅ |

---

## 7. Constraints & Assumptions

- ffmpeg must be installed and accessible in the server's `PATH`.
- The sherpa-onnx model must be pre-downloaded; the tool does not auto-download models.
- Maximum supported file size is 500 MB per upload (MVP limit; configurable via env var).
- STT processing time scales linearly with audio duration; no hard timeout in MVP (configurable in Phase 2).
- SQLite is used for MVP; no distributed job queue. Jobs run sequentially on a single background thread.
