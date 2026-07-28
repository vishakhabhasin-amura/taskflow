const request = require('supertest');
const app = require('../server');
const { reset } = require('../models/task');

beforeEach(() => {
  reset();
});

test('test_add_task: POST /tasks creates a task with the given title', async () => {
  const res = await request(app).post('/tasks').send({ title: 'Buy milk' });
  expect(res.status).toBe(201);
  expect(res.body.title).toBe('Buy milk');
  expect(res.body.completed).toBe(false);
});

test('test_mark_complete: PATCH /tasks/:id correctly toggles completed', async () => {
  const created = await request(app).post('/tasks').send({ title: 'Walk dog' });
  const res = await request(app).patch(`/tasks/${created.body.id}`).send({ completed: true });
  expect(res.status).toBe(200);
  expect(res.body.completed).toBe(true);
});
