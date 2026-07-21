# MatoryUpperUe — UE UI 自动化框架设计

## 概述

基于现有 MatoryClient TCP 协议，构建 Python 自动化框架，支持 UE UI 自动化测试与录制回放。采用 pytest 集成风格 + Page Object 模式。

## 需求

- **自动化测试**：编写 pytest 测试用例验证 UE UI（按钮点击、文本检查、布局正确性等）
- **录制回放**：录制操作生成 pytest 代码，开发者可编辑和版本管理
- **单连接优先**：一次连接一个 UE 实例，后续可扩展多连接
- **Page Object**：封装每个页面的 Widget 定位和操作，提高复用性

## 架构：三层分离

```
L1 协议层 (client/)   →  TCP 通信、协议编解码
L2 元素层 (elements/) →  Widget 模型与操作
L3 页面层 (page/)     →  Page Object 模式
```

加上会话管理 (session.py)、录制器 (recorder.py)、pytest 插件 (pytest_plugin.py)。

## L1 协议层

### `client/protocol.py` — 协议常量与编解码

- `Cmd` 类：SDK 命令名常量（GetSdkVersion, GetEngineVersion, Disconnect, GetWidgetTree, FindButtons, FindText, WidgetExists, GetWidgetDetail, ClickWidget, PressWidget, ReleaseWidget, SetWidgetEnabled, StartRecord, StopRecord）
- `Method` 类：Widget 查找方式（ID, NAME, PATH）
- `Key` 类：协议 args 键名（METHOD, VALUE, ID, FILTER, KEYWORD, BUTTON, SIMULATE, ENABLED）
- `Button` 类：鼠标按键（LEFT, MIDDLE, RIGHT）
- `encode_request(req_id: int, cmd: str, args: dict) -> bytes`：JSON 序列化 + `\n` 分隔
- `decode_response(line: str) -> dict`：反序列化 + `data` 字段统一解析（处理 str/dict/list 三种情况）

协议格式：
- 请求：`{"id": <int>, "cmd": "<string>", "args": {<dict>}}\n`
- 响应：`{"id": <int>, "code": <int>, "msg": "<string>", "data": <any>}\n`

### `client/connection.py` — TCP 连接管理

- `Connection(host="127.0.0.1", port=2666, timeout=5.0)`：底层 socket 生命周期
- `send(data: bytes) -> None`：发送原始字节
- `recv_line() -> str`：从 TCP 流缓冲中提取完整 `\n` 分隔消息，跨调用保留 `_recv_buf`
- `close()`：关闭连接
- 支持 `with` 语句
- 连接失败抛出 `ConnectionError`

## L2 元素层

### `elements/widget.py` — Widget 基类

```python
class Widget:
    def __init__(self, session: Session, method: str, value: str):
        self._session = session
        self._method = method   # "id" / "name" / "path"
        self._value = value

    # 查询
    def exists(self) -> bool
    def get_detail(self) -> dict

    # 交互
    def click(self, *, simulate: bool = False, button: str = "left") -> Widget
    def press(self, button: str = "left") -> Widget
    def release(self, button: str = "left") -> Widget
    def set_enabled(self, enabled: bool = True) -> Widget

    # 便捷属性
    @property
    def id(self) -> str
    @property
    def name(self) -> str
```

设计要点：
- Widget 通过 session 间接通信，不直接持有连接
- 交互方法返回 self，支持链式调用
- `_method` + `_value` 确定定位方式

### `elements/button.py` — ButtonWidget

- `ButtonWidget(Widget)`：无额外方法，类型标记 + IDE 类型提示

### `elements/text.py` — TextWidget

- `TextWidget(Widget)`：增加 `text` 属性获取显示文本

## L3 页面层

### `page/page.py` — Page 基类 + WidgetDescriptor

```python
class WidgetDescriptor:
    """类属性描述符，延迟绑定 Widget 到 Page 实例。"""
    def __init__(self, method: str, value: str, widget_class: type = Widget):
        self._method = method
        self._value = value
        self._widget_class = widget_class
        self._attr_name = None

    def __set_name__(self, owner, name):
        self._attr_name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        # 首次访问时通过 obj.session 创建 Widget 实例并缓存到 obj.__dict__
        if self._attr_name not in obj.__dict__:
            obj.__dict__[self._attr_name] = self._widget_class(
                obj.session, self._method, self._value
            )
        return obj.__dict__[self._attr_name]

class Page:
    def __init__(self, session: Session):
        self._session = session

    @property
    def session(self) -> Session:
        return self._session
```

使用示例：
```python
class MainMenu(Page):
    login_btn = WidgetDescriptor(method="id", value="LoginBtn", widget_class=ButtonWidget)
    title_text = WidgetDescriptor(method="id", value="TitleLabel", widget_class=TextWidget)
    settings_btn = WidgetDescriptor(method="name", value="SettingsButton")

    def click_login(self):
        self.login_btn.click()
        return self
```

