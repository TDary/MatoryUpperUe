"""联机测试用例 — 多客户端协同。"""

import pytest

from .pages.lobby_page import LobbyPage
from .pages.game_page import GamePage


@pytest.mark.ui
class TestMultiplayer:
    """联机协同测试。"""

    def test_host_create_room(self, game_session):
        """房主创建房间。"""
        host = game_session.page(LobbyPage)
        host.wait_loaded()
        host.create_room()

    def test_client_join_room(self, game_session):
        """客户端加入房间。"""
        host = game_session.page(LobbyPage)
        host.create_room()

        client1 = game_session.page(LobbyPage, connection="client1")
        client1.join_room()

        # TODO: 验证房主看到人数变化

    def test_full_2p_flow(self, game_session):
        """2人联机完整流程：创建 → 加入 → 开始 → 游戏内。"""
        # 房主创建房间
        host = game_session.page(LobbyPage)
        host.wait_loaded()
        host.create_room()

        # 客户端加入
        client1 = game_session.page(LobbyPage, connection="client1")
        client1.join_room()

        # 房主开始游戏
        host.start_game()

        # TODO: 验证双方进入游戏
        # host_game = game_session.page(GamePage)
        # client1_game = game_session.page(GamePage, connection="client1")
        # host_game.wait_loaded()
        # client1_game.wait_loaded()

    def test_n_clients_join(self, game_session):
        """N 个客户端依次加入（数量由 --matory-clients 决定）。"""
        host = game_session.page(LobbyPage)
        host.wait_loaded()
        host.create_room()

        # 动态遍历所有客户端连接
        for conn_key in game_session.list_connections():
            if conn_key == "default":
                continue
            client = game_session.page(LobbyPage, connection=conn_key)
            client.join_room()

        # TODO: 验证房主看到正确人数
