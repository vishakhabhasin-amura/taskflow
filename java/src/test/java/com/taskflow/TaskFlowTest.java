package com.taskflow;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpRequest.BodyPublishers;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TaskFlowTest {
    private Server server;
    private HttpClient client;
    private String baseUrl;

    @BeforeEach
    void setUp() throws Exception {
        TaskStore.reset();
        server = new Server(0);
        server.start();
        baseUrl = "http://localhost:" + server.port();
        client = HttpClient.newHttpClient();
    }

    @AfterEach
    void tearDown() {
        server.stop();
    }

    @Test
    void test_add_task_creates_task_with_given_title() throws Exception {
        HttpResponse<String> res = postTask("Buy milk");

        assertEquals(201, res.statusCode());
        Map<String, Object> body = Json.parseObject(res.body());
        assertEquals("Buy milk", body.get("title"));
        assertEquals(Boolean.FALSE, body.get("completed"));
    }

    @Test
    void test_mark_complete_toggles_completed() throws Exception {
        HttpResponse<String> created = postTask("Walk dog");
        int id = (int) Json.parseObject(created.body()).get("id");

        HttpRequest patch =
                HttpRequest.newBuilder(URI.create(baseUrl + "/tasks/" + id))
                        .header("Content-Type", "application/json")
                        .method("PATCH", BodyPublishers.ofString("{\"completed\":true}"))
                        .build();
        HttpResponse<String> res = client.send(patch, BodyHandlers.ofString());

        assertEquals(200, res.statusCode());
        assertTrue(Boolean.TRUE.equals(Json.parseObject(res.body()).get("completed")));
    }

    private HttpResponse<String> postTask(String title) throws Exception {
        HttpRequest req =
                HttpRequest.newBuilder(URI.create(baseUrl + "/tasks"))
                        .header("Content-Type", "application/json")
                        .POST(BodyPublishers.ofString("{\"title\":\"" + title + "\"}"))
                        .build();
        return client.send(req, BodyHandlers.ofString());
    }
}
