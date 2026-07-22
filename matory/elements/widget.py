"""Widget base class — the core element model."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Callable

from matory.client.protocol import Cmd, Key

if TYPE_CHECKING:
    from matory.session import Session


class Widget:
    """Base class for all UI elements.

    Holds a session reference and locator info (method + value).
    All interaction methods return ``self`` for chaining.
    """

    def __init__(self, session: Session, method: str, value: str,
                 *, connection_key: str | None = None) -> None:
        self._session = session
        self._method = method
        self._value = value
        self._connection_key = connection_key

    def __repr__(self) -> str:
        conn = f", connection={self._connection_key!r}" if self._connection_key else ""
        return f"{self.__class__.__name__}({self._method}={self._value!r}{conn})"

    def _send(self, cmd: str, args: dict[str, Any]) -> dict:
        """Send a command through the bound connection."""
        return self._session._send_cmd(cmd, args, connection=self._connection_key)

    # ── Query ──

    def exists(self) -> bool:
        """Check whether this widget exists in the UI tree."""
        resp = self._send(Cmd.WIDGET_EXISTS, {
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
        resp = self._send(Cmd.GET_WIDGET_DETAIL, {Key.ID: self._value})
        return resp.get("data", {})

    # ── Interaction ──

    def click(self, *, simulate: bool = False, button: str = "left") -> Widget:
        """Click this widget. Returns self for chaining."""
        self._send(Cmd.CLICK_WIDGET, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
            Key.SIMULATE: simulate,
            Key.BUTTON: button,
        })
        return self

    def press(self, button: str = "left") -> Widget:
        """Press (mouse-down) this widget. Returns self for chaining."""
        self._send(Cmd.PRESS_WIDGET, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
            Key.BUTTON: button,
        })
        return self

    def release(self, button: str = "left") -> Widget:
        """Release (mouse-up) this widget. Returns self for chaining."""
        self._send(Cmd.RELEASE_WIDGET, {
            Key.METHOD: self._method,
            Key.VALUE: self._value,
            Key.BUTTON: button,
        })
        return self

    def set_enabled(self, enabled: bool = True) -> Widget:
        """Enable or disable this widget. Returns self for chaining."""
        self._send(Cmd.SET_WIDGET_ENABLED, {
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

    # ── Wait / Retry ──

    def wait_until(
        self,
        predicate: Callable[[Widget], bool],
        *,
        timeout: float = 10.0,
        interval: float = 0.5,
    ) -> Widget:
        """Poll until *predicate(widget)* returns True.

        Args:
            predicate: A callable that takes this widget and returns bool.
            timeout: Maximum seconds to wait (default 10.0).
            interval: Seconds between polls (default 0.5).

        Returns:
            self, for chaining.

        Raises:
            TimeoutError: If the predicate is not satisfied within *timeout*.
        """
        deadline = time.monotonic() + timeout
        while True:
            try:
                if predicate(self):
                    return self
            except Exception:
                pass  # transient errors (e.g. widget not ready) are retried
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"wait_until timed out after {timeout}s "
                    f"for {self!r}"
                )
            time.sleep(interval)

    def wait_exists(self, *, timeout: float = 10.0, interval: float = 0.5) -> Widget:
        """Wait until this widget exists in the UI tree.

        Returns self for chaining.
        """
        return self.wait_until(lambda w: w.exists(), timeout=timeout, interval=interval)

    def wait_enabled(self, *, timeout: float = 10.0, interval: float = 0.5) -> Widget:
        """Wait until this widget is enabled.

        Returns self for chaining.
        """
        def _is_enabled(w: Widget) -> bool:
            detail = w.get_detail()
            return detail.get("enabled", False) is True
        return self.wait_until(_is_enabled, timeout=timeout, interval=interval)
