"""大厅页 Page Object。"""

from matory import ButtonWidget, Page, TextWidget, WidgetDescriptor


class LobbyPage(Page):
    """大厅页面。"""

    # TODO: 替换为实际 Widget ID
    enter_room_btn = WidgetDescriptor(id="TODO", widget_class=ButtonWidget)
    status_text = WidgetDescriptor(id="TODO", widget_class=TextWidget)

    def wait_loaded(self):
        """等待大厅页加载完成。"""
        assert self.enter_room_btn.exists()
        return self

    def enter_room(self):
        """进入房间。"""
        self.enter_room_btn.click()
        return self
