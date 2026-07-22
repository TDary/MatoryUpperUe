"""游戏内页面 Page Object。"""

from matory import ButtonWidget, Page, TextWidget, WidgetDescriptor


class GamePage(Page):
    """游戏内页面 — 房主和客户端共用。"""

    # TODO: 替换为实际 Widget ID
    exit_btn = WidgetDescriptor(id="TODO", widget_class=ButtonWidget)
    score_text = WidgetDescriptor(id="TODO", widget_class=TextWidget)
    status_text = WidgetDescriptor(id="TODO", widget_class=TextWidget)

    def wait_loaded(self):
        """等待游戏页面加载完成。"""
        assert self.status_text.exists()
        return self
