"""Session manager — top-level entry point for Matory framework."""

from __future__ import annotations

from typing import Any

from matory.client.connection import Connection
from matory.client.protocol import Cmd, Key, Method, encode_request, decode_response
from matory.errors import CommandError


class Session:
    """Manages the connection lifecycle and provides high-level query methods."""

    def __init__(self, host: str = "127.0.0.1", port: int = 2666, timeout: float = 5.0) -> None:
        self._conn = Connection(host, port, timeout)
        self._req_id = 0

    def __enter__(self) -> Session:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _next_req_id(self) -> int:
        """Return the next incrementing request ID."""
        self._req_id += 1
        return self._req_id

    def _send_cmd(self, cmd: str, args: dict[str, Any] | None = None) -> dict:
        """Send a raw command and return the parsed response."""
        if args is None:
            args = {}
        data = encode_request(self._next_req_id(), cmd, args)
        self._conn.send(data)
        line = self._conn.recv_line()
        resp = decode_response(line)
        if resp.get("code", 0) != 0:
            raise CommandError(resp.get("code", -1), resp.get("msg", "unknown error"))
        return resp

    def close(self) -> None:
        """Close the connection."""
        self._conn.close()
