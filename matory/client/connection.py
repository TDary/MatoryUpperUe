"""TCP connection management for Matory UE SDK."""

from __future__ import annotations

import logging
import socket
from typing import Any

from matory.errors import ConnectionError

logger = logging.getLogger("matory.connection")


class Connection:
    """Manages a TCP connection to the Matory UE SDK server.

    Handles the newline-delimited JSON protocol with internal stream
    buffering to handle TCP packet fragmentation.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 2666, timeout: float = 5.0) -> None:
        self._host = host
        self._port = port
        self._sock: socket.socket | None = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(timeout)
        self._sock.connect((host, port))
        self._recv_buf = b""
        logger.info("Connected to %s:%d", host, port)

    def __enter__(self) -> Connection:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def send(self, data: bytes) -> None:
        """Send raw bytes over the socket."""
        if self._sock is None:
            raise ConnectionError("Connection closed")
        logger.debug("Send: %s", data.decode("utf-8", errors="replace").strip())
        self._sock.sendall(data)

    def recv_line(self) -> str:
        """Read one complete newline-terminated line from the TCP stream.

        Blocks until a full line (ending with ``\\n``) is available.
        Raises ``ConnectionError`` if the socket is closed before a
        complete line arrives.
        """
        if self._sock is None:
            raise ConnectionError("Connection closed")
        while b"\n" not in self._recv_buf:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("Connection lost")
            self._recv_buf += chunk

        newline_pos = self._recv_buf.index(b"\n")
        line = self._recv_buf[:newline_pos]
        self._recv_buf = self._recv_buf[newline_pos + 1 :]
        decoded = line.decode("utf-8")
        logger.debug("Recv: %s", decoded)
        return decoded

    def close(self) -> None:
        """Close the underlying socket. Safe to call multiple times."""
        if self._sock is not None:
            logger.info("Closing connection to %s:%d", self._host, self._port)
            self._sock.close()
            self._sock = None
