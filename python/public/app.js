const form = document.getElementById('task-form');
const input = document.getElementById('title-input');
const dueDateInput = document.getElementById('due-date-input');
const list = document.getElementById('task-list');

// Current local time as a datetime-local value (YYYY-MM-DDTHH:MM), used to
// prevent selecting a past due date.
function nowLocalDatetime() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// Render a stored ISO timestamp (e.g. 2026-08-10T15:30:00+05:30) as its
// wall-clock date and time, dropping the seconds/offset for display.
function formatDue(iso) {
  return iso.slice(0, 16).replace('T', ' ');
}

function isPast(value) {
  return new Date(value).getTime() < Date.now();
}

async function fetchTasks() {
  const res = await fetch('/tasks');
  const tasks = await res.json();
  renderTasks(tasks);
}

function renderTasks(tasks) {
  list.innerHTML = '';
  const now = Date.now();
  for (const task of tasks) {
    const li = document.createElement('li');
    const classes = [];
    if (task.completed) classes.push('completed');
    // Overdue = due timestamp strictly before now.
    if (task.due_date && new Date(task.due_date).getTime() < now) classes.push('overdue');
    li.className = classes.join(' ');

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = task.completed;
    checkbox.addEventListener('change', () => toggleTask(task.id, checkbox.checked));

    const span = document.createElement('span');
    span.className = 'title';
    span.textContent = task.title;

    li.append(checkbox, span);

    if (task.due_date) {
      // Set: rendered read-only, no edit control.
      const due = document.createElement('span');
      due.className = 'due-date';
      due.textContent = formatDue(task.due_date);
      li.append(due);
    } else {
      // Unset: offer a one-time "Add due date" control that cannot pick the past.
      const addInput = document.createElement('input');
      addInput.type = 'datetime-local';
      addInput.className = 'add-due-date-input';
      addInput.min = nowLocalDatetime();

      const addBtn = document.createElement('button');
      addBtn.textContent = 'Add due date';
      addBtn.addEventListener('click', () => {
        if (!addInput.value) return;
        if (isPast(addInput.value)) {
          alert('Due date cannot be in the past.');
          return;
        }
        addDueDate(task.id, addInput.value);
      });

      li.append(addInput, addBtn);
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

async function addDueDate(id, dueDate) {
  await fetch(`/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ due_date: dueDate }),
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
  const body = { title };
  if (dueDateInput.value) {
    if (isPast(dueDateInput.value)) {
      alert('Due date cannot be in the past.');
      return;
    }
    body.due_date = dueDateInput.value;
  }
  await fetch('/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  input.value = '';
  dueDateInput.value = '';
  fetchTasks();
});

// Block past selection in the picker (min updates as the page loads).
dueDateInput.min = nowLocalDatetime();

fetchTasks();
