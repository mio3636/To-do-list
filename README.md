# 今日清单 · To-do List

四人协作的 To-do List 最终整合版。Python 3.10+，无需安装第三方依赖。整合 Tkinter 桌面框架、队友的六项命令行菜单、任务管理函数、JSON 存储和自动化测试。两种界面共用业务层与数据模型。

## 启动

在仓库根目录执行：

```powershell
python PythonProject1/run_todo.py
```

Windows 也可双击仓库根目录的 `start_todo.cmd` 启动桌面版。

或进入项目目录运行 `python -m todo_app`。系统需包含 Tkinter，Windows 官方 Python 安装程序可勾选 Tcl/Tk 支持。

默认数据文件为用户目录下的 `.today-todo/tasks.json`，首次启动显示空列表。开发时可指定独立文件：

```powershell
python PythonProject1/run_todo.py --data ./data/tasks.json
```

项目启动入口为 `PythonProject1/run_todo.py`。

## 队友的命令行模式

```powershell
python PythonProject1/run_todo.py --cli
```

提供新增、查看全部、完成/恢复、删除、筛选已完成、保存退出六项菜单。优先级支持 1/2/3（高/中/低），分类支持 Study/Work/Leisure（学习/工作/生活）及中文。无效菜单、序号和日期会提示后返回菜单。任务修改立即保存，删除需要确认，筛选结果中的序号保持与全部任务一致。

桌面版和命令行版默认使用同一路径；可切换使用，不要同时运行两个实例操作同一文件。

## 使用队友已有的数据

队友的旧 `tasks.json` 是列表格式，使用 description/status、英文分类和数字优先级。可以指定该文件启动任意一种模式，例如：

```powershell
python PythonProject1/run_todo.py --data "D:\旧项目\tasks.json"
python PythonProject1/run_todo.py --cli --data "D:\旧项目\tasks.json"
```

读取时不会改写源文件；首次保存时自动转换为 version=1 的统一格式，并生成 `tasks.json.legacy.bak` 原始备份。如果同名备份已存在且内容不同，使用带序号的备份文件。缺失的旧任务 ID 会得到稳定 ID，数字 ID 转成文本。

损坏 JSON、非法字段或冲突状态会明确报错并停止读取，原文件保留，不会用空列表覆盖。默认启动不会自动寻找其他目录的旧数据，必须用 `--data` 指定。

## 目录与职责

```text
PythonProject1/
  run_todo.py             # 启动入口
  todo_app/
    main.py               # 参数、依赖装配、应用生命周期
    models.py             # 共享 Task 数据结构、输入校验
    ui.py                 # 三栏布局与事件绑定
    services.py           # 任务操作、筛选、统计
    storage.py            # 仓储接口与 JSON 实现
    migration.py          # 旧格式字段转换与输入归一化
    console.py            # 队友任务函数与六项菜单
  tests/
    test_core.py          # 核心行为测试
    test_console.py       # 命令行与跨界面数据测试
    test_storage.py       # 成员存储测试、迁移和保存失败保护
    smoke_ui.py           # 图形界面集成验证
docs/
  COLLABORATION.md         # 四人分工、接口约定、验收清单
  INTEGRATION.md           # 三份文档的整合映射与最终验收说明
  contributions/          # 三份原始代码文档，仅供追溯，不作为程序执行
```

## 使用

- 左侧选择今天、收集箱、未来 7 天、全部任务、已完成，并可筛选分类。
- 中间输入任务后按 Enter 添加；选择任务后在右侧编辑并点击保存，或按 Ctrl+S。
- 双击任务切换完成状态；Ctrl+N 聚焦快速添加框。
- 今天包含逾期的未完成任务；未来 7 天包含今天及后续 6 天。
- 收集箱展示没有截止日期的未完成任务；全部任务展示所有未完成任务，完成任务在已完成视图查看。
- 今天视图添加的任务默认今天截止，其他视图添加的任务无截止日期。
- 删除需确认，可撤销最近一次删除；关闭程序后不保留撤销记录。
- 详情需要点击保存；切换任务或筛选前请先保存编辑内容。

## 验证

```powershell
python -m unittest discover -s PythonProject1/tests -t PythonProject1 -p "test_*.py" -v
```

图形界面验证需要桌面环境，在 `PythonProject1` 下执行：

```powershell
python -m tests.smoke_ui
```

共 26 项自动化测试，另有 Tkinter 界面集成验证，覆盖添加、编辑、完成、搜索、分类、删除撤销和命令行数据共享。测试全部使用临时目录，不读写真实任务。JSON 使用临时文件和原子替换写入；加载异常时提示并停止启动，保留原文件。当前定位为单用户、单实例本地应用，不支持多实例同时写入同一数据文件。

重复任务、子任务、自定义分类、云同步与提醒尚未实现。协作约定详见 [四人分工文档](docs/COLLABORATION.md)，原始提交与最终实现对应关系详见 [整合说明](docs/INTEGRATION.md)。
