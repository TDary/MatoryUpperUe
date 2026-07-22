"""大厅流程测试。"""

import pytest

from .pages.lobby_page import LobbyPage


@pytest.mark.ui
class TestLobby:
    """大厅相关用例。"""

    def test_enter_room(self, session):
        """进入房间。"""
        # TODO: 补充实际逻辑
        lobby = session.page(LobbyPage)
        lobby.wait_loaded()
        lobby.enter_room()
