"""pytest plugin for Matory UE UI automation framework.

Provides:
- ``session`` fixture (session-scoped)
- CLI options: --matory-host, --matory-port, --matory-timeout
- ``ui`` marker
"""

from __future__ import annotations

import pytest

from matory.session import Session


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("matory", "Matory UE UI automation")
    group.addoption(
        "--matory-host",
        default="127.0.0.1",
        help="Matory UE SDK server host (default: 127.0.0.1)",
    )
    group.addoption(
        "--matory-port",
        type=int,
        default=2666,
        help="Matory UE SDK server port (default: 2666)",
    )
    group.addoption(
        "--matory-timeout",
        type=float,
        default=5.0,
        help="Connection timeout in seconds (default: 5.0)",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "ui: marks tests as UE UI tests")


@pytest.fixture(scope="session")
def session(request: pytest.FixtureRequest) -> Session:
    """Provide a Matory Session connected to the UE SDK server."""
    host = request.config.getoption("--matory-host")
    port = request.config.getoption("--matory-port")
    timeout = request.config.getoption("--matory-timeout")
    s = Session(host, port, timeout)
    yield s
    s.close()
