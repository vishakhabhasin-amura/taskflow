from flask import Blueprint, jsonify, request

from models.task import (
    create_task,
    delete_task,
    get_task,
    get_tasks,
    set_due_date,
    update_task,
)

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks_bp.get("")
def list_tasks():
    return jsonify(get_tasks())


@tasks_bp.post("")
def add_task():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    if not title:
        return jsonify({"error": "title is required"}), 400
    # due_date is optional; absent -> None (stored as null).
    return jsonify(create_task(title, body.get("due_date"))), 201


@tasks_bp.patch("/<int:task_id>")
def patch_task(task_id):
    task = get_task(task_id)
    if task is None:
        return jsonify({"error": "task not found"}), 404

    body = request.get_json(silent=True) or {}

    if "due_date" in body:
        # Immutable once set: reject any attempt to supply due_date when one exists.
        if task["due_date"] is not None:
            return jsonify({"error": "due_date cannot be changed once set"}), 400
        set_due_date(task_id, body["due_date"])

    if "completed" in body:
        update_task(task_id, bool(body["completed"]))

    return jsonify(get_task(task_id))


@tasks_bp.delete("/<int:task_id>")
def remove_task(task_id):
    if not delete_task(task_id):
        return jsonify({"error": "task not found"}), 404
    return "", 204
