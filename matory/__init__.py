"""Matory — UE UI automation framework."""

from matory.errors import MatoryError, CommandError, WidgetNotFoundError, ConnectionKeyError
from matory.session import Session
from matory.elements.widget import Widget
from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.page.page import Page, WidgetDescriptor

__all__ = [
    "MatoryError",
    "CommandError",
    "WidgetNotFoundError",
    "ConnectionKeyError",
    "Session",
    "Widget",
    "ButtonWidget",
    "TextWidget",
    "Page",
    "WidgetDescriptor",
]
