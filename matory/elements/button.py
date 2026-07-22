"""ButtonWidget — type marker for button elements."""

from __future__ import annotations

from matory.elements.widget import Widget


class ButtonWidget(Widget):
    """A button UI element.

    No additional methods — serves as a type marker for IDE autocompletion
    and ``isinstance`` checks.
    """
