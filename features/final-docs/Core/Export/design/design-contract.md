# Design Contract — Export

**Feature:** Export
**Module:** Core
**Version:** 1.0.0
**Last Updated:** 2026-06-29

---

## 1. Design Principles

- **Format picker, not multiple buttons:** One "Export" button opens a format picker to avoid cluttering the toolbar.
- **Immediate feedback for client-side exports (MVP):** No loading state; download starts immediately.
- **Job feedback for server-side exports (Phase 2):** Show job progress inline; provide a clear download CTA when ready.
- **Format availability transparency:** Unavailable formats (e.g. DOCX if `python-docx` is not installed) are shown greyed-out with a tooltip explaining why.

---

## 2. Screens

### Screen 1: Transcript View — Export Dropdown (MVP)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ← Sprint Review 2026-06-29        [ Export ▾ ]  [ Extract Requirements ] │
│                                   ┌──────────────────────────┐           │
│                                   │  Export Transcript       │           │
│                                   │  ──────────────────────  │           │
│                                   │  📝  Markdown (.md)      │           │
│                                   │  📄  Plain Text (.txt)   │           │
│                                   └──────────────────────────┘           │
└──────────────────────────────────────────────────────────────────────────┘
```

Clicking any format triggers an immediate browser download.

---

### Screen 2: Requirement Review / Project View — Export Modal (Phase 2)

```
┌────────────────────────────────────────────────────┐
│  Export Project Requirements                  [✕]  │
├────────────────────────────────────────────────────┤
│                                                    │
│  Project Alpha · 12 approved requirements          │
│                                                    │
│  Select format:                                    │
│                                                    │
│  ○  📝  Markdown (.md)          ← Recommended      │
│  ○  📄  Word Document (.docx)                      │
│  ○  📊  CSV Spreadsheet (.csv)                     │
│  ○  🔧  JSON (.json)                               │
│  ○  🐛  Jira CSV (action items only)               │
│                                                    │
│  ℹ  Export includes all active requirements as    │
│     of right now. Rejected items are excluded.    │
│                                                    │
│     [Cancel]      [ Generate Export ]             │
└────────────────────────────────────────────────────┘
```

---

### Screen 3: Export Job — In Progress (Phase 2)

Shown after "Generate Export" is clicked. Modal transitions to a loading state.

```
┌────────────────────────────────────────────────────┐
│  Export Project Requirements                  [✕]  │
├────────────────────────────────────────────────────┤
│                                                    │
│  ⏳  Generating Markdown export…                   │
│                                                    │
│  This usually takes a few seconds.                 │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

### Screen 4: Export Job — Complete (Phase 2)

```
┌────────────────────────────────────────────────────┐
│  Export Ready                                 [✕]  │
├────────────────────────────────────────────────────┤
│                                                    │
│  ✅  Your export is ready!                         │
│                                                    │
│  project-alpha-2026-06-29-requirements.md          │
│  24.1 KB · Valid for 60 minutes                    │
│                                                    │
│     [ ⬇  Download File ]                          │
│                                                    │
│  [ View Export History ]                           │
└────────────────────────────────────────────────────┘
```

---

### Screen 5: Export Job — Failed (Phase 2)

```
┌────────────────────────────────────────────────────┐
│  Export Failed                                [✕]  │
├────────────────────────────────────────────────────┤
│                                                    │
│  ❌  Could not generate DOCX export.               │
│                                                    │
│  Error: DOCX_GENERATION_ERROR                      │
│  python-docx encountered an error during           │
│  document generation.                              │
│                                                    │
│     [✕ Close]      [ Retry ]                      │
└────────────────────────────────────────────────────┘
```

---

### Screen 6: Export History (Phase 2)

```
┌──────────────────────────────────────────────────────────────────┐
│ Project Alpha / Exports                                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📝  Markdown · Requirements      29 Jun 2026 15:00  24.1 KB    │
│      ✅ Done    [ ⬇ Download ]  (expires in 45 min)             │
│  ──────────────────────────────────────────────────────────      │
│  📊  CSV · Requirements           28 Jun 2026 10:30  4.2 KB     │
│      ⌛ Expired   [ Re-export ]                                  │
│  ──────────────────────────────────────────────────────────      │
│  🐛  Jira CSV · Action Items      27 Jun 2026 09:15  1.8 KB     │
│      ✅ Done    [ ⬇ Download ]  (expires in 2 min)              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Component States Summary

| Component | States |
|---|---|
| Export dropdown (MVP) | closed, open, downloading |
| Export modal (Phase 2) | format-picker, generating, done, failed |
| Format option | enabled, disabled (unavailable, greyed-out) |
| Download button | hidden (job not done), enabled (done), expired |
| Export history row | done (with download), expired (re-export CTA), failed |

---

## 4. UX Rules

1. **Transcript export (MVP):** Clicking a format immediately triggers a browser download — no modal, no confirmation. This is the lowest-friction path.
2. **Requirements export (Phase 2):** Opens a modal with format selection because multiple formats exist and the user should choose deliberately.
3. **Format availability:** If DOCX backend library is not installed, the DOCX option is rendered with `opacity: 0.4` and a tooltip: *"DOCX export is not available on this server. Contact your admin."*
4. **Download TTL visibility:** The download link shows "expires in N min" with a countdown. When expired, it changes to "⌛ Expired — Re-export" with a button to re-run the job.
5. **Export history row limit:** Show the 10 most recent exports in the history tab; older ones are archived (not shown) with a "Show older" expand control.
6. **Filename convention:** Always use kebab-case, no spaces: `{project-name}-{YYYY-MM-DD}-requirements.{ext}`.
7. **Empty state:** If no requirements exist when opening the Phase 2 export modal, show: *"No approved requirements to export. Review candidates first."* with a "Go to Review" button.

---

## 5. Edge States

| Scenario | UI Response |
|---|---|
| No transcript segments | Export Transcript button is disabled with tooltip: "No transcript available." |
| Export URL expired | Show "Expired" badge + "Re-export" CTA in export history |
| DOCX library missing | DOCX option greyed out with tooltip; other formats still available |
| Zero approved requirements (Phase 2 export) | Modal shows empty state + redirect CTA instead of format picker |
| Download URL still valid but user re-clicks | Re-uses same download URL (no new job created if original is still valid) |
