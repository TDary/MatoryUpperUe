"""Matory — UE UI automation framework."""

from importlib.metadata import version as _metadata_version

try:
    __version__ = _metadata_version("matory")
except Exception:
    __version__ = "0.0.0"

from matory.errors import (
    MatoryError, CommandError, WidgetNotFoundError,
    ConnectionKeyError, MatoryConnectionError,
)
from matory.session import Session
from matory.elements.widget import Widget
from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.page.page import Page, WidgetDescriptor
from matory.recorder import Recorder, Step

__all__ = [
    "__version__",
    "MatoryError",
    "CommandError",
    "WidgetNotFoundError",
    "ConnectionKeyError",
    "MatoryConnectionError",
    "Session",
    "Widget",
    "ButtonWidget",
    "TextWidget",
    "Page",
    "WidgetDescriptor",
    "Recorder",
    "Step",
]
