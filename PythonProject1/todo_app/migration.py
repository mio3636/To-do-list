"""兼容队友的 description/status、数字优先级和英文分类。"""
import json
from uuid import NAMESPACE_URL, uuid5

from .models import CATEGORIES, PRIORITIES, Task


def normalize_priority(value):
    if value in PRIORITIES:
        return value
    if type(value) not in (int, str):
        raise ValueError("优先级应为 1/2/3 或 高/中/低")
    mapped = {"1": "高", "2": "中", "3": "低"}.get(str(value).strip())
    if mapped is None:
        raise ValueError("优先级应为 1/2/3 或 高/中/低")
    return mapped


def normalize_category(value):
    if not isinstance(value, str):
        raise ValueError("分类必须是文本")
    value = value.strip()
    if value in CATEGORIES:
        return value
    mapped = {"study": "学习", "work": "工作", "leisure": "生活"}.get(value.casefold())
    if mapped is None:
        raise ValueError("分类应为 Study/Work/Leisure 或 学习/工作/生活")
    return mapped


def task_from_legacy(item, index):
    if not isinstance(item, dict):
        raise ValueError(f"第 {index + 1} 项任务必须是对象")
    allowed = {"id", "title", "description", "notes", "category", "priority",
               "due_date", "completed", "status", "created_at"}
    if item.keys() - allowed:
        raise ValueError(f"第 {index + 1} 项任务包含未知字段，请先备份并检查")
    title = item.get("title", item.get("description", ""))
    if "title" in item and "description" in item and item["title"] != item["description"]:
        raise ValueError("title 和 description 不一致，无法自动转换")
    if "status" in item:
        status = item["status"]
        if status not in ("completed", "in progress"):
            raise ValueError("旧任务状态必须为 completed 或 in progress")
        completed = status == "completed"
        if "completed" in item and (type(item["completed"]) is not bool or item["completed"] != completed):
            raise ValueError("任务的 status 和 completed 不一致")
    else:
        completed = item.get("completed", False)
    task_id = item.get("id")
    if task_id is None:
        seed = json.dumps(item, sort_keys=True, ensure_ascii=False)
        task_id = uuid5(NAMESPACE_URL, f"today-todo:legacy:{index}:{seed}").hex
    elif type(task_id) is int:
        task_id = str(task_id)
    return Task(id=task_id, title=title, notes=item.get("notes", ""),
                category=normalize_category(item.get("category", "生活")),
                priority=normalize_priority(item.get("priority", "中")),
                due_date=item.get("due_date", ""), completed=completed,
                created_at=item.get("created_at", ""))
