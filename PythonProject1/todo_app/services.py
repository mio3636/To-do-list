"""任务业务入口；仅在持久化成功后更新内存，界面不直接读写文件。"""
from dataclasses import replace
from datetime import date, timedelta

from .models import Task
from .storage import TaskRepository

VIEWS = ("今天", "收集箱", "未来 7 天", "全部任务", "已完成")


class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository
        self._tasks = repository.load()

    def _commit(self, tasks):
        self.repository.save(tasks)
        self._tasks = tasks

    def all_tasks(self) -> list[Task]:
        """返回包含已完成任务的稳定列表副本，供命令行序号操作使用。"""
        return list(self._tasks)

    def save(self) -> None:
        """支持队友菜单中的“保存并退出”；日常操作也会立即保存。"""
        self.repository.save(self._tasks)

    def get(self, task_id: str) -> Task:
        for task in self._tasks:
            if task.id == task_id:
                return task
        raise ValueError("该任务已不存在，请刷新列表")

    def add(self, title: str, **fields) -> Task:
        task = Task.create(title, **fields)
        self._commit([*self._tasks, task])
        return task

    def update(self, task_id: str, **fields) -> Task:
        allowed = {"title", "notes", "category", "priority", "due_date", "completed"}
        if fields.keys() - allowed:
            raise ValueError("包含不能修改的字段")
        if "title" in fields:
            if not isinstance(fields["title"], str):
                raise ValueError("任务名称必须是文本")
            fields["title"] = fields["title"].strip()
        updated = replace(self.get(task_id), **fields)
        self._commit([updated if t.id == task_id else t for t in self._tasks])
        return updated

    def toggle(self, task_id: str) -> Task:
        return self.update(task_id, completed=not self.get(task_id).completed)

    def delete(self, task_id: str) -> Task:
        task = self.get(task_id)
        self._commit([t for t in self._tasks if t.id != task_id])
        return task

    def restore(self, task: Task) -> None:
        if any(t.id == task.id for t in self._tasks):
            raise ValueError("该任务已存在")
        self._commit([*self._tasks, task])

    def list_tasks(self, view="全部任务", query="", category="全部", today=None):
        if view not in VIEWS:
            raise ValueError("未知视图")
        today = today or date.today()
        end = (today + timedelta(days=6)).isoformat()
        start = today.isoformat()
        result = []
        for task in self._tasks:
            if view == "已完成" and not task.completed:
                continue
            if view != "已完成" and task.completed:
                continue
            # 今天同时展示逾期任务，避免遗漏。
            if view == "今天" and (not task.due_date or task.due_date > start):
                continue
            if view == "收集箱" and task.due_date:
                continue
            if view == "未来 7 天" and not start <= task.due_date <= end:
                continue
            if category != "全部" and task.category != category:
                continue
            if query.casefold() not in f"{task.title} {task.notes}".casefold():
                continue
            result.append(task)
        return sorted(result, key=lambda t: (t.due_date or "9999-12-31",
                                              {"高": 0, "中": 1, "低": 2}[t.priority],
                                              t.created_at, t.id))

    def stats(self):
        return len(self._tasks), sum(t.completed for t in self._tasks)
