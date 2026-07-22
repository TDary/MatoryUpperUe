"""联机游戏页面 Page Object。"""

from matory import ButtonWidget, Page, TextWidget, WidgetDescriptor


class LobbyPage(Page):
    """大厅页面 — 房主和客户端共用。"""

    # TODO: 替换为实际 Widget ID
    create_room_btn = WidgetDescriptor(id="TODO", widget_class=ButtonWidget)
    join_room_btn = WidgetDescriptor(id="TODO", widget_class=ButtonWidget)
    start_btn = WidgetDescriptor(id="TODO", widget_class=ButtonWidget)
    player_count = WidgetDescriptor(id="TODO", widget_class=TextWidget)
    status_text = WidgetDescriptor(id="TODO", widget_class=TextWidget)

    def wait_loaded(self):
        """等待大厅页加载完成。"""
        assert self.create_room_btn.exists()
        return self

    def create_room(self):
        """房主创建房间。"""
        self.create_room_btn.click()
        return self

    def join_room(self):
        """客户端加入房间。"""
        self.join_room_btn.click()
        return self

    def enter_room(self):
        """进入房间（join_room 的别名）。"""
        return self.join_room()

    def start_game(self):
        """房主开始游戏。"""
        self.start_btn.click()
        return self
