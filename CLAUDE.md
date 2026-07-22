# MatoryUpperUe — UE UI 自动化框架

## 项目概述

基于 Matory SDK TCP 协议的 Python 自动化框架，支持 UE UI 自动化测试与录制回放。采用 pytest 集成风格 + Page Object 模式。

## 架构：三层分离

```
L1 协议层 (client/)   →  TCP 通信、协议编解码
L2 元素层 (elements/) →  Widget 模型与操作
L3 页面层 (page/)     →  Page Object 模式
```

加上会话管理 (session.py)、录制器 (recorder.py)、pytest 插件 (pytest_plugin.py)。

## 目录约定

- `matory/` — 框架源码，不要放业务逻辑
- `autotests/` — 自动化用例目录
  - `autotests/pages/` — Page Object 定义（每个页面一个文件）
  - `autotests/test_*.py` — 测试用例（按流程分文件）
- `tests/` — 框架自身的单元测试
- 业务用例只放 `autotests/`，不要放 `tests/`

## 代码规范

- Python 3.10+，使用 `from __future__ import annotations`
- 类型注解：所有公开方法加参数和返回值类型
- 链式调用：Widget 交互方法返回 `self`
- 异常：服务端错误抛 `CommandError`，用户判断用 `WidgetNotFoundError` / `ValueError`
- Widget 定位优先用 `id`（O(1)），`name` 次之，`path` 仅调试用
- Page Object 命名不要以 `Test` 开头（避免 pytest 误采集）

## 测试

```bash
# 框架单元测试（无需 UE 实例）
pytest tests/ -k "not test_example" -v

# 自动化用例（需要 UE 实例运行 SDK）
pytest autotests/ --matory-host=127.0.0.1 --matory-port=2666 -v
```

## 协议格式

- 请求：`{"id": <int>, "cmd": "<string>", "args": {<dict>}}\n`
- 响应：`{"id": <int>, "code": <int>, "msg": "<string>", "data": <any>}\n`
- TCP 流以 `\n` 分隔，Connection 内部缓冲处理拆包/粘包

## 关键依赖关系

- Widget → Session（通过 `_session._conn` 通信）
- Session → Connection（TCP 生命周期）
- Page → WidgetDescriptor（描述符延迟绑定 Widget）
- Recorder → Widget._send_cmd（monkey-patch 拦截操作）
- pytest_plugin → Session（fixture 注入）

## 常用操作

查看 UE Widget 树（写 Page Object 前必做）：

```python
from matory import Session
with Session("127.0.0.1", 2666) as s:
    import json
    print(json.dumps(s.get_widget_tree(), indent=2, ensure_ascii=False))
```
