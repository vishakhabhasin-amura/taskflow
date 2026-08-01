from datetime import date, datetime, time, timedelta, timezone

import pytest

from app import app
from models import task as store
from models.task import reset


@pytest.fixture(autouse=True)
def _reset_store():
    reset()


@pytest.fixture
def client():
    return app.test_client()


def test_add_task_creates_task_with_given_title(client):
    res = client.post("/tasks", json={"title": "Buy milk"})
    assert res.status_code == 201
    assert res.json["title"] == "Buy milk"
    assert res.json["completed"] is False


def test_mark_complete_toggles_completed(client):
    created = client.post("/tasks", json={"title": "Walk dog"})
    task_id = created.json["id"]

    res = client.patch(f"/tasks/{task_id}", json={"completed": True})
    assert res.status_code == 200
    assert res.json["completed"] is True


TASK_KEYS = {"id", "title", "completed", "dueDate", "overdue"}
STORED_KEYS = {"id", "title", "completed", "dueDate"}
INVALID_DUE_DATE_ERROR = "dueDate must be a valid ISO 8601 datetime"
INVALID_SORT_ERROR = "sort must be one of: dueDate"

INVALID_DUE_DATES = [
    ("A3-empty-string", ""),
    ("A4-whitespace-only", "   "),
    ("A5-not-a-date", "not-a-date"),
    ("A6-impossible-month-and-day", "2026-13-45T00:00:00Z"),
    ("A7-impossible-day", "2026-02-30T00:00:00Z"),
    ("A8-epoch-number", 1754067600),
    ("A9-boolean", True),
    ("A9-object", {}),
    ("A9-array", []),
    ("A13-whitespace-padded", " 2026-08-05T17:00:00Z "),
    ("A17-very-long-string", "2026-08-05T17:00:00" + "0" * 10000),
    ("B6-year-out-of-range", "10000-01-01T00:00:00Z"),
    ("B11-leap-day-in-a-non-leap-year", "2027-02-29"),
]
INVALID_DUE_DATE_IDS = [case_id for case_id, _ in INVALID_DUE_DATES]
INVALID_DUE_DATE_VALUES = [value for _, value in INVALID_DUE_DATES]


def _local_date(offset_days=0):
    """
    Purpose:
    Gives a calendar date relative to today in the machine's own timezone, so the
    tests assert the same rule the server applies rather than a fixed zone.

    Input:
    Day offset, negative for the past

    Output:
    date
    """
    return datetime.now().astimezone().date() + timedelta(days=offset_days)


def _end_of_local_day_utc(day):
    """
    Purpose:
    Reproduces the stored form of a date-only due date: the end of that local day in UTC.

    Input:
    date

    Output:
    Canonical UTC ISO 8601 string
    """
    return datetime.combine(day, time.max).astimezone().astimezone(timezone.utc).isoformat()


def _freeze_clock(monkeypatch, moment):
    """
    Purpose:
    Pins the instant every overdue comparison is made against.

    Input:
    pytest monkeypatch fixture, timezone-aware datetime

    Output:
    None
    """
    monkeypatch.setattr(store, "_now_utc", lambda: moment)


def test_create_records_a_supplied_due_date_normalized_to_utc(client):
    res = client.post("/tasks", json={"title": "Ship", "dueDate": "2026-08-05T17:00:00+05:30"})
    assert res.status_code == 201
    assert res.json["dueDate"] == "2026-08-05T11:30:00+00:00"


def test_create_without_a_due_date_succeeds_with_an_explicit_null(client):
    res = client.post("/tasks", json={"title": "Ship"})
    assert res.status_code == 201
    assert res.json["dueDate"] is None
    assert res.json["overdue"] is False


def test_an_explicit_null_due_date_is_treated_as_absent(client):
    res = client.post("/tasks", json={"title": "Ship", "dueDate": None})
    assert res.status_code == 201
    assert res.json["dueDate"] is None
    assert res.json["overdue"] is False


def test_a_trailing_z_designator_is_accepted(client):
    res = client.post("/tasks", json={"title": "Ship", "dueDate": "2026-08-05T17:00:00Z"})
    assert res.status_code == 201
    assert res.json["dueDate"] == "2026-08-05T17:00:00+00:00"


