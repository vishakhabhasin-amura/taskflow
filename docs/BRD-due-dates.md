# BRD — Task Due Dates, Overdue Visibility, and Due-Date Ordering

**Product:** TaskFlow (Python / Flask implementation)
**Branch:** `pod_3_dev`
**Author:** Ideatic Agent
**Date:** 2026-08-01
**Status:** **Approved — implementation in progress.** The plan was approved and the build is
under way in parallel with this revision. This document is the corrected specification the
implementation must match; where the two disagree, this document is authoritative and the
implementation is a defect.

### Revision notes — 2026-08-01

This revision is a targeted correction, not a rewrite. Four changes, each chased through every
downstream item:

| # | Correction | Sections touched |
|---|---|---|
| 1 | **Runtime was wrong.** This machine runs Python **3.9.6**, not 3.12.13, and `datetime.fromisoformat` **rejects** a trailing `Z` on 3.9. The BRD's own contract example and edge case A12 would have returned 400 as previously specified. Approved fix: normalize a trailing `Z` to `+00:00` before parsing — stdlib only, no new dependency | §3.1, §6.2, §7.1, A12, A17, B5, B10, B11, C-T1, C-T6, C-T7, R-7, R-8 |
| 2 | **`python/README.md` was missing from the blast radius**, despite R-2's mitigation naming it. It documents the old data model and an API table with no `dueDate` and no `sort` | §3.7, G-9, §12, R-2 |
| 3 | **A-3 reversed by decision.** A date-only `dueDate` now means the **end** of that day, not midnight at its start. Start-of-day made a task due *today* read overdue for the whole day it was actually due | A-3, A10, §6.2, §7.5, B10–B16, J7, §12 |
| 4 | **Status and provenance corrected.** Header status, date, and branch. Approval now records that R-3 and R-4 were acknowledged | Header, §14 Approval |

Every `file:line` citation below was re-read and re-verified against the working tree at
`0ae158e` (clean, no uncommitted implementation).

---

## 1. Problem statement

TaskFlow lets a user record *what* needs doing, but never *when*. A task dict is
`{id, title, completed}` (`python/models/task.py:7`) and there is no temporal field
anywhere in the product.

The consequence is that urgency is invisible. A task due yesterday and a task with no
deadline at all render as byte-identical list rows (`python/public/app.js:11-32`) —
same markup, same styling, same position. The list is ordered by insertion
(`python/models/task.py:9` appends; `get_tasks` returns in that order), so the order
carries no signal about what is pressing either.

A user with more than a handful of tasks therefore has to hold every deadline in their
own head. Nothing in the product surfaces lateness, and nothing helps them triage.

**Who feels this:** the single end user of a TaskFlow list — the app has no accounts or
roles, so there is exactly one persona.

## 2. Goals and non-goals

### Goals

| # | Goal | How success is measured |
|---|---|---|
| G-1 | A user can optionally record when a task is due | A task can be created with a due date; one created without a due date still succeeds |
| G-2 | Overdue tasks are identifiable at a glance | Overdue tasks are visually distinct in the UI and machine-identifiable in the API, with no per-task manual date comparison by the user |
| G-3 | The list can be ordered by urgency | The task list can be retrieved and displayed ordered by due date, soonest first |

### Non-goals — explicitly out of scope for this iteration

These are flagged, not built. Each is a deliberate exclusion, not an oversight:

| # | Excluded | Note |
|---|---|---|
| NG-1 | Recurring due dates | No repeat rules, no schedule expansion |
| NG-2 | Reminders and notifications | No email, push, in-app alert, or polling. Overdue state is observed only when the user looks at the list |
| NG-3 | Per-user timezone selection | The server's timezone is the only timezone. See A-2 and R-1 |
| NG-4 | Editing a due date after creation | Due date is set at creation only. `PATCH /tasks/<id>` continues to accept `completed` and nothing else |

**Consequence of NG-4 worth stating plainly:** a due date set by mistake cannot be
corrected or cleared. The only remedy available to the user is to delete the task and
recreate it. This is accepted for this iteration and recorded as risk R-3.

## 3. Codebase recon findings

Read in full before drafting, and re-read in full for this revision. The Python
implementation is a three-layer Flask app with no database.

### 3.1 Architecture

| Layer | File | Responsibility |
|---|---|---|
| Entrypoint | `python/app.py` | Creates the Flask app, serves `public/` as static root (`app.py:7`), registers the tasks blueprint (`app.py:8`), serves `index.html` at `/` (`app.py:11-13`) |
| Routes | `python/routes/tasks.py` | Blueprint at `url_prefix="/tasks"` (`tasks.py:5`); four handlers, HTTP contract only |
| Model | `python/models/task.py` | Module-level list `_tasks` and counter `_next_id` (`task.py:1-2`); all task state |
| Frontend | `python/public/index.html`, `app.js` | Static, no build step, vanilla JS |
| Tests | `python/tests/test_tasks.py` | pytest + Flask test client, in-process |
| Docs | `python/README.md` | Stack, run commands, API table (`README.md:26-33`), data model (`README.md:35-39`), repo structure |

**Runtime: Python 3.9.6** — *not* 3.12.13, as an earlier revision of this document stated.
Verified directly on this machine: `python3 -V` and `python/.venv/bin/python -V` both report
`Python 3.9.6`. Flask ≥3.0, pytest ≥8.0 (`python/requirements.txt:1-2`). pytest config in
`python/pyproject.toml:1-3` (`testpaths=["tests"]`, `pythonpath=["."]`).

**Why the version is load-bearing here.** `datetime.fromisoformat` on 3.9 parses only the
output of `datetime.isoformat()`. It therefore **rejects a trailing `Z`**:

```
>>> datetime.fromisoformat("2026-08-05T17:00:00Z")
ValueError: Invalid isoformat string: '2026-08-05T17:00:00Z'
```

Verified on this interpreter. Under the previous revision's specification, the request body
printed in its own API contract (§7.1) and its own edge case A12 — both of which use `Z` and
expect 201 — would have returned 400. The correction is specified in §6.2 (`Z` normalization)
and constrained in C-T1.

### 3.2 Existing feature inventory

The complete product surface, from `python/routes/tasks.py`:

| Feature | Route | Handler | Model call |
|---|---|---|---|
| List all tasks | `GET /tasks` | `list_tasks` (`tasks.py:8-10`) | `get_tasks()` |
| Create task | `POST /tasks` | `add_task` (`tasks.py:13-18`) | `create_task(title)` |
| Toggle completion | `PATCH /tasks/<int:id>` | `patch_task` (`tasks.py:21-27`) | `update_task(id, completed)` |
| Delete task | `DELETE /tasks/<int:id>` | `remove_task` (`tasks.py:30-34`) | `delete_task(id)` |
| Serve UI | `GET /` + static | `index` (`app.py:11-13`) | — |

