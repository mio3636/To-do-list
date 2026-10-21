import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from todo_app.models import Task
from todo_app.services import TaskService
from todo_app.storage import JsonTaskRepository, StorageError


class TodoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "data" / "tasks.json"
        self.repo = JsonTaskRepository(self.path)
        self.service = TaskService(self.repo)

    def test_crud_survives_restart(self):
        task = self.service.add("  完成框架  ", notes="中文备注", due_date="2026-10-21")
        self.assertEqual(task.title, "完成框架")
        self.service.update(task.id, priority="高", title="集成框架")
        restarted = TaskService(self.repo)
        self.assertEqual(restarted.get(task.id).priority, "高")
        self.assertEqual(restarted.get(task.id).notes, "中文备注")
        restarted.toggle(task.id)
        self.assertEqual(restarted.list_tasks(), [])
        self.assertEqual(len(restarted.list_tasks("已完成")), 1)
        restarted.toggle(task.id)
        removed = restarted.delete(task.id)
        restarted.restore(removed)
        self.assertEqual(restarted.stats(), (1, 0))

    def test_date_views_and_boundaries(self):
        for title, due in (("逾期", "2026-10-20"), ("今天", "2026-10-21"),
                           ("第七天", "2026-10-27"), ("第八天", "2026-10-28"), ("未安排", "")):
            self.service.add(title, due_date=due)
        today = date(2026, 10, 21)
        titles = lambda view: [t.title for t in self.service.list_tasks(view, today=today)]
        self.assertEqual(titles("今天"), ["逾期", "今天"])
        self.assertEqual(titles("未来 7 天"), ["今天", "第七天"])
        self.assertEqual(titles("收集箱"), ["未安排"])

    def test_search_and_category(self):
        self.service.add("Review", notes="接口文档", category="工作")
        self.service.add("Review", category="学习")
        self.assertEqual(len(self.service.list_tasks(query="review", category="工作")), 1)
        self.assertEqual(len(self.service.list_tasks(query="接口")), 1)

    def test_priority_sort(self):
        self.service.add("低优先级", priority="低")
        self.service.add("高优先级", priority="高")
        self.assertEqual(self.service.list_tasks()[0].title, "高优先级")

    def test_invalid_input_does_not_write(self):
        for fields in ({"title": "  "}, {"title": "x", "due_date": "2026-02-30"},
                       {"title": "x", "due_date": "20261021"},
                       {"title": "x", "priority": "紧急"}, {"title": "x" * 121}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                self.service.add(**fields)
        self.assertFalse(self.path.exists())

    def test_missing_task_and_protected_fields(self):
        with self.assertRaises(ValueError):
            self.service.delete("missing")
        task = self.service.add("a")
        with self.assertRaises(ValueError):
            self.service.update(task.id, id="other")
        with self.assertRaises(ValueError):
            self.service.restore(task)

    def test_corrupt_file_is_preserved(self):
        self.path.parent.mkdir()
        self.path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(StorageError):
            self.repo.load()
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{broken")

    def test_invalid_schema_is_rejected(self):
        self.path.parent.mkdir()
        task = Task.create("a").to_dict()
        for payload in ({"version": 2, "tasks": []}, {"version": 1, "tasks": [task, task]},
                        {"version": 1, "tasks": [dict(task, completed="false")]}):
            self.path.write_text(json.dumps(payload), encoding="utf-8")
            with self.subTest(payload=payload), self.assertRaises(StorageError):
                self.repo.load()

    def test_failed_save_keeps_memory_unchanged(self):
        class FailingRepository:
            def load(self):
                return []

            def save(self, tasks):
                raise StorageError("磁盘写入失败")
        service = TaskService(FailingRepository())
        with self.assertRaises(StorageError):
            service.add("不能丢失的任务")
        self.assertEqual(service.stats(), (0, 0))


if __name__ == "__main__":
    unittest.main()
