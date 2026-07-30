package com.taskflow;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;

final class TaskHandler implements HttpHandler {

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        try {
            String method = exchange.getRequestMethod();
            String[] parts = exchange.getRequestURI().getPath().split("/");
            // parts: ["", "tasks"] or ["", "tasks", "{id}"]

            if (method.equals("GET") && parts.length == 2) {
                handleList(exchange);
            } else if (method.equals("POST") && parts.length == 2) {
                handleCreate(exchange);
            } else if (method.equals("PATCH") && parts.length == 3) {
                handleUpdate(exchange, Integer.parseInt(parts[2]));
            } else if (method.equals("DELETE") && parts.length == 3) {
                handleDelete(exchange, Integer.parseInt(parts[2]));
            } else {
                sendJson(exchange, 404, "{\"error\":\"not found\"}");
            }
        } finally {
            exchange.close();
        }
    }

    private void handleList(HttpExchange exchange) throws IOException {
        List<Task> tasks = TaskStore.getTasks();
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < tasks.size(); i++) {
            if (i > 0) sb.append(",");
            sb.append(tasks.get(i).toJson());
        }
        sb.append("]");
        sendJson(exchange, 200, sb.toString());
    }

    private void handleCreate(HttpExchange exchange) throws IOException {
        Map<String, Object> body = Json.parseObject(readBody(exchange));
        Object title = body.get("title");
        if (!(title instanceof String) || ((String) title).isEmpty()) {
            sendJson(exchange, 400, "{\"error\":\"title is required\"}");
            return;
        }
        Task task = TaskStore.createTask((String) title);
        sendJson(exchange, 201, task.toJson());
    }

    private void handleUpdate(HttpExchange exchange, int id) throws IOException {
        Map<String, Object> body = Json.parseObject(readBody(exchange));
        boolean completed = Boolean.TRUE.equals(body.get("completed"));
        boolean updated = TaskStore.updateCompleted(id, completed);
        if (!updated) {
            sendJson(exchange, 404, "{\"error\":\"task not found\"}");
            return;
        }
        Optional<Task> task = TaskStore.getTask(id);
        sendJson(exchange, 200, task.get().toJson());
    }

    private void handleDelete(HttpExchange exchange, int id) throws IOException {
        boolean deleted = TaskStore.deleteTask(id);
        if (!deleted) {
            sendJson(exchange, 404, "{\"error\":\"task not found\"}");
            return;
        }
        exchange.sendResponseHeaders(204, -1);
    }

    private String readBody(HttpExchange exchange) throws IOException {
        try (InputStream is = exchange.getRequestBody()) {
            return new String(is.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private void sendJson(HttpExchange exchange, int status, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().add("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, bytes.length);
        exchange.getResponseBody().write(bytes);
    }
}
