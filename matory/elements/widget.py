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
