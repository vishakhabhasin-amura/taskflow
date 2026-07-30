package com.taskflow;

final class Task {
    final int id;
    final String title;
    boolean completed;

    Task(int id, String title) {
        this.id = id;
        this.title = title;
        this.completed = false;
    }

    String toJson() {
        return String.format(
                "{\"id\":%d,\"title\":\"%s\",\"completed\":%b}", id, Json.escape(title), completed);
    }
}
