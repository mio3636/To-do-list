"""整合队友的六项菜单和函数，通过共享服务操作桌面版的同一份数据。"""
from pathlib import Path

from .migration import normalize_category, normalize_priority
from .services import TaskService
from .storage import JsonTaskRepository, StorageError


def load_tasks(path: Path) -> TaskService:
    return TaskService(JsonTaskRepository(path))


def save_tasks(service: TaskService) -> None:
    service.save()


def add_task(service, desc, prio, due, cat):
    return service.add(desc, priority=normalize_priority(prio), due_date=due.strip(),
                       category=normalize_category(cat))


def view_tasks(service, tasks=None, output=print):
    all_tasks = service.all_tasks()
    rows = all_tasks if tasks is None else tasks
    if not rows:
        output("No tasks found. / 没有符合条件的任务。")
        return
    indices = {task.id: index for index, task in enumerate(all_tasks, 1)}
    for task in rows:
        status = "completed" if task.completed else "in progress"
        output(f"[{indices[task.id]}] {task.title} | {status} | "
               f"Priority: {task.priority} | Due: {task.due_date or '未安排'} | {task.category}")
        if task.notes:
            output(f"    Notes: {task.notes}")


def _task_at(service, idx):
    tasks = service.all_tasks()
    if type(idx) is not int or not 1 <= idx <= len(tasks):
        raise ValueError("Invalid task index / 任务序号无效，请先查看任务列表")
    return tasks[idx - 1]


def mark_task_status(service, idx, status):
    if status not in ("completed", "in progress"):
        raise ValueError("任务状态必须为 completed 或 in progress")
    return service.update(_task_at(service, idx).id, completed=status == "completed")


def delete_task(service, idx):
    return service.delete(_task_at(service, idx).id)


def filter_tasks(service, target_status):
    if target_status not in ("completed", "in progress"):
        raise ValueError("任务状态必须为 completed 或 in progress")
    return [task for task in service.all_tasks() if task.completed == (target_status == "completed")]


def run_menu(service, input_fn=input, output=print):
    output("今日清单 · 命令行模式（每次修改自动保存）")
    try:
        while True:
            output("\n===== TODO LIST MENU =====\n"
                   "1. Add new task / 新增任务\n"
                   "2. View all tasks / 查看全部\n"
                   "3. Mark task status / 完成或恢复\n"
                   "4. Delete a task / 删除任务\n"
                   "5. Filter completed tasks / 查看已完成\n"
                   "6. Save & Exit / 保存退出")
            choice = input_fn("Please select option (1-6): ").strip()
            try:
                if choice == "1":
                    desc = input_fn("Task description: ")
                    prio = input_fn("Priority (1=高, 2=中, 3=低; default 2): ").strip() or "2"
                    due = input_fn("Due date (YYYY-MM-DD, optional): ")
                    cat = input_fn("Category (Study/Work/Leisure; default Leisure): ").strip() or "Leisure"
                    add_task(service, desc, prio, due, cat)
                    output("Task added and saved. / 任务已添加并保存。")
                elif choice == "2":
                    view_tasks(service, output=output)
                elif choice == "3":
                    view_tasks(service, output=output)
                    idx = int(input_fn("Input task index: "))
                    status = input_fn("[c]ompleted / [i]n progress: ").strip().casefold()
                    if status not in ("c", "i"):
                        raise ValueError("请输入 c 或 i")
                    mark_task_status(service, idx, "completed" if status == "c" else "in progress")
                    output("Task status saved. / 状态已保存。")
                elif choice == "4":
                    view_tasks(service, output=output)
                    idx = int(input_fn("Input task index to delete: "))
                    _task_at(service, idx)
                    if input_fn("Confirm deletion? [y/N]: ").strip().casefold() == "y":
                        delete_task(service, idx)
                        output("Task deleted and saved. / 任务已删除并保存。")
                elif choice == "5":
                    view_tasks(service, filter_tasks(service, "completed"), output=output)
                elif choice == "6":
                    save_tasks(service)
                    output("Saved. Program exit. / 已保存，程序退出。")
                    return 0
                else:
                    output("Invalid option, choose 1-6. / 请输入 1-6。")
            except (ValueError, StorageError) as exc:
                output(f"操作未完成：{exc}")
    except (EOFError, KeyboardInterrupt):
        output("\n程序退出，已成功执行的修改均已自动保存。")
        return 0
