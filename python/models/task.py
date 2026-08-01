from datetime import date, datetime, time, timezone

DUE_DATE_KEY = "dueDate"
OVERDUE_KEY = "overdue"
SORT_BY_DUE_DATE = "dueDate"
SORT_OPTIONS = (SORT_BY_DUE_DATE,)

_UTC_DESIGNATOR = "Z"
_UTC_OFFSET = "+00:00"
_DATE_ONLY_LENGTH = 10  # "YYYY-MM-DD" — a value of any other length carries a time
_END_OF_DAY = time.max
_UNDATED_PLACEHOLDER = datetime.min.replace(tzinfo=timezone.utc)

_tasks = []
_next_id = 1


def _now_utc():
    """
    Purpose:
    Supplies the current instant used for every overdue comparison.

    Input:
    None

    Output:
    Timezone-aware datetime in UTC
    """
    return datetime.now(timezone.utc)


def _with_utc_offset(value):
    """
    Purpose:
    Rewrites a trailing UTC designator into the numeric offset this interpreter accepts.

    Input:
    ISO 8601 string

    Output:
    Equivalent ISO 8601 string that `datetime.fromisoformat` can parse
    """
    if value.endswith(_UTC_DESIGNATOR):
        return value[: -len(_UTC_DESIGNATOR)] + _UTC_OFFSET
    return value


def parse_due_date(value):
    """
    Purpose:
    Normalizes a client-supplied due date into the single representation the store holds.
    A date without a time means the end of that day in server-local time.

    Input:
    None, or an ISO 8601 date or datetime string

    Output:
    Canonical UTC ISO 8601 string, or None when no due date was supplied.
    Raises ValueError for any value that is not a usable ISO 8601 date or datetime
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("due date must be a string")
    try:
        if len(value) == _DATE_ONLY_LENGTH:
            moment = datetime.combine(date.fromisoformat(value), _END_OF_DAY)
        else:
            moment = datetime.fromisoformat(_with_utc_offset(value))
        if moment.tzinfo is None:
            moment = moment.astimezone()
        return moment.astimezone(timezone.utc).isoformat()
    except (TypeError, OverflowError) as exc:
        raise ValueError("due date is out of the supported range") from exc


def _parse_stored_due_date(value):
    """
    Purpose:
    Turns a stored due date back into an instant for comparison and ordering.

    Input:
    Stored due date string, or None

    Output:
    Timezone-aware datetime, or None when there is no usable due date
    """
    if value is None:
        return None
    try:
        moment = datetime.fromisoformat(_with_utc_offset(value))
    except (ValueError, TypeError):
        # Normalization on write makes this unreachable; a bad stored value must not
        # fail the whole read.
        return None
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment


def _is_overdue(task, due, now):
    """
    Purpose:
    Decides whether a task is late: it has a due date, that date is strictly past,
    and the task is not completed.

    Input:
    Stored task dict, its parsed due date or None, current instant in UTC

    Output:
    Boolean
    """
    if task["completed"] or due is None:
        return False
    return due < now


def _due_date_sort_key(entry):
    """
    Purpose:
    Orders tasks by due date ascending, tasks without one last, ties broken by id.

    Input:
    Tuple of parsed due date, task id, and task view

    Output:
    Tuple usable as a `sorted` key
    """
    due, task_id, _ = entry
    return (due is None, due or _UNDATED_PLACEHOLDER, task_id)


def _view(task, due, now):
    """
    Purpose:
    Copies a stored task and attaches the derived overdue flag, leaving the store untouched.

    Input:
    Stored task dict, its parsed due date or None, current instant in UTC

    Output:
    New dict with every stored field plus `overdue`
    """
    view = dict(task)
    view[OVERDUE_KEY] = _is_overdue(task, due, now)
    return view


def task_view(task):
    """
    Purpose:
    Builds the API representation of one task.

    Input:
    Stored task dict

    Output:
    New dict with every stored field plus `overdue`
    """
    due = _parse_stored_due_date(task.get(DUE_DATE_KEY))
    return _view(task, due, _now_utc())


def task_list_view(sort=None):
    """
    Purpose:
    Builds the API representation of the whole list, optionally ordered by due date,
    without ever reordering or mutating the stored list.

    Input:
    Sort key, or None for insertion order

    Output:
    New list of task view dicts
    """
    now = _now_utc()
    entries = []
    for task in _tasks:
        due = _parse_stored_due_date(task.get(DUE_DATE_KEY))
        entries.append((due, task["id"], _view(task, due, now)))
    if sort == SORT_BY_DUE_DATE:
        entries = sorted(entries, key=_due_date_sort_key)
    return [view for _, _, view in entries]


def create_task(title, due_date=None):
    """
    Purpose:
    Appends a new task to the store.

    Input:
    Title string, optional already-normalized due date string

    Output:
    The stored task dict
    """
    global _next_id
    task = {
        "id": _next_id,
        "title": title,
        "completed": False,
        DUE_DATE_KEY: due_date,
    }
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
