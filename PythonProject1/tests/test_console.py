"""队友菜单和任务函数的集成测试，共享实际 JSON 仓储。"""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from todo_app.console import (add_task, delete_task, filter_tasks, load_tasks,
                              mark_task_status, run_menu, save_tasks, view_tasks)
from todo_app.main import main
from todo_app.services import TaskService
from todo_app.storage import JsonTaskRepository


class TestConsole(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "tasks.json"
        self.service = load_tasks(self.path)

    def menu(self, answers):
        iterator = iter(answers)
        messages = []
        code = run_menu(self.service, input_fn=lambda _: next(iterator), output=messages.append)
        self.assertEqual(code, 0)
        return "\n".join(messages)

    def test_member_functions_share_desktop_data(self):
        task = add_task(self.service, "  完成整合  ", "1", "2026-10-21", "Work")
        self.assertEqual(task.category, "工作")
        self.assertEqual(task.priority, "高")
        mark_task_status(self.service, 1, "completed")
        desktop = TaskService(JsonTaskRepository(self.path))
        self.assertEqual(desktop.list_tasks("已完成")[0].title, "完成整合")
        self.assertEqual(len(filter_tasks(self.service, "completed")), 1)
        mark_task_status(self.service, 1, "in progress")
        self.assertEqual(len(filter_tasks(self.service, "in progress")), 1)
        delete_task(self.service, 1)
        save_tasks(self.service)
        self.assertEqual(load_tasks(self.path).stats(), (0, 0))

    def test_filtered_numbers_match_original_list(self):
        add_task(self.service, "第一个", "2", "", "Study")
        add_task(self.service, "第二个", "2", "", "Leisure")
        mark_task_status(self.service, 2, "completed")
        lines = []
        view_tasks(self.service, filter_tasks(self.service, "completed"), output=lines.append)
        self.assertTrue(lines[0].startswith("[2]"))

    def test_full_menu_flow(self):
        output = self.menu(["1", "测试任务", "1", "2026-10-21", "Study",
                            "2", "3", "1", "c", "5", "3", "1", "i",
                            "4", "1", "y", "6"])
        self.assertIn("completed", output)
        self.assertIn("请输入 1-6", self.menu(["7", "6"]))
        self.assertEqual(load_tasks(self.path).stats(), (0, 0))

    def test_invalid_inputs_return_to_menu(self):
        add_task(self.service, "任务", "2", "", "Work")
        output = self.menu(["3", "abc", "3", "0", "c", "3", "1", "x",
                            "1", "日期错误", "2", "not-a-date", "Study", "6"])
        self.assertGreaterEqual(output.count("操作未完成"), 4)
        self.assertEqual(self.service.stats(), (1, 0))

    def test_delete_requires_confirmation(self):
        add_task(self.service, "保留", "2", "", "Work")
        self.menu(["4", "1", "n", "6"])
        self.assertEqual(self.service.stats(), (1, 0))

    def test_eof_preserves_autosaved_changes(self):
        add_task(self.service, "自动保存", "3", "", "Leisure")
        def eof(_):
            raise EOFError
        self.assertEqual(run_menu(self.service, input_fn=eof, output=lambda _: None), 0)
        self.assertEqual(load_tasks(self.path).stats(), (1, 0))

    def test_corrupt_cli_file_returns_failure_without_rewrite(self):
        self.path.write_bytes(b"broken")
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(["--cli", "--data", str(self.path)]), 1)
        self.assertIn("无法读取", errors.getvalue())
        self.assertEqual(self.path.read_bytes(), b"broken")

    def test_bad_index_and_status_do_not_change_tasks(self):
        add_task(self.service, "任务", "2", "", "Work")
        for index in (0, -1, 2, True):
            with self.subTest(index=index), self.assertRaises(ValueError):
                delete_task(self.service, index)
        with self.assertRaises(ValueError):
            mark_task_status(self.service, 1, "unknown")
        self.assertEqual(self.service.stats(), (1, 0))


if __name__ == "__main__":
    unittest.main()
