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

```python
from matory import Page, WidgetDescriptor, ButtonWidget

class MainMenu(Page):
    login_btn = WidgetDescriptor(id="LoginBtn", widget_class=ButtonWidget)

    def click_login(self):
        self.login_btn.click()
```

### 2. 编写测试

```python
import pytest

@pytest.mark.ui
def test_login(session):
    page = session.page(MainMenu)
    assert page.login_btn.exists()
    page.click_login()
```

### 3. 运行测试

```bash
pytest --matory-host=127.0.0.1 --matory-port=2666
```

### 4. 录制回放

```python
from matory import Session, Recorder

with Session() as s:
    rec = Recorder(s)
    rec.start()
    # ... 手动或自动操作 ...
    rec.stop()
    rec.generate_code("RecordedPage", "tests/test_recorded.py")
```

## 项目结构

```
matory/
├── client/          # L1: 协议层 (TCP + JSON 编解码)
├── elements/        # L2: 元素层 (Widget 模型与操作)
├── page/            # L3: 页面层 (Page Object 模式)
├── session.py       # 会话管理
├── recorder.py      # 录制器
├── pytest_plugin.py # pytest 插件
└── errors.py        # 异常层次
```
