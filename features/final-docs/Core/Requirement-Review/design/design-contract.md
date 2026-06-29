# Design Contract — Requirement Review

**Feature:** Requirement Review
**Module:** Core
**Version:** 1.0.0
**Last Updated:** 2026-06-29

---

## 1. Design Principles

- **Three-panel workspace:** Left = transcript context, Center = candidates to act on, Right = evidence detail. Inspired by IDE split-view patterns.
- **Keyboard-first review flow:** Arrow keys to navigate candidates, A to approve, R to reject — optimized for high-volume review.
- **Decision confidence:** Always show the AI's confidence score and evidence quote alongside each candidate so the BA can decide quickly.
- **No destructive discards:** Rejections are soft; nothing is permanently deleted from the review view.

---

## 2. Screens

### Screen 1: Review Workspace — Three-Panel Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ← Sprint Review 2026-06-29 / Requirement Review        Progress: 12 / 23  [Export ▾]    │
├────────────────────────┬─────────────────────────────────┬───────────────────────────────┤
│  TRANSCRIPT            │  CANDIDATES             [Filters]│  EVIDENCE                    │
│  (47 segments)         │  All  FR  NFR  Rule  ?  ✓  ✗    │                              │
├────────────────────────┤─────────────────────────────────┤───────────────────────────────┤
│                        │  🟢 FR  ·  pending               │  Functional Requirement      │
│  00:00:00 → 00:00:08   │  User login with email/password  │  ──────────────────────────  │
│  Okay, so let's start  │  Confidence: 92%                 │  Title                       │
│  the sprint review…    │                                  │  ┌──────────────────────────┐│
│                        │  ─────────────────────────────   │  │User login with email/pw  ││
│  00:00:08 → 00:00:15   │  ⚪ FR  ·  pending               │  └──────────────────────────┘│
│  We completed the      │  Dashboard role-based access     │                              │
│  login module and      │  Confidence: 85%                 │  Description                 │
│  the dashboard.        │                                  │  ┌──────────────────────────┐│
│                        │  ─────────────────────────────   │  │The system must allow     ││
│  00:00:15 → 00:00:28   │  ⚪ NFR  ·  pending              │  │users to authenticate     ││
│  The authentication    │  Page load < 2 seconds           │  │using email + password.   ││
│  flow was reviewed     │  Confidence: 78%                 │  └──────────────────────────┘│
│  and accepted.         │                                  │                              │
│                        │  ─────────────────────────────   │  Evidence from transcript   │
│  ► 00:00:28 → 00:00:45 │  ✅ FR  ·  approved              │  ┌──────────────────────────┐│
│  [highlighted]         │  Password reset flow             │  │"we need users to be able ││
│  we need users to be   │                                  │  │to log in with their      ││
│  able to log in with   │  ─────────────────────────────   │  │email and a password"     ││
│  their email and a     │  ❌ FR  ·  rejected               │  └──────────────────────────┘│
│  password              │  SSO via Google                  │  Source: 00:00:28 → 00:00:45│
│                        │                                  │                              │
│  ...                   │  ...                             │  Reviewer Note               │
│                        │                                  │  ┌──────────────────────────┐│
│                        │                                  │  │Add a note…               ││
│                        │                                  │  └──────────────────────────┘│
│                        │                                  │                              │
│                        │                                  │  [✕ Reject]  [✔ Approve]    │
└────────────────────────┴─────────────────────────────────┴───────────────────────────────┘
```

**Panel widths (default):** Left 25% / Center 35% / Right 40% — panels are resizable via drag handles.

---

### Screen 2: Approval — Inline Edit Before Approving

```
│  EVIDENCE                                                   │
│  Functional Requirement                                     │
│  ──────────────────────────────────────────────────────     │
│  Title                                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │ User login with email and password (edited)        │    │
│  └────────────────────────────────────────────────────┘    │
│  ▸ Original: "User login with email/password" [show]       │
│                                                             │
│  Description                                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │ The system must allow users to authenticate using  │    │
│  │ their registered email address and a password.     │    │
│  │ Failed attempts must be tracked. Account locks     │    │
│  │ after 5 failures.                                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│  Reviewer Note                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Confirmed with product owner.                      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                             │
│                          [✕ Reject]   [✔ Approve]          │
```

---

### Screen 3: Reject Modal

```
┌──────────────────────────────────────────────────┐
│  Reject Candidate                            [✕]  │
├──────────────────────────────────────────────────┤
│                                                  │
│  "User login with email and password"            │
│                                                  │
│  Rejection reason (optional):                    │
│  ┌────────────────────────────────────────────┐  │
│  │ Out of scope for this release.             │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  This candidate will be marked as rejected but  │
│  will remain visible in the review history.     │
│                                                  │
│     [Cancel]         [ Reject ]                  │
└──────────────────────────────────────────────────┘
```

---

### Screen 4: Project Requirements View

Navigated from the project-level sidebar.

```
┌──────────────────────────────────────────────────────────────────┐
│ Project Alpha / Requirements                    [ Export All ▾ ] │
├──────────────────────────────────────────────────────────────────┤
│  All (12)  FR (8)  NFR (2)  Rules (1)  Questions (4)  ...       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🟢 FR  · active                                                 │
│  User login with email and password                              │
│  From: Sprint Review 2026-06-29  · Approved: 29 Jun 2026        │
│  ──────────────────────────────────────────────────────────      │
│  🟢 FR  · active                                                 │
│  Dashboard role-based access                                     │
│  From: Kick-off Meeting          · Approved: 28 Jun 2026        │
│  ──────────────────────────────────────────────────────────      │
│  🔵 Question  · active                                           │
│  What is the password complexity policy?                         │
│  From: Sprint Review 2026-06-29  · Approved: 29 Jun 2026        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Component States Summary

