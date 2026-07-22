"""Shared test fixtures."""

import pytest

from tests.helpers import MockConnection  # noqa: F401 — re-exported for fixture use


@pytest.fixture
def mock_conn():
    """Provide a MockConnection instance."""
    return MockConnection()