There is **no** filtering, sorting, searching, pagination, or any date/time field
anywhere in the codebase.

### 3.3 Data structure (there is no database)

Storage is a module-level Python list of dicts, `_tasks` (`python/models/task.py:1`),
with a monotonic integer counter `_next_id` (`task.py:2`).

Current entity shape (`task.py:7`):

```python
{"id": int, "title": str, "completed": bool}
```

Properties that materially constrain this work:

- **Non-durable.** Process restart wipes all tasks and resets `_next_id` to 1 (`reset()`,
  `task.py:37-40`, does the same for tests). There is no migration to write — but also no
  backfill problem, because no data survives a deploy. Confirmed empirically during the
  original recon session: restarting the server cleared the store and reissued id 1.
- **`get_tasks()` returns the live list by reference** (`task.py:13-14`) — not a copy. Any
  caller that sorts in place, or mutates a returned dict, corrupts stored state. This is
  the single most dangerous property in the file for this feature (see FR-6, EC-C2, G-6).
- **Single-process, no locking.** `create_task` does a non-atomic read-increment-write on
  `_next_id` (`task.py:5-9`). Flask's dev server is single-threaded by default, so this
  is latent rather than active.
- **No timezone data, no datetime import** anywhere in the module today.

### 3.4 Authentication and authorization model

**There is none.** No login, no session, no token, no user entity, no ownership field on
a task, no authorization check on any route. Every endpoint is fully public and every
caller sees and mutates the same single global task list.

This is a base repo for a workshop, so it is presumably intentional — but it is a
first-class constraint on this work and is treated as such in §10b. Note the phrase "my
tasks" in the user stories does not correspond to anything in the data model: there is no
"my". All tasks belong to everyone.

### 3.5 Conventions to match

- Errors: `jsonify({"error": "<lowercase message>"}), <code>` (`tasks.py:17,26,33`).
- Body parsing: `(request.get_json(silent=True) or {})` — never raises on malformed or
  absent JSON, yields `{}` instead (`tasks.py:15,23`).
- Route params typed via Flask converters: `<int:task_id>` (`tasks.py:21,30`), which
  already returns 404 for non-integer ids without custom code.
- Model functions return the task dict or `None`/`False`; routes translate that to HTTP.
- 204 responses return `"", 204` (`tasks.py:34`).

### 3.6 Test coverage

Two tests only (`python/tests/test_tasks.py:17-30`): create-with-title, and
patch-toggles-completed. An autouse fixture calls `reset()` before each test
(`test_tasks.py:7-9`).

**Untested today:** `GET /tasks`, `DELETE`, the 400 path, both 404 paths, the static
route. Anything I touch in those areas has no regression net beneath it — a fact that
directly shapes §12.

### 3.7 Contracts and consumers

- `python/public/app.js` is the only known runtime consumer. It calls `GET /tasks` on load and
  after every mutation (`app.js:5-9,40,45,58`), rendering with `textContent` (`app.js:23`)
  — so it is not XSS-prone today, and must not become so.
- **Critical parity finding, re-verified for this revision:** `python/public/`,
  `Node/public/`, and `java/src/main/resources/public/` are **byte-identical**. Re-ran
  `diff -rq python/public/ Node/public/` and `diff -rq python/public/ java/src/main/resources/public/`
  — both produce no output. The finding stands unchanged. The three implementations
  deliberately share one frontend; editing `python/public/app.js` breaks that parity. See
  G-7 and R-2.
- **`python/README.md` is a documentation consumer of the same contract**, and was missed by
  the previous revision. It asserts the Python implementation has the "Same API and data
  model as Node/" (`README.md:3`) and the "same static HTML + vanilla JS as `Node/public/`"
  (`README.md:9`), publishes an API table with no `dueDate` field and no `sort` parameter
  (`README.md:26-33`), and publishes the data model as
  `{ "id": 1, "title": "string", "completed": false }` (`README.md:35-39`). All four
  statements go stale with this change. It is now in the blast radius (G-9).

## 4. Duplication analysis

Checked every proposed capability against §3.2 before writing a requirement:

| Capability | Status | Decision |
|---|---|---|
| Store a due date on a task | **Net new** | Add to the existing dict in `create_task`. Do not introduce a parallel store or a second entity |
| Determine overdue | **Net new** | Derive at read time from the stored due date. Do **not** persist an `overdue` flag — it would go stale the instant the clock passes it |
| Sort tasks | **Net new** | Add to the existing `GET /tasks` path. No new endpoint |
| Optional field on create | **Partially exists** | `add_task` already implements optional-field handling shape for `title`; reuse the same `(request.get_json(silent=True) or {}).get(...)` idiom rather than inventing a new parsing style |
| Input validation + 400 | **Partially exists** | `tasks.py:16-17` already establishes the pattern. Extend it, don't add a validation framework |
| Rendering a task row | **Exists** | Extend `renderTasks` in `app.js:11-32`. Do not write a second render path |
| Date formatting utility | **Net new** | Use stdlib `datetime` only. Adding a dependency for this would be unjustifiable — including for the `Z` handling in §6.2, which is a two-line string replacement, not a parsing problem |

No capability in this BRD duplicates existing functionality. Nothing is being replaced.

## 5. Functional requirements

| ID | Requirement |
|---|---|
| **FR-1** | When creating a task, a user may supply a due date. The task is created and the due date is recorded against it. |
| **FR-2** | The due date is optional. Creating a task without one succeeds exactly as it does today, and the task's due date is explicitly absent (`null`), not an empty string or a sentinel date. |
| **FR-3** | A supplied due date that is not a valid ISO 8601 datetime is rejected with `400` and the task is **not** created. Validation happens before any state change. A trailing `Z` **is** valid ISO 8601 and must be accepted — see §6.2, which specifies how, given the runtime in §3.1. |
| **FR-4** | Every task returned by the API carries a machine-readable indication of whether it is overdue, computed by the server. A client never has to compare dates to answer "is this late?". |
| **FR-5** | A task is overdue when it has a due date, that due date is strictly in the past relative to the server's current time, **and** the task is not completed. A completed task is never overdue, regardless of its due date. A task with no due date is never overdue. *(Unchanged by the A-3 reversal — the rule is the same; what moved is where a date-only input lands on the clock.)* |
| **FR-6** | The task list can be requested ordered by due date, soonest first. Tasks with no due date sort **after** all tasks that have one. Ties (equal due dates, or two tasks both without one) are broken by ascending `id`, so ordering is total and deterministic. |
| **FR-7** | Requesting the list without asking for ordering returns tasks in insertion order, exactly as today. The stored order is never mutated by a sort request. |
| **FR-8** | The UI displays a task's due date when it has one, and renders overdue tasks in a visually distinct way that is apparent without reading the date. |
| **FR-9** | The UI presents the task list ordered by due date, soonest first. |
| **FR-10** | The UI lets a user optionally enter a due date when creating a task, and submitting the form with the due date left empty creates a task with no due date. |

