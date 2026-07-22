# MatoryUpperUe — UE UI 自动化框架

## 项目概述

基于 Matory SDK TCP 协议的 Python 自动化框架，支持 UE UI 自动化测试与录制回放。采用 pytest 集成风格 + Page Object 模式。支持多连接同时操控多个 UE 实例。

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
  - `autotests/test_multiplayer.py` — 联机协同用例（用 game_session fixture）
- `tests/` — 框架自身的单元测试
- 业务用例只放 `autotests/`，不要放 `tests/`
- 单 UE 用例用 `session` fixture，多 UE 联机用 `game_session` fixture

## 代码规范

- Python 3.10+，使用 `from __future__ import annotations`
- 类型注解：所有公开方法加参数和返回值类型
- 链式调用：Widget 交互方法返回 `self`
- 异常层次：`MatoryError` → `CommandError` / `WidgetNotFoundError` / `ConnectionKeyError`
- Widget 定位优先用 `id`（O(1)），`name` 次之，`path` 仅调试用
- Page Object 命名不要以 `Test` 开头（避免 pytest 误采集）
- Widget 所有通信通过 `session._send_cmd()`，不在 Widget 内重复实现
- 多连接：Widget 通过 `_connection_key` 路由到指定连接，默认走 Session 默认连接
- 日志：框架使用 Python `logging`（logger `matory.session` / `matory.connection`），Session 支持可选 `log_file` 参数写文件

## 多连接设计

- Session 持有 `_connections: dict[str, Connection]` 注册表，默认 key 为 `"default"`
- `add_connection(key, host, port)` 添加命名连接
- Widget/WidgetDescriptor/Page 可选 `connection` 参数指定连接
- 连接解析优先级：描述符 `connection=` > 页面 `connection=` > Session 默认
- 所有现有代码无需改动（默认连接自动选中）

## 测试

```bash
# 框架单元测试（无需 UE 实例）
pytest tests/ -k "not test_example" -v

# 单 UE 自动化用例
pytest autotests/ --matory-host=127.0.0.1 --matory-port=2666 -v

# 多 UE 联机用例
pytest autotests/test_multiplayer.py --matory-clients=4 --matory-client-base-port=2667 -v

# pytest 多端点（通用方式）
pytest autotests/ --matory-endpoints client=10.0.0.2:2666 -v

# 带文件日志
pytest autotests/ --matory-host=127.0.0.1 --matory-port=2666 --matory-log-file=matory.log -v
```

## 协议格式

- 请求：`{"id": <int>, "cmd": "<string>", "args": {<dict>}}\n`
- 响应：`{"id": <int>, "code": <int>, "msg": "<string>", "data": <any>}\n`
- TCP 流以 `\n` 分隔，Connection 内部缓冲处理拆包/粘包

## 关键依赖关系

- Widget → Session._send_cmd(connection=)（所有通信统一走 Session，可指定连接）
- Session → Connection 注册表（多连接管理，默认 key "default"）
- Page → WidgetDescriptor（描述符延迟绑定 Widget，可指定连接）
- Recorder → Session._send_cmd()（实例级拦截，录制连接信息）
- pytest_plugin → Session（fixture 注入，支持 --matory-endpoints）

## 常用操作

查看 UE Widget 树（写 Page Object 前必做）：

```python
from matory import Session
with Session("127.0.0.1", 2666) as s:
    import json
    print(json.dumps(s.get_widget_tree(), indent=2, ensure_ascii=False))
```

多连接协同测试：

```python
with Session("127.0.0.1", 2666) as s:
    s.add_connection("client", "10.0.0.2", 2666)
    host_btn = s.find_button(id="3")                        # 默认连接
    client_btn = s.find_button(id="3", connection="client") # client 连接
```
