"""Tests for TCP Connection."""

import json
from unittest.mock import MagicMock, patch

import pytest

from matory.client.connection import Connection
from matory.client.protocol import encode_request
from matory.errors import MatoryConnectionError


class FakeSocket:
    """A minimal fake socket that returns pre-loaded response data."""

    def __init__(self, responses: list[bytes]):
        self._sent: list[bytes] = []
        self._recv_data = b"".join(responses)
        self._recv_pos = 0
        self.timeout = None
        self.closed = False

    def sendall(self, data: bytes) -> None:
        self._sent.append(data)

    def recv(self, bufsize: int) -> bytes:
        if self._recv_pos >= len(self._recv_data):
            return b""
        chunk = self._recv_data[self._recv_pos : self._recv_pos + bufsize]
        self._recv_pos += len(chunk)
        return chunk

    def settimeout(self, timeout: float) -> None:
        self.timeout = timeout

    def close(self) -> None:
        self.closed = True

    def connect(self, addr: tuple) -> None:
        pass


def _make_response(code: int = 0, msg: str = "ok", data=None) -> bytes:
    """Build a JSON response line as bytes."""
    payload = json.dumps({"id": 1, "code": code, "msg": msg, "data": data}) + "\n"
    return payload.encode("utf-8")


@patch("matory.client.connection.socket.socket")
def test_connection_send_and_recv(mock_socket_cls):
    fake = FakeSocket([_make_response(data="1.0.0")])
    mock_socket_cls.return_value = fake

    conn = Connection("127.0.0.1", 2666, 5.0, auto_reconnect=False)
    data = encode_request(1, "GetSdkVersion", {})
    conn.send(data)
    line = conn.recv_line()
    conn.close()

    assert len(fake._sent) == 1
    resp = json.loads(line)
    assert resp["code"] == 0
    assert fake.closed is True


@patch("matory.client.connection.socket.socket")
def test_connection_context_manager(mock_socket_cls):
    fake = FakeSocket([_make_response(data="1.0.0")])
    mock_socket_cls.return_value = fake

    with Connection("127.0.0.1", 2666, 5.0, auto_reconnect=False) as conn:
        pass

    assert fake.closed is True


@patch("matory.client.connection.socket.socket")
def test_connection_recv_line_buffers_across_calls(mock_socket_cls):
    """TCP may split one message across multiple recv calls."""
    full = _make_response(data="hello")
    part1 = full[:10]
    part2 = full[10:]
    fake = FakeSocket([part1, part2])
    mock_socket_cls.return_value = fake

    conn = Connection("127.0.0.1", 2666, 5.0, auto_reconnect=False)
    line = conn.recv_line()
    conn.close()

    resp = json.loads(line)
    assert resp["data"] == "hello"


@patch("matory.client.connection.socket.socket")
def test_connection_recv_line_two_messages(mock_socket_cls):
    """Two messages in one recv should return the first and buffer the rest."""
    msg1 = _make_response(data="first")
    msg2 = _make_response(data="second")
    fake = FakeSocket([msg1 + msg2])
    mock_socket_cls.return_value = fake

    conn = Connection("127.0.0.1", 2666, 5.0, auto_reconnect=False)
    line1 = conn.recv_line()
    line2 = conn.recv_line()
    conn.close()

    assert json.loads(line1)["data"] == "first"
    assert json.loads(line2)["data"] == "second"


@patch("matory.client.connection.socket.socket")
def test_connection_recv_line_connection_error(mock_socket_cls):
    """Empty recv should raise ConnectionError when auto_reconnect is False."""
    fake = FakeSocket([])
    mock_socket_cls.return_value = fake

    conn = Connection("127.0.0.1", 2666, 5.0, auto_reconnect=False)
    with pytest.raises(MatoryConnectionError):
        conn.recv_line()
    conn.close()


@patch("matory.client.connection.socket.socket")
def test_connection_reconnect_on_recv_failure(mock_socket_cls):
    """Connection should auto-reconnect when recv fails."""
    # First socket: returns empty (connection lost)
    fake1 = FakeSocket([])
    # Second socket: returns valid response after reconnect
    fake2 = FakeSocket([_make_response(data="reconnected")])
    mock_socket_cls.side_effect = [fake1, fake2]

    conn = Connection("127.0.0.1", 2666, 5.0, auto_reconnect=True, max_retries=3)
    line = conn.recv_line()
    conn.close()

    assert json.loads(line)["data"] == "reconnected"


@patch("matory.client.connection.socket.socket")
def test_connection_reconnect_max_retries_exhausted(mock_socket_cls):
    """Should raise ConnectionError after max retries exhausted."""
    fake1 = FakeSocket([])
    # Reconnect attempts all fail (connect raises)
    failing_sock = FakeSocket([])
    failing_sock.connect = lambda addr: (_ for _ in ()).throw(OSError("refused"))
    mock_socket_cls.side_effect = [fake1, failing_sock, failing_sock, failing_sock]

    conn = Connection("127.0.0.1", 2666, 5.0, auto_reconnect=True, max_retries=3, retry_delay=0)
    with pytest.raises(MatoryConnectionError, match="Failed to reconnect"):
        conn.recv_line()
    conn.close()


@patch("matory.client.connection.socket.socket")
def test_connection_auto_reconnect_disabled(mock_socket_cls):
    """When auto_reconnect is False, connection loss raises immediately."""
    fake = FakeSocket([])
    mock_socket_cls.return_value = fake

    conn = Connection("127.0.0.1", 2666, 5.0, auto_reconnect=False)
    with pytest.raises(MatoryConnectionError):
        conn.recv_line()
    conn.close()
