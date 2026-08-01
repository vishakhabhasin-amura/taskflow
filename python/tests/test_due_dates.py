"""
QA Test Suite — Due Date Feature (Python backend only)
Covers: AC-1, AC-2, AC-3, AC-4, AC-6
Out of scope: AC-5 (colour indicators — frontend concern), timezones, notifications
Spec ref: taskflow/SPEC-due-dates.md
"""

import pytest
from datetime import date, timedelta

from app import app
from models.task import reset

# ---------------------------------------------------------------------------
# Date constants relative to today so tests remain valid on any run date.
# Assumption A1: overdue = strictly before today; today itself is NOT overdue.
# ---------------------------------------------------------------------------
TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
LAST_WEEK = (date.today() - timedelta(days=7)).isoformat()
NEXT_WEEK = (date.today() + timedelta(days=7)).isoformat()


@pytest.fixture(autouse=True)
def _reset_store():
    reset()


@pytest.fixture
def client():
    return app.test_client()


# ===========================================================================
# AC-1: Setting a due date on creation
# ===========================================================================

def test_create_task_with_due_date_returns_201_and_stored_date(client):
    """Spec Scenario 1 — POST with due_date stores the date and returns 201."""
    res = client.post("/tasks", json={"title": "Submit report", "due_date": TOMORROW})
    assert res.status_code == 201
    assert res.json["due_date"] == TOMORROW


def test_create_task_without_due_date_field_defaults_to_null(client):
    """Spec Scenario 2 step 1 — POST with no due_date key is valid; due_date is null."""
    res = client.post("/tasks", json={"title": "Buy groceries"})
    assert res.status_code == 201
    assert res.json["due_date"] is None


def test_create_task_with_explicit_null_due_date_is_valid(client):
    """Explicitly passing due_date: null on creation is treated the same as omitting it."""
    res = client.post("/tasks", json={"title": "Read book", "due_date": None})
    assert res.status_code == 201
    assert res.json["due_date"] is None


def test_create_task_with_due_date_preserves_title_and_completed_defaults(client):
    """AC-1 + AC-6 — Response includes all four fields with correct defaults."""
    res = client.post("/tasks", json={"title": "Code review", "due_date": NEXT_WEEK})
    body = res.json
    assert body["title"] == "Code review"
    assert body["completed"] is False
    assert body["due_date"] == NEXT_WEEK
    assert "id" in body


# ===========================================================================
# AC-2: Adding a due date to an existing task that has none
# ===========================================================================

def test_patch_adds_due_date_to_undated_task(client):
    """Spec Scenario 2 step 2 — PATCH due_date on a null-dated task succeeds."""
    created = client.post("/tasks", json={"title": "Buy groceries"})
    task_id = created.json["id"]

    res = client.patch(f"/tasks/{task_id}", json={"due_date": YESTERDAY})
    assert res.status_code == 200
    assert res.json["due_date"] == YESTERDAY


def test_patch_due_date_response_contains_all_task_fields(client):
    """AC-2 response must include id, title, completed, and due_date."""
    created = client.post("/tasks", json={"title": "Team sync"})
    task_id = created.json["id"]

    res = client.patch(f"/tasks/{task_id}", json={"due_date": TOMORROW})
    body = res.json
    assert "id" in body
    assert body["title"] == "Team sync"
    assert body["completed"] is False
    assert body["due_date"] == TOMORROW


def test_patch_due_date_is_reflected_in_subsequent_get(client):
    """AC-2 — After PATCH, GET /tasks returns the updated due_date."""
    created = client.post("/tasks", json={"title": "Prepare slides"})
    task_id = created.json["id"]
    client.patch(f"/tasks/{task_id}", json={"due_date": NEXT_WEEK})

    tasks = client.get("/tasks").json
    match = next(t for t in tasks if t["id"] == task_id)
    assert match["due_date"] == NEXT_WEEK


# ===========================================================================
# AC-3: Due date is immutable once set
# ===========================================================================

def test_patch_due_date_rejected_when_already_set(client):
    """Spec Scenario 3 — PATCH with a new due_date on a task that already has one returns 400."""
    created = client.post("/tasks", json={"title": "Submit report", "due_date": TOMORROW})
    task_id = created.json["id"]

    res = client.patch(f"/tasks/{task_id}", json={"due_date": NEXT_WEEK})
    assert res.status_code == 400


def test_patch_due_date_rejected_returns_correct_error_body(client):
    """AC-3 — 400 response body must match: { 'error': 'due_date cannot be changed once set' }."""
    created = client.post("/tasks", json={"title": "Submit report", "due_date": TOMORROW})
    task_id = created.json["id"]

    res = client.patch(f"/tasks/{task_id}", json={"due_date": NEXT_WEEK})
    assert res.json == {"error": "due_date cannot be changed once set"}


def test_patch_due_date_rejected_even_when_same_value(client):
    """AC-3 — Re-sending the same due_date value is still a change attempt and must be rejected."""
    created = client.post("/tasks", json={"title": "Dentist", "due_date": TOMORROW})
    task_id = created.json["id"]

    res = client.patch(f"/tasks/{task_id}", json={"due_date": TOMORROW})
    assert res.status_code == 400


def test_patch_completed_does_not_modify_due_date(client):
    """Spec Scenario 5 — Toggling completed leaves due_date untouched."""
    created = client.post("/tasks", json={"title": "File taxes", "due_date": NEXT_WEEK})
    task_id = created.json["id"]

    res = client.patch(f"/tasks/{task_id}", json={"completed": True})
    assert res.status_code == 200
    assert res.json["completed"] is True
    assert res.json["due_date"] == NEXT_WEEK


