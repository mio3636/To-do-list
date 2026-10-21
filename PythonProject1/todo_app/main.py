"""应用装配入口；--data 可指定独立的数据文件。"""
import argparse
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from .services import TaskService
from .storage import JsonTaskRepository, StorageError
from .ui import TodoApp


def main():
    parser = argparse.ArgumentParser(description="今日清单桌面应用")
    parser.add_argument("--data", type=Path,
                        default=Path.home() / ".today-todo" / "tasks.json")
    args = parser.parse_args()
    root = tk.Tk()
    root.withdraw()
    try:
        service = TaskService(JsonTaskRepository(args.data))
    except StorageError as exc:
        messagebox.showerror("任务数据读取失败", str(exc), parent=root)
        root.destroy()
        return 1
    TodoApp(root, service)
    root.deiconify()
    root.mainloop()
    return 0