def test_a_date_only_due_date_is_stored_as_the_end_of_that_local_day(client):
    day = date(2026, 8, 5)
    res = client.post("/tasks", json={"title": "Ship", "dueDate": day.isoformat()})
    assert res.status_code == 201
    assert res.json["dueDate"] == _end_of_local_day_utc(day)


def test_a_leap_day_is_accepted(client):
    day = date(2028, 2, 29)
    res = client.post("/tasks", json={"title": "Leap", "dueDate": day.isoformat()})
    assert res.status_code == 201
    assert res.json["dueDate"] == _end_of_local_day_utc(day)


@pytest.mark.parametrize("value", INVALID_DUE_DATE_VALUES, ids=INVALID_DUE_DATE_IDS)
def test_an_invalid_due_date_is_rejected_without_touching_the_store(client, value):
    res = client.post("/tasks", json={"title": "Ship", "dueDate": value})
    assert res.status_code == 400
    assert res.json["error"] == INVALID_DUE_DATE_ERROR
    assert store._tasks == []
    assert store._next_id == 1


def test_a_missing_title_takes_precedence_over_an_invalid_due_date(client):
    res = client.post("/tasks", json={"dueDate": "not-a-date"})
    assert res.status_code == 400
    assert res.json["error"] == "title is required"


def test_an_absent_body_still_reports_the_missing_title(client):
    res = client.post("/tasks")
    assert res.status_code == 400
    assert res.json["error"] == "title is required"


def test_a_malformed_json_body_still_reports_the_missing_title(client):
    res = client.post("/tasks", data="{not json", content_type="application/json")
    assert res.status_code == 400
    assert res.json["error"] == "title is required"


def test_unknown_body_keys_are_ignored(client):
    res = client.post("/tasks", json={"title": "Ship", "colour": "red", "id": 99})
    assert res.status_code == 201
    assert res.json["id"] == 1
    assert set(res.json) == TASK_KEYS


def test_a_rejected_due_date_is_not_echoed_back(client):
    payload = "<script>alert(1)</script>"
    res = client.post("/tasks", json={"title": "Ship", "dueDate": payload})
    assert res.status_code == 400
    assert payload not in res.get_data(as_text=True)


def test_a_due_date_equal_to_now_is_not_overdue(client, monkeypatch):
    moment = datetime(2026, 8, 5, 17, 0, tzinfo=timezone.utc)
    client.post("/tasks", json={"title": "Ship", "dueDate": moment.isoformat()})
    _freeze_clock(monkeypatch, moment)
    assert client.get("/tasks").json[0]["overdue"] is False


def test_a_due_date_one_second_in_the_past_is_overdue(client, monkeypatch):
    moment = datetime(2026, 8, 5, 17, 0, tzinfo=timezone.utc)
    client.post("/tasks", json={"title": "Ship", "dueDate": moment.isoformat()})
    _freeze_clock(monkeypatch, moment + timedelta(seconds=1))
    assert client.get("/tasks").json[0]["overdue"] is True


def test_a_due_date_one_second_in_the_future_is_not_overdue(client, monkeypatch):
    moment = datetime(2026, 8, 5, 17, 0, tzinfo=timezone.utc)
    client.post("/tasks", json={"title": "Ship", "dueDate": moment.isoformat()})
    _freeze_clock(monkeypatch, moment - timedelta(seconds=1))
    assert client.get("/tasks").json[0]["overdue"] is False


def test_the_clock_crossing_a_due_date_flips_overdue_without_a_write(client, monkeypatch):
    moment = datetime(2026, 8, 5, 17, 0, tzinfo=timezone.utc)
    client.post("/tasks", json={"title": "Ship", "dueDate": moment.isoformat()})
    stored_before = dict(store._tasks[0])

    _freeze_clock(monkeypatch, moment - timedelta(seconds=1))
    assert client.get("/tasks").json[0]["overdue"] is False

    _freeze_clock(monkeypatch, moment + timedelta(seconds=1))
    assert client.get("/tasks").json[0]["overdue"] is True

    assert dict(store._tasks[0]) == stored_before


def test_a_far_past_due_date_is_overdue(client):
    res = client.post("/tasks", json={"title": "Ancient", "dueDate": "1900-01-01T00:00:00Z"})
    assert res.status_code == 201
    assert res.json["overdue"] is True


