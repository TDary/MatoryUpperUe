"""TextWidget — text display element with readable content."""

from __future__ import annotations

from typing import Any

from matory.elements.widget import Widget


class TextWidget(Widget):
    """A text-display UI element with a readable ``text`` property."""

    @property
    def text(self) -> str:
        """The displayed text content of this widget."""
        detail = self.get_detail()
        return detail.get("text", "")