## 6. Data model changes

### 6.1 Entity shape

```python
# before                                # after
{                                       {
  "id": int,                              "id": int,
  "title": str,                           "title": str,
  "completed": bool,                      "completed": bool,
}                                         "dueDate": str | None,   # stored, ISO 8601
                                        }
```

Plus one **derived, non-stored** field present only on API responses:

```python
"overdue": bool     # computed per request; never written to _tasks
```

### 6.2 Field decisions and rationale

| Decision | Choice | Why |
|---|---|---|
| JSON key | `dueDate` (camelCase) | The frontend is shared byte-identical with the Node and Java implementations (§3.7). One JSON key must serve all three. `dueDate` matches the JS and Java conventions those two will use. The cost is that it is un-idiomatic inside Python — accepted deliberately, because contract parity outranks single-language idiom here. Alternative `due_date` is rejected on those grounds |
| Stored type | ISO 8601 **string**, timezone-aware, normalized to UTC | Flask's default JSON provider serializes `datetime` objects as **RFC 822 / HTTP-date** strings, not ISO 8601 — storing a `datetime` would silently emit `"Sat, 01 Aug 2026 17:00:00 GMT"` to a client expecting ISO. Storing a normalized string avoids that trap entirely and keeps the store JSON-serializable |
| Normalization | Parse on input, re-serialize to canonical UTC ISO on store | Guarantees one representation on the wire regardless of what the client sent, so the stored value round-trips and every comparison operates on a single form |
| **`Z` suffix — required shim** | **Before parsing, a trailing `Z` is replaced with `+00:00`, then `datetime.fromisoformat` is called on the result** | Not cosmetic and not optional. On this runtime (Python 3.9.6, §3.1) `fromisoformat` raises `ValueError` on a trailing `Z`, and `Z` is the form both this document's own contract example (§7.1) and any RFC 3339 client emit. Without the shim, A12 returns 400 and the documented happy path fails. It is a string replacement using nothing outside the stdlib, so **G-5 still holds — `requirements.txt` is unchanged**. Verified on 3.9.6: with the shim, `"2026-08-05T17:00:00Z"`, `"2026-08-05T17:00:00+05:30"`, `"2026-08-05"` (date-only) and year 9999 all parse; `"Z"` alone (which normalizes to `"+00:00"`), whitespace-padded values, and a 10,000-character string all still raise `ValueError` and therefore still 400. The shim widens acceptance by exactly one suffix and nothing else |
| Naive input | Interpreted as server-local time, then converted to UTC | Per NG-3 there is no per-user timezone. Documented in A-2 |
| **Date-only input** | **Interpreted as the END of that day — `23:59:59.999999` server-local — then converted to UTC** | Reversed from the earlier start-of-day reading. The HTML `date` input emits date-only values, so start-of-day combined with FR-5's strictly-past rule marked a task due *today* as overdue for the entire day it was actually due. End-of-day is the only reading under which "due today" behaves the way a user expects. Full rationale in A-3; observable consequences in §7.5 and B12–B16 |
| Input with a time component | Used exactly as given — offset honored, or server-local if naive | **Unchanged** by the A-3 reversal. Only the no-time case moved |
| **Sort key** | **The parsed `datetime`, not the stored string** | End-of-day normalization puts `.999999` microseconds on every date-only value while timed values usually carry none, so stored strings now vary in length. Lexicographic ordering of the canonical UTC form does still happen to be correct — verified across mixed-precision samples, zero mismatches — but only because `+` sorts before `.` in ASCII, which is a coincidence rather than a property anyone should depend on. Sorting on the parsed value is order-correct by construction. Parse once per task per request (H2) |
| `overdue` | Derived at read time, never stored | A stored boolean is wrong the moment the clock crosses the due date, with no write to correct it. Deriving is the only correct option |

### 6.3 Migration

**None required.** The store is in-memory and empty at every process start (§3.3). There
are no existing rows, no backfill, and no rollback migration. Tasks created before this
change cannot exist after a restart.

This is the one respect in which the absence of a database makes this feature markedly
cheaper than it would be in a real system — and it is worth stating explicitly that a
future durable store would need a nullable-column migration plus a backfill of `NULL`.

## 7. Interface / API contract changes

All changes are **additive**. No existing field is removed, renamed, or retyped. No
existing status code changes.

### 7.1 `POST /tasks` — accepts a new optional field

```jsonc
// request
{ "title": "Ship the release", "dueDate": "2026-08-05T17:00:00Z" }   // dueDate optional

// 201 response
{ "id": 1, "title": "Ship the release", "completed": false,
  "dueDate": "2026-08-05T17:00:00+00:00", "overdue": false }
```

- The `Z` in that request body is **only** accepted because of the normalization shim in
  §6.2. On this runtime, parsing it without the shim raises `ValueError` and the request
  becomes a 400 (§3.1, C-T1). This example is a contract, and it is now correct.
- Omitting `dueDate` → `"dueDate": null`. **Backward compatible:** an existing client
  that posts only `title` behaves exactly as before.
- `dueDate` present but invalid → `400 {"error": "dueDate must be a valid ISO 8601 datetime"}`.
- Existing `400 {"error": "title is required"}` is unchanged and still takes precedence.

### 7.2 `GET /tasks` — new optional query parameter

```
GET /tasks              → insertion order (unchanged behavior)
GET /tasks?sort=dueDate → due date ascending, no-due-date last, id tiebreak
```

- Unknown `sort` value → `400 {"error": "sort must be one of: dueDate"}`. Rejecting
  rather than silently ignoring prevents a typo from looking like a sorting bug.
- **Backward compatible:** no parameter means no behavior change.

### 7.3 `PATCH /tasks/<id>` — response shape only

Continues to accept `completed` and **only** `completed` (NG-4). A `dueDate` key in the
body is ignored, not an error — consistent with how the handler ignores unknown keys
today. The response gains `dueDate` and `overdue`, like every other task response.

Note `overdue` may flip as a side effect of this call: completing an overdue task
correctly makes it not-overdue (FR-5).

### 7.4 `DELETE /tasks/<id>`

Unchanged. Still `204` / `404` with no body.

### 7.5 Date-only round-trip — consequence of A-3

A date-only `dueDate` does **not** round-trip as the string the client sent. This is a
direct, intended consequence of end-of-day normalization, and it must be stated in the
contract rather than discovered by a client:

