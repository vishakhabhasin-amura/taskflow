from flask import Blueprint, jsonify, request

from models.task import (
    create_task,
    delete_task,
    get_tasks,
    is_overdue,
    sorted_by_due_date,
    update_task,
)

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


def _with_overdue(task):
    return {**task, "isOverdue": is_overdue(task)}


@tasks_bp.get("")
def list_tasks():
    tasks = get_tasks()
    if request.args.get("sort") == "dueDate":
        tasks = sorted_by_due_date(tasks)
    return jsonify([_with_overdue(t) for t in tasks])


@tasks_bp.post("")
def add_task():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    if not title:
        return jsonify({"error": "title is required"}), 400
    return jsonify(_with_overdue(create_task(title, body.get("dueDate")))), 201


@tasks_bp.patch("/<int:task_id>")
def patch_task(task_id):
    completed = (request.get_json(silent=True) or {}).get("completed")
    task = update_task(task_id, bool(completed))
    if task is None:
        return jsonify({"error": "task not found"}), 404
    return jsonify(_with_overdue(task))


@tasks_bp.delete("/<int:task_id>")
def remove_task(task_id):
    if not delete_task(task_id):
        return jsonify({"error": "task not found"}), 404
    return "", 204
