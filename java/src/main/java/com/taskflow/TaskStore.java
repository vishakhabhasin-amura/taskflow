package com.taskflow;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

final class TaskStore {
    private static final List<Task> tasks = new ArrayList<>();
    private static int nextId = 1;

    private TaskStore() {}

    static synchronized Task createTask(String title) {
        Task task = new Task(nextId++, title);
        tasks.add(task);
        return task;
    }

    static synchronized List<Task> getTasks() {
        return new ArrayList<>(tasks);
    }

    static synchronized Optional<Task> getTask(int id) {
        return tasks.stream().filter(t -> t.id == id).findFirst();
    }

    static synchronized boolean updateCompleted(int id, boolean completed) {
        Optional<Task> task = getTask(id);
        task.ifPresent(t -> t.completed = completed);
        return task.isPresent();
    }

    static synchronized boolean deleteTask(int id) {
        return tasks.removeIf(t -> t.id == id);
    }

    static synchronized void reset() {
        tasks.clear();
        nextId = 1;
    }
}
