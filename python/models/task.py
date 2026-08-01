from datetime import date

_tasks = []
_next_id = 1


def create_task(title, due_date=None):
    global _next_id
    task = {"id": _next_id, "title": title, "completed": False, "dueDate": due_date}
    _next_id += 1
    _tasks.append(task)
    return task


def get_tasks():
    return _tasks


def is_overdue(task):
    if not task["dueDate"] or task["completed"]:
        return False
    return task["dueDate"] < date.today().isoformat()


def sorted_by_due_date(tasks):
    return sorted(tasks, key=lambda t: (not t["dueDate"], t["dueDate"] or ""))


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