便捷工厂函数：
- `WidgetDescriptor(id="xxx")` 等价于 `WidgetDescriptor(method="id", value="xxx")`
- 即第一个关键字参数名决定 method，value 为参数值

## 会话管理

### `session.py`

```python
class Session:
    def __init__(self, host="127.0.0.1", port=2666, timeout=5.0):
        self._conn = Connection(host, port, timeout)

    # 快捷查询
    def find_button(self, *, id=None, name=None, path=None) -> ButtonWidget
    def find_text(self, *, keyword="", id=None, name=None) -> TextWidget
    def find_widget(self, *, id=None, name=None, path=None) -> Widget
    def get_widget_tree(self) -> dict

    # 版本信息
    def get_sdk_version(self) -> str
    def get_engine_version(self) -> str

    # 页面工厂
    def page(self, page_class: type[Page]) -> Page:
        return page_class(self)

    # 录制
    def start_record(self) -> None
    def stop_record(self) -> dict

    # 生命周期
    def disconnect(self) -> None
    def close(self) -> None
```

Session 内部通过 `self._conn` 发送命令，`find_*` 方法内部调用协议层命令后构造对应 Widget 对象返回。

## 录制器

### `recorder.py`

- `Recorder(session: Session)` 包装 Session，拦截所有 Widget 操作
- 维护操作序列 `_steps: list[Step]`，每个 Step 记录：操作类型、Widget 定位信息、参数
- `start()` / `stop()` — 开始/停止拦截
- `generate_code(class_name: str, output_path: str)` — 将操作序列生成 pytest 测试代码
  - 自动识别相同 Widget 的操作，聚合到 Page Object 中
  - 生成的代码遵循 Page Object + pytest 风格
  - 输出格式：

```python
# Generated by Matory Recorder
from matory import Page, WidgetDescriptor, ButtonWidget
from matory import Session

class RecordedPage(Page):
    btn_login = WidgetDescriptor(id="LoginBtn", widget_class=ButtonWidget)

class TestRecorded:
    def test_recorded_flow(self, session):
        page = session.page(RecordedPage)
        page.btn_login.click(simulate=False)
```

## pytest 插件

### `pytest_plugin.py`

注册为 `pytest11` 入口点，自动激活。

**conftest fixtures**：
- `session` fixture（scope="session"）：自动创建 Session，测试结束后关闭
- `page` fixture：参数化，通过 `--matory-page` 指定 Page 类路径

**CLI 选项**：
- `--matory-host`：UE 服务端地址（默认 127.0.0.1）
- `--matory-port`：UE 服务端端口（默认 2666）
- `--matory-timeout`：连接超时秒数（默认 5.0）

**Markers**：
- `@pytest.mark.ui`：标记 UI 测试用例

## 项目目录结构

```
F:/MatoryUpperUe/
├── matory/                     # 包根
│   ├── __init__.py             # 导出 Session, Widget, Page 等
│   ├── client/
│   │   ├── __init__.py         # 导出 Connection, Cmd, Method, Key, Button
│   │   ├── connection.py       # TCP 连接管理
│   │   └── protocol.py         # 协议常量与编解码
│   ├── elements/
│   │   ├── __init__.py         # 导出 Widget, ButtonWidget, TextWidget
│   │   ├── widget.py           # Widget 基类
│   │   ├── button.py           # ButtonWidget
│   │   └── text.py             # TextWidget
│   ├── page/
│   │   ├── __init__.py         # 导出 Page, WidgetDescriptor
│   │   └── page.py             # Page 基类 + WidgetDescriptor
│   ├── session.py              # 会话管理
│   ├── recorder.py             # 录制器
│   └── pytest_plugin.py        # pytest 插件
├── tests/                      # 测试目录
│   ├── conftest.py             # pytest 配置（注册插件）
│   ├── pages/                  # Page Object 定义
│   │   └── main_menu.py        # 示例 Page
│   └── test_example.py         # 示例测试
├── pyproject.toml              # 项目配置 + pytest11 入口
└── README.md
```

## 依赖

- Python >= 3.10
- pytest >= 7.0（测试运行）
- 无第三方通信依赖（纯 socket）

## 错误处理策略

- `ConnectionError`：连接失败/断开，pytest 报 ERROR 而非 FAIL
- `WidgetNotFoundError`：Widget 定位失败（exists 返回 False），由用户 assert 判断
- `CommandError`：服务端返回 code != 0，包含 code + msg 信息
- 所有异常继承自 `MatoryError` 基类

## 与现有代码的关系

- `test_matory.py` 保留为集成测试/参考文档
- 协议常量从 `test_matory.py` 迁移到 `protocol.py`
- TCP 流缓冲逻辑从 `MatoryClient._recv_buf` 迁移到 `Connection.recv_line()`
- `parse_data_field` 迁移到 `protocol.decode_response`