def test_patch_due_date_still_rejected_after_task_is_completed(client):
    """Spec Scenario 5 — Immutability persists even after a task is marked completed."""
    created = client.post("/tasks", json={"title": "File taxes", "due_date": NEXT_WEEK})
    task_id = created.json["id"]

    client.patch(f"/tasks/{task_id}", json={"completed": True})

    res = client.patch(f"/tasks/{task_id}", json={"due_date": LAST_WEEK})
    assert res.status_code == 400
    assert res.json == {"error": "due_date cannot be changed once set"}


# ===========================================================================
# AC-4: Sort order — GET /tasks returns tasks sorted by due_date ascending,
#        null due_date tasks always last, insertion order preserved within nulls.
# ===========================================================================

def test_get_tasks_sorted_by_due_date_ascending(client):
    """Spec Scenario 4 — Tasks are ordered earliest due_date first."""
    client.post("/tasks", json={"title": "Task D", "due_date": NEXT_WEEK})
    client.post("/tasks", json={"title": "Task B", "due_date": LAST_WEEK})
    client.post("/tasks", json={"title": "Task C", "due_date": TOMORROW})

    tasks = client.get("/tasks").json
    dated = [t for t in tasks if t["due_date"] is not None]
    dates = [t["due_date"] for t in dated]
    assert dates == sorted(dates), f"Expected ascending order, got: {dates}"


def test_get_tasks_null_due_dates_sorted_after_all_dated_tasks(client):
    """AC-4 — Tasks with no due date appear after all tasks that have a due date."""
    client.post("/tasks", json={"title": "Undated task"})
    client.post("/tasks", json={"title": "Future task", "due_date": NEXT_WEEK})
    client.post("/tasks", json={"title": "Past task", "due_date": LAST_WEEK})

    tasks = client.get("/tasks").json
    null_indices = [i for i, t in enumerate(tasks) if t["due_date"] is None]
    dated_indices = [i for i, t in enumerate(tasks) if t["due_date"] is not None]

    if null_indices and dated_indices:
        assert min(null_indices) > max(dated_indices), (
            "All undated tasks must appear after all dated tasks"
        )


def test_get_tasks_null_group_preserves_insertion_order(client):
    """AC-4 — Within the undated group, tasks appear in the order they were created."""
    client.post("/tasks", json={"title": "First undated"})
    client.post("/tasks", json={"title": "Second undated"})
    client.post("/tasks", json={"title": "Third undated"})

    tasks = client.get("/tasks").json
    titles = [t["title"] for t in tasks]
    assert titles == ["First undated", "Second undated", "Third undated"]


def test_get_tasks_overdue_task_appears_before_future_task(client):
    """AC-4 — An overdue task (past date) sorts before an upcoming task (future date)."""
    client.post("/tasks", json={"title": "Future", "due_date": NEXT_WEEK})
    client.post("/tasks", json={"title": "Overdue", "due_date": LAST_WEEK})

    tasks = client.get("/tasks").json
    titles = [t["title"] for t in tasks]
    assert titles.index("Overdue") < titles.index("Future")


def test_get_tasks_due_today_sorts_before_future_and_after_overdue(client):
    """AC-4 + Assumption A1 — Today's task sits between overdue and future tasks in sort."""
    client.post("/tasks", json={"title": "Future", "due_date": NEXT_WEEK})
    client.post("/tasks", json={"title": "Today", "due_date": TODAY})
    client.post("/tasks", json={"title": "Overdue", "due_date": LAST_WEEK})

    tasks = client.get("/tasks").json
    titles = [t["title"] for t in tasks]
    assert titles.index("Overdue") < titles.index("Today") < titles.index("Future")


def test_get_tasks_mixed_dated_and_undated_full_sort_order(client):
    """Spec Scenario 4 full — Overdue → Today → Future → Undated."""
    client.post("/tasks", json={"title": "Task A"})                          # null
    client.post("/tasks", json={"title": "Task B", "due_date": LAST_WEEK})  # overdue
    client.post("/tasks", json={"title": "Task C", "due_date": TODAY})      # due today
    client.post("/tasks", json={"title": "Task D", "due_date": NEXT_WEEK})  # upcoming

    tasks = client.get("/tasks").json
    titles = [t["title"] for t in tasks]
    assert titles == ["Task B", "Task C", "Task D", "Task A"]


# ===========================================================================
# AC-6: Data model — due_date field is present in all API responses
# ===========================================================================

def test_create_task_response_always_includes_due_date_field(client):
    """AC-6 — POST response includes due_date even when not provided."""
    res = client.post("/tasks", json={"title": "Quick task"})
    assert "due_date" in res.json


def test_get_all_tasks_response_includes_due_date_on_every_task(client):
    """AC-6 — Every task in GET /tasks response has a due_date field."""
    client.post("/tasks", json={"title": "With date", "due_date": TOMORROW})
    client.post("/tasks", json={"title": "Without date"})

    tasks = client.get("/tasks").json
    for task in tasks:
        assert "due_date" in task, f"Task missing due_date field: {task}"


def test_patch_response_includes_due_date_field(client):
    """AC-6 — PATCH response includes due_date field regardless of what was patched."""
    created = client.post("/tasks", json={"title": "Track this"})
    task_id = created.json["id"]

    res = client.patch(f"/tasks/{task_id}", json={"completed": True})
    assert "due_date" in res.json
