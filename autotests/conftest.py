"""Matory 自动化测试 — 自定义 fixture。"""

import pytest
from matory import Session


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("matory", "Matory UE UI automation")
    group.addoption(
        "--matory-clients",
        type=int,
        default=2,
        help="联机客户端数量，默认 2（不含房主）",
    )
    group.addoption(
        "--matory-client-base-port",
        type=int,
        default=2667,
        help="客户端起始端口，默认 2667（房主用 2666，客户端依次 +1）",
    )


@pytest.fixture(scope="session")
def game_session(request: pytest.FixtureRequest) -> Session:
    """联机测试 Session — 房主为默认连接，客户端按数量动态添加。

    用法:
        pytest autotests/test_multiplayer/ --matory-clients=3 --matory-client-base-port=2667

    连接命名:
        default  → 房主 (127.0.0.1:2666)
        client1  → 客户端1 (127.0.0.1:2667)
        client2  → 客户端2 (127.0.0.1:2668)
        ...
    """
    host = request.config.getoption("--matory-host")
    port = request.config.getoption("--matory-port")
    timeout = request.config.getoption("--matory-timeout")

    s = Session(host, port, timeout)

    client_count = request.config.getoption("--matory-clients")
    base_port = request.config.getoption("--matory-client-base-port")

    for i in range(1, client_count + 1):
        s.add_connection(
            f"client{i}",
            host,
            base_port + (i - 1),
        )

    yield s
    s.close()
