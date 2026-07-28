let tasks = [];
let nextId = 1;

function createTask(title) {
  const task = { id: nextId++, title, completed: false };
  tasks.push(task);
  return task;
}

function getTasks() {
  return tasks;
}

function getTask(id) {
  return tasks.find((t) => t.id === id);
}

function updateTask(id, updates) {
  const task = getTask(id);
  if (!task) return null;
  Object.assign(task, updates);
  return task;
}

function deleteTask(id) {
  const index = tasks.findIndex((t) => t.id === id);
  if (index === -1) return false;
  tasks.splice(index, 1);
  return true;
}

function reset() {
  tasks = [];
  nextId = 1;
}

module.exports = { createTask, getTasks, getTask, updateTask, deleteTask, reset };
