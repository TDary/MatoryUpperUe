# MatoryUpperUe

UE UI 自动化测试框架，基于 Matory SDK TCP 协议。

## 特性

- **pytest 集成**：用 pytest 编写和运行 UI 测试
- **Page Object 模式**：WidgetDescriptor 描述符延迟绑定，提高复用性
- **录制回放**：录制操作自动生成 pytest 测试代码
- **链式调用**：`widget.click().set_enabled(False)` 流畅 API

## 安装

```bash
pip install -e ".[test]"
```

## 快速开始

### 1. 编写 Page Object

在 `autotests/pages/` 下定义页面：

```python
# autotests/pages/main_page.py
from matory import Page, WidgetDescriptor, ButtonWidget

class MainPage(Page):
    btn_0 = WidgetDescriptor(id="3", widget_class=ButtonWidget)
    btn_1 = WidgetDescriptor(id="5", widget_class=ButtonWidget)

    def click_btn_0(self):
        self.btn_0.click()
        return self
```

### 2. 编写测试

在 `autotests/` 下编写用例：

```python
# autotests/test_main.py
import pytest
from .pages.main_page import MainPage

@pytest.mark.ui
class TestMainPage:
    def test_button_exists(self, session):
        page = session.page(MainPage)
        assert page.btn_0.exists()

    def test_click_button(self, session):
        page = session.page(MainPage)
        page.btn_0.click()

    def test_sdk_version(self, session):
        assert session.get_sdk_version() == "1.0.0"
```

### 3. 运行测试

```bash
# 运行自动化用例（连接 UE 实例）
pytest autotests/ --matory-host=127.0.0.1 --matory-port=2666 -v

# 运行框架单元测试（无需 UE 实例）
pytest tests/ -k "not test_example" -v
```

### 4. 录制回放

```python
from matory import Session, Recorder

with Session() as s:
    rec = Recorder(s)
    rec.start()
    # ... 手动或自动操作 ...
    rec.stop()
    rec.generate_code("RecordedPage", "autotests/test_recorded.py")
```

## API 参考

### Session

```python
with Session(host="127.0.0.1", port=2666, timeout=5.0) as s:
    s.get_sdk_version()          # → "1.0.0"
    s.get_engine_version()       # → "5.6.1"
    s.get_widget_tree()          # → dict
    s.find_button(id="3")        # → ButtonWidget
    s.find_text(keyword="标题")   # → TextWidget
    s.find_widget(id="99")       # → Widget
    s.page(MainPage)             # → MainPage 实例
    s.start_record()             # 开始录制
    s.stop_record()              # 停止录制 → dict
```

### Widget

```python
widget.exists()                        # → bool
widget.get_detail()                    # → dict
widget.click(simulate=False, button="left")  # → self (链式)
widget.press("left")                   # → self
widget.release("left")                 # → self
widget.set_enabled(True)               # → self
widget.id                              # → str
widget.name                            # → str
```

### WidgetDescriptor

```python
class MyPage(Page):
    # 三种定位方式
    btn  = WidgetDescriptor(id="3", widget_class=ButtonWidget)
    text = WidgetDescriptor(name="TitleLabel", widget_class=TextWidget)
    panel = WidgetDescriptor(path="/Canvas/Panel")
```

## 多页面流程写法

核心思路：**一个页面一个 Page Object** → **`session.page()` 切换页面** → **点击 → 等待/断言 → 下一步**

### 1. 每个页面定义一个 Page Object

```python
# autotests/pages/login_page.py
from matory import Page, WidgetDescriptor, ButtonWidget, TextWidget

class LoginPage(Page):
    login_btn = WidgetDescriptor(id="102", widget_class=ButtonWidget)
    error_text = WidgetDescriptor(id="103", widget_class=TextWidget)

    def wait_loaded(self):
        assert self.login_btn.exists()
        return self

    def login(self):
        self.login_btn.click()
        return self
```

```python
# autotests/pages/lobby_page.py
class LobbyPage(Page):
    enter_room_btn = WidgetDescriptor(id="200", widget_class=ButtonWidget)
    status_text = WidgetDescriptor(id="201", widget_class=TextWidget)
```

### 2. 用 session.page() 串联流程

```python
# autotests/test_login.py
import pytest
from .pages.login_page import LoginPage
from .pages.lobby_page import LobbyPage

@pytest.mark.ui
class TestLoginFlow:
    def test_login_success(self, session):
        # 登录页 → 点击登录
        login = session.page(LoginPage)
        login.wait_loaded()
        login.login()

        # 大厅页 → 验证已进入
        lobby = session.page(LobbyPage)
        assert lobby.status_text.exists()

    def test_full_flow(self, session):
        # 登录
        session.page(LoginPage).login()
        # 大厅 → 进入房间
        session.page(LobbyPage).enter_room_btn.click()
        # 房间 → 开始游戏
        session.page(RoomPage).start_btn.click()
```

### 3. 查 Widget ID

写 Page Object 前先查 UE 里的 Widget：

```python
from matory import Session

with Session("127.0.0.1", 2666) as s:
    import json
    # 查整棵 Widget 树
    print(json.dumps(s.get_widget_tree(), indent=2, ensure_ascii=False))
    # 查某个 Widget 详情
    print(s.find_widget(id="3").get_detail())
```

## 项目结构

```
MatoryUpperUe/
├── matory/                     # 框架包
│   ├── client/                 # L1: 协议层 (TCP + JSON 编解码)
│   │   ├── protocol.py         #   协议常量 + encode/decode
│   │   └── connection.py       #   TCP 连接 + 流缓冲
│   ├── elements/               # L2: 元素层 (Widget 模型与操作)
│   │   ├── widget.py           #   Widget 基类
│   │   ├── button.py           #   ButtonWidget
│   │   └── text.py             #   TextWidget
│   ├── page/                   # L3: 页面层 (Page Object 模式)
│   │   └── page.py             #   Page + WidgetDescriptor
│   ├── session.py              # 会话管理
│   ├── recorder.py             # 录制器
│   ├── pytest_plugin.py        # pytest 插件
│   └── errors.py               # 异常层次
├── autotests/                  # 自动化用例目录
│   ├── pages/                  #   Page Object 定义
│   │   └── main_page.py        #   示例页面
│   ├── test_main.py            #   示例用例
│   └── conftest.py             #   注册 pytest 插件
├── tests/                      # 框架单元测试
├── test_matory.py              # SDK 集成测试脚本
└── pyproject.toml
```