```jsonc
// request
{ "title": "File the return", "dueDate": "2026-08-05" }

// 201 response — server-local timezone IST (+05:30), verified on this machine
{ "id": 1, "title": "File the return", "completed": false,
  "dueDate": "2026-08-05T18:29:59.999999+00:00", "overdue": false }
```

- The stored value is end-of-day **local**, expressed in **UTC**. On a server west of UTC the
  stored UTC date is the *following* calendar day: `2026-08-05T23:59:59.999999-05:00`
  normalizes to `2026-08-06T04:59:59.999999+00:00`.
- **The UI must therefore render the local calendar date derived from the stored timestamp —
  never the raw stored string, and never its leading 10 characters.** Slicing the stored
  string displays the wrong day for any server with a negative UTC offset, and is the most
  likely way to get this wrong. See J7.
- This is **not** a breaking change: no client sends or reads `dueDate` today (§3.7), so no
  existing consumer can observe the difference.

**Interaction with the sort ordering rules (FR-6) — checked, and there is one:** because a
date-only value now lands at 23:59:59.999999 instead of 00:00:00, a date-only task and a
timed task on the same day sort in the opposite relative order to what the previous revision
implied. `2026-08-05` now sorts **after** `2026-08-05T17:00:00Z`, not before. FR-6 itself
needs no change — it orders by the stored instant, and the stored instant is simply later —
but the behaviour is now pinned by edge case B16 so it cannot silently regress. Nothing else
in FR-6 is affected: the no-due-date-last rule, the id tiebreak, and the totality of the
ordering are all untouched.

## 8. Edge cases

Enumerated by category. Every row is a test case in §12.

### A. Input validation — `dueDate` on `POST /tasks`

| ID | Condition | Expected behavior |
|---|---|---|
| A1 | `dueDate` absent | 201, `dueDate: null`, `overdue: false` |
| A2 | `dueDate: null` explicitly | 201, treated identically to absent |
| A3 | `dueDate: ""` | 400 — empty string is not a valid datetime, and must not be silently coerced to null |
| A4 | `dueDate: "   "` | 400 |
| A5 | `dueDate: "not-a-date"` | 400 |
| A6 | `dueDate: "2026-13-45T00:00:00Z"` | 400 — syntactically ISO-shaped but not a real date. Verified: rejected both with and without the §6.2 shim (`month must be in 1..12` after normalization) |
| A7 | `dueDate: "2026-02-30T00:00:00Z"` | 400 — real-looking but impossible date. Verified: rejected with the shim applied (`day is out of range for month`) |
| A8 | `dueDate: 1754067600` (number) | 400 — epoch integers are not accepted; type must be string |
| A9 | `dueDate: true` / `{}` / `[]` | 400 — wrong type. Type is checked before the `Z` shim runs, so `.endswith` is never called on a non-string |
| A10 | `dueDate: "2026-08-05"` (date only, no time) | **201 — accepted, and stored as the END of that day** (`23:59:59.999999` server-local → UTC), per A-3 and §6.2. `datetime.fromisoformat` accepts the date-only form on 3.9.6 (verified); the end-of-day time is applied by us, not by the parser. Response carries the normalized timestamp, not the submitted string (§7.5) |
| A11 | `dueDate: "2026-08-05T17:00:00+05:30"` | 201 — offset honored, normalized to UTC on store. Verified to parse on 3.9.6 |
| A12 | `dueDate: "2026-08-05T17:00:00Z"` | **201 — but only via the §6.2 shim.** Verified on Python 3.9.6: raw `datetime.fromisoformat("2026-08-05T17:00:00Z")` raises `ValueError: Invalid isoformat string`; after replacing the trailing `Z` with `+00:00` it parses to `2026-08-05 17:00:00+00:00`. The previous revision's claim that `Z` is accepted natively "on 3.12.13" was wrong about this machine and would have made this case a 400 |
| A13 | `dueDate` with whitespace padding (`"  2026-08-05  "`) | 400 — reject rather than trim, matching the strictness of A3. Verified: still raises with the shim applied, since the shim only touches a trailing `Z` |
| A14 | Both `title` missing and `dueDate` invalid | 400 with the **title** error — existing check runs first, preserving current behavior exactly |
| A15 | Extra unknown keys in body | Ignored, as today |
| A16 | Malformed JSON body / no body | 400 `title is required` — `get_json(silent=True)` yields `{}`, unchanged from today |
| A17 | Very long `dueDate` string (10k chars) | 400, and must not hang the parser. Verified on 3.9.6 with the shim: a 10,000-character string raises `ValueError` immediately |
| A18 | `dueDate: "Z"` (the suffix alone) | 400. Verified: the shim rewrites it to `"+00:00"`, which `fromisoformat` rejects. Called out explicitly because it is the one input the shim rewrites into a *different* invalid string — the outcome is still a clean 400, never a 500 |

### B. Boundary values

| ID | Condition | Expected behavior |
|---|---|---|
| B1 | Due date exactly equal to "now" | **Not** overdue — FR-5 says strictly past. Prevents a task flickering overdue at the instant of creation |
| B2 | Due date 1 second in the past | Overdue |
| B3 | Due date 1 second in the future | Not overdue |
| B4 | Due date far past (year 1900) | Overdue, no error |
| B5 | Due date far future (year 9999) | Not overdue, no error. Verified: `9999-12-31T23:59:59` parses on 3.9.6 |
| B6 | Year beyond datetime range (10000+) | 400, not an unhandled `ValueError` |
| B7 | Empty task list, sorted | `[]`, 200 — not an error |
| B8 | Single task, sorted | Returns that one task |
| B9 | All tasks lack due dates, sorted | All returned in id order (FR-6 tiebreak) |
| B10 | Leap day `2028-02-29` (date-only) | Accepted. Verified to parse on 3.9.6. **Stored as `2028-02-29T23:59:59.999999` server-local, normalized to UTC** (A-3) — the end-of-day rule applies to leap days like any other date, and must not be special-cased |
| B11 | Leap day in a non-leap year `2027-02-29` | 400 (`day is out of range for month`, verified on 3.9.6). **Rejected at parse time, before the end-of-day time is applied** — validation precedes normalization, so an invalid date can never reach the 23:59:59.999999 substitution and be rescued by it |
| B12 | Date-only `dueDate` equal to **today**, read at any moment during that day | **Not overdue.** This is the case that motivated the A-3 reversal: end-of-day puts the deadline at 23:59:59.999999 local, which is still in the future for the whole of the day the task is due |
| B13 | The same task read after that local day has ended | **Overdue.** The transition happens once, at local midnight, with no write (cf. C4) |
| B14 | Date-only `dueDate` of **yesterday** | Overdue, from the first instant of today onward |
| B15 | Date-only `dueDate` of **tomorrow** | Not overdue |
| B16 | Date-only `2026-08-05` and timed `2026-08-05T17:00:00Z`, both present, sorted | The **timed** task sorts first, the date-only task second — end-of-day is the later instant (§7.5). Pinned as a test so the A-3 reversal cannot silently regress the ordering |

