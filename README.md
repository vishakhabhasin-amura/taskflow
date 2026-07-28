# TaskFlow


A minimal to-do list application.

## Stack

- Backend: Node.js + Express
- Storage: in-memory array (no external database)
- Frontend: static HTML + vanilla JS (`public/`)
- Tests: Jest + Supertest

## Run

```bash
npm install
npm start        # serves on http://localhost:3000
npm test
```

## API

| Method | Route       | Behavior                          |
|--------|-------------|------------------------------------|
| GET    | /tasks      | Returns all tasks                  |
| POST   | /tasks      | Creates a task — body: `{ title }` |
| PATCH  | /tasks/:id  | Updates a task — body: `{ completed }` |
| DELETE | /tasks/:id  | Deletes a task by id               |

## Data model

```js
{ id: number, title: string, completed: boolean }
```

## Repo structure

```
taskflow/
├── server.js              — Express app entrypoint
├── routes/tasks.js         — route handlers (the "controller" layer)
├── models/task.js           — in-memory data store (the "model" layer)
├── public/
│   ├── index.html            — static page, no build step
│   └── app.js                 — vanilla JS: fetch() calls + DOM rendering
├── tests/tasks.test.js      — Jest + Supertest tests
├── package.json
└── .gitignore
```

Three layers, cleanly separated:

- **`models/task.js`** — owns the data. A plain in-memory array (`tasks`) plus an
  auto-incrementing `nextId`. No database, so restarting the server wipes all tasks —
  deliberate, to keep setup trivial.
- **`routes/tasks.js`** — owns the HTTP contract. Translates requests into calls against the
  model and shapes responses/status codes.
- **`server.js`** — wires it together: JSON body parsing, mounts the router at `/tasks`, and
  serves `public/` as static files for anything else.

## Request flow

**Browser load** — Express's `express.static` middleware in `server.js` serves
`public/index.html`, which pulls in `app.js`.

**Adding a task** (`app.js`'s form submit handler):

```
browser form submit
  → app.js: fetch POST /tasks { title }
    → server.js: express.json() parses body → routes to tasksRouter
      → routes/tasks.js POST handler: validates title present
        → models/task.js createTask(title): pushes { id, title, completed: false }
      ← 201 + the new task JSON
  → app.js: re-fetches full list, re-renders <ul>
```

**Toggling complete** / **deleting**: same shape — `app.js` calls `PATCH /tasks/:id` or
`DELETE /tasks/:id`, the router looks up the task by id via `models/task.js`, mutates or
removes it, and `app.js` re-fetches to refresh the DOM. The frontend holds no state of its
own — every action reloads the full list from `GET /tasks`.

**Endpoint → model function mapping**:

| Route | Model call | Response |
|---|---|---|
| `GET /tasks` | `getTasks()` | full array |
| `POST /tasks` | `createTask(title)` | 201 + new task, or 400 if no title |
| `PATCH /tasks/:id` | `updateTask(id, {completed})` | 200 + updated task, or 404 |
| `DELETE /tasks/:id` | `deleteTask(id)` | 204, or 404 |

## Tests

`tests/tasks.test.js` uses Supertest against the exported `app` object directly — it never
starts a real HTTP server or hits the network. That's why `server.js` guards `app.listen()`
behind `if (require.main === module)`: when Jest `require`s the file, that block is skipped
and only `module.exports = app` runs, so the test file can drive requests in-process.
`models/task.js` also exports a `reset()` used in `beforeEach` so each test starts from an
empty task list rather than leaking state between tests.