| Component | States |
|---|---|
| Candidate card (center panel) | pending, selected, approved, rejected |
| Evidence panel | empty (no selection), loaded, editing, saving |
| Approve button | enabled (pending or rejected candidate), disabled (already approved) |
| Reject button | enabled (pending or approved candidate) |
| Progress indicator | 0/N to N/N with color transition (grey → green as complete) |
| Left transcript panel | idle, segment highlighted (when candidate selected) |

---

## 4. Type Badge Colors

| Type | Badge Color |
|---|---|
| `functional_requirement` | Green |
| `non_functional_requirement` | Blue |
| `business_rule` | Purple |
| `open_question` | Amber |
| `decision` | Teal |
| `action_item` | Orange |

---

## 5. UX Rules

1. **Keyboard navigation:**
   - `↑` / `↓` — navigate between candidates in the center panel
   - `A` — approve selected candidate (with current edits)
   - `R` — reject selected candidate (opens rejection modal)
   - `E` — focus the description edit textarea
   - `Esc` — cancel edit / close modal

2. **Auto-advance:** After approving or rejecting, the selection automatically moves to the next `pending` candidate.

3. **Transcript scroll sync:** When a candidate is selected, the left transcript panel smoothly scrolls to the first source segment and highlights all source segments with a soft background color.

4. **Edit auto-save:** Changes to `title`, `description`, or `reviewer_note` auto-save 1 second after the user stops typing (debounce). A "Saved" toast appears briefly.

5. **Confidence score visual:** Shown as both a percentage number and a color-coded pill (green ≥ 80%, amber 50–79%, red < 50%).

6. **Reject vs Approve state persistence:** If the user refreshes the page, all candidate statuses are reloaded from the server; no local state is lost.

7. **Panel collapse:** Each panel can be collapsed to a narrow strip to maximize space for the active panel (useful on smaller screens).

---

## 6. Edge States

| Scenario | UI Response |
|---|---|
| No candidates (extraction returned 0) | Center panel shows: "No candidates were extracted. Re-run extraction or add requirements manually." |
| All candidates reviewed | Center panel banner: "✅ All 23 candidates reviewed — 18 approved, 5 rejected." with "Export" CTA |
| Network error on approve/reject | Inline error below the action button; action reverted visually; retry button shown |
| Candidate being edited by another user (future) | Optimistic lock warning: "This candidate was modified by another user. Refresh to see latest." |
