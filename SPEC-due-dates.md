# Feature Spec: Task Due Dates & Priority Display

**Status:** Draft — pending open question resolution before implementation  
**Affects:** All three implementations (Node, Python, Java) — shared frontend + per-stack backend

---

## Summary

Tasks gain an optional due date. Once set, a due date is permanent. The task list is always sorted by due date (soonest first, undated tasks last). Overdue tasks are visually flagged in red.

---

## Acceptance Criteria

### AC-1 — Setting a due date on creation
- The "Add" form includes an optional date input field labelled **"Due date"**.
- Submitting without a due date creates a task with `due_date: null`. The field is optional; no validation error is shown for an empty date.
- Submitting with a due date creates a task with `due_date` stored as `YYYY-MM-DD`.
- The API (`POST /tasks`) accepts an optional `due_date` string in the request body. Requests without `due_date` are valid and unchanged.

### AC-2 — Adding a due date to an existing task
- Each task in the list that has `due_date: null` shows an **"Add due date"** control (e.g., a small date input + confirm button inline with the task row).
- Submitting that control sends `PATCH /tasks/:id` with `{ "due_date": "YYYY-MM-DD" }`.
- On success, the "Add due date" control disappears and is replaced by the rendered due date.
- If a task already has a `due_date` set, no edit control is shown. The date is displayed as read-only text.

### AC-3 — Due date is immutable once set
- The server rejects any `PATCH /tasks/:id` that attempts to change an already-set `due_date` with **HTTP 400** and the error body `{ "error": "due_date cannot be changed once set" }`.
- The frontend never renders an edit control for a task that has a `due_date`.

### AC-4 — Sort order
- `GET /tasks` returns tasks sorted ascending by `due_date` (earliest due date first).
- Tasks with `due_date: null` are always placed at the **end** of the list, after all dated tasks.
- Within the null-date group, original insertion order is preserved.

### AC-5 — Colour-coded priority indicator
- Each task row has a left border or background tint applied according to its due date relative to today's server date:
  - **Red** — overdue: `due_date` is before today's date (strictly before start of today).
  - Tasks with `due_date: null` have no colour indicator.
- The colour is computed on the frontend using the browser's current date at render time.

### AC-6 — Data model change
- Task shape changes from `{ id, title, completed }` to `{ id, title, completed, due_date }` where `due_date` is either a `YYYY-MM-DD` string or `null`.
- All existing `GET /tasks` consumers receive `due_date: null` for tasks created before this change.

---

## Assumptions

| # | Assumption |
|---|------------|
| A1 | **Overdue means strictly before today.** A task due today (same calendar date as server date) is NOT overdue — it is current. A task due yesterday or earlier IS overdue. |
| A2 | **Date-only, no time.** `due_date` stores a calendar date (`YYYY-MM-DD`), not a datetime. There is no time-of-day component. |
| A3 | **Server timezone is the source of truth for storage; browser date is used for colour rendering.** These may differ by one day near midnight, which is acceptable per the out-of-scope timezone exclusion. |
| A4 | **"Once set" means once persisted by the server.** A user filling in the date input but not yet submitting has not "set" the date. |
| A5 | **Sorting is server-side** (returned order from `GET /tasks`). The frontend renders in the order received. |

---

## Open Questions

> These must be decided by a human before implementation begins.

| # | Question | Impact |
|---|----------|--------|
| OQ-1 | **What colour(s) apply to tasks that have a due date but are NOT overdue?** Only red (overdue) was specified. Should "due today", "due within 3 days", and "due later" each have a distinct colour, or is there just one non-red state with no colour? | Affects AC-5 and CSS spec entirely |
| OQ-2 | **Within overdue tasks, what is the sort sub-order?** Most overdue first (oldest date at top), or least overdue first (most recently past due at top)? Current spec defaults to ascending (most overdue = oldest = first). | Affects AC-4 |
| OQ-3 | **Should the "Add due date" control for existing tasks be always visible inline, or revealed on hover/click?** Affects layout density for long task lists. | Frontend/UX only |

---

## Out of Scope

- Timezone handling — server timezone is used as-is; no conversion or user timezone preference.
- Task status fields beyond `completed`.
- Notifications, reminders, or alerts for upcoming or overdue tasks.
- Editing a due date after it has been set.

---

## Files Likely to be Affected

### Shared Frontend (identical across all three stacks)
| File | Change |
|------|--------|
| `Node/public/index.html` | Add date input to the "Add" form; add CSS classes for red overdue state |
| `Node/public/app.js` | Render due date per task; render "Add due date" control when `due_date` is null; apply colour class based on date comparison; send `due_date` in POST body; send `PATCH` for adding due date |

> Python and Java serve the same `public/` files from their own directories. All three copies must be updated.

