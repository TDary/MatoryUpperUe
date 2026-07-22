"""Page Object pattern — base Page class and WidgetDescriptor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from matory.session import Session


class Page:
    """Base class for Page Objects.

    A Page Object represents a logical screen or region in the UE UI.
    Subclasses define widget locators and action methods.

    Usage::

        class MainMenu(Page):
            start_btn = WidgetDescriptor(name="StartBtn")

            def click_start(self):
                self.start_btn.click()
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """The Session this page is bound to."""
        return self._session


class WidgetDescriptor:
    """Descriptor that lazily resolves a widget on first access.

    Usage inside a Page subclass::

        class MyPage(Page):
            my_button = WidgetDescriptor(name="MyButton")

        p = session.page(MyPage)
        p.my_button.click()  # resolved at access time
    """

    def __init__(self, *, id: str | None = None, name: str | None = None, path: str | None = None) -> None:
        self._id = id
        self._name = name
        self._path = path

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr_name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        # Lazy-resolve the widget through the session
        from matory.elements.button import ButtonWidget
        from matory.elements.text import TextWidget
        from matory.elements.widget import Widget

        if self._id is not None:
            return obj._session.find_widget(id=self._id)
        elif self._name is not None:
            return obj._session.find_widget(name=self._name)
        elif self._path is not None:
            return obj._session.find_widget(path=self._path)
        raise ValueError("WidgetDescriptor requires at least one locator (id, name, or path)")
