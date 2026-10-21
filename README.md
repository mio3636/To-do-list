# 今日清单 · To-do List

四人协作的 Python + Tkinter 桌面项目主体框架。Python 3.10+，无需安装第三方依赖。已接通任务新增、编辑、完成/恢复、删除/撤销、搜索、分类和本地保存，可在此基础上分模块开发。

## 启动

在仓库根目录执行：

```powershell
python PythonProject1/run_todo.py
```

或进入项目目录运行 `python -m todo_app`。系统需包含 Tkinter，Windows 官方 Python 安装程序可勾选 Tcl/Tk 支持。

默认数据文件为用户目录下的 `.today-todo/tasks.json`，首次启动显示空列表。开发时可指定独立文件：

```powershell
python PythonProject1/run_todo.py --data ./data/tasks.json
```

项目启动入口为 `PythonProject1/run_todo.py`。

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
  tests/
    test_core.py          # 核心行为测试
    smoke_ui.py           # 图形界面集成验证
docs/
  COLLABORATION.md         # 四人分工、接口约定、验收清单
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

测试全部使用临时目录，不读写真实任务。JSON 使用临时文件和原子替换写入；加载异常时提示并停止启动，保留原文件。当前定位为单用户、单实例本地应用，不支持多实例同时写入同一数据文件。

重复任务、子任务、自定义分类、云同步与提醒作为后续扩展项，尚未实现。协作约定详见 [四人分工文档](docs/COLLABORATION.md)。
