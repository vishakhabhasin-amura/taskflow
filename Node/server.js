const express = require('express');
const path = require('path');
const tasksRouter = require('./routes/tasks');

const app = express();
app.use(express.json());
app.use('/tasks', tasksRouter);
app.use(express.static(path.join(__dirname, 'public')));

const PORT = process.env.PORT || 3000;

if (require.main === module) {
  app.listen(PORT, () => console.log(`TaskFlow listening on port ${PORT}`));
}

module.exports = app;
