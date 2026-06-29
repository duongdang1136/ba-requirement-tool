# Design Contract — Project & Meeting Management

**Feature:** Project & Meeting Management
**Module:** Project Management
**Version:** 1.0.0
**Last Updated:** 2026-06-29

---

## 1. Design Principles

- **Flat navigation:** Two levels only — Projects → Meetings. Deep nesting is avoided.
- **Status as progress indicator:** Meeting status badges are the primary affordance for understanding where a meeting is in the pipeline.
- **Action-driven cards:** Each meeting card shows the single most relevant next action (e.g. "Upload File", "Process", "Review Transcript", "Extract").
- **Minimal onboarding friction:** Creating a project + meeting + uploading a file should be achievable in under 60 seconds.

---

## 2. Screens

### Screen 1: Project List (Home)

```
┌──────────────────────────────────────────────────────────────────┐
│  BA Requirement Tool                          [+ New Project]    │
├──────────────────────────────────────────────────────────────────┤
│  🔍 Search projects…                                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  📁  E-commerce Redesign 2026                            │   │
│  │  5 meetings  ·  Last updated 2 hours ago                 │   │
│  │  ████████░░  4/5 meetings processed                      │   │
│  │                                          [ Open → ]      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  📁  Mobile App MVP                                      │   │
│  │  2 meetings  ·  Last updated yesterday                   │   │
│  │  ██░░░░░░░░  1/2 meetings processed                      │   │
│  │                                          [ Open → ]      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  [ Show archived (1) ]                                           │
└──────────────────────────────────────────────────────────────────┘
```

---

### Screen 2: New Project Modal

```
┌──────────────────────────────────────────────────┐
│  New Project                                 [✕]  │
├──────────────────────────────────────────────────┤
│                                                  │
│  Project Name *                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ E-commerce Redesign 2026                   │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  Description (optional)                          │
│  ┌────────────────────────────────────────────┐  │
│  │ Full redesign for Q3 launch.               │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│     [Cancel]            [ Create Project ]       │
└──────────────────────────────────────────────────┘
```

---

### Screen 3: Project Detail — Meeting List

```
┌──────────────────────────────────────────────────────────────────┐
│ ← Projects / E-commerce Redesign 2026        [+ New Meeting]     │
├──────────────────────────────────────────────────────────────────┤
│  📁  E-commerce Redesign 2026                                    │
│  Full redesign of the storefront for the 2026 Q3 launch.         │
│                                          [⋯ Archive Project]     │
├──────────────────────────────────────────────────────────────────┤
│  🔍 Search meetings…                                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  🟢 Reviewed                                             │   │
│  │  Kick-off Meeting                   28 Jun 2026          │   │
│  │  23 requirements approved                                │   │
│  │                               [ Export → ]              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  🔵 Transcribed                                          │   │
│  │  Sprint Review 2026-06-29           29 Jun 2026          │   │
│  │  47 segments · ready to extract                          │   │
│  │                [ Review Transcript ]  [ Extract → ]     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ⚪ Draft                                                 │   │
│  │  Design Review Session              30 Jun 2026          │   │
│  │  No recording uploaded yet                               │   │
│  │                                    [ Upload File ]       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ❌ Failed                                                │   │
│  │  Stakeholder Interview              27 Jun 2026          │   │
│  │  FFMPEG_ERROR — processing failed                        │   │
│  │                          [ Replace File & Retry ]        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

### Screen 4: New Meeting Modal

```
┌──────────────────────────────────────────────────┐
│  New Meeting                                 [✕]  │
├──────────────────────────────────────────────────┤
│                                                  │
│  Meeting Title *                                 │
│  ┌────────────────────────────────────────────┐  │
│  │ Sprint Review 2026-06-29                   │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  Date                                            │
│  ┌────────────────┐                              │
│  │  29 Jun 2026   │  📅                          │
│  └────────────────┘                              │
│                                                  │
│  Description (optional)                          │
│  ┌────────────────────────────────────────────┐  │
│  │ End of Sprint 12 review.                   │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│     [Cancel]           [ Create Meeting ]        │
└──────────────────────────────────────────────────┘
```

---

### Screen 5: Meeting Status Badge Reference

| Status | Badge Color | Label | Primary CTA on Card |
|---|---|---|---|
| `draft` | Grey | Draft | "Upload File" |
| `uploaded` | Blue | Uploaded | "Start Transcription" |
| `processing` | Blue (pulse) | Processing… | (no CTA, spinner) |
| `transcribed` | Teal | Transcribed | "Review Transcript" / "Extract" |
| `extracting` | Blue (pulse) | Extracting… | (no CTA, spinner) |
| `extraction_done` | Purple | Ready to Review | "Review Requirements" |
| `reviewed` | Green | Reviewed ✅ | "Export" |
| `failed` | Red | Failed ❌ | "Replace File & Retry" |

---

## 3. Component States Summary

| Component | States |
|---|---|
| Project card | active, archived |
| Meeting card | one state per `MeetingStatus` |
| New project modal | closed, open, saving, saved, error |
| New meeting modal | closed, open, saving, saved, error |
| Search filter | empty, has-query, no-results |

---

## 4. UX Rules

1. **Meeting cards are action-oriented:** Each card shows exactly one primary CTA matching the current status. The user always knows their next step without reading docs.
2. **Status polling on list:** If any meeting is in `processing` or `extracting` status, the meeting list silently polls `GET /projects/{id}/meetings` every 10 seconds to refresh status badges.
3. **Create-then-upload flow:** After creating a new meeting, the modal closes and the user is navigated directly to the Meeting detail page (which shows the upload drop zone).
4. **Empty state — no projects:** On first launch, show a large "Get started" empty state:
   ```
   You don't have any projects yet.
   [ + Create your first project ]
   ```
5. **Archive confirmation:** Archiving a project shows a confirmation dialog: *"Archive 'E-commerce Redesign 2026'? It will be hidden from your active projects list."* Archive is reversible.
6. **Search debounce:** Name search fires after 300 ms of typing inactivity. Results update inline without a page reload.
7. **Meeting date display:** Dates are shown in human-friendly format relative to today ("Today", "Yesterday", "28 Jun 2026") in the meeting list.

---

## 5. Edge States

| Scenario | UI Response |
|---|---|
| No projects yet | Empty state with "Create your first project" CTA |
| Project has 0 meetings | Project detail shows empty state: "No meetings yet. Add your first meeting to get started." |
| Search returns no results | Show: "No meetings matching '{query}'. [Clear search]" |
| Project name taken | Inline validation error below name field: "A project with this name already exists." |
| Archived project viewed | Subtle "Archived" banner at top of project detail; "Restore Project" button |
| Meeting creation on archived project | Backend returns `PROJECT_ARCHIVED`; UI shows toast: "Cannot add a meeting to an archived project." |
