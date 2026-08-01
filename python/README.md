# TaskFlow (Python)

Flask implementation of TaskFlow. It started as a port of [Node/](../Node/README.md) and shared the
same API, data model, and frontend — due dates have since moved it ahead of both other stacks. See
"Divergence from Node and Java" below.

## Stack

- Backend: Python 3 + Flask
- Storage: in-memory list (`models/task.py`)
- Frontend: static HTML + vanilla JS in `public/` (no longer identical to `Node/public/`)
- Tests: pytest + Flask's test client (in-process, mirrors Node's Supertest usage — no mocking,
  no real socket)

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py     # serves on http://localhost:3000
.venv/bin/pytest -v
```

Verified locally: the suite passes, and the live server was hit directly (`GET /`, `GET /tasks`,
`POST /tasks`) to confirm static file serving and the API work end-to-end, not just under the
test client.

## API

| Method | Route       | Behavior                          |
|--------|-------------|------------------------------------|
| GET    | /tasks      | Returns all tasks in insertion order. Optional `?sort=dueDate` returns them by due date ascending, tasks without a due date last, ties broken by ascending id. Any other `sort` value is `400` |
| POST   | /tasks      | Creates a task — body: `{ title, dueDate? }`. `dueDate` is an optional ISO 8601 date or datetime string; anything else is `400` |
| PATCH  | /tasks/:id  | Updates a task — body: `{ completed }`. A `dueDate` in the body is ignored; due dates are set at creation only |
| DELETE | /tasks/:id  | Deletes a task by id               |

### Due dates

- `dueDate` is stored as a canonical UTC ISO 8601 string. A value carrying an offset is converted to
  UTC; a value without one is read as server-local time first (there is no per-user timezone).
- A date with no time — `"2026-08-05"`, which is exactly what an HTML `<input type="date">` sends —
  means the **end** of that day, so a task due today is not overdue at any point during today.
- `overdue` is derived on every read and never stored: it is true when a task has a due date, that
  date is strictly in the past, and the task is not completed.
- Because a date-only value round-trips as an end-of-day UTC instant, a client must render the local
  calendar date derived from the stored value, not the raw stored string.

## Data model

Stored (`models/task.py`):

```json
{ "id": 1, "title": "string", "completed": false, "dueDate": "2026-08-05T18:29:59.999999+00:00" }
```

`dueDate` is `null` when the task has none. Every API response adds one derived field that is never
written to the store:

```json
{ "overdue": false }
```

## Divergence from Node and Java

`python/public/` used to be byte-identical to `Node/public/` and
`java/src/main/resources/public/`; all three implementations deliberately shared one frontend. The
due-date work changed `python/public/index.html` and `python/public/app.js` only, so that parity is
now **knowingly broken**.

Copying either of the other frontends over `python/public/` would silently remove the due-date
input, the due-date column, and the overdue badge. Port the change instead of copying, or bring the
other two implementations up to the same contract first.

## Repo structure

```
python/
├── app.py                 — Flask app entrypoint, registers the tasks blueprint
├── routes/tasks.py         — route handlers (the "controller" layer)
├── models/task.py           — in-memory task store (the "model" layer)
├── public/                   — static frontend (diverged from Node/ — see above)
├── tests/test_tasks.py     — pytest + Flask test client
├── requirements.txt
└── pyproject.toml          — pytest config (testpaths, pythonpath)
```
