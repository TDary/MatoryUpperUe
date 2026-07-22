"""Session manager — top-level entry point for Matory framework."""

from __future__ import annotations

import logging
from typing import Any, Callable

from matory.client.connection import Connection
from matory.client.protocol import Cmd, Key, Method, encode_request, decode_response
from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.elements.widget import Widget
from matory.errors import CommandError, ConnectionKeyError

logger = logging.getLogger("matory.session")


class Session:
    """Manages the connection lifecycle and provides high-level query methods.

    Supports multiple named connections.  The ``"default"`` connection is
    created automatically on construction; additional connections can be
    added with :meth:`add_connection`.

    Usage::

        with Session("127.0.0.1", 2666) as s:
            btn = s.find_button(id="42")
            btn.click()
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 2666, timeout: float = 5.0) -> None:
        self._connections: dict[str, Connection] = {}
        self._default_key: str = "default"
        self._req_id = 0
        self.add_connection("default", host, port, timeout, set_default=True)

    def __enter__(self) -> Session:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ── Connection registry ──

    def add_connection(self, key: str, host: str = "127.0.0.1", port: int = 2666,
                       timeout: float = 5.0, *, set_default: bool = False) -> None:
        """Create a new named connection and register it.

        Args:
            key: Unique name for this connection.
            host: Server hostname.
            port: Server port.
            timeout: Connection timeout in seconds.
            set_default: If True, make this the default connection.
        """
        self._connections[key] = Connection(host, port, timeout)
        if set_default:
            self._default_key = key

    def remove_connection(self, key: str) -> None:
        """Close and remove a named connection.

        Raises ValueError if attempting to remove the default connection.
        """
        if key == self._default_key:
            raise ValueError("Cannot remove the default connection")
        conn = self._connections.pop(key, None)
        if conn is not None:
            conn.close()

    def list_connections(self) -> list[str]:
        """Return a list of all registered connection keys."""
        return list(self._connections.keys())

    def get_connection(self, key: str | None = None) -> Connection:
        """Return the Connection for *key*, or the default if *key* is None.

        Raises ConnectionKeyError if the key does not exist.
        """
        resolved = key if key is not None else self._default_key
        if resolved not in self._connections:
            raise ConnectionKeyError(resolved, list(self._connections.keys()))
        return self._connections[resolved]

    @property
    def default(self) -> str:
        """The key of the default connection."""
        return self._default_key

    @default.setter
    def default(self, key: str) -> None:
        if key not in self._connections:
            raise ConnectionKeyError(key, list(self._connections.keys()))
        self._default_key = key

    # ── Backward-compatible _conn property ──

    @property
    def _conn(self) -> Connection:
        """The default connection (backward-compatible accessor)."""
        return self._connections[self._default_key]

    @_conn.setter
    def _conn(self, value: Connection) -> None:
        """Set the default connection (backward-compatible mutator).

        Handles the case where ``Session.__new__`` was used (skipping
        ``__init__``) so that ``_connections`` / ``_default_key`` may
        not exist yet.
        """
        if not hasattr(self, "_connections") or self._connections is None:
            self._connections = {}
        if not hasattr(self, "_default_key") or self._default_key is None:
            self._default_key = "default"
        self._connections[self._default_key] = value

    # ── Internal helpers ──

    def _next_req_id(self) -> int:
        """Return the next incrementing request ID."""
        self._req_id += 1
        return self._req_id

    def _send_cmd(self, cmd: str, args: dict[str, Any] | None = None, *,
                  connection: str | None = None) -> dict:
        """Send a raw command and return the parsed response."""
        if args is None:
            args = {}
        conn = self.get_connection(connection)
        conn_key = connection or self._default_key
        logger.debug("[%s] >> cmd=%s args=%s", conn_key, cmd, args)
        data = encode_request(self._next_req_id(), cmd, args)
        conn.send(data)
        line = conn.recv_line()
        resp = decode_response(line)
        if resp.get("code", 0) != 0:
            logger.warning("[%s] << cmd=%s error: code=%s msg=%s", conn_key, cmd, resp.get("code"), resp.get("msg"))
            raise CommandError(resp.get("code", -1), resp.get("msg", "unknown error"))
        logger.debug("[%s] << cmd=%s data=%s", conn_key, cmd, resp.get("data"))
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

    def find_button(self, *, id: str | None = None, name: str | None = None,
                    path: str | None = None, connection: str | None = None) -> ButtonWidget:
        """Find the first button matching the locator.

        Raises ``WidgetNotFoundError`` if no button is found.
        """
        method, value = self._resolve_method_value(id, name, path)
        resp = self._send_cmd(Cmd.FIND_BUTTONS, {Key.METHOD: method, Key.VALUE: value},
                              connection=connection)
        buttons = resp.get("data", [])
        if not isinstance(buttons, list) or not buttons:
            from matory.errors import WidgetNotFoundError
            raise WidgetNotFoundError(method=method, value=value)
        first = buttons[0]
        widget_id = str(first.get("id", value))
        return ButtonWidget(self, Method.ID, widget_id, connection_key=connection)

    def find_text(self, *, keyword: str = "", id: str | None = None,
                  name: str | None = None, connection: str | None = None) -> TextWidget:
        """Find the first text widget matching the query.

        Raises ``WidgetNotFoundError`` if no text widget is found.
        """
        args: dict[str, Any] = {}
        if keyword:
            args[Key.KEYWORD] = keyword
        if id is not None:
            args[Key.METHOD] = Method.ID
            args[Key.VALUE] = id
        elif name is not None:
            args[Key.METHOD] = Method.NAME
            args[Key.VALUE] = name
        resp = self._send_cmd(Cmd.FIND_TEXT, args, connection=connection)
        texts = resp.get("data", [])
        if not isinstance(texts, list) or not texts:
            from matory.errors import WidgetNotFoundError
            raise WidgetNotFoundError(method="keyword", value=keyword)
        first = texts[0]
        widget_id = str(first.get("id", ""))
        return TextWidget(self, Method.ID, widget_id, connection_key=connection)

    def find_widget(self, *, id: str | None = None, name: str | None = None,
                    path: str | None = None, connection: str | None = None) -> Widget:
        """Find a widget by locator."""
        method, value = self._resolve_method_value(id, name, path)
        return Widget(self, method, value, connection_key=connection)

    # ── Page factory ──

    def page(self, page_class: type, *, connection: str | None = None) -> Any:
        """Create a Page Object instance bound to this session."""
        return page_class(self, connection=connection)

    # ── Recording ──

    def start_record(self) -> None:
        """Start UI recording on the server."""
        self._send_cmd(Cmd.START_RECORD, {})

    def stop_record(self) -> dict:
        """Stop UI recording and return the result."""
        resp = self._send_cmd(Cmd.STOP_RECORD, {})
        return resp.get("data", {})

    # ── Wait / Retry ──

    def wait_until(
        self,
        predicate: Callable[..., bool],
        *,
        timeout: float = 10.0,
        interval: float = 0.5,
    ) -> None:
        """Poll until *predicate()* returns True.

        Args:
            predicate: A callable with no required args that returns bool.
            timeout: Maximum seconds to wait (default 10.0).
            interval: Seconds between polls (default 0.5).

        Raises:
            TimeoutError: If the predicate is not satisfied within *timeout*.
        """
        import time
        deadline = time.monotonic() + timeout
        while True:
            try:
                if predicate():
                    return
            except Exception:
                pass
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Session.wait_until timed out after {timeout}s"
                )
            time.sleep(interval)

    # ── Health Check ──

    def is_alive(self, *, connection: str | None = None) -> bool:
        """Check if a connection is alive by sending a lightweight command.

        Returns True if the server responds, False if the connection is dead.
        """
        try:
            self._send_cmd(Cmd.GET_SDK_VERSION, {}, connection=connection)
            return True
        except Exception:
            return False

    # ── Lifecycle ──

    def disconnect(self) -> None:
        """Send Disconnect command on the default connection and close all."""
        exc = None
        try:
            self._send_cmd(Cmd.DISCONNECT, {})
        except Exception as e:
            exc = e
        finally:
            self.close()
        if exc is not None:
            raise exc

    def close(self) -> None:
        """Close all connections without sending Disconnect."""
        for conn in self._connections.values():
            conn.close()
        self._connections.clear()