def test_a_far_future_due_date_is_not_overdue(client):
    res = client.post("/tasks", json={"title": "Distant", "dueDate": "9999-12-31T00:00:00Z"})
    assert res.status_code == 201
    assert res.json["overdue"] is False


def test_a_task_due_today_is_not_overdue(client):
    res = client.post("/tasks", json={"title": "Today", "dueDate": _local_date().isoformat()})
    assert res.status_code == 201
    assert res.json["overdue"] is False


def test_a_task_due_yesterday_is_overdue(client):
    res = client.post("/tasks", json={"title": "Yesterday", "dueDate": _local_date(-1).isoformat()})
    assert res.status_code == 201
    assert res.json["overdue"] is True


def test_a_task_due_tomorrow_is_not_overdue(client):
    res = client.post("/tasks", json={"title": "Tomorrow", "dueDate": _local_date(1).isoformat()})
    assert res.status_code == 201
    assert res.json["overdue"] is False


def test_completing_an_overdue_task_clears_overdue(client):
    created = client.post("/tasks", json={"title": "Late", "dueDate": "1900-01-01T00:00:00Z"}).json
    assert created["overdue"] is True

    patched = client.patch(f"/tasks/{created['id']}", json={"completed": True})
    assert patched.status_code == 200
    assert patched.json["completed"] is True
    assert patched.json["overdue"] is False

    listed = client.get("/tasks?sort=dueDate").json[0]
    assert listed["overdue"] is False
    assert set(listed) == TASK_KEYS


def test_patch_ignores_a_due_date_in_the_body(client):
    created = client.post("/tasks", json={"title": "Ship", "dueDate": "2026-08-05T17:00:00Z"}).json
    res = client.patch(
        f"/tasks/{created['id']}",
        json={"completed": True, "dueDate": "2030-01-01T00:00:00Z"},
    )
    assert res.status_code == 200
    assert res.json["dueDate"] == created["dueDate"]


def test_sorting_orders_by_due_date_with_undated_tasks_last_and_an_id_tiebreak(client):
    client.post("/tasks", json={"title": "later", "dueDate": "2026-09-01T00:00:00Z"})
    client.post("/tasks", json={"title": "undated first"})
    client.post("/tasks", json={"title": "sooner", "dueDate": "2026-08-01T00:00:00Z"})
    client.post("/tasks", json={"title": "undated second"})
    client.post("/tasks", json={"title": "tie", "dueDate": "2026-08-01T00:00:00Z"})

    res = client.get("/tasks?sort=dueDate")
    assert res.status_code == 200
    assert [t["id"] for t in res.json] == [3, 5, 1, 2, 4]


def test_a_timed_due_date_sorts_before_a_date_only_one_on_the_same_day(client):
    day = date(2026, 8, 5)
    client.post("/tasks", json={"title": "end of day", "dueDate": day.isoformat()})
    client.post(
        "/tasks",
        json={"title": "last second", "dueDate": datetime.combine(day, time(23, 59, 59)).isoformat()},
    )
    client.post(
        "/tasks",
        json={"title": "morning", "dueDate": datetime.combine(day, time(9, 0)).isoformat()},
    )

    assert [t["title"] for t in client.get("/tasks?sort=dueDate").json] == [
        "morning",
        "last second",
        "end of day",
    ]


def test_sorting_an_empty_list_returns_an_empty_list(client):
    res = client.get("/tasks?sort=dueDate")
    assert res.status_code == 200
    assert res.json == []


def test_sorting_a_single_task_returns_that_task(client):
    client.post("/tasks", json={"title": "Only", "dueDate": "2026-08-05T17:00:00Z"})
    assert [t["title"] for t in client.get("/tasks?sort=dueDate").json] == ["Only"]


def test_sorting_tasks_without_due_dates_falls_back_to_id_order(client):
    for title in ["A", "B", "C"]:
        client.post("/tasks", json={"title": title})
    assert [t["id"] for t in client.get("/tasks?sort=dueDate").json] == [1, 2, 3]


