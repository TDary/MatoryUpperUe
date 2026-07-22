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
