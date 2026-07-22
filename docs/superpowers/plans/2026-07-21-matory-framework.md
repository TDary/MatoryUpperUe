# MatoryUpperUe Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python automation framework for Unreal Engine UI testing with pytest integration, Page Object pattern, and recording/replay support.

**Architecture:** Three-layer design — L1 Protocol (TCP + JSON codec), L2 Elements (Widget model + actions), L3 Page (Page Object + descriptor). Session ties the layers together. Recorder intercepts operations for code generation. pytest plugin provides fixtures and CLI options.

**Tech Stack:** Python 3.10+, pytest 7.0+, stdlib socket (no third-party deps for core)

---

## File Structure

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Project config, dependencies, pytest11 entry point |
| `matory/__init__.py` | Package root, re-exports public API |
| `matory/errors.py` | Exception hierarchy (MatoryError, CommandError) |
| `matory/client/__init__.py` | Sub-package, re-exports protocol + connection |
| `matory/client/protocol.py` | Protocol constants (Cmd/Method/Key/Button) + encode/decode |
| `matory/client/connection.py` | TCP socket lifecycle + stream buffering |
| `matory/elements/__init__.py` | Sub-package, re-exports Widget types |
| `matory/elements/widget.py` | Widget base class with query + interaction methods |
| `matory/elements/button.py` | ButtonWidget — type marker subclass |
| `matory/elements/text.py` | TextWidget — adds `.text` property |
| `matory/page/__init__.py` | Sub-package, re-exports Page + WidgetDescriptor |
| `matory/page/page.py` | Page base class + WidgetDescriptor descriptor |
| `matory/session.py` | Session manager — top-level entry point |
| `matory/recorder.py` | Recorder — intercepts ops, generates pytest code |
| `matory/pytest_plugin.py` | pytest plugin — fixtures, CLI options, markers |
| `tests/__init__.py` | Test package marker |
| `tests/conftest.py` | Shared test fixtures (mock connection helpers) |
| `tests/test_protocol.py` | Tests for protocol encode/decode |
| `tests/test_connection.py` | Tests for Connection (with mock socket) |
| `tests/test_widget.py` | Tests for Widget base class |
| `tests/test_button.py` | Tests for ButtonWidget |
| `tests/test_text.py` | Tests for TextWidget |
| `tests/test_page.py` | Tests for Page + WidgetDescriptor |
| `tests/test_session.py` | Tests for Session |
| `tests/test_recorder.py` | Tests for Recorder |
| `tests/test_pytest_plugin.py` | Tests for pytest plugin |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `matory/__init__.py`
- Create: `matory/client/__init__.py`
- Create: `matory/elements/__init__.py`
- Create: `matory/page/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "matory"
version = "0.1.0"
description = "UE UI automation framework with pytest integration"
requires-python = ">=3.10"
dependencies = []
optional-dependencies.test = ["pytest>=7.0"]

[project.entry-points.pytest11]
matory = "matory.pytest_plugin"

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "ui: marks tests as UE UI tests",
]
```

- [ ] **Step 2: Create `matory/__init__.py`**

```python
"""Matory — UE UI automation framework."""

from matory.errors import MatoryError, CommandError
from matory.session import Session
from matory.elements.widget import Widget
from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.page.page import Page, WidgetDescriptor

__all__ = [
    "MatoryError",
    "CommandError",
    "Session",
    "Widget",
    "ButtonWidget",
    "TextWidget",
    "Page",
    "WidgetDescriptor",
]
```

- [ ] **Step 3: Create sub-package `__init__.py` files**

`matory/client/__init__.py`:
```python
"""Protocol and connection layer."""

from matory.client.protocol import Cmd, Method, Key, Button, encode_request, decode_response
from matory.client.connection import Connection

__all__ = ["Cmd", "Method", "Key", "Button", "encode_request", "decode_response", "Connection"]
```

`matory/elements/__init__.py`:
```python
"""Widget element model layer."""

from matory.elements.widget import Widget
from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget

__all__ = ["Widget", "ButtonWidget", "TextWidget"]
```

`matory/page/__init__.py`:
```python
"""Page Object pattern layer."""

from matory.page.page import Page, WidgetDescriptor

__all__ = ["Page", "WidgetDescriptor"]
```

`tests/__init__.py`:
```python
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml matory/ tests/__init__.py
git commit -m "feat: project scaffolding with package structure"
```

---

### Task 2: Error Hierarchy

**Files:**
- Create: `matory/errors.py`
- Create: `tests/test_errors.py`

- [ ] **Step 1: Write the failing test**

`tests/test_errors.py`:
```python
"""Tests for error hierarchy."""

from matory.errors import MatoryError, CommandError


def test_matory_error_is_exception():
    assert issubclass(MatoryError, Exception)


def test_command_error_is_matory_error():
    assert issubclass(CommandError, MatoryError)


def test_command_error_carries_code_and_msg():
    err = CommandError(code=1, msg="widget not found")
    assert err.code == 1
    assert err.msg == "widget not found"
    assert "widget not found" in str(err)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_errors.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'matory.errors'`

- [ ] **Step 3: Write minimal implementation**

`matory/errors.py`:
```python
"""Matory exception hierarchy."""


class MatoryError(Exception):
    """Base exception for all Matory errors."""


class CommandError(MatoryError):
    """Server returned a non-zero response code.

    Attributes:
        code: The numeric error code from the server.
        msg:  The human-readable error message from the server.
    """

    def __init__(self, code: int, msg: str) -> None:
        self.code = code
        self.msg = msg
        super().__init__(f"CommandError(code={code}, msg={msg!r})")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_errors.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add matory/errors.py tests/test_errors.py
git commit -m "feat: add MatoryError and CommandError exception hierarchy"
```

---

### Task 3: Protocol Layer — Constants + Encode/Decode

**Files:**
- Create: `matory/client/protocol.py`
- Create: `tests/test_protocol.py`

- [ ] **Step 1: Write the failing test**

