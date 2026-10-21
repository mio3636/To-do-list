"""共享数据模型；界面、业务、存储统一使用 Task。"""
from dataclasses import asdict, dataclass
from datetime import date, datetime
from uuid import uuid4

PRIORITIES = ("高", "中", "低")
CATEGORIES = ("工作", "学习", "生活")


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    notes: str = ""
    category: str = "生活"
    priority: str = "中"
    due_date: str = ""
    completed: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("任务 ID 不能为空")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("请输入任务名称")
        if len(self.title) > 120:
            raise ValueError("任务名称最多 120 个字符")
        if self.priority not in PRIORITIES or self.category not in CATEGORIES:
            raise ValueError("任务优先级或分类无效")
        if not isinstance(self.notes, str) or type(self.completed) is not bool:
            raise ValueError("任务备注或完成状态无效")
        if not isinstance(self.due_date, str) or not isinstance(self.created_at, str):
            raise ValueError("日期必须是文本")
        if self.due_date:
            try:
                parsed = date.fromisoformat(self.due_date)
                if parsed.isoformat() != self.due_date:
                    raise ValueError
            except ValueError:
                raise ValueError("截止日期格式应为 YYYY-MM-DD") from None

    @classmethod
    def create(cls, title: str, **fields):
        return cls(id=uuid4().hex, title=title.strip(),
                   created_at=datetime.now().isoformat(timespec="seconds"), **fields)

    def to_dict(self):
        return asdict(self)
