"""登录流程测试。"""

import pytest

from .pages.login_page import LoginPage


@pytest.mark.ui
class TestLogin:
    """登录相关用例。"""

    def test_login_success(self, session):
        """登录成功。"""
        # TODO: 补充实际逻辑
        login = session.page(LoginPage)
        login.wait_loaded()
        login.login()

    def test_login_failed(self, session):
        """登录失败。"""
        # TODO: 补充错误账号等场景
        pass
