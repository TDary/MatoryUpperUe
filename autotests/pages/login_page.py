"""登录页 Page Object。"""

from matory import ButtonWidget, Page, TextWidget, WidgetDescriptor


class LoginPage(Page):
    """登录页面。"""

    # TODO: 替换为实际 Widget ID
    login_btn = WidgetDescriptor(id="TODO", widget_class=ButtonWidget)
    error_text = WidgetDescriptor(id="TODO", widget_class=TextWidget)

    def wait_loaded(self):
        """等待登录页加载完成。"""
        assert self.login_btn.exists()
        return self

    def login(self):
        """执行登录操作。"""
        # TODO: 输入账号密码、点击登录等
        self.login_btn.click()
        return self
