from flask import Blueprint, jsonify, request

from models.task import create_task, delete_task, get_tasks, update_task

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks_bp.get("")
def list_tasks():
    return jsonify(get_tasks())


@tasks_bp.post("")
def add_task():
    title = (request.get_json(silent=True) or {}).get("title")
    if not title:
        return jsonify({"error": "title is required"}), 400
    return jsonify(create_task(title)), 201


@tasks_bp.patch("/<int:task_id>")
def patch_task(task_id):
    completed = (request.get_json(silent=True) or {}).get("completed")
    task = update_task(task_id, bool(completed))
    if task is None:
        return jsonify({"error": "task not found"}), 404
    return jsonify(task)


@tasks_bp.delete("/<int:task_id>")
def remove_task(task_id):
    if not delete_task(task_id):
        return jsonify({"error": "task not found"}), 404
    return "", 204
