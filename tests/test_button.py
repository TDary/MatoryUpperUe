"""Tests for ButtonWidget."""

from matory.elements.button import ButtonWidget
from matory.elements.widget import Widget


def test_button_widget_is_widget():
    assert issubclass(ButtonWidget, Widget)
