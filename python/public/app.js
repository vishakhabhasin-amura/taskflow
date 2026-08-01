const form = document.getElementById('task-form');
const input = document.getElementById('title-input');
const dueDateInput = document.getElementById('due-date-input');
const formError = document.getElementById('form-error');
const list = document.getElementById('task-list');

const SORT_BY_DUE_DATE = 'dueDate';
const OVERDUE_LABEL = 'Overdue';
const GENERIC_ERROR = 'Could not add the task. Please try again.';

/**
 * Purpose:
 * Turns a stored UTC due date into the calendar date the viewer is actually in.
 * Input: ISO 8601 string
 * Output: Localized date string, or an empty string when the value is unusable
 */
function formatDueDate(isoValue) {
  const parsed = new Date(isoValue);
  if (Number.isNaN(parsed.getTime())) return '';
  return parsed.toLocaleDateString();
}

/**
 * Purpose:
 * Shows or clears the form-level error region.
 * Input: Message string, or null to clear
 * Output: None
 */
function setFormError(message) {
  formError.textContent = message || '';
  formError.hidden = !message;
}

async function fetchTasks() {
  const query = new URLSearchParams({ sort: SORT_BY_DUE_DATE });
  const res = await fetch(`/tasks?${query}`);
  const tasks = await res.json();
  renderTasks(tasks);
}

function renderTasks(tasks) {
  list.innerHTML = '';
  for (const task of tasks) {
    const li = document.createElement('li');
    li.className = [task.completed ? 'completed' : '', task.overdue ? 'overdue' : '']
      .filter(Boolean)
      .join(' ');

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = task.completed;
    checkbox.addEventListener('change', () => toggleTask(task.id, checkbox.checked));

    const span = document.createElement('span');
    span.textContent = task.title;

    li.append(checkbox, span);

    if (task.dueDate) {
      const due = document.createElement('time');
      due.className = 'due-date';
      due.dateTime = task.dueDate;
      due.textContent = formatDueDate(task.dueDate);
      li.append(due);
    }

    if (task.overdue) {
      const badge = document.createElement('span');
      badge.className = 'overdue-badge';
      badge.textContent = OVERDUE_LABEL;
      li.append(badge);
    }

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', () => deleteTask(task.id));

    li.append(deleteBtn);
    list.appendChild(li);
  }
}

async function toggleTask(id, completed) {
  await fetch(`/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ completed }),
  });
  fetchTasks();
}

async function deleteTask(id) {
  await fetch(`/tasks/${id}`, { method: 'DELETE' });
  fetchTasks();
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const title = input.value.trim();
  if (!title) return;

  const payload = { title };
  if (dueDateInput.value) payload.dueDate = dueDateInput.value;

  setFormError(null);
  const res = await fetch('/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    setFormError(body.error || GENERIC_ERROR);
    return;
  }

  input.value = '';
  dueDateInput.value = '';
  fetchTasks();
});

fetchTasks();
