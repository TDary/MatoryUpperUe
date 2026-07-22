"""pytest plugin for Matory UE UI automation framework.

Provides:
- ``session`` fixture (session-scoped, single default connection)
- ``sessions`` fixture (session-scoped, dict of named Sessions)
- CLI options: --matory-host, --matory-port, --matory-timeout, --matory-endpoints
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
    group.addoption(
        "--matory-endpoints",
        action="append",
        default=[],
        metavar="NAME=HOST:PORT",
        help="Additional named endpoints (repeatable), e.g. client=10.0.0.2:2666",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "ui: marks tests as UE UI tests")


@pytest.fixture(scope="session")
def session(request: pytest.FixtureRequest) -> Session:
    """Provide a Matory Session connected to the default UE SDK server."""
    host = request.config.getoption("--matory-host")
    port = request.config.getoption("--matory-port")
    timeout = request.config.getoption("--matory-timeout")
    s = Session(host, port, timeout)

    # Register additional connections from --matory-endpoints
    _register_endpoints(s, request)

    yield s
    s.close()


@pytest.fixture(scope="session")
def sessions(request: pytest.FixtureRequest) -> dict[str, Session]:
    """Provide a dict of named Sessions for multi-UE testing.

    Always contains a ``"default"`` entry (same as the ``session`` fixture).
    Additional entries are created from ``--matory-endpoints`` options.
    """
    host = request.config.getoption("--matory-host")
    port = request.config.getoption("--matory-port")
    timeout = request.config.getoption("--matory-timeout")

    primary = Session(host, port, timeout)
    _register_endpoints(primary, request)

    result: dict[str, Session] = {"default": primary}

    # Create separate Session objects for each additional endpoint
    endpoints = request.config.getoption("--matory-endpoints") or []
    for ep in endpoints:
        try:
            name, addr = ep.split("=", 1)
            ep_host, ep_port_str = addr.rsplit(":", 1)
            ep_port = int(ep_port_str)
        except ValueError:
            raise ValueError(
                f"Invalid --matory-endpoints format: {ep!r}. "
                f"Expected NAME=HOST:PORT (e.g. client=10.0.0.2:2666)"
            )
        secondary = Session(ep_host, ep_port, timeout)
        result[name] = secondary

    yield result

    for s in result.values():
        s.close()


def _register_endpoints(session: Session, request: pytest.FixtureRequest) -> None:
    """Register additional connections on a Session from --matory-endpoints."""
    endpoints = request.config.getoption("--matory-endpoints") or []
    for ep in endpoints:
        try:
            name, addr = ep.split("=", 1)
            ep_host, ep_port_str = addr.rsplit(":", 1)
            ep_port = int(ep_port_str)
        except ValueError:
            raise ValueError(
                f"Invalid --matory-endpoints format: {ep!r}. "
                f"Expected NAME=HOST:PORT (e.g. client=10.0.0.2:2666)"
            )
        session.add_connection(name, ep_host, ep_port)
