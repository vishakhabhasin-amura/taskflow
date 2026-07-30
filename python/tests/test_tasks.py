import pytest

from app import app
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
