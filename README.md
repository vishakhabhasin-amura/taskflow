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
