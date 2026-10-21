# 四人协作约定

> 最终整合版已经接入三份队友提交。实现对应关系和已验证行为见 [INTEGRATION.md](INTEGRATION.md)；以下分工与接口约定继续用于维护。

## 分工

| 成员 | 主要负责 | 主要文件 | 后续任务 |
| --- | --- | --- | --- |
| 你：主体框架负责人 | 目录、启动流程、共享模型、接口、集成 | main.py、models.py、run_todo.py | 审核接口变更，整合各分支 |
| 成员二：界面 | 页面与交互 | ui.py | 视觉优化、未保存编辑提示、键盘操作 |
| 成员三：任务业务 | 增删改查、筛选与扩展 | services.py | 子任务、重复任务、排序扩展 |
| 成员四：数据与质量 | 持久化、测试、异常处理 | storage.py、tests/ | 备份恢复、SQLite 实现、回归测试 |

主体框架提供可运行的最小实现，其他成员可逐步替换各自模块。共享模型、接口签名的改动先在团队沟通，避免同时改动公共文件。

## 调用关系

`run_todo.py → main.py → TodoApp → TaskService → TaskRepository`

`main.py` 负责创建 JSON 仓储、业务服务并注入界面。界面不能直接操作 JSON 文件，仓储不能依赖 Tkinter。这样业务与存储可脱离图形桌面进行测试。

## 数据与接口

`Task` 是不可变数据类，字段：`id, title, notes, category, priority, due_date, completed, created_at`。

- id：UUID 十六进制文本，创建后不能变更。
- title：去除首尾空白后非空，最多 120 字符。
- category：工作、学习、生活；priority：高、中、低。
- due_date：空字符串或严格的 YYYY-MM-DD 日期。
- created_at：本地创建时间 ISO 文本。

仓储接口：`load() -> list[Task]`、`save(tasks: list[Task]) -> None`，读写失败抛出 `StorageError`。

业务接口：

| 方法 | 返回与含义 |
| --- | --- |
| add(title, **fields) | 返回已保存的新任务 |
| get(task_id) | 返回任务；不存在抛出 ValueError |
| update(task_id, **fields) | 返回更新任务，仅允许修改业务字段 |
| toggle(task_id) | 返回切换完成状态后的任务 |
| delete(task_id) | 返回被删除任务，用于撤销 |
| restore(task) | 恢复被删除任务，拒绝重复 ID |
| list_tasks(view, query, category, today) | 日期、优先级排序的筛选结果；today 为测试注入点 |
| stats() | (总数, 已完成数) |
| all_tasks() | 包含已完成任务的稳定列表副本，供 CLI 序号操作使用 |
| save() | 显式保存当前数据，供 CLI 保存退出使用 |

JSON 格式：`{"version": 1, "tasks": [...]}`。后续改格式须同步新增迁移逻辑；不要直接改版本导致旧数据无法读取。

## Git 协作

每人从最新 main 建立自己的功能分支，例如 `feature/ui`、`feature/tasks`、`feature/storage`。只提交自己负责的文件，提交前运行核心测试，合入 main 前进行界面联调。勿提交虚拟环境、个人任务数据、IDE 配置或凭证。

## 集成验收

1. 使用空数据文件启动，显示空状态，三个主要区域布局完整。
2. 添加中文任务，编辑分类、备注、日期和优先级，重启后内容保留。
3. 空标题、无效日期被拒绝，已有数据保持不变。
4. 完成后在已完成中可查看并恢复；删除后可撤销。
5. 搜索、分类、日期边界与逾期任务显示符合 README 约定。
6. 损坏的 JSON 提示错误，原始文件不被覆盖。
7. 核心测试与 Tkinter 集成验证通过。