### Node.js Backend
| File | Change |
|------|--------|
| `Node/models/task.js` | Add `due_date: null` to the task factory; sort tasks by `due_date` in list operation |
| `Node/routes/tasks.js` | Accept `due_date` in POST; validate immutability in PATCH; return 400 if `due_date` already set |
| `Node/tests/tasks.test.js` | New test cases (see Scenarios) |

### Python Backend
| File | Change |
|------|--------|
| `python/models/task.py` | Add `due_date: None` to task dict; sort by `due_date` |
| `python/routes/tasks.py` | Accept `due_date` in POST; validate immutability in PATCH |
| `python/tests/test_tasks.py` | New test cases |

### Java Backend
| File | Change |
|------|--------|
| `java/src/main/java/com/taskflow/Task.java` | Add `dueDate` field (String, nullable) |
| `java/src/main/java/com/taskflow/TaskStore.java` | Include `dueDate` in storage; sort list by `due_date`; enforce immutability check |
| `java/src/main/java/com/taskflow/TaskHandler.java` | Parse `due_date` from POST and PATCH bodies; return 400 on immutability violation |
| `java/src/main/java/com/taskflow/Json.java` | Serialize/deserialize `due_date` field (nullable string) |
| `java/src/test/java/com/taskflow/TaskFlowTest.java` | New test cases |

---

## Example Scenarios

### Scenario 1 — Creating a task with a due date
**Input:** User fills in title = `"Submit report"`, due date = `2026-08-10`, clicks Add  
**API call:** `POST /tasks` → `{ "title": "Submit report", "due_date": "2026-08-10" }`  
**Expected response:** `201` → `{ "id": 1, "title": "Submit report", "completed": false, "due_date": "2026-08-10" }`  
**Expected UI:** Task appears in list with due date shown; if today is before 2026-08-10, no red highlight; no "Add due date" control visible for this task.

---

### Scenario 2 — Creating a task without a due date, then adding one
**Input (step 1):** User fills in title = `"Buy groceries"`, leaves due date blank, clicks Add  
**API call:** `POST /tasks` → `{ "title": "Buy groceries" }`  
**Expected response:** `201` → `{ "id": 2, "title": "Buy groceries", "completed": false, "due_date": null }`  
**Expected UI (step 1):** Task appears at the bottom (after all dated tasks); no colour; "Add due date" control visible.

**Input (step 2):** User enters `2026-07-30` into the inline date control and confirms  
**API call:** `PATCH /tasks/2` → `{ "due_date": "2026-07-30" }`  
**Expected response:** `200` → `{ "id": 2, "title": "Buy groceries", "completed": false, "due_date": "2026-07-30" }`  
**Expected UI (step 2):** Today is 2026-08-01. Task moves up in the list (sorted before undated tasks); displayed with **red** highlight because 2026-07-30 is before today; "Add due date" control is gone; due date shown as read-only.

---

### Scenario 3 — Attempting to change an existing due date
**Setup:** Task id=3 already has `due_date: "2026-08-05"`  
**API call:** `PATCH /tasks/3` → `{ "due_date": "2026-09-01" }`  
**Expected response:** `400` → `{ "error": "due_date cannot be changed once set" }`  
**Expected UI:** No "Add due date" control is rendered for this task, so this scenario can only be triggered directly against the API. Frontend never issues this call.

---

### Scenario 4 — Sort order with mixed due dates
**Setup:** Four tasks exist with due dates (server date is 2026-08-01):
- Task A: `due_date: null`
- Task B: `due_date: "2026-07-25"` (overdue)
- Task C: `due_date: "2026-08-01"` (due today, not overdue per A1)
- Task D: `due_date: "2026-08-10"` (upcoming)

**API call:** `GET /tasks`  
**Expected response order:** B → C → D → A  
**Expected UI colours:** B is red; C and D have no red (pending resolution of OQ-1); A has no colour.

---

### Scenario 5 — Due date not accepted for already-completed task patch (immutability still applies)
**Setup:** Task id=5 has `due_date: "2026-08-03"`, `completed: false`. User completes it.  
**API call (toggle):** `PATCH /tasks/5` → `{ "completed": true }`  
**Expected response:** `200` → `{ "id": 5, "title": "...", "completed": true, "due_date": "2026-08-03" }`  
**Constraint verified:** `due_date` is unchanged. A subsequent `PATCH /tasks/5` with `{ "due_date": "2026-09-01" }` must still return `400`.

---

## Handoff Checklist

- [x] **AC-1 through AC-6** — clear acceptance criteria, not a restatement of the stakeholder request
- [x] **Assumptions A1–A5** — at least one stated explicitly (overdue definition, date-only storage, immutability timing)
- [x] **OQ-1 through OQ-3** — open questions flagged for a human to decide before implementation
- [x] **Files affected** — listed per stack with specific change description
- [x] **Scenarios 1–5** — five scenarios with specific inputs and expected outputs (exceeds minimum of 3)
