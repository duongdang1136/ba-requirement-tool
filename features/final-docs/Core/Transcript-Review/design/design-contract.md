# Design Contract — Transcript Review

**Feature:** Transcript Review
**Module:** Core
**Version:** 1.0.0
**Last Updated:** 2026-06-29

---

## 1. Design Principles

- **Non-destructive editing:** Always show original alongside edited; never hide source data.
- **Minimal friction:** One click to edit, auto-save on exit — no explicit save button required per segment.
- **Scannable layout:** Timestamps left-aligned, text right; readable at a glance when scrolling quickly.
- **Confidence-preserving:** Muted visual treatment of original text so it doesn't compete with the edited version.

---

## 2. Screens

### Screen 1: Transcript View — Default (Read Mode)

Full-width transcript list. Each row = one segment.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Sprint Review 2026-06-29                     [ Export ▾ ]  [ Extract ] │
├──────────────────────────────────────────────────────────────────────────┤
│  47 segments · 43 min 0 sec · Transcribed ✅                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  00:00:00 → 00:00:08                                             │   │
│  │  ✏ Okay, so let's start the sprint review for this cycle.        │   │
│  │  ░ okay so let's start the sprint review for this cycle          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  00:00:08 → 00:00:15                                             │   │
│  │  we completed the login module and the dashboard                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  00:00:15 → 00:00:28                                             │   │
│  │  the authentication flow was reviewed and accepted               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

**Legend:**
- `✏ [text]` — has user edit (edited_text shown, styled distinctly)
- `░ [text]` — original STT text (shown in muted color below edited)
- Plain `[text]` — no edit yet; shows original_text as primary

---

### Screen 2: Transcript View — Segment in Edit Mode

User has clicked on a segment to edit it.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Sprint Review 2026-06-29                     [ Export ▾ ]  [ Extract ] │
├──────────────────────────────────────────────────────────────────────────┤
│  47 segments · 43 min 0 sec · Transcribed ✅                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  00:00:08 → 00:00:15                                   [Revert]  │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │ We completed the login module and the dashboard.         │  │   │
│  │  └────────────────────────────────────────────────────────────┘  │   │
│  │  ░ Original: we completed the login module and the dashboard     │   │
│  │                          [✕ Cancel]  [Ctrl+↵ Save]              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Edit mode behaviors:**
- The textarea auto-focuses and cursor is placed at end of text.
- Original text shown in muted label below the textarea (read-only reference).
- "Revert" button shown only if `edited_text != null`.
- `[✕ Cancel]` reverts to display mode without saving.
- `[Ctrl+↵ Save]` saves immediately.
- Clicking outside the segment card triggers auto-save.

---

### Screen 3: Transcript View — Saving State

```
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  00:00:08 → 00:00:15                                ⏳ Saving…  │   │
│  │  We completed the login module and the dashboard.                │   │
│  │  ░ we completed the login module and the dashboard              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
```

---

### Screen 4: Transcript View — Saved State (transient, 2s)

```
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  00:00:08 → 00:00:15                                    Saved ✓  │   │
│  │  ✏ We completed the login module and the dashboard.              │   │
│  │  ░ we completed the login module and the dashboard              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
```

---

### Screen 5: Transcript View — Save Error State

```
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  00:00:08 → 00:00:15                                             │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │ We completed the login module and the dashboard.           │  │   │
│  │  └────────────────────────────────────────────────────────────┘  │   │
│  │  ⚠ Could not save.  [Retry]                                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
```

---

### Screen 6: Export Modal

```
┌──────────────────────────────────────────────────┐
│  Export Transcript                           [✕]  │
├──────────────────────────────────────────────────┤
│                                                  │
│  Choose format:                                  │
│                                                  │
│  ○  📝  Markdown (.md)                          │
│  ○  📄  Plain Text (.txt)                       │
│                                                  │
│  ℹ  Edited text is used where available;        │
│     original text fills in the rest.             │
│                                                  │
│        [Cancel]   [ Download ]                   │
└──────────────────────────────────────────────────┘
```

---

### Screen 7: Revert Confirmation Modal

```
┌──────────────────────────────────────────────────┐
│  Revert Segment                              [✕]  │
├──────────────────────────────────────────────────┤
│                                                  │
│  This will discard your edit and restore the     │
│  original transcription for this segment.        │
│                                                  │
│  Original text:                                  │
│  "we completed the login module and the          │
│  dashboard"                                      │
│                                                  │
│  This cannot be undone.                          │
│                                                  │
│        [Cancel]   [ Revert ]                     │
└──────────────────────────────────────────────────┘
```

---

## 3. Component States Summary

| Component | States |
|---|---|
| Segment card | read, edit, saving, saved, error, reverted |
| Segment text area | pristine (original only), edited (has edited_text) |
| Save indicator | hidden, saving, saved (2s), error |
| Revert button | hidden (no edits), visible (edited_text exists) |
| Export button | always visible when transcript is loaded |
| Extract button | disabled (MVP, always shown but inactive until Phase 2) |

---

## 4. UX Rules

1. **Single edit at a time:** Clicking a new segment while another is in edit mode auto-saves the previous segment first, then activates the new one.
2. **Empty text prevention:** The save action is disabled (button greyed + Ctrl+Enter blocked) if the textarea is empty or contains only whitespace.
3. **Keyboard shortcuts:**
   - `Ctrl+Enter` — save current segment
   - `Escape` — cancel edit (no save)
4. **Scroll position:** When auto-saving on blur, do not change scroll position.
5. **Edited indicator:** A subtle left-border color change (e.g. blue) + ✏ icon on the segment header marks segments with edits. Reverted segments return to the default style.
6. **Loading state:** On initial page load, show a skeleton list of 10 segment cards while data is fetched.
7. **Empty transcript:** If `total_count === 0`, show: *"No speech was detected in this recording. You can re-transcribe or continue to export."*
8. **Accessibility:** `textarea` has `aria-label="Edit segment {index}"`. Save/Cancel buttons are focusable. Tab order: timestamp → textarea → cancel → save → next segment.

---

## 5. Edge States

| Scenario | UI Response |
|---|---|
| Transcript not ready | Redirect to Meeting detail with toast: "Transcript not available yet" |
| Network loss during save | Show error state in segment; retry button available |
| All segments have edits | Subtle "All segments reviewed" banner at top of list |
| Very long segment text (>500 chars) | Textarea expands to show full text; max-height with scroll |
| Page reload with unsaved edits | On reload, show unsaved state is recovered from last successful save (no local draft in MVP) |