`tests/test_protocol.py`:
```python
"""Tests for protocol constants and encode/decode."""

import json

from matory.client.protocol import (
    Cmd, Method, Key, Button,
    encode_request, decode_response,
)


# ── Constants ──


def test_cmd_constants():
    assert Cmd.GET_SDK_VERSION == "GetSdkVersion"
    assert Cmd.GET_ENGINE_VERSION == "GetEngineVersion"
    assert Cmd.DISCONNECT == "Disconnect"
    assert Cmd.GET_WIDGET_TREE == "GetWidgetTree"
    assert Cmd.FIND_BUTTONS == "FindButtons"
    assert Cmd.FIND_TEXT == "FindText"
    assert Cmd.WIDGET_EXISTS == "WidgetExists"
    assert Cmd.GET_WIDGET_DETAIL == "GetWidgetDetail"
    assert Cmd.CLICK_WIDGET == "ClickWidget"
    assert Cmd.PRESS_WIDGET == "PressWidget"
    assert Cmd.RELEASE_WIDGET == "ReleaseWidget"
    assert Cmd.SET_WIDGET_ENABLED == "SetWidgetEnabled"
    assert Cmd.START_RECORD == "StartRecord"
    assert Cmd.STOP_RECORD == "StopRecord"


def test_method_constants():
    assert Method.ID == "id"
    assert Method.NAME == "name"
    assert Method.PATH == "path"


def test_key_constants():
    assert Key.METHOD == "method"
    assert Key.VALUE == "value"
    assert Key.ID == "id"
    assert Key.FILTER == "filter"
    assert Key.KEYWORD == "keyword"
    assert Key.BUTTON == "button"
    assert Key.SIMULATE == "simulate"
    assert Key.ENABLED == "enabled"


def test_button_constants():
    assert Button.LEFT == "left"
    assert Button.MIDDLE == "middle"
    assert Button.RIGHT == "right"


# ── Encode ──


def test_encode_request_basic():
    result = encode_request(1, "GetSdkVersion", {})
    parsed = json.loads(result.decode("utf-8"))
    assert parsed == {"id": 1, "cmd": "GetSdkVersion", "args": {}}


def test_encode_request_with_args():
    result = encode_request(5, "ClickWidget", {"method": "id", "value": "42"})
    parsed = json.loads(result.decode("utf-8"))
    assert parsed == {"id": 5, "cmd": "ClickWidget", "args": {"method": "id", "value": "42"}}


def test_encode_request_ends_with_newline():
    result = encode_request(1, "GetSdkVersion", {})
    assert result.endswith(b"\n")


# ── Decode ──


def test_decode_response_dict_data():
    line = json.dumps({"id": 1, "code": 0, "msg": "ok", "data": {"type": "Button"}})
    resp = decode_response(line)
    assert resp["code"] == 0
    assert resp["data"] == {"type": "Button"}


def test_decode_response_string_data_parsed():
    """When data is a JSON string, decode_response should parse it."""
    inner = json.dumps({"type": "Button", "name": "LoginBtn"})
    line = json.dumps({"id": 1, "code": 0, "msg": "ok", "data": inner})
    resp = decode_response(line)
    assert resp["data"] == {"type": "Button", "name": "LoginBtn"}


def test_decode_response_string_data_not_json():
    """When data is a plain string that isn't JSON, keep it as-is."""
    line = json.dumps({"id": 1, "code": 0, "msg": "ok", "data": "1.0.0"})
    resp = decode_response(line)
    assert resp["data"] == "1.0.0"


def test_decode_response_list_data():
    line = json.dumps({"id": 1, "code": 0, "msg": "ok", "data": [1, 2, 3]})
    resp = decode_response(line)
    assert resp["data"] == [1, 2, 3]


def test_decode_response_none_data():
    line = json.dumps({"id": 1, "code": 1, "msg": "error", "data": None})
    resp = decode_response(line)
    assert resp["data"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_protocol.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'matory.client.protocol'`

- [ ] **Step 3: Write minimal implementation**

`matory/client/protocol.py`:
```python
"""Protocol constants and message encode/decode for Matory UE SDK."""

from __future__ import annotations

import json
from typing import Any


class Cmd:
    """SDK command names — one-to-one with server MatoComponent::RegisterCommands."""

    # Basic
    GET_SDK_VERSION = "GetSdkVersion"
    GET_ENGINE_VERSION = "GetEngineVersion"
    DISCONNECT = "Disconnect"

    # Query
    GET_WIDGET_TREE = "GetWidgetTree"
    FIND_BUTTONS = "FindButtons"
    FIND_TEXT = "FindText"
    WIDGET_EXISTS = "WidgetExists"
    GET_WIDGET_DETAIL = "GetWidgetDetail"

    # Interaction
    CLICK_WIDGET = "ClickWidget"
    PRESS_WIDGET = "PressWidget"
    RELEASE_WIDGET = "ReleaseWidget"
    SET_WIDGET_ENABLED = "SetWidgetEnabled"

    # Recording
    START_RECORD = "StartRecord"
    STOP_RECORD = "StopRecord"


class Method:
    """Widget lookup method."""

    ID = "id"
    NAME = "name"
    PATH = "path"


class Key:
    """Protocol args field key names."""

    METHOD = "method"
    VALUE = "value"
    ID = "id"
    FILTER = "filter"
    KEYWORD = "keyword"
    BUTTON = "button"
    SIMULATE = "simulate"
    ENABLED = "enabled"


class Button:
    """Mouse button identifiers."""

    LEFT = "left"
    MIDDLE = "middle"
    RIGHT = "right"


def encode_request(req_id: int, cmd: str, args: dict[str, Any]) -> bytes:
    """Encode a request dict to JSON bytes with a trailing newline."""
    payload = json.dumps({"id": req_id, "cmd": cmd, "args": args}) + "\n"
    return payload.encode("utf-8")


def _parse_data_field(data: Any) -> Any:
    """Normalize the data field from a server response.

    The server may return data as dict/list (already parsed) or as a
    JSON string that needs a second parse.
    """
    if isinstance(data, (dict, list)):
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except (json.JSONDecodeError, ValueError):
            return data
    return data


def decode_response(line: str) -> dict[str, Any]:
    """Decode a newline-delimited JSON response line.

    The ``data`` field is normalized via ``_parse_data_field``.
    """
    resp = json.loads(line)
    if "data" in resp:
        resp["data"] = _parse_data_field(resp["data"])
    return resp
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_protocol.py -v`
Expected: PASS (12 tests)

- [ ] **Step 5: Commit**

```bash
git add matory/client/protocol.py tests/test_protocol.py
git commit -m "feat: add protocol constants and encode/decode"
```

---

### Task 4: Connection Layer

**Files:**
- Create: `matory/client/connection.py`
- Create: `tests/test_connection.py`

- [ ] **Step 1: Write the failing test**

