"""Tests for TextWidget."""

import json

from matory.client.protocol import Cmd, Key
from matory.elements.text import TextWidget
from matory.elements.widget import Widget
from matory.session import Session


def _make_text_widget(mock_conn, method="id", value="100"):
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0
    return TextWidget(session, method, value)


def test_text_widget_is_widget():
    assert issubclass(TextWidget, Widget)


def test_text_property(mock_conn):
    mock_conn.add_response(data={"type": "TextBlock", "text": "Hello World", "id": 100})
    tw = _make_text_widget(mock_conn, "id", "100")
    assert tw.text == "Hello World"
