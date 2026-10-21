"""Tkinter 主体界面；业务通过注入的 TaskService 调用。"""
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from .models import CATEGORIES, PRIORITIES
from .services import VIEWS, TaskService
from .storage import StorageError

BG = "#F8FAFC"
INK = "#0F172A"
PRIMARY = "#6366F1"


class TodoApp:
    def __init__(self, root: tk.Tk, service: TaskService):
        self.root, self.service = root, service
        self.view = "今天"
        self.selected_id = None
        self.deleted_task = None
        self.query = tk.StringVar()
        self.category_filter = tk.StringVar(value="全部")
        self.quick_title = tk.StringVar()
        self.title = tk.StringVar()
        self.category = tk.StringVar(value="生活")
        self.priority = tk.StringVar(value="中")
        self.due_date = tk.StringVar()
        self.status = tk.StringVar(value="准备就绪 · 双击任务可切换完成状态")
        root.title("今日清单 · To-do List")
        root.geometry("1160x720")
        root.minsize(960, 600)
        root.configure(bg=BG)
        self._styles()
        self._build()
        self.query.trace_add("write", lambda *_: self.refresh())
        self.category_filter.trace_add("write", lambda *_: self.refresh())
        root.bind("<Control-n>", self._focus_quick)
        root.bind("<Control-s>", lambda _: self.save())
        self.refresh()

    def _styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=INK, font=("Microsoft YaHei UI", 10))
        style.configure("Heading.TLabel", font=("Microsoft YaHei UI", 22, "bold"))
        style.configure("Muted.TLabel", foreground="#64748B")
        style.configure("TButton", padding=(12, 8), font=("Microsoft YaHei UI", 10))
        style.configure("Accent.TButton", background=PRIMARY, foreground="white")
        style.map("Accent.TButton", background=[("active", "#4F46E5")])
        style.configure("Treeview", rowheight=42, font=("Microsoft YaHei UI", 10),
                        background="white", fieldbackground="white", borderwidth=0)
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"), padding=8)

    def _build(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        sidebar = ttk.Frame(self.root, padding=20)
        sidebar.grid(row=0, column=0, sticky="ns")
        ttk.Label(sidebar, text="✓ 今日清单", font=("Microsoft YaHei UI", 17, "bold")).pack(anchor="w", pady=(8, 6))
        ttk.Label(sidebar, text="把每一天，安排得刚刚好", style="Muted.TLabel").pack(anchor="w", pady=(0, 28))
        self.nav_buttons = {}
        for view in VIEWS:
            button = ttk.Button(sidebar, text=view, command=lambda v=view: self.change_view(v))
            button.pack(fill="x", pady=4)
            self.nav_buttons[view] = button
        ttk.Separator(sidebar).pack(fill="x", pady=22)
        ttk.Label(sidebar, text="清单分类", style="Muted.TLabel").pack(anchor="w")
        ttk.Combobox(sidebar, textvariable=self.category_filter, values=("全部", *CATEGORIES),
                     state="readonly", width=15).pack(fill="x", pady=10)
        ttk.Label(sidebar, text="Ctrl+N  新建任务\nCtrl+S  保存详情", style="Muted.TLabel").pack(side="bottom", anchor="w")

        center = ttk.Frame(self.root, padding=(12, 24, 18, 12))
        center.grid(row=0, column=1, sticky="nsew")
        center.columnconfigure(0, weight=1)
        center.rowconfigure(6, weight=1)
        self.heading = ttk.Label(center, style="Heading.TLabel")
        self.heading.grid(row=0, column=0, sticky="w")
        self.summary = ttk.Label(center, style="Muted.TLabel")
        self.summary.grid(row=1, column=0, sticky="w", pady=(8, 12))
        self.progress = ttk.Progressbar(center, maximum=100)
        self.progress.grid(row=2, column=0, sticky="ew", pady=(0, 18))
        quick = ttk.Frame(center)
        quick.grid(row=3, column=0, sticky="ew")
        quick.columnconfigure(0, weight=1)
        self.quick_entry = ttk.Entry(quick, textvariable=self.quick_title, font=("Microsoft YaHei UI", 11))
        self.quick_entry.grid(row=0, column=0, sticky="ew", ipady=7)
        self.quick_entry.bind("<Return>", lambda _: self.add())
        ttk.Button(quick, text="＋ 添加", style="Accent.TButton", command=self.add).grid(row=0, column=1, padx=(8, 0))
        ttk.Label(center, text="输入任务后按 Enter；今天视图中新任务默认今天截止", style="Muted.TLabel").grid(row=4, column=0, sticky="w", pady=(6, 16))
        search = ttk.Frame(center)
        search.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        search.columnconfigure(1, weight=1)
        ttk.Label(search, text="搜索任务  ").grid(row=0, column=0)
        ttk.Entry(search, textvariable=self.query).grid(row=0, column=1, sticky="ew", ipady=4)
        table = ttk.Frame(center)
        table.grid(row=6, column=0, sticky="nsew")
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table, columns=("state", "title", "due", "priority"), show="headings", selectmode="browse")
        for name, label, width in (("state", "状态", 58), ("title", "任务名称", 220),
                                   ("due", "截止日期", 100), ("priority", "优先级", 65)):
            self.tree.heading(name, text=label)
            self.tree.column(name, width=width, minwidth=45, stretch=name == "title")
        self.tree.tag_configure("overdue", foreground="#DC2626")
        self.tree.tag_configure("done", foreground="#64748B")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self.select)
        self.tree.bind("<Double-1>", lambda _: self.toggle())
        self.empty_label = ttk.Label(center, text="")
        self.empty_label.grid(row=7, column=0, sticky="w", pady=8)

        detail = ttk.Frame(self.root, padding=(16, 26, 20, 12), width=260)
        detail.grid(row=0, column=2, sticky="ns")
        ttk.Label(detail, text="任务详情", font=("Microsoft YaHei UI", 15, "bold")).pack(anchor="w", pady=(0, 18))
        for label, variable in (("任务名称", self.title), ("截止日期（YYYY-MM-DD，可留空）", self.due_date)):
            ttk.Label(detail, text=label).pack(anchor="w", pady=(8, 4))
            ttk.Entry(detail, textvariable=variable, width=27).pack(fill="x", ipady=5)
        for label, variable, values in (("所属清单", self.category, CATEGORIES), ("优先级", self.priority, PRIORITIES)):
            ttk.Label(detail, text=label).pack(anchor="w", pady=(12, 4))
            ttk.Combobox(detail, textvariable=variable, values=values, state="readonly").pack(fill="x")
        ttk.Label(detail, text="备注").pack(anchor="w", pady=(12, 4))
        self.notes = tk.Text(detail, width=26, height=7, wrap="word", font=("Microsoft YaHei UI", 10), relief="solid", borderwidth=1)
        self.notes.pack(fill="both", expand=True)
        self.detail_buttons = []
        for label, callback in (("保存详情", self.save), ("完成 / 恢复任务", self.toggle), ("删除任务", self.delete)):
            button = ttk.Button(detail, text=label, command=callback)
            button.pack(fill="x", pady=(8, 0))
            self.detail_buttons.append(button)
        self.undo_button = ttk.Button(detail, text="撤销删除", command=self.undo, state="disabled")
        self.undo_button.pack(fill="x", pady=(8, 0))
        ttk.Label(self.root, textvariable=self.status, padding=(20, 8), style="Muted.TLabel").grid(row=1, column=0, columnspan=3, sticky="ew")

    def _focus_quick(self, _event=None):
        self.quick_entry.focus_set()
        return "break"

    def change_view(self, view):
        self.view = view
        self.refresh()

    def refresh(self):
        for view, button in self.nav_buttons.items():
            button.configure(style="Accent.TButton" if view == self.view else "TButton")
        total, completed = self.service.stats()
        self.heading.configure(text=self.view)
        self.summary.configure(text=f"{date.today():%Y年%m月%d日}  ·  共 {total} 项，已完成 {completed} 项")
        self.progress["value"] = 100 * completed / total if total else 0
        for item in self.tree.get_children():
            self.tree.delete(item)
        tasks = self.service.list_tasks(self.view, self.query.get().strip(), self.category_filter.get())
        today = date.today().isoformat()
        for task in tasks:
            tag = "done" if task.completed else "overdue" if task.due_date and task.due_date < today else ""
            self.tree.insert("", "end", iid=task.id, values=("✓" if task.completed else "○", task.title,
                             task.due_date or "未安排", task.priority), tags=(tag,))
        self.empty_label.configure(text="没有符合条件的任务。试试添加任务或调整筛选条件。" if not tasks else f"当前显示 {len(tasks)} 项任务")
        if self.selected_id and self.tree.exists(self.selected_id):
            self.tree.selection_set(self.selected_id)
            self.tree.focus(self.selected_id)
        else:
            self.selected_id = None
            self._fill_detail(None)

    def _fill_detail(self, task):
        self.title.set(task.title if task else "")
        self.category.set(task.category if task else "生活")
        self.priority.set(task.priority if task else "中")
        self.due_date.set(task.due_date if task else "")
        self.notes.delete("1.0", "end")
        if task:
            self.notes.insert("1.0", task.notes)
        for button in self.detail_buttons:
            button.configure(state="normal" if task else "disabled")

    def select(self, _event=None):
        selected = self.tree.selection()
        if selected:
            self.selected_id = selected[0]
            self._fill_detail(self.service.get(self.selected_id))

    def _run(self, action, success):
        try:
            action()
        except (ValueError, StorageError) as exc:
            messagebox.showerror("操作未完成", str(exc), parent=self.root)
            return False
        self.refresh()
        self.status.set(success)
        return True

    def add(self):
        def action():
            task = self.service.add(self.quick_title.get(), category=(self.category_filter.get()
                                    if self.category_filter.get() != "全部" else "生活"),
                                    due_date=date.today().isoformat() if self.view == "今天" else "")
            self.selected_id = task.id
            self.quick_title.set("")
            self.query.set("")
            if self.view not in ("今天", "收集箱", "全部任务"):
                self.view = "收集箱"
        self._run(action, "任务已添加并保存")

    def save(self):
        if self.selected_id:
            self._run(lambda: self.service.update(self.selected_id, title=self.title.get(),
                      category=self.category.get(), priority=self.priority.get(),
                      due_date=self.due_date.get().strip(), notes=self.notes.get("1.0", "end-1c")), "详情已保存")

    def toggle(self):
        if self.selected_id:
            self._run(lambda: self.service.toggle(self.selected_id), "任务状态已更新")

    def delete(self):
        if not self.selected_id:
            return
        if not messagebox.askyesno("删除任务", "确定删除选中的任务？可以撤销最近一次删除。", parent=self.root):
            return
        def action():
            self.deleted_task = self.service.delete(self.selected_id)
            self.selected_id = None
            self.undo_button.configure(state="normal")
        self._run(action, "任务已删除，可点击“撤销删除”恢复")

    def undo(self):
        if self.deleted_task:
            def action():
                self.service.restore(self.deleted_task)
                self.deleted_task = None
                self.undo_button.configure(state="disabled")
            self._run(action, "任务已恢复，可在原视图或全部任务中查看")
