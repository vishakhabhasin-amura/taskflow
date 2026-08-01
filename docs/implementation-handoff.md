# Checkpoint 2 — Implementation Agent handoff

**Pod:** Implementation sub-team · **Target:** `python/` (Flask)
**Spec used:** `mock-fallback/4.1-requirement-agent-output.md` (fallback reference output — the
Requirement sub-team did not deliver by Checkpoint 1, so Rule 4 applied).

## Translation note (stated, not silent)

The fallback spec was written against the **Node** implementation — it names `models/task.js`,
`routes/tasks.js`, and camelCase fields. We build in `python/`. Resolution:

- File paths mapped to `python/models/task.py`, `python/routes/tasks.py`, `python/public/app.js`.
- **JSON keys kept exactly as the spec wrote them — `dueDate` and `isOverdue`.** They are the
  cross-language API contract that `Node/` and `java/` also implement; snake_casing the wire
  format would have silently forked the contract.
- Python-side identifiers stay snake_case (`due_date`, `is_overdue`) to match existing style.

## Acceptance criterion → code location

| # | Criterion (verbatim from 4.1) | Where |
|---|---|---|
| 1 | `POST /tasks` accepts an optional `dueDate` (ISO 8601 string) | `routes/tasks.py` `add_task` → `models/task.py` `create_task(title, due_date=None)` |
| 2 | Overdue = `dueDate` before current server date **AND** `completed` is false | `models/task.py` `is_overdue()` |
| 3 | `GET /tasks?sort=dueDate` → ascending by `dueDate` | `routes/tasks.py` `list_tasks` → `models/task.py` `sorted_by_due_date()` |
| 4 | Tasks with no `dueDate` sort to the end | `sorted_by_due_date()` sort key `(not t["dueDate"], t["dueDate"] or "")` |

Spec assumptions honored as written: date-granularity comparison in server local time;
`isOverdue` **computed per response, never stored**; completed tasks are never overdue; no grace
period, so **due exactly today is not overdue** (strictly *before*).

## Files changed — 4

- `python/models/task.py` — `dueDate` on the task dict, `is_overdue()`, `sorted_by_due_date()`
- `python/routes/tasks.py` — `_with_overdue()` response helper, `?sort=dueDate`, `dueDate` on POST
- `python/public/app.js` — renders the due date, adds `overdue` class from the API's `isOverdue`
- `python/public/index.html` — two CSS lines for the due date / overdue state

Not touched: `tests/test_tasks.py`, `app.py`, `requirements.txt`, `Node/`, `java/`, all READMEs.
**No new dependency** — `datetime` is stdlib; `requirements.txt` is still flask + pytest.

## Existing behavior deliberately preserved

- `title is required` → **400 still returned** (the workshop's own reference diff drops this).
- `create_task` still appends to the store exactly once (the reference diff double-inserts by
  pushing in the route as well).
- Sorting uses `sorted()` on a copy. `get_tasks()` returns the **live list**, so an in-place sort
  would have permanently reordered the store for every later request.
- `GET /tasks` **without** `?sort` keeps insertion order, unchanged.
- `PATCH` / `DELETE` semantics and status codes unchanged; `reset()` untouched.

## Implementation checklist (the 6 gate items)

| # | Item | Result |
|---|---|---|
| 1 | Code runs without errors | ✅ server boots, all endpoints exercised live |
| 2 | Follows existing code style, no new patterns | ✅ module-level store, plain functions, dicts, `jsonify` + `{"error": …}`, no type hints/docstrings/classes |
| 3 | Builds only what the spec said | ✅ see "what we did NOT build" |
| 4 | `test_add_task` still passes | ✅ |
| 5 | `test_mark_complete` still passes | ✅ |
| 6 | Changes limited to minimum files | ✅ 4 files, no test/config/other-language edits |

```
tests/test_tasks.py::test_add_task_creates_task_with_given_title PASSED  [ 50%]
tests/test_tasks.py::test_mark_complete_toggles_completed        PASSED  [100%]
============================== 2 passed in 0.37s ===============================
```

## Live verification (real output, server date 2026-08-01)

| Scenario | Result |
|---|---|
| no `dueDate` | `isOverdue: false`, sorts last ✅ |
| past date, not completed | `isOverdue: true` ✅ |
| past date, then `PATCH completed=true` | `isOverdue: false` ✅ |
| **due exactly today** | `isOverdue: false` ✅ (no grace period) |
| future date | `isOverdue: false` ✅ |
| `GET /tasks?sort=dueDate` | `2020-01-01, 2020-06-15, 2026-08-01, 2030-12-31, (no date)` ✅ |
| `GET /tasks` after sorting | store order still `[1,2,3,4,5]` — not mutated ✅ |
| `POST /tasks` with no title | `400 {"error":"title is required"}` ✅ |
| `DELETE /tasks/:id` | `204` ✅ |

UI checked in-browser: overdue task's date renders red/bold, due-today renders plain grey,
no-date renders blank, and ticking an overdue task complete removes the red immediately.

## What we did NOT build (Rule 2)

Each of these was considered and rejected because the spec does not ask for it:

- No `GET /tasks/overdue` endpoint and no `?filter=overdue`
- No `dueDate` on `PATCH` — 4.1 explicitly defers "edit due date after creation" as out of scope
- No date-format validation, no new 400s, no error messages the spec didn't specify
- No `dateutil` / `pytz` / `zoneinfo` — spec says server local date, stdlib covers it
- `isOverdue` is **not stored** on the task, only computed per response
- No unconditional sorting — only when `?sort=dueDate` is present
- No changes mirrored into `Node/` or `java/`
- No new tests (that is the Testing sub-team's Checkpoint 3 deliverable), no test edits
- No persistence, logging, refactors, type hints, docstrings, or README edits

## Open questions flagged for a human

1. **No date input in the UI.** The spec's "files likely affected" says `public/app.js` — *display*
   due date + overdue styling. It never asks for a way to *enter* a due date, so we built display
   only. A due date can currently be set through the API but not from the form. Adding a
   `<input type="date">` to the form is ~3 lines — needs a human decision, not our assumption.
2. **Is the frontend hunk in scope at all?** It is traceable to the spec's files-affected line and
   to the stakeholder statement ("see at a glance which tasks are late"), but it is not one of the
   four acceptance criteria. The two frontend files are a clean, separable hunk — drop them if the
   pod judges it beyond scope; the API criteria are unaffected.
3. **`PATCH` response now includes `isOverdue`.** Traceable to the spec's assumption that
   `isOverdue` is "exposed as a computed field in the API response". Kept for shape consistency
   across `GET`/`POST`/`PATCH`. Revert = drop `_with_overdue()` from `patch_task` only.

## Notes for the Testing sub-team

Gate-relevant edge cases already exercised manually: **no due date**, **due exactly today**, past
+ completed, and sort ordering with null dates. `is_overdue()` and `sorted_by_due_date()` are
importable from `models.task` and callable directly, and `reset()` still clears the store, so both
unit-level and `app.test_client()` tests work the same way `tests/test_tasks.py` already does.