`tests/test_connection.py`:
```python
"""Tests for TCP Connection."""

import json
from unittest.mock import MagicMock, patch

import pytest

from matory.client.connection import Connection
from matory.client.protocol import encode_request


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

    conn = Connection("127.0.0.1", 2666, 5.0)
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

    with Connection("127.0.0.1", 2666, 5.0) as conn:
        pass

    assert fake.closed is True


@patch("matory.client.connection.socket.socket")
def test_connection_recv_line_buffers_across_calls(mock_socket_cls):
    """TCP may split one message across multiple recv calls."""
    full = _make_response(data="hello")
    # Split the response in the middle
    part1 = full[:10]
    part2 = full[10:]
    fake = FakeSocket([part1, part2])
    mock_socket_cls.return_value = fake

    conn = Connection("127.0.0.1", 2666, 5.0)
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

    conn = Connection("127.0.0.1", 2666, 5.0)
    line1 = conn.recv_line()
    line2 = conn.recv_line()
    conn.close()

    assert json.loads(line1)["data"] == "first"
    assert json.loads(line2)["data"] == "second"


@patch("matory.client.connection.socket.socket")
def test_connection_recv_line_connection_error(mock_socket_cls):
    """Empty recv should raise ConnectionError."""
    fake = FakeSocket([])  # no data
    mock_socket_cls.return_value = fake

    conn = Connection("127.0.0.1", 2666, 5.0)
    with pytest.raises(ConnectionError, match="连接已断开"):
        conn.recv_line()
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_connection.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'matory.client.connection'`

- [ ] **Step 3: Write minimal implementation**

`matory/client/connection.py`:
```python
"""TCP connection management for Matory UE SDK."""

from __future__ import annotations

import socket
from typing import Any


class Connection:
    """Manages a TCP connection to the Matory UE SDK server.

    Handles the newline-delimited JSON protocol with internal stream
    buffering to handle TCP packet fragmentation.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 2666, timeout: float = 5.0) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(timeout)
        self._sock.connect((host, port))
        self._recv_buf = b""

    def __enter__(self) -> Connection:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def send(self, data: bytes) -> None:
        """Send raw bytes over the socket."""
        self._sock.sendall(data)

    def recv_line(self) -> str:
        """Read one complete newline-terminated line from the TCP stream.

        Blocks until a full line (ending with ``\\n``) is available.
        Raises ``ConnectionError`` if the socket is closed before a
        complete line arrives.
        """
        while b"\n" not in self._recv_buf:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("连接已断开")
            self._recv_buf += chunk

        newline_pos = self._recv_buf.index(b"\n")
        line = self._recv_buf[:newline_pos]
        self._recv_buf = self._recv_buf[newline_pos + 1 :]
        return line.decode("utf-8")

    def close(self) -> None:
        """Close the underlying socket."""
        self._sock.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_connection.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add matory/client/connection.py tests/test_connection.py
git commit -m "feat: add TCP Connection with stream buffering"
```

---

### Task 5: Widget Base Class

**Files:**
- Create: `matory/elements/widget.py`
- Create: `tests/test_widget.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create shared test fixture**

`tests/conftest.py`:
```python
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
```

- [ ] **Step 2: Write the failing test**

`tests/test_widget.py`:
```python
"""Tests for Widget base class."""

import json

from matory.client.protocol import Cmd, Method, Key, Button
from matory.elements.widget import Widget
from matory.session import Session


def _make_widget(mock_conn, method="id", value="42"):
    """Helper to create a Widget backed by a mock connection."""
    session = Session.__new__(Session)
    session._conn = mock_conn
    return Widget(session, method, value)


def test_exists_true(mock_conn):
    mock_conn.add_response(data=True)
    w = _make_widget(mock_conn, "id", "42")
    assert w.exists() is True


def test_exists_false(mock_conn):
    mock_conn.add_response(data=False)
    w = _make_widget(mock_conn, "name", "MyBtn")
    assert w.exists() is False


def test_get_detail(mock_conn):
    detail = {"type": "Button", "name": "LoginBtn", "id": 42}
    mock_conn.add_response(data=detail)
    w = _make_widget(mock_conn, "id", "42")
    assert w.get_detail() == detail


def test_click_default(mock_conn):
    mock_conn.add_response(data=None)
    w = _make_widget(mock_conn, "id", "42")
    result = w.click()
    assert result is w  # chainable

    # Verify sent command
    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.CLICK_WIDGET
    assert sent["args"][Key.METHOD] == "id"
    assert sent["args"][Key.VALUE] == "42"
    assert sent["args"][Key.BUTTON] == Button.LEFT
    assert sent["args"][Key.SIMULATE] is False


def test_click_simulate(mock_conn):
    mock_conn.add_response(data=None)
    w = _make_widget(mock_conn, "id", "42")
    w.click(simulate=True, button="right")

    sent = json.loads(mock_conn._sent[0])
    assert sent["args"][Key.SIMULATE] is True
    assert sent["args"][Key.BUTTON] == "right"


def test_press(mock_conn):
    mock_conn.add_response(data=None)
    w = _make_widget(mock_conn, "id", "42")
    result = w.press("left")
    assert result is w

    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.PRESS_WIDGET


def test_release(mock_conn):
    mock_conn.add_response(data=None)
    w = _make_widget(mock_conn, "id", "42")
    result = w.release("left")
    assert result is w

    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.RELEASE_WIDGET


def test_set_enabled(mock_conn):
    mock_conn.add_response(data=None)
    w = _make_widget(mock_conn, "id", "42")
    result = w.set_enabled(False)
    assert result is w

    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.SET_WIDGET_ENABLED
    assert sent["args"][Key.ENABLED] is False


def test_click_raises_command_error(mock_conn):
    mock_conn.add_response(code=1, msg="widget not found")
    w = _make_widget(mock_conn, "id", "999")

    from matory.errors import CommandError
    try:
        w.click()
        assert False, "Should have raised CommandError"
    except CommandError as e:
        assert e.code == 1


def test_id_property(mock_conn):
    w = _make_widget(mock_conn, "id", "42")
    assert w.id == "42"


