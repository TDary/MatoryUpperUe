"""自动化用例示例 — 连接真实 UE 实例运行。

运行方式:
    pytest autotests/ --matory-host=127.0.0.1 --matory-port=2666 -v
"""

import pytest

from .pages.main_page import MainPage


@pytest.mark.ui
class TestTestUI:
    """测试 UE 主界面。"""

    def test_sdk_version(self, session):
        version = session.get_sdk_version()
        assert version == "1.0.0"

    def test_engine_version(self, session):
        version = session.get_engine_version()
        assert "5." in version

    def test_button_0_exists(self, session):
        page = session.page(MainPage)
        assert page.btn_0.exists()

    def test_click_button_0(self, session):
        page = session.page(MainPage)
        page.btn_0.click()

    def test_click_button_chain(self, session):
        page = session.page(MainPage)
        page.btn_0.click().set_enabled(True)

    def test_widget_tree_not_empty(self, session):
        tree = session.get_widget_tree()
        assert tree is not None
