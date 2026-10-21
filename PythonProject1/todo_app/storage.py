"""JSON 存储实现。后续可按 TaskRepository 接口替换成 SQLite。"""
import json
import os
import tempfile
from pathlib import Path
from typing import Protocol

from .migration import task_from_legacy
from .models import Task


class StorageError(Exception):
    """读写失败时向界面提供可理解的错误。"""


class TaskRepository(Protocol):
    def load(self) -> list[Task]: ...
    def save(self, tasks: list[Task]) -> None: ...


class JsonTaskRepository:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._legacy_bytes = None

    def load(self) -> list[Task]:
        try:
            raw = self.path.read_bytes()
            payload = json.loads(raw.decode("utf-8-sig"))
            if isinstance(payload, list):
                tasks = [task_from_legacy(item, index) for index, item in enumerate(payload)]
            else:
                if not isinstance(payload, dict) or type(payload.get("version")) is not int or payload["version"] != 1:
                    raise ValueError("不支持的数据版本")
                if not isinstance(payload.get("tasks"), list):
                    raise ValueError("任务列表格式错误")
                tasks = [Task(**item) for item in payload["tasks"]]
            if len({task.id for task in tasks}) != len(tasks):
                raise ValueError("存在重复的任务 ID")
            self._legacy_bytes = raw if isinstance(payload, list) else None
            return tasks
        except FileNotFoundError:
            self._legacy_bytes = None
            return []
        except (OSError, ValueError, TypeError) as exc:
            raise StorageError(f"无法读取任务数据，请检查文件：{self.path}\n{exc}") from exc

    def save(self, tasks: list[Task]) -> None:
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self._legacy_bytes is not None:
                backup = self.path.with_name(self.path.name + ".legacy.bak")
                # 保留旧格式原始字节；已有备份不覆盖，使用序号区分。
                number = 1
                while True:
                    try:
                        with backup.open("xb") as stream:
                            stream.write(self._legacy_bytes)
                            stream.flush()
                            os.fsync(stream.fileno())
                        break
                    except FileExistsError:
                        if backup.read_bytes() == self._legacy_bytes:
                            break
                        backup = self.path.with_name(f"{self.path.name}.legacy.{number}.bak")
                        number += 1
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                             dir=self.path.parent, suffix=".tmp",
                                             delete=False) as stream:
                temporary = Path(stream.name)
                json.dump({"version": 1, "tasks": [t.to_dict() for t in tasks]},
                          stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            self._legacy_bytes = None
        except OSError as exc:
            raise StorageError(f"保存失败，原有任务未被覆盖：{exc}") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass  # 临时文件清理失败不掩盖真正的保存结果。
