"""Matory — UE UI automation framework."""

from matory.errors import (
    MatoryError, CommandError, WidgetNotFoundError,
    ConnectionKeyError, ConnectionError,
)
from matory.session import Session
from matory.elements.widget import Widget
from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.page.page import Page, WidgetDescriptor
from matory.recorder import Recorder, Step

__all__ = [
    "MatoryError",
    "CommandError",
    "WidgetNotFoundError",
    "ConnectionKeyError",
    "ConnectionError",
    "Session",
    "Widget",
    "ButtonWidget",
    "TextWidget",
    "Page",
    "WidgetDescriptor",
    "Recorder",
    "Step",
]
