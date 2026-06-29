# Design Contract — Requirement Extraction

**Feature:** Requirement Extraction
**Module:** Core
**Version:** 1.0.0
**Last Updated:** 2026-06-29

---

## 1. Design Principles

- **Trust but verify:** LLM output is presented as suggestions, not facts. Visual language (labels, confidence scores) makes the LLM's role clear.
- **Transparency:** Always show where a candidate came from (evidence quote + segment link).
- **Low ceremony:** Triggering extraction is a single button press; users should not need to configure prompts or models.
- **Progress feedback:** LLM calls can take 30–120 seconds; the UI must communicate this clearly without blocking the interface.

---

## 2. Screens

### Screen 1: Transcript View — Extract Button (Entry Point)

The "Extract Requirements" button appears in the Transcript Review toolbar once the transcript is ready.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Sprint Review 2026-06-29        [ Export ▾ ]  [ 🤖 Extract Requirements ]│
├──────────────────────────────────────────────────────────────────────────┤
│  47 segments · 43 min 0 sec · Transcribed ✅                             │
│  ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

Clicking "Extract Requirements" opens a confirmation modal.

---

### Screen 2: Extraction Confirmation Modal

```
┌──────────────────────────────────────────────────┐
│  Extract Requirements                        [✕]  │
├──────────────────────────────────────────────────┤
│                                                  │
│  🤖 AI will analyze your transcript and          │
│  identify:                                       │
│                                                  │
│  ✦  Functional Requirements                      │
│  ✦  Non-Functional Requirements                  │
│  ✦  Business Rules                               │
│  ✦  Open Questions                               │
│  ✦  Decisions                                    │
│  ✦  Action Items                                 │
│                                                  │
│  Using: Ollama / llama3 (local)                  │
│  Estimated time: 1–3 minutes                     │
│                                                  │
│  All candidates require your review before       │
│  being added to the project requirements.        │
│                                                  │
│     [Cancel]   [ 🚀 Start Extraction ]           │
└──────────────────────────────────────────────────┘
```

---

### Screen 3: Extraction — In Progress

Replaces the extract button with a status indicator. User can still read the transcript.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Sprint Review 2026-06-29        [ Export ▾ ]  ⏳ Extracting… (1m 12s) │
├──────────────────────────────────────────────────────────────────────────┤
│  47 segments · 43 min 0 sec · Transcribed ✅                             │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  🤖 AI is analyzing your transcript for requirements…            │   │
│  │     You can continue reading while this runs.                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│  ...transcript segments...                                               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 4: Extraction — Complete

Banner and button redirect to the Requirement Review workspace.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Sprint Review 2026-06-29        [ Export ▾ ]  [ 📋 Review 23 Candidates ]│
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  ✅  Extraction complete — 23 candidates found                   │   │
│  │  FR: 12 · NFR: 3 · Rules: 2 · Questions: 4 · Decisions: 1 · AI: 1│  │
│  │                                                                  │   │
│  │               [ 📋 Review Candidates → ]                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│  ...transcript segments...                                               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 5: Extraction — Failed

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Sprint Review 2026-06-29        [ Export ▾ ]  [ 🤖 Extract Requirements ]│
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  ❌  Extraction failed: LLM_TIMEOUT                              │   │
│  │  The AI did not respond in time. Check your LLM configuration   │   │
│  │  or try again.                                                   │   │
│  │                          [Retry]   [View Log]                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component States Summary

| Component | States |
|---|---|
| Extract button | enabled (transcript ready), disabled (job active), hidden (extraction done) |
| Extraction progress banner | hidden, running, done, failed |
| "Review Candidates" button | hidden, visible (extraction done) |
| Candidate count badge | hidden, shows count breakdown on done |

---

## 4. UX Rules

1. **LLM provider disclosure:** The confirmation modal always shows which LLM is configured (provider name + model). If unconfigured, show an error modal with a link to settings instead of the confirmation.
2. **Non-blocking progress:** The extraction banner is shown inline (not a modal) so users can still scroll and read the transcript during extraction.
3. **Timer display:** Show elapsed time (counting up) in the extract button area while the job runs.
4. **Re-extraction warning:** If candidates already exist (from a previous run), the confirmation modal adds a warning: *"This will replace all existing candidates (including any you have already reviewed)."*
5. **Result summary:** The completion banner shows a one-line breakdown by type (counts per category).
6. **Error codes:** Display the error code name alongside a human-readable explanation. Include a "View Log" option that shows the raw error message in a collapsible section.

---

## 5. Edge States

| Scenario | UI Response |
|---|---|
| LLM not configured | Extract button click shows error modal: "No LLM provider configured. Go to Settings → AI Model." |
| Transcript has 0 segments | Extract button is disabled with tooltip: "No transcript content to analyze." |
| LLM returns 0 candidates | Show completion banner: "Extraction complete — no candidates were identified. You may re-run or add requirements manually." |
| Meeting navigated away during extraction | Persistent banner in meeting list: "⏳ Sprint Review 2026-06-29 — Extraction in progress" |