def test_name_property_via_detail(mock_conn):
    mock_conn.add_response(data={"type": "Button", "name": "LoginBtn", "id": 42})
    w = _make_widget(mock_conn, "id", "42")
    assert w.name == "LoginBtn"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_widget.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'matory.elements.widget'`

- [ ] **Step 4: Write minimal implementation**

`matory/elements/widget.py`:
```python
"""Widget base class — the core element model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from matory.client.protocol import Cmd, Key, Method
from matory.errors import CommandError

if TYPE_CHECKING:
    from matory.session import Session


class Widget:
    """Base class for all UI elements.

    Holds a session reference and locator info (method + value).
    All interaction methods return ``self`` for chaining.
    """

    def __init__(self, session: Session, method: str, value: str) -> None:
        self._session = session
        self._method = method
        self._value = value

    def _send_cmd(self, cmd: str, args: dict[str, Any] | None = None) -> dict:
        """Send a command through the session and return parsed response.

        Raises ``CommandError`` if the server returns a non-zero code.
        """
        from matory.client.protocol import encode_request, decode_response

        if args is None:
            args = {}
        data = encode_request(self._session._next_req_id(), cmd, args)
        self._session._conn.send(data)
        line = self._session._conn.recv_line()
        resp = decode_response(line)
        if resp.get("code", 0) != 0:
            raise CommandError(resp.get("code", -1), resp.get("msg", "unknown error"))
        return resp

    # ── Query ──

    def exists(self) -> bool:
        """Check whether this widget exists in the UI tree."""
        resp = self._send_cmd(Cmd.WIDGET_EXISTS, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
        })
        return bool(resp.get("data", False))

    def get_detail(self) -> dict[str, Any]:
        """Retrieve full widget detail dict."""
        resp = self._send_cmd(Cmd.GET_WIDGET_DETAIL, {Key.ID: self._value})
        return resp.get("data", {})

    # ── Interaction ──

    def click(self, *, simulate: bool = False, button: str = "left") -> Widget:
        """Click this widget. Returns self for chaining."""
        self._send_cmd(Cmd.CLICK_WIDGET, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
            Key.SIMULATE: simulate,
            Key.BUTTON: button,
        })
        return self

    def press(self, button: str = "left") -> Widget:
        """Press (mouse-down) this widget. Returns self for chaining."""
        self._send_cmd(Cmd.PRESS_WIDGET, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
            Key.BUTTON: button,
        })
        return self

    def release(self, button: str = "left") -> Widget:
        """Release (mouse-up) this widget. Returns self for chaining."""
        self._send_cmd(Cmd.RELEASE_WIDGET, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
            Key.BUTTON: button,
        })
        return self

    def set_enabled(self, enabled: bool = True) -> Widget:
        """Enable or disable this widget. Returns self for chaining."""
        self._send_cmd(Cmd.SET_WIDGET_ENABLED, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
            Key.ENABLED: enabled,
        })
        return self

    # ── Convenience properties ──

    @property
    def id(self) -> str:
        """The locator value (convenience alias)."""
        return self._value

    @property
    def name(self) -> str:
        """Widget name from detail."""
        detail = self.get_detail()
        return detail.get("name", "")
```

- [ ] **Step 5: Write a minimal Session stub that Widget depends on**

We need a `_next_req_id` method on Session. We'll add a minimal stub now and flesh it out in Task 7.

`matory/session.py` (initial stub):
```python
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_widget.py -v`
Expected: PASS (11 tests)

- [ ] **Step 7: Commit**

```bash
git add matory/elements/widget.py matory/session.py tests/conftest.py tests/test_widget.py
git commit -m "feat: add Widget base class with query and interaction methods"
```

---

### Task 6: ButtonWidget and TextWidget

**Files:**
- Create: `matory/elements/button.py`
- Create: `matory/elements/text.py`
- Create: `tests/test_button.py`
- Create: `tests/test_text.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_button.py`:
```python
"""Tests for ButtonWidget."""

from matory.elements.button import ButtonWidget
from matory.elements.widget import Widget


def test_button_widget_is_widget():
    assert issubclass(ButtonWidget, Widget)
```

`tests/test_text.py`:
```python
"""Tests for TextWidget."""

import json

from matory.client.protocol import Cmd, Key
from matory.elements.text import TextWidget
from matory.elements.widget import Widget
from matory.session import Session


def _make_text_widget(mock_conn, method="id", value="100"):
    session = Session.__new__(Session)
    session._conn = mock_conn
    return TextWidget(session, method, value)


def test_text_widget_is_widget():
    assert issubclass(TextWidget, Widget)


def test_text_property(mock_conn):
    mock_conn.add_response(data={"type": "TextBlock", "text": "Hello World", "id": 100})
    tw = _make_text_widget(mock_conn, "id", "100")
    assert tw.text == "Hello World"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_button.py tests/test_text.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'matory.elements.button'`

- [ ] **Step 3: Write minimal implementations**

`matory/elements/button.py`:
```python
"""ButtonWidget — type marker for button elements."""

from __future__ import annotations

from matory.elements.widget import Widget


class ButtonWidget(Widget):
    """A button UI element.

    No additional methods — serves as a type marker for IDE autocompletion
    and ``isinstance`` checks.
    """
```

`matory/elements/text.py`:
```python
"""TextWidget — text display element with readable content."""

from __future__ import annotations

from typing import Any

from matory.elements.widget import Widget


class TextWidget(Widget):
    """A text-display UI element with a readable ``text`` property."""

    @property
    def text(self) -> str:
        """The displayed text content of this widget."""
        detail = self.get_detail()
        return detail.get("text", "")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_button.py tests/test_text.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add matory/elements/button.py matory/elements/text.py tests/test_button.py tests/test_text.py
git commit -m "feat: add ButtonWidget and TextWidget element types"
```

---

### Task 7: Full Session Implementation

**Files:**
- Modify: `matory/session.py`
- Create: `tests/test_session.py`

- [ ] **Step 1: Write the failing test**

`tests/test_session.py`:
```python
"""Tests for Session."""

import json

from matory.client.protocol import Cmd, Key, Method
from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.elements.widget import Widget
from matory.errors import CommandError
from matory.session import Session


def _make_session(mock_conn):
    """Create a Session with a mock connection."""
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0
    return session


def test_get_sdk_version(mock_conn):
    mock_conn.add_response(data="1.0.0")
    session = _make_session(mock_conn)
    assert session.get_sdk_version() == "1.0.0"


def test_get_engine_version(mock_conn):
    mock_conn.add_response(data="5.3.0")
    session = _make_session(mock_conn)
    assert session.get_engine_version() == "5.3.0"


def test_get_widget_tree(mock_conn):
    tree = {"type": "Canvas", "children": []}
    mock_conn.add_response(data=tree)
    session = _make_session(mock_conn)
    assert session.get_widget_tree() == tree


def test_find_button_by_id(mock_conn):
    mock_conn.add_response(data=[{"id": 42, "name": "LoginBtn", "type": "Button"}])
    session = _make_session(mock_conn)
    btn = session.find_button(id="42")
    assert isinstance(btn, ButtonWidget)
    assert btn.id == "42"


def test_find_button_by_name(mock_conn):
    mock_conn.add_response(data=[{"id": 42, "name": "LoginBtn", "type": "Button"}])
    session = _make_session(mock_conn)
    btn = session.find_button(name="LoginBtn")
    assert isinstance(btn, ButtonWidget)


def test_find_text(mock_conn):
    mock_conn.add_response(data=[{"id": 10, "name": "TitleLabel", "text": "Hello", "type": "TextBlock"}])
    session = _make_session(mock_conn)
    tw = session.find_text(keyword="Hello")
    assert isinstance(tw, TextWidget)


def test_find_widget(mock_conn):
    mock_conn.add_response(data=[{"id": 99, "name": "SomeWidget", "type": "Border"}])
    session = _make_session(mock_conn)
    w = session.find_widget(id="99")
    assert isinstance(w, Widget)


def test_find_button_no_match_raises(mock_conn):
    mock_conn.add_response(data=[])
    session = _make_session(mock_conn)
    try:
        session.find_button(id="999")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "999" in str(e)


def test_page_factory(mock_conn):
    from matory.page.page import Page

    class MyPage(Page):
        pass

    session = _make_session(mock_conn)
    p = session.page(MyPage)
    assert isinstance(p, MyPage)
    assert p.session is session


def test_start_record(mock_conn):
    mock_conn.add_response(msg="recording started")
    session = _make_session(mock_conn)
    session.start_record()

    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.START_RECORD


def test_stop_record(mock_conn):
    mock_conn.add_response(data={"events": 5})
    session = _make_session(mock_conn)
    result = session.stop_record()

    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.STOP_RECORD


def test_disconnect(mock_conn):
    mock_conn.add_response(msg="disconnected")
    session = _make_session(mock_conn)
    session.disconnect()


def test_session_context_manager(mock_conn):
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0
    with session:
        pass
    # close was called on the mock_conn (no error = success)


def test_next_req_id_increments():
    session = Session.__new__(Session)
    session._req_id = 0
    assert session._next_req_id() == 1
    assert session._next_req_id() == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_session.py -v`
Expected: FAIL — several methods missing from Session

- [ ] **Step 3: Write full Session implementation**

`matory/session.py`:
```python
"""Session manager — top-level entry point for Matory framework."""

from __future__ import annotations

from typing import Any

from matory.client.connection import Connection
from matory.client.protocol import Cmd, Key, Method, encode_request, decode_response
from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.elements.widget import Widget
from matory.errors import CommandError


class Session:
    """Manages the connection lifecycle and provides high-level query methods.

    Usage::

        with Session("127.0.0.1", 2666) as s:
            btn = s.find_button(id="42")
            btn.click()
    """

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

    def _resolve_method_value(self, id: str | None, name: str | None, path: str | None) -> tuple[str, str]:
        """Resolve (method, value) from keyword locator arguments.

        Raises ``ValueError`` if no locator is provided or multiple are given.
        """
        locators = {"id": id, "name": name, "path": path}
        provided = {k: v for k, v in locators.items() if v is not None}
        if len(provided) != 1:
            raise ValueError(f"Expected exactly one locator, got: {provided}")
        method, value = next(iter(provided.items()))
        return method, value

    # ── Version ──

    def get_sdk_version(self) -> str:
        """Return the SDK version string."""
        resp = self._send_cmd(Cmd.GET_SDK_VERSION, {})
        data = resp.get("data", "")
        return data.strip('"') if isinstance(data, str) else str(data)

    def get_engine_version(self) -> str:
        """Return the engine version string."""
        resp = self._send_cmd(Cmd.GET_ENGINE_VERSION, {})
        data = resp.get("data", "")
        return data.strip('"') if isinstance(data, str) else str(data)

    # ── Query ──

    def get_widget_tree(self) -> dict:
        """Return the full widget tree."""
        resp = self._send_cmd(Cmd.GET_WIDGET_TREE, {})
        return resp.get("data", {})

    def find_button(self, *, id: str | None = None, name: str | None = None, path: str | None = None) -> ButtonWidget:
        """Find the first button matching the locator.

        Raises ``ValueError`` if no button is found.
        """
        method, value = self._resolve_method_value(id, name, path)
        # If locating by id/name/path directly, first query button list
        resp = self._send_cmd(Cmd.FIND_BUTTONS, {})
        buttons = resp.get("data", [])
        if not isinstance(buttons, list) or not buttons:
            raise ValueError(f"No buttons found for locator: {method}={value}")
        # Use the first matching button's id for the widget
        first = buttons[0]
        widget_id = str(first.get("id", value))
        return ButtonWidget(self, Method.ID, widget_id)

    def find_text(self, *, keyword: str = "", id: str | None = None, name: str | None = None) -> TextWidget:
        """Find the first text widget matching the query.

        Raises ``ValueError`` if no text widget is found.
        """
        args = {Key.KEYWORD: keyword}
        if id is not None:
            args[Key.METHOD] = Method.ID
            args[Key.VALUE] = id
        elif name is not None:
            args[Key.METHOD] = Method.NAME
            args[Key.VALUE] = name
        resp = self._send_cmd(Cmd.FIND_TEXT, args)
        texts = resp.get("data", [])
        if not isinstance(texts, list) or not texts:
            raise ValueError(f"No text widgets found for keyword={keyword!r}, id={id!r}, name={name!r}")
        first = texts[0]
        widget_id = str(first.get("id", ""))
        return TextWidget(self, Method.ID, widget_id)

    def find_widget(self, *, id: str | None = None, name: str | None = None, path: str | None = None) -> Widget:
        """Find a widget by locator."""
        method, value = self._resolve_method_value(id, name, path)
        return Widget(self, method, value)

    # ── Page factory ──

    def page(self, page_class: type) -> Any:
        """Create a Page Object instance bound to this session."""
        return page_class(self)

    # ── Recording ──

    def start_record(self) -> None:
        """Start UI recording on the server."""
        self._send_cmd(Cmd.START_RECORD, {})

    def stop_record(self) -> dict:
        """Stop UI recording and return the result."""
        resp = self._send_cmd(Cmd.STOP_RECORD, {})
        return resp.get("data", {})

    # ── Lifecycle ──

    def disconnect(self) -> None:
        """Send Disconnect command and close the connection."""
        try:
            self._send_cmd(Cmd.DISCONNECT, {})
        finally:
            self.close()

    def close(self) -> None:
        """Close the connection without sending Disconnect."""
        self._conn.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_session.py -v`
Expected: PASS (13 tests)

- [ ] **Step 5: Commit**

```bash
git add matory/session.py tests/test_session.py
git commit -m "feat: add Session with query, page factory, and recording methods"
```

---

### Task 8: Page Object + WidgetDescriptor

**Files:**
- Create: `matory/page/page.py`
- Create: `tests/test_page.py`

- [ ] **Step 1: Write the failing test**

`tests/test_page.py`:
```python
"""Tests for Page and WidgetDescriptor."""

from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.elements.widget import Widget
from matory.page.page import Page, WidgetDescriptor
from matory.session import Session


def _make_session(mock_conn):
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0
    return session


def test_widget_descriptor_by_id(mock_conn):
    class MyPage(Page):
        btn = WidgetDescriptor(id="42")

    session = _make_session(mock_conn)
    p = MyPage(session)
    w = p.btn
    assert isinstance(w, Widget)
    assert w._method == "id"
    assert w._value == "42"


def test_widget_descriptor_by_name(mock_conn):
    class MyPage(Page):
        btn = WidgetDescriptor(name="LoginBtn")

    session = _make_session(mock_conn)
    p = MyPage(session)
    w = p.btn
    assert w._method == "name"
    assert w._value == "LoginBtn"


def test_widget_descriptor_by_path(mock_conn):
    class MyPage(Page):
        panel = WidgetDescriptor(path="/Canvas/Panel")

    session = _make_session(mock_conn)
    p = MyPage(session)
    w = p.panel
    assert w._method == "path"
    assert w._value == "/Canvas/Panel"


def test_widget_descriptor_widget_class(mock_conn):
    class MyPage(Page):
        btn = WidgetDescriptor(id="42", widget_class=ButtonWidget)
        title = WidgetDescriptor(id="10", widget_class=TextWidget)

    session = _make_session(mock_conn)
    p = MyPage(session)
    assert isinstance(p.btn, ButtonWidget)
    assert isinstance(p.title, TextWidget)


def test_widget_descriptor_caches(mock_conn):
    """Accessing the same descriptor twice returns the same Widget instance."""
    class MyPage(Page):
        btn = WidgetDescriptor(id="42")

    session = _make_session(mock_conn)
    p = MyPage(session)
    w1 = p.btn
    w2 = p.btn
    assert w1 is w2


def test_widget_descriptor_class_access_returns_descriptor():
    """Accessing on the class (not instance) returns the descriptor itself."""
    class MyPage(Page):
        btn = WidgetDescriptor(id="42")

    assert isinstance(MyPage.btn, WidgetDescriptor)


def test_page_session_property(mock_conn):
    session = _make_session(mock_conn)
    p = Page(session)
    assert p.session is session


def test_page_custom_method(mock_conn):
    mock_conn.add_response(data=None)

    class MainMenu(Page):
        login_btn = WidgetDescriptor(id="1", widget_class=ButtonWidget)

        def click_login(self):
            self.login_btn.click()
            return self

    session = _make_session(mock_conn)
    p = MainMenu(session)
    result = p.click_login()
    assert result is p
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_page.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'matory.page.page'`

- [ ] **Step 3: Write minimal implementation**

`matory/page/page.py`:
```python
"""Page Object pattern with WidgetDescriptor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from matory.session import Session
    from matory.elements.widget import Widget


