"""JSON 存储实现。后续可按 TaskRepository 接口替换成 SQLite。"""
import json
import os
import tempfile
from pathlib import Path
from typing import Protocol

from .models import Task


class StorageError(Exception):
    """读写失败时向界面提供可理解的错误。"""


class TaskRepository(Protocol):
    def load(self) -> list[Task]: ...
    def save(self, tasks: list[Task]) -> None: ...


class JsonTaskRepository:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self) -> list[Task]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or payload.get("version") != 1:
                raise ValueError("不支持的数据版本")
            if not isinstance(payload.get("tasks"), list):
                raise ValueError("任务列表格式错误")
            tasks = [Task(**item) for item in payload["tasks"]]
            if len({task.id for task in tasks}) != len(tasks):
                raise ValueError("存在重复的任务 ID")
            return tasks
        except FileNotFoundError:
            return []
        except (OSError, ValueError, TypeError) as exc:
            raise StorageError(f"无法读取任务数据，请检查文件：{self.path}\n{exc}") from exc

    def save(self, tasks: list[Task]) -> None:
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                             dir=self.path.parent, suffix=".tmp",
                                             delete=False) as stream:
                temporary = Path(stream.name)
                json.dump({"version": 1, "tasks": [t.to_dict() for t in tasks]},
                          stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except OSError as exc:
            raise StorageError(f"保存失败，原有任务未被覆盖：{exc}") from exc
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
