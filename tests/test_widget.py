"""Tests for Widget base class."""

import json

from matory.client.protocol import Cmd, Method, Key, Button
from matory.elements.widget import Widget
from matory.session import Session


def _make_widget(mock_conn, method="id", value="42"):
    """Helper to create a Widget backed by a mock connection."""
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0
    return Widget(session, method, value)


def test_exists_true(mock_conn):
    mock_conn.add_response(data=True)
    w = _make_widget(mock_conn, "id", "42")
    assert w.exists() is True


def test_exists_false(mock_conn):
    mock_conn.add_response(data=False)
    w = _make_widget(mock_conn, "name", "MyBtn")
    assert w.exists() is False


def test_get_detail(mock_conn):
    detail = {"type": "Button", "name": "LoginBtn", "id": 42}
    mock_conn.add_response(data=detail)
    w = _make_widget(mock_conn, "id", "42")
    assert w.get_detail() == detail


def test_click_default(mock_conn):
    mock_conn.add_response(data=None)
    w = _make_widget(mock_conn, "id", "42")
    result = w.click()
    assert result is w  # chainable

    # Verify sent command
    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.CLICK_WIDGET
    assert sent["args"][Key.METHOD] == "id"
    assert sent["args"][Key.VALUE] == "42"
    assert sent["args"][Key.BUTTON] == Button.LEFT
    assert sent["args"][Key.SIMULATE] is False


def test_click_simulate(mock_conn):
    mock_conn.add_response(data=None)
    w = _make_widget(mock_conn, "id", "42")
    w.click(simulate=True, button="right")

    sent = json.loads(mock_conn._sent[0])
    assert sent["args"][Key.SIMULATE] is True
    assert sent["args"][Key.BUTTON] == "right"


def test_press(mock_conn):
    mock_conn.add_response(data=None)
    w = _make_widget(mock_conn, "id", "42")
    result = w.press("left")
    assert result is w

    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.PRESS_WIDGET


def test_release(mock_conn):
    mock_conn.add_response(data=None)
    w = _make_widget(mock_conn, "id", "42")
    result = w.release("left")
    assert result is w

    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.RELEASE_WIDGET


def test_set_enabled(mock_conn):
    mock_conn.add_response(data=None)
    w = _make_widget(mock_conn, "id", "42")
    result = w.set_enabled(False)
    assert result is w

    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.SET_WIDGET_ENABLED
    assert sent["args"][Key.ENABLED] is False


def test_click_raises_command_error(mock_conn):
    mock_conn.add_response(code=1, msg="widget not found")
    w = _make_widget(mock_conn, "id", "999")

    from matory.errors import CommandError
    try:
        w.click()
        assert False, "Should have raised CommandError"
    except CommandError as e:
        assert e.code == 1


def test_id_property(mock_conn):
    w = _make_widget(mock_conn, "id", "42")
    assert w.id == "42"


def test_name_property_via_detail(mock_conn):
    mock_conn.add_response(data={"type": "Button", "name": "LoginBtn", "id": 42})
    w = _make_widget(mock_conn, "id", "42")
    assert w.name == "LoginBtn"
