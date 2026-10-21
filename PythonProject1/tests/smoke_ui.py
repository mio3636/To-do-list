"""需要图形桌面；使用临时数据验证界面与业务集成，不操作个人数据。"""
import tempfile
import tkinter as tk
from pathlib import Path

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
            print("PASS: Tkinter 创建、添加、详情保存、完成、切换视图、搜索")
        finally:
            root.destroy()


if __name__ == "__main__":
    main()
