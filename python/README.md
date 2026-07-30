# TaskFlow (Python)

Same API and data model as [Node/](../Node/README.md), built with Flask.

## Stack

- Backend: Python 3 + Flask
- Storage: in-memory list (`models/task.py`)
- Frontend: same static HTML + vanilla JS as `Node/public/`
- Tests: pytest + Flask's test client (in-process, mirrors Node's Supertest usage — no mocking,
  no real socket)

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py     # serves on http://localhost:3000
.venv/bin/pytest -v
```

Verified locally: both tests pass, and the live server was hit directly (`GET /`, `GET /tasks`,
`POST /tasks`) to confirm static file serving and the API work end-to-end, not just under the
test client.

## API

| Method | Route       | Behavior                          |
|--------|-------------|------------------------------------|
| GET    | /tasks      | Returns all tasks                  |
| POST   | /tasks      | Creates a task — body: `{ title }` |
| PATCH  | /tasks/:id  | Updates a task — body: `{ completed }` |
| DELETE | /tasks/:id  | Deletes a task by id               |

## Data model

```json
{ "id": 1, "title": "string", "completed": false }
```

## Repo structure

```
python/
├── app.py                 — Flask app entrypoint, registers the tasks blueprint
├── routes/tasks.py         — route handlers (the "controller" layer)
├── models/task.py           — in-memory task store (the "model" layer)
├── public/                   — same static frontend as Node/
├── tests/test_tasks.py     — pytest + Flask test client
├── requirements.txt
└── pyproject.toml          — pytest config (testpaths, pythonpath)
```
