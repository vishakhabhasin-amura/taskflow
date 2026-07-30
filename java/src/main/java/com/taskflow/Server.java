package com.taskflow;

import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.net.InetSocketAddress;

public final class Server {
    private final HttpServer httpServer;

    public Server(int port) throws IOException {
        httpServer = HttpServer.create(new InetSocketAddress(port), 0);
        httpServer.createContext("/tasks", new TaskHandler());
        httpServer.createContext("/", new StaticFileHandler());
    }

    public void start() {
        httpServer.start();
    }

    public void stop() {
        httpServer.stop(0);
    }

    public int port() {
        return httpServer.getAddress().getPort();
    }

    public static void main(String[] args) throws IOException {
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "3000"));
        Server server = new Server(port);
        server.start();
        System.out.println("TaskFlow (Java) listening on port " + port);
    }
}