### C. Concurrency

| ID | Condition | Expected behavior |
|---|---|---|
| C1 | Two simultaneous creates | Both persist with distinct ids. Pre-existing non-atomic `_next_id` risk (§3.3) is **not worsened** by this change |
| C2 | Sort request concurrent with a create | Sorting must operate on a copy. **In-place sort of the list returned by `get_tasks()` would permanently reorder the store** — the highest-severity failure mode in this BRD |
| C3 | Task completed during a sorted read | Either pre- or post-completion `overdue` is acceptable; the response must be internally consistent, never a partially-updated dict |
| C4 | Clock moves past a due date between two reads | `overdue` flips false→true with no write. Correct and expected. With A-3, the commonest instance of this is local midnight rolling a date-only task from not-overdue to overdue (B12→B13) |

### D. Idempotency and retry

| ID | Condition | Expected behavior |
|---|---|---|
| D1 | Same create POSTed twice | Two distinct tasks. No dedupe exists today; this feature does not add one |
| D2 | `GET /tasks?sort=dueDate` repeated with no mutation | Byte-identical response — the id tiebreak (FR-6) guarantees a total order, so ordering never varies between identical calls |
| D3 | Create times out client-side, retried | May duplicate. Pre-existing behavior, unchanged, flagged not fixed |

### E. Authentication and authorization

| ID | Condition | Expected behavior |
|---|---|---|
| E1 | Unauthenticated create with a due date | Succeeds — there is no auth (§3.4). This change does **not** add an auth requirement, and equally must not add a new unauthenticated surface beyond the existing `/tasks` blueprint |
| E2 | One client reads another's tasks | Already fully shared. Not a regression — but confirms the user story phrase "my tasks" has no data-model backing (R-4) |
| E3 | Due date used as an oracle | A malformed date's error message must not echo the raw input back (see §11), avoiding a trivially reflected-input vector. This applies to the shim too: the rewritten string is never surfaced either |
| E4 | New endpoints introduced | **None.** No new route, no new surface, therefore no new attack surface |

### F. Failure and partial failure

| ID | Condition | Expected behavior |
|---|---|---|
| F1 | Date parsing raises unexpectedly | Caught, 400, no task created. Never a 500, never a partial write |
| F2 | Validation fails after `_next_id` would have incremented | **Validate before calling `create_task`.** Id must not be consumed by a rejected request |
| F3 | Sort comparator raises on a malformed stored value | Cannot occur if §6.2 normalization holds; defensively, a bad stored value must not 500 the whole list |
| F4 | Server restart | All tasks lost, including due dates. Pre-existing (§3.3), documented, not fixed |
| F5 | `Z` shim applied to a non-string | Cannot occur — the type check (A9) runs first. Stated so the ordering of the two checks is a requirement, not an accident: a bare `.endswith("Z")` on an int would be an `AttributeError` and a 500 |

### G. Data integrity

| ID | Condition | Expected behavior |
|---|---|---|
| G1 | Stored `dueDate` mutated by a read | Must not happen. Response serialization operates on copies |
| G2 | `overdue` written into `_tasks` | Must not happen — derived only (§6.2) |
| G3 | Insertion order after a sorted read | Unchanged (FR-7) — verified by a test that sorts, then re-reads unsorted |
| G4 | `reset()` clears due dates too | Yes — it clears the whole list (`task.py:37-40`), so it needs no change, but this must be asserted so a future refactor cannot silently break test isolation |

### H. Scale and performance

| ID | Condition | Expected behavior |
|---|---|---|
| H1 | 10,000 tasks sorted | `sorted()` is O(n log n) on an in-memory list; acceptable. No pagination exists and none is added (out of scope, but noted as a real limit) |
| H2 | Overdue computed per task per request | O(n) per request. Acceptable at this scale; avoid re-parsing the same string more than once per task per request. Note the §6.2 sort-key decision means the sort path parses too — the same parse must serve both `overdue` and the sort key, not run twice |
| H3 | Unbounded response size | Pre-existing — `GET /tasks` has always returned everything. Not worsened, and not to be capped: truncation for display is a frontend concern |

### I. Backward compatibility

| ID | Condition | Expected behavior |
|---|---|---|
| I1 | Old client posts `{title}` only | Works identically. **Both existing tests must pass unmodified** |
| I2 | Old client reads `GET /tasks` | Receives two extra keys. Additive; the existing frontend ignores unknown keys (`app.js:11-32` reads only `id`, `title`, `completed`) |
| I3 | Client relying on insertion order | Unaffected — default order preserved (FR-7) |
| I4 | Node / Java implementations | **Diverge after this change.** The contract is no longer identical across the three. Flagged as R-2 |
| I5 | `python/README.md` after this change | **Goes stale unless updated.** Its API table, data-model block, and both "same as Node" claims all become false (§3.7). Updating it is a deliverable, not a courtesy — it is the artefact R-2's mitigation depends on |

### J. Frontend / rendering

