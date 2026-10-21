"""整合成员二的存储测试，并覆盖旧格式迁移与失败保护。"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from todo_app.models import Task
from todo_app.storage import JsonTaskRepository, StorageError


class TestTaskStorage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "tasks.json"
        self.repo = JsonTaskRepository(self.path)

    def test_load_empty_file(self):
        self.assertEqual(self.repo.load(), [])

    def test_save_and_load(self):
        tasks = [Task.create("Test Task", notes="中文备注")]
        self.repo.save(tasks)
        self.assertTrue(self.path.exists())
        self.assertEqual(self.repo.load(), tasks)

    def test_corrupted_json(self):
        raw = b"{ this is not valid json ]"
        self.path.write_bytes(raw)
        with self.assertRaises(StorageError):
            self.repo.load()
        self.assertEqual(self.path.read_bytes(), raw)

    def test_legacy_mapping_and_backup(self):
        legacy = [{"id": 1, "description": "复习", "priority": "1", "due_date": "2026-10-21",
                   "category": "Study", "status": "completed"},
                  {"description": "整理房间", "priority": 3, "category": "Leisure", "status": "in progress"}]
        raw = json.dumps(legacy, ensure_ascii=False).encode("utf-8")
        self.path.write_bytes(raw)
        tasks = self.repo.load()
        self.assertEqual(tasks[0].id, "1")
        self.assertEqual(tasks[0].title, "复习")
        self.assertEqual(tasks[0].priority, "高")
        self.assertEqual(tasks[0].category, "学习")
        self.assertTrue(tasks[0].completed)
        self.assertEqual(tasks[1].priority, "低")
        self.assertEqual(tasks, JsonTaskRepository(self.path).load())
        self.assertEqual(self.path.read_bytes(), raw, "读取不能改写旧文件")
        self.repo.save(tasks)
        self.assertEqual(self.path.with_name("tasks.json.legacy.bak").read_bytes(), raw)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["version"], 1)
        self.assertEqual(JsonTaskRepository(self.path).load(), tasks)

    def test_member2_minimal_legacy_data(self):
        self.path.write_text(json.dumps([{"id": 1, "description": "Test Task", "status": "in progress"}]), encoding="utf-8")
        task = self.repo.load()[0]
        self.assertEqual(task.title, "Test Task")
        self.assertFalse(task.completed)

    def test_bom_and_empty_legacy_list(self):
        self.path.write_text("[]", encoding="utf-8-sig")
        self.assertEqual(self.repo.load(), [])
        self.repo.save([])
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["tasks"], [])

    def test_invalid_legacy_data_is_not_silently_dropped(self):
        for item in ({"description": "a", "status": "unknown"},
                     {"description": "a", "category": "Other"},
                     {"description": "a", "priority": "0"},
                     {"description": "a", "extra": "不能丢失的字段"},
                     {"description": "a", "status": "completed", "completed": False}):
            raw = json.dumps([item]).encode()
            self.path.write_bytes(raw)
            with self.subTest(item=item), self.assertRaises(StorageError):
                self.repo.load()
            self.assertEqual(self.path.read_bytes(), raw)

    def test_failed_atomic_replace_preserves_original(self):
        original = [Task.create("保留原始数据")]
        self.repo.save(original)
        before = self.path.read_bytes()
        with patch("todo_app.storage.os.replace", side_effect=OSError("磁盘异常")):
            with self.assertRaises(StorageError):
                self.repo.save([Task.create("保存失败")])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_existing_backup_is_preserved(self):
        backup = self.path.with_name("tasks.json.legacy.bak")
        backup.write_bytes(b"older backup")
        self.path.write_bytes(b"[]")
        self.repo.load()
        self.repo.save([])
        self.assertEqual(backup.read_bytes(), b"older backup")
        self.assertEqual(self.path.with_name("tasks.json.legacy.1.bak").read_bytes(), b"[]")


if __name__ == "__main__":
    unittest.main()
