from datetime import datetime, timedelta, timezone

# Default timezone for due-date timestamps.
IST = timezone(timedelta(hours=5, minutes=30))

_tasks = []
_next_id = 1


def _normalize_due_date(value):
    """Normalize an incoming due date to a canonical ISO-8601 timestamp in IST.

    - None stays None.
    - A date-only value (YYYY-MM-DD) defaults to start of day (00:00) in IST.
    - A datetime without an offset is interpreted as IST.
    - A datetime with an offset is converted to the equivalent IST wall-clock.
    """
    if value is None:
        return None
    s = value.strip()
    if len(s) == 10:  # YYYY-MM-DD -> start of day, IST
        dt = datetime.fromisoformat(s).replace(tzinfo=IST)
    else:
        dt = datetime.fromisoformat(s)
        dt = dt.replace(tzinfo=IST) if dt.tzinfo is None else dt.astimezone(IST)
    return dt.isoformat()


def create_task(title, due_date=None):
    global _next_id
    task = {
        "id": _next_id,
        "title": title,
        "completed": False,
        "due_date": _normalize_due_date(due_date),
    }
    _next_id += 1
    _tasks.append(task)
    return task


def get_tasks():
    # Ascending by due_date timestamp (earliest first); null due dates last,
    # preserving insertion order within the null group. sorted() is stable.
    def key(t):
        if t["due_date"] is None:
            return (1, 0.0)
        return (0, datetime.fromisoformat(t["due_date"]).timestamp())

    return sorted(_tasks, key=key)


def get_task(task_id):
    return next((t for t in _tasks if t["id"] == task_id), None)


def update_task(task_id, completed):
    task = get_task(task_id)
    if task is None:
        return None
    task["completed"] = completed
    return task


def set_due_date(task_id, due_date):
    task = get_task(task_id)
    if task is None:
        return None
    task["due_date"] = _normalize_due_date(due_date)
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
