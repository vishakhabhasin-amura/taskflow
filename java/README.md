# TaskFlow (Java)

Same API and data model as [Node/](../Node/README.md), built on only the JDK's built-in
`com.sun.net.httpserver` (no Spring/servlet container) plus a tiny hand-rolled JSON helper —
the schema is a fixed, flat 3-field object, so a full JSON library would be overkill.

⚠️ **Not verified locally** — no JDK/Maven was available in the environment this was written
in, so this has not been compiled or run. Run `mvn test` before trusting it.

## Stack

- Backend: Java 17, JDK `HttpServer` (no framework)
- Storage: in-memory list
- Frontend: same static HTML + vanilla JS as `Node/public/`
- Tests: JUnit 5, real HTTP requests via `java.net.http.HttpClient` (mirrors Node's Supertest
  usage — no mocking)

## Run

```bash
mvn package
java -jar target/taskflow.jar   # serves on http://localhost:3000
mvn test
```

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
java/
├── pom.xml
├── src/main/java/com/taskflow/
│   ├── Server.java             — HttpServer entrypoint, wires up contexts
│   ├── TaskHandler.java         — /tasks route handling (the "controller" layer)
│   ├── TaskStore.java            — in-memory task store (the "model" layer)
│   ├── Task.java                  — data class + JSON serialization
│   ├── Json.java                   — minimal JSON parse/escape for this fixed schema
│   └── StaticFileHandler.java       — serves public/ resources
├── src/main/resources/public/     — same static frontend as Node/
└── src/test/java/com/taskflow/TaskFlowTest.java
```