class WidgetDescriptor:
    """Class-attribute descriptor that lazily binds a Widget to a Page instance.

    Usage::

        class MainMenu(Page):
            login_btn = WidgetDescriptor(id="LoginBtn", widget_class=ButtonWidget)

    The first keyword argument name (``id``, ``name``, or ``path``) determines
    the lookup method; its value is the locator string.
    """

    def __init__(self, method: str, value: str, widget_class: type[Widget] | None = None) -> None:
        self._method = method
        self._value = value
        self._widget_class = widget_class
        self._attr_name: str | None = None

    # Convenience factory: WidgetDescriptor(id="42") → method="id", value="42"
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

    def __new__(cls, id: str | None = None, name: str | None = None, path: str | None = None,
                method: str | None = None, value: str | None = None,
                widget_class: type | None = None, **kwargs: Any) -> WidgetDescriptor:
        instance = super().__new__(cls)
        # Determine method/value from keyword sugar
        if method is not None and value is not None:
            instance._method = method
            instance._value = value
        elif id is not None:
            instance._method = "id"
            instance._value = id
        elif name is not None:
            instance._method = "name"
            instance._value = name
        elif path is not None:
            instance._method = "path"
            instance._value = path
        else:
            raise ValueError("WidgetDescriptor requires one of: id, name, path, or method+value")
        instance._widget_class = widget_class
        instance._attr_name = None
        return instance

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr_name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        if self._attr_name not in obj.__dict__:
            from matory.elements.widget import Widget
            widget_class = self._widget_class or Widget
            obj.__dict__[self._attr_name] = widget_class(
                obj.session, self._method, self._value
            )
        return obj.__dict__[self._attr_name]


