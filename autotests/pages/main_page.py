"""测试 UI 主页面。"""

from matory import ButtonWidget, Page, TextWidget, WidgetDescriptor


class MainPage(Page):
    """UE 测试界面的 Page Object。"""

    btn_0 = WidgetDescriptor(id="3", widget_class=ButtonWidget)
    btn_1 = WidgetDescriptor(id="5", widget_class=ButtonWidget)
    btn_2 = WidgetDescriptor(id="7", widget_class=ButtonWidget)
    btn_3 = WidgetDescriptor(id="9", widget_class=ButtonWidget)

    def click_btn_0(self):
        self.btn_0.click()
        return self
