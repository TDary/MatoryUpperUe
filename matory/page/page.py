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

    def __new__(cls, id: str | None = None, name: str | None = None, path: str | None = None,
                method: str | None = None, value: str | None = None,
                widget_class: type | None = None, *, connection: str | None = None) -> WidgetDescriptor:
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
        instance._connection = connection
        instance._attr_name: str | None = None
        return instance

    def __init__(self, id: str | None = None, name: str | None = None, path: str | None = None,
                 method: str | None = None, value: str | None = None,
                 widget_class: type | None = None, *, connection: str | None = None,
                 **kwargs: Any) -> None:
        # All initialization is done in __new__; this is a no-op.
        # Reject unknown keyword arguments (e.g. typos like widgt_class).
        if kwargs:
            raise TypeError(f"WidgetDescriptor got unexpected keyword argument(s): {', '.join(kwargs)}")

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr_name = name

    def __get__(self, obj: Any, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        if self._attr_name not in obj.__dict__:
            from matory.elements.widget import Widget
            widget_class = self._widget_class or Widget
            conn_key = self._connection or obj._connection_key
            obj.__dict__[self._attr_name] = widget_class(
                obj.session, self._method, self._value, connection_key=conn_key
            )
        return obj.__dict__[self._attr_name]


class Page:
    """Base class for Page Objects.

    Subclass this and define WidgetDescriptor class attributes to describe
    the UI elements on a page.
    """

    def __init__(self, session: Session, *, connection: str | None = None) -> None:
        self._session = session
        self._connection_key = connection

    @property
    def session(self) -> Session:
        return self._session
