let tasks = [];
let nextId = 1;

// Default timezone for due-date timestamps.
const IST_OFFSET = '+05:30';

// Normalize an incoming due date to a canonical ISO-8601 timestamp in IST.
// - null/undefined stays null.
// - A date-only value (YYYY-MM-DD) defaults to start of day (00:00) in IST.
// - A datetime without an offset is interpreted as IST.
// - A datetime with an offset is converted to the equivalent IST wall-clock.
function normalizeDueDate(value) {
  if (value === null || value === undefined) return null;
  const s = String(value).trim();

  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    return `${s}T00:00:00${IST_OFFSET}`;
  }

  const m = /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(s);
  if (m) {
    const [, date, hh, mm, ss] = m;
    return `${date}T${hh}:${mm}:${ss || '00'}${IST_OFFSET}`;
  }

  // Value carries an offset (or Z): convert to the equivalent IST wall-clock.
  const d = new Date(s);
  const ist = new Date(d.getTime() + (5 * 60 + 30) * 60000);
  const pad = (n) => String(n).padStart(2, '0');
  return (
    `${ist.getUTCFullYear()}-${pad(ist.getUTCMonth() + 1)}-${pad(ist.getUTCDate())}` +
    `T${pad(ist.getUTCHours())}:${pad(ist.getUTCMinutes())}:${pad(ist.getUTCSeconds())}${IST_OFFSET}`
  );
}

function createTask(title, dueDate = null) {
  const task = { id: nextId++, title, completed: false, due_date: normalizeDueDate(dueDate) };
  tasks.push(task);
  return task;
}

function getTasks() {
  // Ascending by due_date timestamp (earliest first); null due dates last,
  // preserving insertion order within the null group. Array.sort is stable.
  return [...tasks].sort((a, b) => {
    const aNull = a.due_date === null || a.due_date === undefined;
    const bNull = b.due_date === null || b.due_date === undefined;
    if (aNull && bNull) return 0;
    if (aNull) return 1;
    if (bNull) return -1;
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
  });
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

function setDueDate(id, dueDate) {
  const task = getTask(id);
  if (!task) return null;
  task.due_date = normalizeDueDate(dueDate);
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

module.exports = { createTask, getTasks, getTask, updateTask, setDueDate, deleteTask, reset };
