_tasks = []
_next_id = 1


def create_task(title):
    global _next_id
    task = {"id": _next_id, "title": title, "completed": False}
    _next_id += 1
    _tasks.append(task)
    return task


def get_tasks():
    return _tasks


def get_task(task_id):
    return next((t for t in _tasks if t["id"] == task_id), None)


def update_task(task_id, completed):
    task = get_task(task_id)
    if task is None:
        return None
    task["completed"] = completed
    return task


def delete_task(task_id):
    task = get_task(task_id)
    if task is None:
        return False
    _tasks.remove(task)
    return True


def reset():
    global _next_id
    _tasks.clear()
    _next_id = 1
