const express = require('express');
const { createTask, getTasks, updateTask, deleteTask } = require('../models/task');

const router = express.Router();

router.get('/', (req, res) => {
  res.json(getTasks());
});

router.post('/', (req, res) => {
  const { title } = req.body;
  if (!title) {
    return res.status(400).json({ error: 'title is required' });
  }
  const task = createTask(title);
  res.status(201).json(task);
});

router.patch('/:id', (req, res) => {
  const id = Number(req.params.id);
  const task = updateTask(id, { completed: req.body.completed });
  if (!task) {
    return res.status(404).json({ error: 'task not found' });
  }
  res.json(task);
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
