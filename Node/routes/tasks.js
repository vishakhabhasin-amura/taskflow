const express = require('express');
const {
  createTask,
  getTasks,
  getTask,
  updateTask,
  setDueDate,
  deleteTask,
} = require('../models/task');

const router = express.Router();

router.get('/', (req, res) => {
  res.json(getTasks());
});

router.post('/', (req, res) => {
  const { title, due_date } = req.body;
  if (!title) {
    return res.status(400).json({ error: 'title is required' });
  }
  // due_date is optional; absent -> null. Stored value is normalized to IST.
  const task = createTask(title, due_date ?? null);
  res.status(201).json(task);
});

router.patch('/:id', (req, res) => {
  const id = Number(req.params.id);
  const task = getTask(id);
  if (!task) {
    return res.status(404).json({ error: 'task not found' });
  }

  if ('due_date' in req.body) {
    // Immutable once set: reject any attempt to supply due_date when one exists.
    if (task.due_date !== null && task.due_date !== undefined) {
      return res.status(400).json({ error: 'due_date cannot be changed once set' });
    }
    setDueDate(id, req.body.due_date);
  }
  if ('completed' in req.body) {
    updateTask(id, { completed: req.body.completed });
  }

  res.json(getTask(id));
});

router.delete('/:id', (req, res) => {
  const id = Number(req.params.id);
  const deleted = deleteTask(id);
  if (!deleted) {
    return res.status(404).json({ error: 'task not found' });
  }
  res.status(204).send();
});

module.exports = router;
