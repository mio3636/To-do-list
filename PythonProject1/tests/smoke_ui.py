"""需要图形桌面；使用临时数据验证界面与业务集成，不操作个人数据。"""
import tempfile
import tkinter as tk
from pathlib import Path
from unittest.mock import patch

from todo_app.console import add_task, load_tasks
from todo_app.services import TaskService
from todo_app.storage import JsonTaskRepository
from todo_app.ui import TodoApp


def main():
    with tempfile.TemporaryDirectory() as temporary:
        root = tk.Tk()
        root.withdraw()
        try:
            service = TaskService(JsonTaskRepository(Path(temporary) / "tasks.json"))
            app = TodoApp(root, service)
            root.update()
            app.quick_title.set("界面集成验证")
            app.add()
            root.update()
            assert len(app.tree.get_children()) == 1
            app.select()
            app.title.set("详情保存验证")
            app.notes.insert("1.0", "中文备注")
            app.save()
            root.update()
            assert service.list_tasks()[0].title == "详情保存验证"
            assert service.list_tasks()[0].notes == "中文备注"
            app.toggle()
            root.update()
            assert len(app.tree.get_children()) == 0
            app.change_view("已完成")
            root.update()
            assert len(app.tree.get_children()) == 1
            app.query.set("不存在的文字")
            root.update()
            assert len(app.tree.get_children()) == 0
            app.query.set("")
            app.category_filter.set("工作")
            root.update()
            assert len(app.tree.get_children()) == 0
            app.category_filter.set("全部")
            root.update()
            app.tree.selection_set(app.tree.get_children()[0])
            app.select()
            with patch("todo_app.ui.messagebox.askyesno", return_value=True):
                app.delete()
            root.update()
            assert service.stats() == (0, 0)
            app.undo()
            root.update()
            assert service.stats() == (1, 1)
            console_service = load_tasks(Path(temporary) / "tasks.json")
            add_task(console_service, "命令行创建，桌面读取", "1", "", "Work")
            restarted = TaskService(JsonTaskRepository(Path(temporary) / "tasks.json"))
            assert len(restarted.list_tasks("收集箱", category="工作")) == 1
            print("PASS: Tkinter 添加、编辑、完成、搜索、分类、删除撤销及 CLI 数据共享")
        finally:
            root.destroy()


if __name__ == "__main__":
    main()
