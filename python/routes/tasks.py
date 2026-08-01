from flask import Blueprint, jsonify, request

from models.task import (
    DUE_DATE_KEY,
    SORT_OPTIONS,
    create_task,
    delete_task,
    parse_due_date,
    task_list_view,
    task_view,
    update_task,
)

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")

SORT_PARAM = "sort"
INVALID_DUE_DATE_ERROR = "dueDate must be a valid ISO 8601 datetime"
INVALID_SORT_ERROR = "sort must be one of: " + ", ".join(SORT_OPTIONS)


@tasks_bp.get("")
def list_tasks():
    sort = request.args.get(SORT_PARAM)
    if sort is not None and sort not in SORT_OPTIONS:
        return jsonify({"error": INVALID_SORT_ERROR}), 400
    return jsonify(task_list_view(sort))


@tasks_bp.post("")
def add_task():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    if not title:
        return jsonify({"error": "title is required"}), 400
    try:
        due_date = parse_due_date(body.get(DUE_DATE_KEY))
    except ValueError:
        return jsonify({"error": INVALID_DUE_DATE_ERROR}), 400
    return jsonify(task_view(create_task(title, due_date))), 201


@tasks_bp.patch("/<int:task_id>")
def patch_task(task_id):
    completed = (request.get_json(silent=True) or {}).get("completed")
    task = update_task(task_id, bool(completed))
    if task is None:
        return jsonify({"error": "task not found"}), 404
    return jsonify(task_view(task))


@tasks_bp.delete("/<int:task_id>")
def remove_task(task_id):
    if not delete_task(task_id):
        return jsonify({"error": "task not found"}), 404
    return "", 204