| ID | Condition | Expected behavior |
|---|---|---|
| J1 | Task with no due date | Renders as today, no empty date element, no layout shift |
| J2 | Overdue task | Visually distinct via a mechanism that does not rely on color alone (accessibility) |
| J3 | Completed **and** past due | Renders completed, **not** overdue (FR-5) |
| J4 | Date input left empty on submit | Task created with no due date; must not send `dueDate: ""` (which A3 rejects) |
| J5 | 400 returned to the browser | Surfaced to the user; the form must not silently no-op |
| J6 | Task title containing HTML | Still escaped via `textContent`. **The existing XSS-safety property must not regress** — no `innerHTML` introduced for the date or badge |
| J7 | Task created from a date-only value (the HTML `date` input's only output) | The row shows the calendar date the user picked, obtained by converting the stored UTC timestamp back to local time — **not** `dueDate.slice(0, 10)`, which shows the wrong day on any server west of UTC (§7.5). And a task the user marks due today shows as due, not late, for the whole of that day (B12) |

## 9. Constraints

### Technical
- **C-T1** **Python 3.9.6** (verified on this machine, §3.1 — the previously documented
  3.12.13 was wrong), Flask ≥3.0, stdlib only. On 3.9, `datetime.fromisoformat` parses only
  the output of `datetime.isoformat()`: it accepts `+05:30`, the date-only form, and year
  9999, but **raises `ValueError` on a trailing `Z`**. `Z` support therefore requires the
  normalization shim specified in §6.2 — a string replacement, not a library. Adding
  `dateutil` or `pendulum` remains unjustified, so G-5 holds and `requirements.txt` is
  unchanged.
- **C-T2** Flask's default JSON provider emits RFC 822 for `datetime`, not ISO 8601.
  Forces the string-storage decision in §6.2.
- **C-T3** `get_tasks()` returns the live list by reference (`task.py:13-14`). Constrains
  every read path to copy before transforming.
- **C-T4** No database, so no schema, no migration, no durability.
- **C-T5** Single-process dev server; no locking primitives in use.
- **C-T6** On 3.9, fractional seconds must be exactly 3 or 6 digits:
  `datetime.fromisoformat("2026-08-05T17:00:00.5+00:00")` raises `ValueError`, while 3.11+
  accepts it. The same request therefore yields 400 here and 201 on a newer interpreter.
  Documented, not worked around — normalizing fractional-second precision would mean
  hand-parsing ISO 8601, which is exactly what `fromisoformat` exists to avoid. See R-8.
- **C-T7** `datetime.UTC` is a 3.11+ alias and does not exist on 3.9.6. Use `timezone.utc`.
  Stated because it is the second-easiest way to write code that looks right and fails to
  import on this runtime.

### Data
- **C-D1** Zero persistence — data lifetime is one process lifetime.
- **C-D2** No PII beyond free-text titles. Due dates add no new sensitive data class.

### Operational
- **C-O1** No deploy pipeline, no environments, no monitoring, no logging configured
  anywhere in the app today.
- **C-O2** Server timezone is process-level and unconfigurable per user (NG-3). It is also
  what defines "end of day" for A-3, so the same server serving users in two timezones will
  roll date-only tasks to overdue on the server's midnight, not theirs (R-1).

### Compatibility
- **C-C1** Both existing tests must pass **unmodified** (§10a).
- **C-C2** The existing `GET /tasks` default order is a contract; it cannot change.
- **C-C3** `python/public/` is byte-identical to the Node and Java frontends (re-verified,
  §3.7). Any edit breaks a repo-wide invariant.
- **C-C4** `python/README.md` publishes the API and data model as documentation. It is part
  of the contract surface and must be updated in the same change, not later (I5, G-9).

### Scope and effort
- **C-S1** Python only. Node and Java are untouched this iteration.
- **C-S2** NG-1 through NG-4 are hard boundaries, including no due-date editing.
- **C-S3** No opportunistic refactoring of the known `get_tasks()` aliasing issue beyond
  what this feature strictly requires.

### Dependency
- **C-P1** No external services, no network calls, no upstream teams. Fully self-contained.
  The `Z` shim deliberately keeps it that way (C-T1).

## 10. Guardrails

### 10a. Regression guardrails — protecting the existing codebase

| # | Guardrail |
|---|---|
| **G-1** | **Additive only.** No existing field, route, status code, or response key is removed or renamed |
| **G-2** | **Both existing tests pass unmodified.** If either needs an edit, that is a breaking change and stops work for re-approval — it is not quietly rewritten |
| **G-3** | **Default `GET /tasks` order is untouched.** Sorting is strictly opt-in (FR-7, C-C2) |
| **G-4** | **Validate before mutate.** No id consumed and no dict appended on a rejected request (F2). Type check before the `Z` shim, parse before end-of-day substitution (A9, F5, B11) |
| **G-5** | **No new dependencies.** `requirements.txt` unchanged. The `Z` normalization is stdlib string handling precisely so this guardrail survives contact with the runtime limitation in C-T1 |
| **G-6** | **Never sort or mutate the list returned by `get_tasks()` in place.** Use `sorted()` on a copy; build response dicts as copies (C2, G1, G2) |
| **G-7** | **Frontend parity is broken knowingly.** `python/public/` diverges from Node and Java. Called out in the PR **and in `python/README.md`**, not discovered later (R-2) |
| **G-8** | **No opportunistic refactoring.** The `_next_id` race and the `get_tasks()` aliasing issue are noted as follow-ups, not fixed here (C-S3) |
| **G-9** | **Blast radius, complete** — every file this feature may touch: |

| File | Change | Risk | Verified by |
|---|---|---|---|
| `python/models/task.py` | `create_task` gains an optional param; add a derived-view helper | **Medium** — the only stateful module | New unit tests + both existing tests |
| `python/routes/tasks.py` | Validation in `add_task` (incl. the `Z` shim and end-of-day rule); `sort` handling in `list_tasks` | **Medium** — shared request path | New route tests + existing tests |
| `python/public/app.js` | Date input, due-date render (local date derived from the stored UTC value, J7), overdue class, sorted fetch | **Low** — presentation only | Manual browser check + running app |
| `python/public/index.html` | Date input field, overdue CSS | **Low** | Manual browser check |
| `python/README.md` | Data-model block (`README.md:35-39`) gains `dueDate`; API table (`README.md:26-33`) gains the `dueDate` request field and the `sort=dueDate` query parameter; the two "same as `Node/`" claims (`README.md:3,9`) are replaced with an explicit note that the Python implementation has intentionally diverged | **Low** in isolation, but this file **is** R-2's mitigation — a stale README is the exact mechanism by which the parity break bites a later reader | Diff review against the shipped §7 contract; the documented response shape must match an actual `curl` response verbatim (§12) |
| `python/tests/test_tasks.py` | **Additions only**, no edits to the two existing tests | **Low** | Diff review — existing test bodies must be untouched |
| `python/requirements.txt` | **No change** (G-5) | — | Diff review |
| `Node/`, `java/` | **No change** (C-S1) | — | Diff review |

- **G-10** No feature flag. The change is additive, opt-in at the API level, and the store
  is non-durable, so rollback is a plain `git revert` with no data consequence.

### 10b. Authentication and authorization guardrails

The app has **no authentication of any kind** (§3.4). That is the starting position, and
this feature must neither depend on it nor quietly worsen it.

| # | Guardrail |
|---|---|
| **A-G1** | **No new endpoint or surface.** Only existing routes are extended (E4). Nothing new to leave unprotected |
| **A-G2** | **Default deny is not weakened.** Since nothing is currently protected, the concrete obligation is: introduce no new capability that would need protection and not get it |
| **A-G3** | **No access widening.** Due dates and sorting expose no task that was not already visible to every caller. No new read path, no new field on someone else's data |
| **A-G4** | **No secrets** in source, logs, errors, URLs, or fixtures. This feature introduces none — no credentials, no tokens, no keys |
| **A-G5** | **No input reflection.** A rejected `dueDate` produces a fixed error message and never echoes the submitted value, nor the `Z`-normalized rewrite of it (E3), so a malformed date cannot become a reflection vector |
| **A-G6** | **No XSS regression.** All new frontend text nodes use `textContent`. `innerHTML` is not introduced for the date, the badge, or anything else (J6) |
| **A-G7** | **Accepted risk, explicitly.** Building on an unauthenticated app is a deliberate, acknowledged decision for this workshop iteration — recorded as R-4 and **acknowledged at approval** (see §14 Approval), not assumed |

## 11. Error handling specification

Per failure mode, not a promise to "handle errors".

| Mode | Detection | Response | Message | Log | Recovery |
|---|---|---|---|---|---|
| Missing title | `add_task`, before all else | 400 | `title is required` (**unchanged**) | none (matches today) | Terminal; client resubmits |
| Wrong-typed `dueDate` | `add_task`, type check **before** the `Z` shim (A9, F5) | 400 | `dueDate must be a valid ISO 8601 datetime` | none | Terminal |
| Invalid `dueDate` string | `add_task`, after title check, after `Z` normalization, before `create_task` | 400 | same message | none | Terminal; client resubmits |
| `Z`-normalized value still unparseable (e.g. `"Z"` → `"+00:00"`, A18) | same parse call | 400 | same message — the rewritten string is never surfaced (A-G5) | none | Terminal |
| Unknown `sort` value | `list_tasks`, before reading the store | 400 | `sort must be one of: dueDate` | none | Terminal |
| Non-integer task id | Flask `<int:>` converter | 404 | Flask default (**unchanged**) | none | Terminal |
| Task not found | existing model return | 404 | `task not found` (**unchanged**) | none | Terminal |
| Malformed / absent JSON | `get_json(silent=True)` → `{}` | 400 | `title is required` (**unchanged**) | none | Terminal |
| Unexpected parse exception | `try/except (ValueError, TypeError, OverflowError)` around parsing | 400 | same invalid-date message | none | Terminal, no partial state |

Cross-cutting rules:

- **One message for every invalid `dueDate`.** Wrong type, unparseable string, and
  post-shim failure all return the same text, so the error surface reveals nothing about
  internals — including nothing about the existence of the `Z` shim.
- **Validation precedes state change.** Every 400 path leaves `_tasks` and `_next_id`
  exactly as they were (F2, G-4).
- **Normalization precedes nothing dangerous.** The `Z` shim and the end-of-day substitution
  are transformations on a candidate value, applied before any store write. An invalid date
  can never be rescued by the end-of-day substitution (B11).
- **No stack traces, no `repr` of input, no internal paths** in any response body (A-G5).
- **Nothing fails silently** — no bare `except`, no swallowed exception, no `pass` in an
  exception handler. An invalid due date is always an explicit 400, never a `None` that
  quietly becomes "no due date".
- **No new 500s.** Every input reachable via the HTTP API resolves to a specified 2xx or
  4xx. Any 500 discovered during verification is a defect, not an edge case.
- **Message style matches existing convention**: lowercase, no trailing period, under
  `{"error": ...}`.
- Logging stays absent, consistent with the rest of the app (C-O1). Adding a logging
  framework is out of scope.

## 12. Acceptance criteria — the definition of "error free"

The end state is error free only when **all** of the following hold. Each is checkable, not
a judgment call.

**Requirements coverage**
- [ ] Every FR-1 … FR-10 has at least one automated test asserting it.
- [ ] Every edge case A1–A18, B1–B16, C2–C4, D1–D2, E3, F1–F3, F5, G1–G4, I1–I3, I5 has a
      test, or a written reason why it is untestable in-process (C1's true concurrency and
      F4's restart are expected to fall in the latter group).
- [ ] **A12 asserted explicitly against this interpreter:** `POST /tasks` with
      `"dueDate": "2026-08-05T17:00:00Z"` returns **201**, not 400. This is the case the
      previous revision got wrong; it is the single most important new assertion.
- [ ] **A-3 asserted end to end:** a date-only `dueDate` set to today's local date returns
      `overdue: false` (B12) and the same value set to yesterday returns `overdue: true`
      (B14), with the stored value ending in a 23:59:59.999999-derived UTC timestamp (§7.5).
- [ ] Frontend cases J1–J7 verified by loading the running app in a browser — not inferred
      from reading the code.

**Regression**
- [ ] `pytest -v` green, and the **two pre-existing tests are byte-identical** to their
      current form (`git diff` on `test_tasks.py` shows additions only).
- [ ] `GET /tasks` with no query parameter returns insertion order — asserted by a test
      that creates out-of-order due dates, requests sorted, then requests unsorted.
- [ ] `_tasks` order is unchanged after a sorted read (G3).
- [ ] `Node/` and `java/` have zero diff.
- [ ] `requirements.txt` has zero diff (G-5) — the `Z` handling added no dependency.

**Correctness**
- [ ] No response contains a stored `overdue` key in `_tasks` — asserted by inspecting the
      store directly after a read.
- [ ] Every 400 path asserted to leave the store unchanged (task count and `_next_id`).
- [ ] No input in §8 produces a 500. A dedicated test sweeps the malformed-input table,
      including A18 (`"Z"` alone) and A9 (non-string types), which are the two inputs the
      `Z` shim could plausibly turn into an unhandled exception.

**Documentation**
- [ ] **`python/README.md` updated** (G-9, C-C4): the data-model block shows `dueDate`; the
      API table lists the optional `dueDate` request field on `POST /tasks` and the
      `sort=dueDate` query parameter on `GET /tasks`; the two "same as `Node/`" claims are
      replaced with an explicit statement that the Python implementation has diverged and
      why (R-2).
- [ ] The README's documented response shape matches a real `curl` response byte for byte —
      copied from an actual run, not written from memory.

**Cleanliness**
- [ ] `python3 -m compileall` clean; no syntax errors, no import errors. Run with the
      **3.9.6** interpreter, since C-T7 (`datetime.UTC`) is an import-time failure there and
      would pass silently on a newer one.
- [ ] No debug output (`print`, `breakpoint`), no commented-out code, no TODOs left.
- [ ] No secrets, no credentials, no `.env` additions.

**Real-world verification**
- [ ] App starts via `python app.py` and serves on its port. *(Run by the human — this
      document's author does not start servers.)*
- [ ] Manual end-to-end: create with due date → create without → **create one due today via
      the date picker and confirm it does NOT show as overdue** → observe overdue styling on
      a past date → observe sorted order → complete an overdue task and watch the badge
      clear → delete.
- [ ] `curl` sweep of every endpoint including the new 400 paths, with responses recorded.

## 13. Rollout and rollback

**Deployment.** No pipeline exists (C-O1). "Rollout" is: merge to `pod_3_dev`, and each
developer restarts their local server. No migration, no sequencing, no coordination.

**Order of work.**
1. `models/task.py` — storage + derived view (with tests)
2. `routes/tasks.py` — validation, `Z` normalization, end-of-day rule, sort (with tests)
3. `public/` — frontend (manual verification)
4. `README.md` — API table, data model, parity note
5. Full suite + manual sweep

Backend lands before frontend so the API is provably correct before anything consumes it.
Documentation lands last so it describes what actually shipped, not what was planned.

**Monitoring.** None available. Verification is entirely pre-merge, which is precisely why
§12 is strict.

**Rollback.** `git revert` of the feature commit. Because the store is non-durable
(§3.3/6.3), reverting has **zero data consequence** — no orphaned columns, no stranded
rows, nothing to clean up. A restart returns the app to exactly its prior state. This is
the cheapest rollback profile this feature could possibly have.

## 14. Assumptions, open questions, and risks

### Assumptions — proceeding on these

| # | Assumption |
|---|---|
| **A-1** | "Overdue" excludes completed tasks. A finished task that was late is *done*, not *late* (FR-5). This is the one semantic call most likely to be contested |
| **A-2** | Naive datetimes (no offset) are server-local, converted to UTC on store. Direct consequence of NG-3 |
| **A-3** | **A due date with no time component (`2026-08-05`) means the END of that day — `23:59:59.999999` server-local, normalized to UTC.** *Reversed from the earlier start-of-day reading.* Rationale: the HTML `date` input emits date-only values and nothing else, so date-only is the *normal* case from the UI, not an exotic one. Under start-of-day, a task the user marks as due today has a deadline of 00:00:00 — already past by the time they finish typing — so FR-5's strictly-past rule renders it overdue for the entire day it is actually due. That is wrong to a user and would read as a bug, not a definition. End-of-day is the only interpretation under which "due today" means due today. **A due date supplied *with* a time component is unaffected** and still uses that time exactly as given (offset honored, server-local if naive). FR-5 is unchanged; only where a date-only value lands on the clock has moved. Consequences: §6.2, §7.5 (round-trip and sort interaction), A10, B10–B16, J7 |
| **A-4** | Due dates may be in the past at creation time — a user recording something already late is legitimate, not an error |
| **A-5** | The JSON key is `dueDate`, not `due_date`, for cross-implementation parity (§6.2) |
| **A-6** | The UI sorts by due date by default (FR-9), while the API does not (FR-7). The user story asks for the sorted *view*; the API default must stay stable for compatibility |
| **A-7** | Sort direction is ascending only. No `?order=desc` — not requested, not built |
| **A-8** | End-of-day precision is `23:59:59.999999` (microsecond resolution, the finest `datetime` offers) rather than `23:59:59`. The one-second difference is unobservable in practice, but picking the true maximum avoids a task being "not yet overdue" and "already past its day" simultaneously in the final second |

### Open questions — do not block; defaults are stated above

| # | Question | Default if unanswered |
|---|---|---|
| **Q-1** | Should overdue tasks also sort ahead of non-overdue ones, or is pure chronological ordering enough? | Pure chronological (FR-6). Overdue tasks are the oldest dates, so they naturally surface first |
| **Q-2** | Should the UI show relative time ("2 days late") as well as the date? | Absolute date only. Relative formatting is scope creep and adds a rendering-time dependency on the clock |

### Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R-1** | Server-timezone assumption produces surprising overdue flips for a user in another timezone. A-3 sharpens this: "end of day" is the *server's* day, so a user east or west of the server sees the flip at the wrong local midnight | Medium | Low | Documented (NG-3, A-2, A-3, C-O2). Storing normalized UTC means a future per-user timezone feature is additive, not a rewrite |
| **R-2** | Frontend parity with Node and Java breaks; a later pod copies a stale frontend and silently loses the feature | **High** | Medium | G-7 — called out explicitly in the PR description **and in `python/README.md`, which is now in the blast radius (G-9) with a checkable acceptance item (§12)**. The previous revision named the README as the mitigation but never listed it as a file to change, so the mitigation had nothing behind it |
| **R-3** | A mistyped due date is uncorrectable (NG-4); the user must delete and recreate | Medium | Medium | Accepted this iteration, and **acknowledged at approval**. First candidate for the next one |
| **R-4** | Building on a completely unauthenticated app; "my tasks" has no data-model meaning (§3.4, E2) | High | **High in any real deployment** | Explicitly accepted for the workshop (A-G7), and **acknowledged at approval** |
| **R-5** | In-place sort silently corrupts stored order — the single most likely serious defect here | Medium | **High** | G-6 plus a dedicated regression test (G3), asserted directly against the store |
| **R-6** | Thin existing test coverage (§3.6) means regressions in `GET`/`DELETE` would go unnoticed | Medium | Medium | §12 adds coverage for the paths this feature touches |
| **R-7** | A future interpreter upgrade to 3.11+ makes the `Z`-normalization shim redundant, and a later reader removes it as dead code without checking which interpreter is actually deployed | Low | Low | None needed for correctness: the shim is harmless on every version — `"…T17:00:00+00:00"` parses identically on 3.7 through current, so leaving it in place costs nothing. Removing it is a cleanup task, not a fix, and is out of scope under G-8. C-T1 records *why* it exists so the reasoning survives the upgrade |
| **R-8** | Interpreter-version-dependent acceptance: `"2026-08-05T17:00:00.5+00:00"` (1-digit fractional seconds) is a 400 on 3.9.6 and a 201 on 3.11+ (C-T6). The same client gets different status codes from two servers running the same code | Low | Low | Documented, not worked around. Normalizing fractional-second precision means hand-parsing ISO 8601, which defeats the purpose of using `fromisoformat`. If the runtime is ever upgraded, re-run the §8 A-table — it is the acceptance boundary that moves |

---

## Approval

**Approved.** Implementation is under way against this specification.

Approval explicitly included acknowledgement of the two accepted risks:

- **R-3** — a due date set at creation cannot be edited or cleared (NG-4); the only remedy is
  delete and recreate. Accepted for this iteration.
- **R-4** — the application has no authentication of any kind (§3.4), so "my tasks" has no
  data-model meaning and every caller shares one global list. Accepted for this workshop
  iteration only, and **not** acceptable in any real deployment.

Three decisions were taken after the original approval and are incorporated above rather than
requiring re-approval, because each narrows behaviour to what was already intended:

1. **`Z` normalization** (§6.2, C-T1) — required to make the already-approved API contract in
   §7.1 actually work on the real runtime. Without it the approved contract was unshippable.
2. **A-3 reversed to end-of-day** — a correction to a rule that produced user-visible wrong
   behaviour (a task due today reading as overdue all day).
3. **`python/README.md` added to the blast radius** (G-9) — closing a gap where R-2's stated
   mitigation referenced a file the change plan never touched.

Anything discovered during implementation that falls outside this document goes back as a BRD
amendment, not a silent scope change.
