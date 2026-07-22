"""房间页 Page Object。"""

from matory import ButtonWidget, Page, TextWidget, WidgetDescriptor


class RoomPage(Page):
    """房间页面。"""

    # TODO: 替换为实际 Widget ID
    start_btn = WidgetDescriptor(id="TODO", widget_class=ButtonWidget)
    status_text = WidgetDescriptor(id="TODO", widget_class=TextWidget)

    def wait_loaded(self):
        """等待房间页加载完成。"""
        assert self.start_btn.exists()
        return self

    def start_game(self):
        """开始游戏。"""
        self.start_btn.click()
        return self
