# Feature Spec: Task Due Dates & Priority Display

**Status:** Amended 2026-08-01 — adds date+time support, IST default timezone, and UI past-date prevention. Implemented in Node + Python.  
**Affects:** All three implementations (Node, Python, Java) — shared frontend + per-stack backend

---

## Summary

Tasks gain an optional due date **and time**. Once set, a due date is permanent. Timestamps are stored server-side in the default timezone **IST (UTC+05:30)**. The task list is always sorted by due date (soonest first, undated tasks last). Overdue tasks are visually flagged in red. The UI does not allow choosing a due date in the past.

---

## Acceptance Criteria

### AC-1 — Setting a due date on creation
- The "Add" form includes an optional **date-and-time** input field labelled **"Due date"** (`datetime-local`). The picker does not allow selecting a moment in the past (its minimum is the current time).
- Submitting without a due date creates a task with `due_date: null`. The field is optional; no validation error is shown for an empty date.
- Submitting with a due date creates a task whose `due_date` is stored as an ISO-8601 timestamp in IST, e.g. `2026-08-10T15:30:00+05:30`. A date with no time defaults to start of day (`00:00`) IST.
- The API (`POST /tasks`) accepts an optional `due_date` string in the request body. Requests without `due_date` are valid and unchanged. The server normalizes the value to IST; it does **not** reject past timestamps (past selection is prevented in the UI only).

### AC-2 — Adding a due date to an existing task
- Each task in the list that has `due_date: null` shows an **"Add due date"** control (a small `datetime-local` input + confirm button inline with the task row). Like the create form, it does not allow selecting a past moment.
- Submitting that control sends `PATCH /tasks/:id` with `{ "due_date": "<ISO-8601 timestamp>" }`.
- On success, the "Add due date" control disappears and is replaced by the rendered due date.
- If a task already has a `due_date` set, no edit control is shown. The date is displayed as read-only text.

### AC-3 — Due date is immutable once set
- The server rejects any `PATCH /tasks/:id` that attempts to change an already-set `due_date` with **HTTP 400** and the error body `{ "error": "due_date cannot be changed once set" }`.
- The frontend never renders an edit control for a task that has a `due_date`.

### AC-4 — Sort order
- `GET /tasks` returns tasks sorted ascending by `due_date` (earliest due timestamp first).
- Tasks with `due_date: null` are always placed at the **end** of the list, after all dated tasks.
- Within the null-date group, original insertion order is preserved.

### AC-5 — Colour-coded priority indicator
- Each task row has a left border or background tint applied according to its due timestamp relative to the current moment:
  - **Red** — overdue: `due_date` is strictly before now.
  - Tasks with `due_date: null` have no colour indicator.
- The colour is computed on the frontend by comparing the stored timestamp against the browser's current time at render time (both are absolute instants, so the comparison is timezone-safe).

### AC-6 — Data model change
- Task shape changes from `{ id, title, completed }` to `{ id, title, completed, due_date }` where `due_date` is either an ISO-8601 timestamp string in IST (e.g. `2026-08-10T15:30:00+05:30`) or `null`.
- All existing `GET /tasks` consumers receive `due_date: null` for tasks created before this change.

---

## Assumptions

| # | Assumption |
|---|------------|
| A1 | **Overdue means strictly before now.** A task whose due timestamp is in the future (or exactly now) is not overdue; a task whose due timestamp has passed IS overdue. |
| A2 | **Date and time supported.** `due_date` stores a timestamp (date + time). Time is optional on input; a date with no time defaults to start of day (`00:00`) IST. |
| A3 | **IST is the default server timezone.** Timestamps are stored/returned as ISO-8601 in IST (UTC+05:30). Values sent without an offset are interpreted as IST; the overdue colour compares absolute instants, so it is timezone-safe. |
| A4 | **"Once set" means once persisted by the server.** A user filling in the input but not yet submitting has not "set" the date. |
| A5 | **Sorting is server-side** (returned order from `GET /tasks`). The frontend renders in the order received. |

---

## Open Questions

> Resolved before implementation.

| # | Question | Resolution |
|---|----------|------------|
| OQ-1 | What colour(s) apply to tasks that have a due date but are NOT overdue? | Only red (overdue). Dated-but-not-overdue and undated tasks get no colour. |
| OQ-2 | Within overdue tasks, what is the sort sub-order? | Ascending by timestamp (most overdue / earliest first), consistent with AC-4. |
| OQ-3 | Should the "Add due date" control be always visible or revealed on hover/click? | Always visible inline. |

---

## Out of Scope

- Per-user timezone preferences — IST (UTC+05:30) is the single default timezone for all timestamps; no user-selectable timezone.
- Server-side rejection of past due dates — past selection is prevented in the UI only; the API still accepts past timestamps.
- Task status fields beyond `completed`.
- Notifications, reminders, or alerts for upcoming or overdue tasks.
- Editing a due date after it has been set.

---

## Files Likely to be Affected

### Shared Frontend (identical across all three stacks)
| File | Change |
|------|--------|
| `Node/public/index.html` | Add `datetime-local` input to the "Add" form; add CSS classes for red overdue state |
| `Node/public/app.js` | Render due timestamp per task; render "Add due date" control when `due_date` is null; prevent past selection (min = now + submit guard); apply colour class based on instant comparison; send `due_date` in POST body; send `PATCH` for adding due date |

> Python and Java serve the same `public/` files from their own directories. All three copies must be updated.

