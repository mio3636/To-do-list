"""应用装配入口；--data 可指定独立的数据文件。"""
import argparse
from pathlib import Path
import sys

from .services import TaskService
from .storage import JsonTaskRepository, StorageError


def main(argv=None):
    parser = argparse.ArgumentParser(description="今日清单桌面应用")
    parser.add_argument("--data", type=Path,
                        default=Path.home() / ".today-todo" / "tasks.json")
    parser.add_argument("--cli", action="store_true", help="运行队友提供的六项命令行菜单")
    args = parser.parse_args(argv)
    if args.cli:
        from .console import load_tasks, run_menu
        try:
            return run_menu(load_tasks(args.data))
        except StorageError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    try:
        import tkinter as tk
        from tkinter import messagebox
        from .ui import TodoApp
    except ImportError:
        print("桌面模式需要 Tkinter。请安装 Tcl/Tk，或使用 --cli。", file=sys.stderr)
        return 1
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"无法打开图形桌面，请使用 --cli。\n{exc}", file=sys.stderr)
        return 1
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
