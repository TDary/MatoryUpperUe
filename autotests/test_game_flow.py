"""完整游戏流程测试。"""

import pytest

from .pages.login_page import LoginPage
from .pages.lobby_page import LobbyPage
from .pages.room_page import RoomPage


@pytest.mark.ui
class TestGameFlow:
    """端到端全流程用例。"""

    def test_full_flow(self, session):
        """登录 → 大厅 → 房间 → 开始。"""
        # TODO: 补充实际逻辑和断言
        session.page(LoginPage).login()
        session.page(LobbyPage).enter_room()
        session.page(RoomPage).start_game()
