const form = document.getElementById('task-form');
const input = document.getElementById('title-input');
const list = document.getElementById('task-list');

async function fetchTasks() {
  const res = await fetch('/tasks');
  const tasks = await res.json();
  renderTasks(tasks);
}

function renderTasks(tasks) {
  list.innerHTML = '';
  for (const task of tasks) {
    const li = document.createElement('li');
    li.className = task.completed ? 'completed' : '';

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = task.completed;
    checkbox.addEventListener('change', () => toggleTask(task.id, checkbox.checked));

    const span = document.createElement('span');
    span.textContent = task.title;

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', () => deleteTask(task.id));

    li.append(checkbox, span, deleteBtn);
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
  await fetch('/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  input.value = '';
  fetchTasks();
});

fetchTasks();
