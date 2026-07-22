"""Widget base class — the core element model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from matory.client.protocol import Cmd, Key

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

    # ── Query ──

    def exists(self) -> bool:
        """Check whether this widget exists in the UI tree."""
        resp = self._session._send_cmd(Cmd.WIDGET_EXISTS, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
        })
        return bool(resp.get("data", False))

    def get_detail(self) -> dict[str, Any]:
        """Retrieve full widget detail dict.

        Note: This command requires the widget to be located by ID.
        Widgets returned by ``find_button`` and ``find_text`` are
        automatically converted to ID-based locators.
        """
        resp = self._session._send_cmd(Cmd.GET_WIDGET_DETAIL, {Key.ID: self._value})
        return resp.get("data", {})

    # ── Interaction ──

    def click(self, *, simulate: bool = False, button: str = "left") -> Widget:
        """Click this widget. Returns self for chaining."""
        self._session._send_cmd(Cmd.CLICK_WIDGET, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
            Key.SIMULATE: simulate,
            Key.BUTTON: button,
        })
        return self

    def press(self, button: str = "left") -> Widget:
        """Press (mouse-down) this widget. Returns self for chaining."""
        self._session._send_cmd(Cmd.PRESS_WIDGET, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
            Key.BUTTON: button,
        })
        return self

    def release(self, button: str = "left") -> Widget:
        """Release (mouse-up) this widget. Returns self for chaining."""
        self._session._send_cmd(Cmd.RELEASE_WIDGET, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
            Key.BUTTON: button,
        })
        return self

    def set_enabled(self, enabled: bool = True) -> Widget:
        """Enable or disable this widget. Returns self for chaining."""
        self._session._send_cmd(Cmd.SET_WIDGET_ENABLED, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
            Key.ENABLED: enabled,
        })
        return self

    # ── Convenience properties ──

    @property
    def locator_value(self) -> str:
        """The locator value used to find this widget."""
        return self._value

    @property
    def name(self) -> str:
        """Widget name from detail (performs a network call)."""
        detail = self.get_detail()
        return detail.get("name", "")