### Node.js Backend
| File | Change |
|------|--------|
| `Node/models/task.js` | Add `due_date: null` to the task factory; normalize incoming values to ISO-8601 in IST; sort tasks by due timestamp in list operation |
| `Node/routes/tasks.js` | Accept `due_date` in POST; validate immutability in PATCH; return 400 if `due_date` already set |
| `Node/tests/tasks.test.js` | New test cases (owned by the QA/testing team) |

### Python Backend
| File | Change |
|------|--------|
| `python/models/task.py` | Add `due_date: None` to task dict; normalize incoming values to ISO-8601 in IST; sort by due timestamp |
| `python/routes/tasks.py` | Accept `due_date` in POST; validate immutability in PATCH |
| `python/tests/test_tasks.py` | New test cases (owned by the QA/testing team) |

### Java Backend
| File | Change |
|------|--------|
| `java/src/main/java/com/taskflow/Task.java` | Add `dueDate` field (String, nullable) |
| `java/src/main/java/com/taskflow/TaskStore.java` | Include `dueDate` in storage; normalize to IST; sort list by due timestamp; enforce immutability check |
| `java/src/main/java/com/taskflow/TaskHandler.java` | Parse `due_date` from POST and PATCH bodies; return 400 on immutability violation |
| `java/src/main/java/com/taskflow/Json.java` | Serialize/deserialize `due_date` field (nullable string) |
| `java/src/test/java/com/taskflow/TaskFlowTest.java` | New test cases |

---

## Example Scenarios

### Scenario 1 — Creating a task with a due date
**Input:** User fills in title = `"Submit report"`, due date = `2026-08-10T15:30`, clicks Add  
**API call:** `POST /tasks` → `{ "title": "Submit report", "due_date": "2026-08-10T15:30" }`  
**Expected response:** `201` → `{ "id": 1, "title": "Submit report", "completed": false, "due_date": "2026-08-10T15:30:00+05:30" }`  
**Expected UI:** Task appears in list with the due date shown; if the due time is in the future, no red highlight; no "Add due date" control visible for this task.

---

### Scenario 2 — Creating a task without a due date, then adding one
**Input (step 1):** User fills in title = `"Buy groceries"`, leaves due date blank, clicks Add  
**API call:** `POST /tasks` → `{ "title": "Buy groceries" }`  
**Expected response:** `201` → `{ "id": 2, "title": "Buy groceries", "completed": false, "due_date": null }`  
**Expected UI (step 1):** Task appears at the bottom (after all dated tasks); no colour; "Add due date" control visible.

**Input (step 2):** Current time is 2026-08-01T09:00 IST. User picks `2026-08-05T18:00` in the inline control and confirms. (The control's minimum is now, so a past moment cannot be chosen.)  
**API call:** `PATCH /tasks/2` → `{ "due_date": "2026-08-05T18:00" }`  
**Expected response:** `200` → `{ "id": 2, "title": "Buy groceries", "completed": false, "due_date": "2026-08-05T18:00:00+05:30" }`  
**Expected UI (step 2):** Task moves up in the list (sorted before undated tasks); no red highlight because the due time is in the future; "Add due date" control is gone; due date shown as read-only.

---

### Scenario 3 — Attempting to change an existing due date
**Setup:** Task id=3 already has `due_date: "2026-08-05T18:00:00+05:30"`  
**API call:** `PATCH /tasks/3` → `{ "due_date": "2026-09-01T10:00" }`  
**Expected response:** `400` → `{ "error": "due_date cannot be changed once set" }`  
**Expected UI:** No "Add due date" control is rendered for this task, so this scenario can only be triggered directly against the API. Frontend never issues this call.

---

### Scenario 4 — Sort order with mixed due dates
**Setup:** Current time is 2026-08-01T12:00 IST. Four tasks exist:
- Task A: `due_date: null`
- Task B: `due_date: "2026-07-25T09:00:00+05:30"` (past → overdue)
- Task C: `due_date: "2026-08-01T18:00:00+05:30"` (later today → not yet overdue)
- Task D: `due_date: "2026-08-10T10:00:00+05:30"` (upcoming)

**API call:** `GET /tasks`  
**Expected response order:** B → C → D → A  
**Expected UI colours:** B is red; C and D have no red; A has no colour.

---

### Scenario 5 — Due date not accepted for already-completed task patch (immutability still applies)
**Setup:** Task id=5 has `due_date: "2026-08-03T12:00:00+05:30"`, `completed: false`. User completes it.  
**API call (toggle):** `PATCH /tasks/5` → `{ "completed": true }`  
**Expected response:** `200` → `{ "id": 5, "title": "...", "completed": true, "due_date": "2026-08-03T12:00:00+05:30" }`  
**Constraint verified:** `due_date` is unchanged. A subsequent `PATCH /tasks/5` with `{ "due_date": "2026-09-01T10:00" }` must still return `400`.

---

## Handoff Checklist

- [x] **AC-1 through AC-6** — clear acceptance criteria, not a restatement of the stakeholder request
- [x] **Assumptions A1–A5** — at least one stated explicitly (overdue definition, timestamp storage in IST, immutability timing)
- [x] **OQ-1 through OQ-3** — open questions resolved before implementation
- [x] **Files affected** — listed per stack with specific change description
- [x] **Scenarios 1–5** — five scenarios with specific inputs and expected outputs (exceeds minimum of 3)
