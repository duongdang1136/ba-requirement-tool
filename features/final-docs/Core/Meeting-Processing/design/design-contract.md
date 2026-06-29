# Design Contract — Meeting Processing

**Feature:** Meeting Processing
**Module:** Core
**Version:** 1.0.0
**Last Updated:** 2026-06-29

---

## 1. Design Principles

- **Progressive disclosure:** Upload → Process → Monitor. Each step unlocks the next.
- **Clear system state:** Users always know what the system is doing (uploading, normalizing, transcribing).
- **Non-blocking upload:** Upload progress bar is shown; user can navigate away during long transcriptions.
- **Fail gracefully:** Errors show a specific cause + actionable next step (not a generic "something went wrong").

---

## 2. Screens

### Screen 1: Meeting Detail — No Media Uploaded

Accessed from the meeting list. Initial state when no media has been uploaded.

```
┌──────────────────────────────────────────────────────────────┐
│ ← Projects / Project Alpha / Meetings / Sprint Review 2026   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📄 Sprint Review 2026-06-29                                 │
│  Status: Draft                        Created: 29 Jun 2026   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                     │    │
│  │         📁  Drop audio/video file here              │    │
│  │              or click to browse                     │    │
│  │                                                     │    │
│  │    Supported: .mp3  .wav  .m4a  .mp4  (max 500MB)  │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ℹ  Transcription runs offline — your files stay private.   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

### Screen 2: File Upload — In Progress

Shown while the file is being uploaded to the server.

```
┌──────────────────────────────────────────────────────────────┐
│ ← Projects / Project Alpha / Meetings / Sprint Review 2026   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📄 Sprint Review 2026-06-29                                 │
│  Status: Uploading…                                          │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  📎 standup-2026-06-29.mp3  (24.1 MB)               │    │
│  │  ████████████████░░░░░░░░░░░░  67%                  │    │
│  │  Uploading… please wait                             │    │
│  │                              [✕ Cancel]             │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

### Screen 3: File Uploaded — Ready to Process

Upload complete. User initiates transcription.

```
┌──────────────────────────────────────────────────────────────┐
│ ← Projects / Project Alpha / Meetings / Sprint Review 2026   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📄 Sprint Review 2026-06-29                                 │
│  Status: Uploaded          ✅ standup-2026-06-29.mp3         │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  File ready                                        │     │
│  │  standup-2026-06-29.mp3 · 24.1 MB · mp3           │     │
│  │                               [🔄 Replace file]   │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  🎙  Ready to transcribe                           │     │
│  │  Offline transcription via sherpa-onnx.            │     │
│  │  Estimated time: ~2–4 min for 24 MB audio.         │     │
│  │                                                    │     │
│  │              [ ▶  Start Transcription ]            │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

### Screen 4: Processing — In Progress

Polling state while the job runs.

```
┌──────────────────────────────────────────────────────────────┐
│ ← Projects / Project Alpha / Meetings / Sprint Review 2026   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📄 Sprint Review 2026-06-29                                 │
│  Status: Transcribing…                                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                     │    │
│  │   ⚙  Processing your recording                     │    │
│  │                                                     │    │
│  │   ✅  Normalizing audio…       Done                 │    │
│  │   ⏳  Running transcription…   In progress          │    │
│  │   ○   Saving transcript        Waiting              │    │
│  │                                                     │    │
│  │   This may take a few minutes. You can safely       │    │
│  │   navigate away and come back later.                │    │
│  │                                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

### Screen 5: Processing — Complete

```
┌──────────────────────────────────────────────────────────────┐
│ ← Projects / Project Alpha / Meetings / Sprint Review 2026   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📄 Sprint Review 2026-06-29                                 │
│  Status: Transcribed ✅                                       │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  ✅  Transcription complete!                         │    │
│  │      47 segments · Completed in 2m 43s              │    │
│  │                                                     │    │
│  │         [ 📝  Review Transcript ]                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

### Screen 6: Processing — Failed

```
┌──────────────────────────────────────────────────────────────┐
│ ← Projects / Project Alpha / Meetings / Sprint Review 2026   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📄 Sprint Review 2026-06-29                                 │
│  Status: Failed ❌                                            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  ❌  Transcription failed                            │    │
│  │                                                     │    │
│  │  Error: FFMPEG_ERROR                                │    │
│  │  ffmpeg could not process this file. The recording  │    │
│  │  may be corrupted or in an unsupported codec.       │    │
│  │                                                     │    │
│  │  [ 🔄  Replace File & Retry ]   [ ℹ  View Log ]    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Component States Summary

| Component | States |
|---|---|
| Drop zone | idle, hover (drag-over), uploading, uploaded, error |
| Process button | hidden (no file), enabled (file uploaded), disabled (job active) |
| Status stepper | hidden, normalizing, transcribing, done, failed |
| Error banner | hidden, ffmpeg_error, model_not_found, generic |

---

## 4. UX Rules

1. **Drag & drop zone** is the primary upload affordance; clicking also opens a native file picker.
2. **MIME type validation** happens client-side before upload to give immediate feedback without a server round-trip.
3. **File size validation** also happens client-side; files > 500 MB show an inline error on the drop zone.
4. **Start Transcription** button is shown only after a successful upload; it is hidden/disabled if a job is active.
5. **Polling interval:** Frontend polls `GET /meetings/{id}/status` every 3 seconds while job status is not `done` or `failed`.
6. **Navigation away:** A toast notification ("Transcription running in background") is shown when the user navigates away from the page during an active job.
7. **Re-upload warning:** If a media file already exists, replacing it shows a confirmation modal: *"Replacing this file will delete the existing transcript. This cannot be undone."*
8. **Accessibility:** All icons include aria-labels; the stepper announces step completion to screen readers via `aria-live="polite"`.

---

## 5. Empty / Edge States

| Scenario | UI Response |
|---|---|
| No ffmpeg on server | Job fails with `FFMPEG_ERROR`; UI shows install instructions link |
| Model not found | Job fails with `MODEL_NOT_FOUND`; UI links to model download guide |
| File is silent / empty audio | Job completes with 0 segments; UI shows "No speech detected" hint |
| Meeting already has `done` job | "Re-transcribe" link shown; clicking shows confirmation modal |
