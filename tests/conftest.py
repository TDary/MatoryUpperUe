"""Shared test fixtures."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from matory.client.connection import Connection


def _make_response(code: int = 0, msg: str = "ok", data=None) -> str:
    """Build a JSON response line as a string."""
    return json.dumps({"id": 1, "code": code, "msg": msg, "data": data})


class MockConnection:
    """A mock Connection that returns pre-configured responses in order."""

    def __init__(self, responses: list[dict[str, Any]] | None = None) -> None:
        self._responses: list[str] = []
        self._sent: list[bytes] = []
        if responses:
            for r in responses:
                self._responses.append(json.dumps(r))

    def add_response(self, code: int = 0, msg: str = "ok", data=None) -> None:
        self._responses.append(_make_response(code, msg, data))

    def send(self, data: bytes) -> None:
        self._sent.append(data)

    def recv_line(self) -> str:
        if not self._responses:
            raise RuntimeError("No more mock responses")
        return self._responses.pop(0)

    def close(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


@pytest.fixture
def mock_conn():
    """Provide a MockConnection instance."""
    return MockConnection()
