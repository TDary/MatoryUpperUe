"""Shared test fixtures."""

import pytest

from tests.helpers import MockConnection  # noqa: F401 — re-exported for fixture use
from matory.session import Session


def make_session(mock_conn: MockConnection) -> Session:
    """Create a Session backed by a MockConnection (for unit tests only).

    Uses ``Session.__new__()`` to skip the real TCP connect, then
    installs the mock as the default connection.
    """
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0
    session._closed = False
    session._send_hooks = []
    return session


@pytest.fixture
def mock_conn():
    """Provide a MockConnection instance."""
    return MockConnection()