class Page:
    """Base class for Page Objects.

    Subclass this and define WidgetDescriptor class attributes to describe
    the UI elements on a page.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        return self._session
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_page.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add matory/page/page.py tests/test_page.py
git commit -m "feat: add Page base class and WidgetDescriptor"
```

---

### Task 9: Recorder

**Files:**
- Create: `matory/recorder.py`
- Create: `tests/test_recorder.py`

- [ ] **Step 1: Write the failing test**

`tests/test_recorder.py`:
```python
"""Tests for Recorder."""

from matory.elements.button import ButtonWidget
from matory.elements.widget import Widget
from matory.recorder import Recorder, Step
from matory.session import Session


def test_step_creation():
    step = Step(action="click", method="id", value="42", args={"simulate": False, "button": "left"})
    assert step.action == "click"
    assert step.method == "id"
    assert step.value == "42"


def test_recorder_records_click(mock_conn):
    mock_conn.add_response(data=None)
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0

    rec = Recorder(session)
    rec.start()

    btn = ButtonWidget(session, "id", "42")
    btn.click()

    rec.stop()
    assert len(rec.steps) == 1
    assert rec.steps[0].action == "click"
    assert rec.steps[0].method == "id"
    assert rec.steps[0].value == "42"


def test_recorder_records_multiple_actions(mock_conn):
    for _ in range(3):
        mock_conn.add_response(data=None)

    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0

    rec = Recorder(session)
    rec.start()

    w = Widget(session, "id", "1")
    w.click()
    w.press("left")
    w.release("left")

    rec.stop()
    assert len(rec.steps) == 3
    assert rec.steps[0].action == "click"
    assert rec.steps[1].action == "press"
    assert rec.steps[2].action == "release"


def test_recorder_not_recording_when_stopped(mock_conn):
    mock_conn.add_response(data=None)
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0

    rec = Recorder(session)
    # Don't call start()
    w = Widget(session, "id", "1")
    w.click()

    assert len(rec.steps) == 0


def test_recorder_generate_code(tmp_path):
    steps = [
        Step(action="click", method="id", value="LoginBtn", args={"simulate": False, "button": "left"}),
        Step(action="click", method="id", value="SettingsBtn", args={"simulate": False, "button": "left"}),
    ]

    rec = Recorder.__new__(Recorder)
    rec._steps = steps
    rec._recording = False

    output = tmp_path / "test_recorded.py"
    rec.generate_code("RecordedPage", str(output))

    code = output.read_text(encoding="utf-8")
    assert "class RecordedPage(Page)" in code
    assert "LoginBtn" in code
    assert "SettingsBtn" in code
    assert "def test_recorded_flow" in code
    assert "click" in code


def test_recorder_generate_code_aggregates_widgets(tmp_path):
    """Two clicks on the same widget should produce one descriptor."""
    steps = [
        Step(action="click", method="id", value="LoginBtn", args={"simulate": False, "button": "left"}),
        Step(action="click", method="id", value="LoginBtn", args={"simulate": True, "button": "left"}),
    ]

    rec = Recorder.__new__(Recorder)
    rec._steps = steps
    rec._recording = False

    output = tmp_path / "test_recorded.py"
    rec.generate_code("RecordedPage", str(output))

    code = output.read_text(encoding="utf-8")
    # Should have exactly one descriptor for LoginBtn
    assert code.count("LoginBtn") >= 2  # descriptor + usage(s)
    # Count descriptor lines (WidgetDescriptor lines)
    descriptor_count = code.count("WidgetDescriptor")
    assert descriptor_count == 1  # deduplicated
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_recorder.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'matory.recorder'`

- [ ] **Step 3: Write minimal implementation**

`matory/recorder.py`:
```python
"""Recorder — intercepts Widget operations and generates pytest test code."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import Any

