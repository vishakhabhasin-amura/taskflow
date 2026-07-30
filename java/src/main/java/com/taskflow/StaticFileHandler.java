package com.taskflow;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

final class StaticFileHandler implements HttpHandler {
    @Override
    public void handle(HttpExchange exchange) throws IOException {
        try {
            String path = exchange.getRequestURI().getPath();
            if (path.equals("/")) path = "/index.html";
            String resourcePath = "public" + path;

            try (InputStream is = getClass().getClassLoader().getResourceAsStream(resourcePath)) {
                if (is == null) {
                    byte[] notFound = "not found".getBytes(StandardCharsets.UTF_8);
                    exchange.sendResponseHeaders(404, notFound.length);
                    exchange.getResponseBody().write(notFound);
                    return;
                }
                byte[] bytes = is.readAllBytes();
                String contentType =
                        path.endsWith(".html") ? "text/html"
                        : path.endsWith(".js") ? "application/javascript"
                        : "text/plain";
                exchange.getResponseHeaders().add("Content-Type", contentType);
                exchange.sendResponseHeaders(200, bytes.length);
                exchange.getResponseBody().write(bytes);
            }
        } finally {
            exchange.close();
        }
    }
}
