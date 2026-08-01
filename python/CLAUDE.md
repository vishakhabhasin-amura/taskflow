# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

The Python implementation of **TaskFlow**, a minimal to-do app built for an "Agentic AI SDLC workshop". The repo root (`../`) holds three independent implementations — `Node/` (Express), `java/` (Maven), and `python/` (Flask) — that all implement the **same API contract and data model**, so a change in one language usually has a mirror in the others. When editing behavior here, check `../Node/` for the reference implementation to stay consistent.

## Commands

Run from this `python/` directory:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python app.py                 # serve on http://localhost:3000 (override with PORT=)
.venv/bin/pytest -v                      # run all tests
.venv/bin/pytest tests/test_tasks.py::test_add_task_creates_task_with_given_title -v   # single test
```

`pyproject.toml` sets `pythonpath = ["."]`, so tests and the app import top-level packages (`app`, `models.task`, `routes.tasks`) directly — no `src/` layout, no install step needed.

## Architecture

Three layers, mirroring an MVC split:

- `app.py` — Flask entrypoint. Registers the tasks blueprint and serves the static frontend from `public/` (mounted at `/`, via `static_url_path=""`).
- `routes/tasks.py` — the controller. A `tasks_bp` blueprint under `/tasks` handling GET/POST/PATCH/DELETE, all request/response and status-code logic.
- `models/task.py` — the model. An **in-memory store held in module-level globals** (`_tasks`, `_next_id`).

### The state gotcha

`models/task.py` keeps tasks in module-level lists/counters, so **state persists across requests for the life of the process** and there is no database. Two consequences:

- Restarting `app.py` wipes all tasks.
- Tests must reset this shared state between cases. `tests/test_tasks.py` does this with an `autouse` fixture calling `models.task.reset()`. Any new test file must do the same, or tests will leak state into each other.

Tests use Flask's in-process `test_client()` — no mocking, no real socket — matching Node's Supertest approach.

## API contract (keep identical across all three implementations)

| Method | Route         | Behavior                                    | Success |
|--------|---------------|---------------------------------------------|---------|
| GET    | `/tasks`      | Returns all tasks                           | 200     |
| POST   | `/tasks`      | Create — body `{ title }`; empty → 400      | 201     |
| PATCH  | `/tasks/:id`  | Update — body `{ completed }`; missing → 404| 200     |
| DELETE | `/tasks/:id`  | Delete by id; missing → 404                 | 204     |

Task shape: `{ "id": 1, "title": "string", "completed": false }`. `id` is a server-assigned auto-incrementing integer.
