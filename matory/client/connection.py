"""TCP connection management for Matory UE SDK."""

from __future__ import annotations

import logging
import socket
import threading
from typing import Any

from matory.errors import MatoryConnectionError

logger = logging.getLogger("matory.connection")


class Connection:
    """Manages a TCP connection to the Matory UE SDK server.

    Handles the newline-delimited JSON protocol with internal stream
    buffering to handle TCP packet fragmentation. Supports automatic
    reconnection and is thread-safe.

    Thread safety: all send/recv operations are protected by an internal
    lock so that multiple threads can share a Connection safely.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 2666,
        timeout: float = 5.0,
        *,
        auto_reconnect: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._auto_reconnect = auto_reconnect
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._sock: socket.socket | None = None
        self._recv_buf = b""
        self._lock = threading.Lock()
        self._connect()

    def _connect(self) -> None:
        """Create a new socket and connect to the server."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self._timeout)
        self._sock.connect((self._host, self._port))
        self._recv_buf = b""
        logger.info("Connected to %s:%d", self._host, self._port)

    def __enter__(self) -> Connection:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _try_reconnect(self) -> None:
        """Attempt to reconnect after a connection loss."""
        if not self._auto_reconnect:
            raise MatoryConnectionError("Connection lost and auto_reconnect is disabled")
        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(
                    "Reconnect attempt %d/%d to %s:%d",
                    attempt, self._max_retries, self._host, self._port,
                )
                self._connect()
                return
            except OSError as e:
                logger.warning("Reconnect attempt %d failed: %s", attempt, e)
                if attempt < self._max_retries:
                    import time
                    time.sleep(self._retry_delay)
        raise MatoryConnectionError(
            f"Failed to reconnect to {self._host}:{self._port} "
            f"after {self._max_retries} attempts"
        )

    def send(self, data: bytes) -> None:
        """Send raw bytes over the socket. Thread-safe."""
        with self._lock:
            self._send_unlocked(data)

    def _send_unlocked(self, data: bytes) -> None:
        """Send raw bytes (caller must hold _lock)."""
        if self._sock is None:
            raise MatoryConnectionError("Connection closed")
        try:
            logger.debug("Send: %s", data.decode("utf-8", errors="replace").strip())
            self._sock.sendall(data)
        except OSError:
            self._try_reconnect()
            self._sock.sendall(data)

    def recv_line(self) -> str:
        """Read one newline-terminated line from the TCP stream. Thread-safe.

        Blocks until a full line (ending with ``\\n``) is available or
        the socket timeout expires.

        Raises:
            MatoryConnectionError: If the connection is lost and reconnection fails.
            TimeoutError: If no complete line arrives within the socket timeout.
        """
        with self._lock:
            return self._recv_line_unlocked()

    def _recv_line_unlocked(self) -> str:
        """Read one line (caller must hold _lock).

        Limits reconnection attempts within a single recv_line call to
        avoid infinite loops when the server keeps dropping connections.
        """
        if self._sock is None:
            raise MatoryConnectionError("Connection closed")
        reconnect_attempts = 0
        max_recv_reconnects = self._max_retries
        while b"\n" not in self._recv_buf:
            try:
                chunk = self._sock.recv(4096)
            except socket.timeout:
                raise TimeoutError(
                    f"recv_line timed out after {self._timeout}s "
                    f"waiting for response from {self._host}:{self._port}"
                )
            except OSError:
                chunk = b""
            if not chunk:
                reconnect_attempts += 1
                if reconnect_attempts > max_recv_reconnects:
                    raise MatoryConnectionError(
                        f"Connection to {self._host}:{self._port} lost "
                        f"after {max_recv_reconnects} reconnection attempts"
                    )
                self._try_reconnect()
                continue
            reconnect_attempts = 0  # reset on successful recv
            self._recv_buf += chunk

        newline_pos = self._recv_buf.index(b"\n")
        line = self._recv_buf[:newline_pos]
        self._recv_buf = self._recv_buf[newline_pos + 1 :]
        decoded = line.decode("utf-8")
        logger.debug("Recv: %s", decoded)
        return decoded

    def send_and_recv(self, data: bytes) -> str:
        """Send data and receive one response line atomically. Thread-safe.

        This is the preferred method for request-response communication
        as it holds the lock across both send and recv, preventing other
        threads from interleaving their requests.
        """
        with self._lock:
            self._send_unlocked(data)
            return self._recv_line_unlocked()

    def close(self) -> None:
        """Close the underlying socket. Safe to call multiple times."""
        with self._lock:
            if self._sock is not None:
                logger.info("Closing connection to %s:%d", self._host, self._port)
                self._sock.close()
                self._sock = None