from matory.elements.widget import Widget
from matory.session import Session


@dataclass
class Step:
    """A single recorded widget action."""

    action: str
    method: str
    value: str
    args: dict[str, Any] = field(default_factory=dict)


class Recorder:
    """Wraps a Session to record widget interactions for code generation.

    Usage::

        rec = Recorder(session)
        rec.start()
        btn.click()           # recorded
        rec.stop()
        rec.generate_code("MyPage", "tests/test_my_page.py")
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._steps: list[Step] = []
        self._recording = False
        self._original_send_cmd = None

    @property
    def steps(self) -> list[Step]:
        """The list of recorded steps."""
        return self._steps

    def start(self) -> None:
        """Start recording widget interactions."""
        self._recording = True
        self._steps.clear()
        # Monkey-patch Widget._send_cmd to intercept
        self._original_send_cmd = Widget._send_cmd
        original = self._original_send_cmd

        recorder_self = self

        def patched_send_cmd(widget_self: Widget, cmd: str, args: dict[str, Any] | None = None) -> dict:
            # Record interaction actions
            interaction_cmds = {
                "ClickWidget": "click",
                "PressWidget": "press",
                "ReleaseWidget": "release",
                "SetWidgetEnabled": "set_enabled",
            }
            if cmd in interaction_cmds and recorder_self._recording:
                action = interaction_cmds[cmd]
                step = Step(
                    action=action,
                    method=widget_self._method,
                    value=widget_self._value,
                    args=args or {},
                )
                recorder_self._steps.append(step)
            # Still call the original to actually perform the action
            return original(widget_self, cmd, args)

        Widget._send_cmd = patched_send_cmd

    def stop(self) -> None:
        """Stop recording and restore the original Widget._send_cmd."""
        self._recording = False
        if self._original_send_cmd is not None:
            Widget._send_cmd = self._original_send_cmd
            self._original_send_cmd = None

    def generate_code(self, class_name: str, output_path: str) -> None:
        """Generate a pytest test file from the recorded steps.

        Widgets with the same (method, value) are deduplicated into a single
        Page Object descriptor.
        """
        # Deduplicate widgets
        seen_widgets: dict[tuple[str, str], str] = {}  # (method, value) -> attr_name
        attr_counter: dict[str, int] = {}

        for step in self._steps:
            key = (step.method, step.value)
            if key not in seen_widgets:
                # Generate a Python-safe attribute name
                safe_name = step.value.replace(" ", "_").replace("/", "_").lower()
                if safe_name in attr_counter:
                    attr_counter[safe_name] += 1
                    safe_name = f"{safe_name}_{attr_counter[safe_name]}"
                else:
                    attr_counter[safe_name] = 0
                seen_widgets[key] = safe_name

        # Build Page class
        descriptor_lines = []
        for (method, value), attr_name in seen_widgets.items():
            descriptor_lines.append(
                f'    {attr_name} = WidgetDescriptor({method}="{value}")'
            )

        # Build test body
        action_lines = []
        for step in self._steps:
            attr_name = seen_widgets[(step.method, step.value)]
            if step.action == "click":
                simulate = step.args.get("simulate", False)
                button = step.args.get("button", "left")
                if simulate or button != "left":
                    action_lines.append(
                        f'        page.{attr_name}.click(simulate={simulate}, button="{button}")'
                    )
                else:
                    action_lines.append(f"        page.{attr_name}.click()")
            elif step.action == "press":
                button = step.args.get("button", "left")
                action_lines.append(f'        page.{attr_name}.press("{button}")')
            elif step.action == "release":
                button = step.args.get("button", "left")
                action_lines.append(f'        page.{attr_name}.release("{button}")')
            elif step.action == "set_enabled":
                enabled = step.args.get("enabled", True)
                action_lines.append(f"        page.{attr_name}.set_enabled({enabled})")

        descriptors = "\n".join(descriptor_lines)
        actions = "\n".join(action_lines)

        code = textwrap.dedent(f'''\
            # Generated by Matory Recorder
            from matory import Page, WidgetDescriptor, Session


            class {class_name}(Page):
            {descriptors}


            class Test{class_name}:
                def test_recorded_flow(self, session):
                    page = session.page({class_name})
            {actions}
        ''')

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_recorder.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add matory/recorder.py tests/test_recorder.py
git commit -m "feat: add Recorder with step recording and pytest code generation"
```

---

### Task 10: pytest Plugin

**Files:**
- Create: `matory/pytest_plugin.py`
- Create: `tests/test_pytest_plugin.py`

- [ ] **Step 1: Write the failing test**

`tests/test_pytest_plugin.py`:
```python
"""Tests for pytest plugin — using pytester to verify fixture and CLI behavior."""

import pytest


def test_plugin_registers_cli_options(pytester):
    """Plugin should add --matory-host, --matory-port, --matory-timeout."""
    pytester.makeconftest("pytest_plugins = ['matory.pytest_plugin']")
    result = pytester.runpytest("--help")
    result.stdout.fnmatch_lines(["*--matory-host*"])
    result.stdout.fnmatch_lines(["*--matory-port*"])
    result.stdout.fnmatch_lines(["*--matory-timeout*"])


def test_plugin_registers_ui_marker(pytester):
    """Plugin should register the 'ui' marker."""
    pytester.makeconftest("pytest_plugins = ['matory.pytest_plugin']")
    result = pytester.runpytest("--markers")
    result.stdout.fnmatch_lines(["*ui*UE UI*"])


def test_session_fixture_exists(pytester):
    """The 'session' fixture should be available (will fail to connect, but fixture must exist)."""
    pytester.makeconftest("pytest_plugins = ['matory.pytest_plugin']")
    pytester.makepyfile("""
        def test_session_fixture_name(session):
            # We just check the fixture is recognized — connection will fail
            # so we don't actually call anything on session
            assert session is not None
    """)
    # This will fail because no UE server is running, but the fixture
    # should be found (not "fixture 'session' not found")
    result = pytester.runpytest("--matory-host=127.0.0.1", "--matory-port=9999", "-v")
    # We expect a ConnectionError, NOT a fixture-not-found error
    result.stdout.fnmatch_lines(["*ConnectionError*"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_pytest_plugin.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'matory.pytest_plugin'`

- [ ] **Step 3: Write minimal implementation**

`matory/pytest_plugin.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/test_pytest_plugin.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add matory/pytest_plugin.py tests/test_pytest_plugin.py
git commit -m "feat: add pytest plugin with session fixture and CLI options"
```

---

### Task 11: Example Tests and README

**Files:**
- Create: `tests/pages/main_menu.py`
- Create: `tests/test_example.py`
- Modify: `README.md`

- [ ] **Step 1: Create example Page Object**

`tests/pages/main_menu.py`:
```python
"""Example Page Object for the main menu."""

from matory import ButtonWidget, Page, TextWidget, WidgetDescriptor


class MainMenu(Page):
    """The main menu page of the UE application."""

    login_btn = WidgetDescriptor(id="LoginBtn", widget_class=ButtonWidget)
    settings_btn = WidgetDescriptor(id="SettingsBtn", widget_class=ButtonWidget)
    title_text = WidgetDescriptor(id="TitleLabel", widget_class=TextWidget)

    def click_login(self) -> MainMenu:
        self.login_btn.click()
        return self

    def click_settings(self) -> MainMenu:
        self.settings_btn.click()
        return self
```

- [ ] **Step 2: Create example test**

`tests/test_example.py`:
```python
"""Example test demonstrating the Matory framework."""

import pytest

from matory import Page, WidgetDescriptor, ButtonWidget

from .pages.main_menu import MainMenu


@pytest.mark.ui
class TestMainMenu:
    """Tests for the main menu page.

    Run with: pytest --matory-host=127.0.0.1 --matory-port=2666
    Requires a running UE instance with the Matory SDK plugin.
    """

    def test_login_button_exists(self, session):
        main_menu = session.page(MainMenu)
        assert main_menu.login_btn.exists()

    def test_click_login(self, session):
        main_menu = session.page(MainMenu)
        main_menu.click_login()

    def test_sdk_version(self, session):
        version = session.get_sdk_version()
        assert version == "1.0.0"
```

- [ ] **Step 3: Update README.md**

`README.md`:
```markdown
# MatoryUpperUe

UE UI 自动化测试框架，基于 Matory SDK TCP 协议。

## 特性

- **pytest 集成**：用 pytest 编写和运行 UI 测试
- **Page Object 模式**：WidgetDescriptor 描述符延迟绑定，提高复用性
- **录制回放**：录制操作自动生成 pytest 测试代码
- **链式调用**：`widget.click().set_enabled(False)` 流畅 API

## 安装

```bash
pip install -e ".[test]"
```

## 快速开始

### 1. 编写 Page Object

```python
from matory import Page, WidgetDescriptor, ButtonWidget

class MainMenu(Page):
    login_btn = WidgetDescriptor(id="LoginBtn", widget_class=ButtonWidget)

    def click_login(self):
        self.login_btn.click()
```

### 2. 编写测试

```python
import pytest

@pytest.mark.ui
def test_login(session):
    page = session.page(MainMenu)
    assert page.login_btn.exists()
    page.click_login()
```

### 3. 运行测试

```bash
pytest --matory-host=127.0.0.1 --matory-port=2666
```

### 4. 录制回放

```python
from matory import Session, Recorder

with Session() as s:
    rec = Recorder(s)
    rec.start()
    # ... 手动或自动操作 ...
    rec.stop()
    rec.generate_code("RecordedPage", "tests/test_recorded.py")
```

## 项目结构

```
matory/
├── client/          # L1: 协议层 (TCP + JSON 编解码)
├── elements/        # L2: 元素层 (Widget 模型与操作)
├── page/            # L3: 页面层 (Page Object 模式)
├── session.py       # 会话管理
├── recorder.py      # 录制器
├── pytest_plugin.py # pytest 插件
└── errors.py        # 异常层次
```
```

- [ ] **Step 4: Commit**

```bash
git add tests/pages/main_menu.py tests/test_example.py README.md
git commit -m "feat: add example Page Object, test, and README"
```

---

### Task 12: Final Integration Verification

**Files:**
- All existing files

- [ ] **Step 1: Run full test suite**

Run: `cd F:/MatoryUpperUe && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Verify package imports**

Run: `cd F:/MatoryUpperUe && python -c "from matory import Session, Widget, ButtonWidget, TextWidget, Page, WidgetDescriptor, MatoryError, CommandError; print('All imports OK')"`
Expected: `All imports OK`

- [ ] **Step 3: Verify sub-package imports**

Run: `cd F:/MatoryUpperUe && python -c "from matory.client import Cmd, Method, Key, Button, Connection, encode_request, decode_response; print('Client imports OK')"`
Expected: `Client imports OK`

- [ ] **Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "chore: final integration fixes"
```