def test_a_sorted_read_leaves_the_default_and_stored_order_intact(client):
    client.post("/tasks", json={"title": "C", "dueDate": "2026-12-01T00:00:00Z"})
    client.post("/tasks", json={"title": "A", "dueDate": "2026-01-01T00:00:00Z"})
    client.post("/tasks", json={"title": "B"})

    assert [t["id"] for t in client.get("/tasks?sort=dueDate").json] == [2, 1, 3]
    assert [t["id"] for t in client.get("/tasks").json] == [1, 2, 3]
    assert [t["id"] for t in store._tasks] == [1, 2, 3]


def test_repeating_a_sorted_read_returns_a_byte_identical_response(client):
    client.post("/tasks", json={"title": "later", "dueDate": "2026-09-01T00:00:00Z"})
    client.post("/tasks", json={"title": "undated"})
    client.post("/tasks", json={"title": "sooner", "dueDate": "2026-08-01T00:00:00Z"})

    assert client.get("/tasks?sort=dueDate").data == client.get("/tasks?sort=dueDate").data


def test_an_unknown_sort_value_is_rejected_before_the_store_is_read(client):
    client.post("/tasks", json={"title": "Ship"})
    res = client.get("/tasks?sort=title")
    assert res.status_code == 400
    assert res.json["error"] == INVALID_SORT_ERROR
    assert len(store._tasks) == 1
    assert store._next_id == 2


def test_a_read_never_mutates_stored_tasks(client):
    client.post("/tasks", json={"title": "A", "dueDate": "2026-08-05T17:00:00Z"})
    client.post("/tasks", json={"title": "B"})
    before = [dict(t) for t in store._tasks]

    client.get("/tasks?sort=dueDate")
    client.get("/tasks")

    assert [dict(t) for t in store._tasks] == before


def test_overdue_is_never_written_into_the_store(client):
    client.post("/tasks", json={"title": "Late", "dueDate": "1900-01-01T00:00:00Z"})
    client.post("/tasks", json={"title": "Undated"})

    client.get("/tasks?sort=dueDate")
    client.get("/tasks")

    for stored in store._tasks:
        assert "overdue" not in stored
        assert set(stored) == STORED_KEYS


def test_a_malformed_stored_due_date_does_not_fail_the_list(client):
    client.post("/tasks", json={"title": "Ship"})
    store._tasks[0]["dueDate"] = "definitely-not-a-date"

    res = client.get("/tasks?sort=dueDate")
    assert res.status_code == 200
    assert res.json[0]["overdue"] is False


def test_reset_clears_due_dates_and_the_id_counter(client):
    client.post("/tasks", json={"title": "Ship", "dueDate": "2026-08-05T17:00:00Z"})
    reset()
    assert store._tasks == []
    assert store._next_id == 1
    assert client.get("/tasks").json == []


def test_the_same_create_posted_twice_makes_two_distinct_tasks(client):
    body = {"title": "Ship", "dueDate": "2026-08-05T17:00:00Z"}
    first = client.post("/tasks", json=body).json
    second = client.post("/tasks", json=body).json
    assert first["id"] != second["id"]
    assert len(client.get("/tasks").json) == 2


def test_an_old_client_posting_only_a_title_sees_every_existing_key_unchanged(client):
    created = client.post("/tasks", json={"title": "Buy milk"})
    assert created.status_code == 201
    assert created.json["id"] == 1
    assert created.json["title"] == "Buy milk"
    assert created.json["completed"] is False
    assert set(created.json) == TASK_KEYS

    listed = client.get("/tasks").json
    assert [t["id"] for t in listed] == [1]
    assert set(listed[0]) == TASK_KEYS


def test_no_edge_case_input_produces_a_server_error(client):
    due_dates = INVALID_DUE_DATE_VALUES + [
        None,
        "2026-08-05",
        "2026-08-05T17:00:00Z",
        "2026-08-05T17:00:00+05:30",
        "2028-02-29",
        "1900-01-01T00:00:00Z",
        "9999-12-31T00:00:00Z",
    ]
    for value in due_dates:
        res = client.post("/tasks", json={"title": "Ship", "dueDate": value})
        assert res.status_code < 500, str(value)[:40]

    for body in [{}, {"title": ""}, {"title": None}, {"dueDate": "not-a-date"}]:
        assert client.post("/tasks", json=body).status_code < 500, body

    for sort in ["", "dueDate", "nope", "id", "DUEDATE", "due date"]:
        assert client.get("/tasks", query_string={"sort": sort}).status_code < 500, sort
