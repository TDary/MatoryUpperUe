"""Tests for Session."""

import json
import threading

import pytest

from tests.helpers import MockConnection
from matory.client.protocol import Cmd, Key, Method
from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.elements.widget import Widget
from matory.errors import CommandError, WidgetNotFoundError, ConnectionKeyError
from matory.session import Session


def _make_session(mock_conn):
    """Create a Session with a mock connection."""
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0
    return session


def test_get_sdk_version(mock_conn):
    mock_conn.add_response(data="1.0.0")
    session = _make_session(mock_conn)
    assert session.get_sdk_version() == "1.0.0"


def test_get_engine_version(mock_conn):
    mock_conn.add_response(data="5.3.0")
    session = _make_session(mock_conn)
    assert session.get_engine_version() == "5.3.0"


def test_get_widget_tree(mock_conn):
    tree = {"type": "Canvas", "children": []}
    mock_conn.add_response(data=tree)
    session = _make_session(mock_conn)
    assert session.get_widget_tree() == tree


def test_find_button_by_id(mock_conn):
    mock_conn.add_response(data=[{"id": 42, "name": "LoginBtn", "type": "Button"}])
    session = _make_session(mock_conn)
    btn = session.find_button(id="42")
    assert isinstance(btn, ButtonWidget)
    assert btn.locator_value == "42"


def test_find_button_sends_locator(mock_conn):
    """find_button should pass the locator args to the server."""
    mock_conn.add_response(data=[{"id": 42, "name": "LoginBtn", "type": "Button"}])
    session = _make_session(mock_conn)
    session.find_button(name="LoginBtn")
    sent = json.loads(mock_conn._sent[0])
    assert sent["args"][Key.METHOD] == "name"
    assert sent["args"][Key.VALUE] == "LoginBtn"


def test_find_text(mock_conn):
    mock_conn.add_response(data=[{"id": 10, "name": "TitleLabel", "text": "Hello", "type": "TextBlock"}])
    session = _make_session(mock_conn)
    tw = session.find_text(keyword="Hello")
    assert isinstance(tw, TextWidget)


def test_find_widget(mock_conn):
    mock_conn.add_response(data=[{"id": 99, "name": "SomeWidget", "type": "Border"}])
    session = _make_session(mock_conn)
    w = session.find_widget(id="99")
    assert isinstance(w, Widget)


def test_find_button_no_match_raises_widget_not_found(mock_conn):
    mock_conn.add_response(data=[])
    session = _make_session(mock_conn)
    try:
        session.find_button(id="999")
        assert False, "Should have raised WidgetNotFoundError"
    except WidgetNotFoundError as e:
        assert e.method == "id"
        assert e.value == "999"


def test_page_factory(mock_conn):
    from matory.page.page import Page

    class MyPage(Page):
        pass

    session = _make_session(mock_conn)
    p = session.page(MyPage)
    assert isinstance(p, MyPage)
    assert p.session is session


def test_start_record(mock_conn):
    mock_conn.add_response(msg="recording started")
    session = _make_session(mock_conn)
    session.start_record()

    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.START_RECORD


def test_stop_record(mock_conn):
    mock_conn.add_response(data={"events": 5})
    session = _make_session(mock_conn)
    result = session.stop_record()

    sent = json.loads(mock_conn._sent[0])
    assert sent["cmd"] == Cmd.STOP_RECORD


def test_disconnect(mock_conn):
    mock_conn.add_response(msg="disconnected")
    session = _make_session(mock_conn)
    session.disconnect()


def test_session_context_manager(mock_conn):
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0
    with session:
        pass
    # close was called on the mock_conn (no error = success)


def test_next_req_id_increments():
    session = Session.__new__(Session)
    session._req_id = 0
    session._lock = threading.Lock()
    assert session._next_req_id() == 1
    assert session._next_req_id() == 2


def test_add_connection(mock_conn):
    """add_connection creates a second named connection."""
    session = _make_session(mock_conn)
    # Add a second mock connection for "ue2"
    mock_conn2 = MockConnection()
    session._connections["ue2"] = mock_conn2
    assert "ue2" in session.list_connections()


def test_list_connections(mock_conn):
    session = _make_session(mock_conn)
    assert session.list_connections() == ["default"]


def test_get_connection_default(mock_conn):
    session = _make_session(mock_conn)
    assert session.get_connection() is mock_conn


def test_get_connection_by_key(mock_conn):
    session = _make_session(mock_conn)
    mock_conn2 = MockConnection()
    session._connections["ue2"] = mock_conn2
    assert session.get_connection("ue2") is mock_conn2


def test_get_connection_missing_raises(mock_conn):
    session = _make_session(mock_conn)
    with pytest.raises(ConnectionKeyError) as exc_info:
        session.get_connection("nope")
    assert exc_info.value.key == "nope"


def test_default_property(mock_conn):
    session = _make_session(mock_conn)
    assert session.default == "default"
    mock_conn2 = MockConnection()
    session._connections["ue2"] = mock_conn2
    session.default = "ue2"
    assert session.default == "ue2"


def test_default_set_nonexistent_raises(mock_conn):
    session = _make_session(mock_conn)
    with pytest.raises(ConnectionKeyError):
        session.default = "nope"


def test_remove_connection(mock_conn):
    session = _make_session(mock_conn)
    mock_conn2 = MockConnection()
    session._connections["ue2"] = mock_conn2
    session.remove_connection("ue2")
    assert "ue2" not in session.list_connections()


def test_remove_default_raises(mock_conn):
    session = _make_session(mock_conn)
    with pytest.raises(ValueError, match="Cannot remove"):
        session.remove_connection("default")


def test_send_cmd_with_connection_kwarg(mock_conn):
    """_send_cmd with connection= routes through the named connection."""
    mock_conn2 = MockConnection()
    mock_conn2.add_response(data="2.0.0")
    session = _make_session(mock_conn)
    session._connections["ue2"] = mock_conn2
    # Send through ue2
    resp = session._send_cmd("GetSdkVersion", {}, connection="ue2")
    assert resp.get("data") == "2.0.0"
    assert len(mock_conn2._sent) == 1
    assert len(mock_conn._sent) == 0  # default not used


def test_send_cmd_default_when_none(mock_conn):
    """_send_cmd without connection= uses default."""
    mock_conn.add_response(data="1.0.0")
    session = _make_session(mock_conn)
    resp = session._send_cmd("GetSdkVersion", {})
    assert len(mock_conn._sent) == 1


def test_conn_property_backward_compat(mock_conn):
    """_conn property maps to default connection for backward compat."""
    session = _make_session(mock_conn)
    assert session._conn is mock_conn
    # Setting _conn should update the default connection
    mock_conn2 = MockConnection()
    session._conn = mock_conn2
    assert session._conn is mock_conn2
    assert session._connections["default"] is mock_conn2


def test_conn_property_lazy_init():
    """_conn setter creates _connections dict if missing (Session.__new__ case)."""
    session = Session.__new__(Session)
    mock = MockConnection()
    session._conn = mock
    session._req_id = 0
    assert session._conn is mock
    assert "default" in session._connections


def test_find_button_with_connection(mock_conn):
    """find_button passes connection= to _send_cmd and to ButtonWidget."""
    mock_conn2 = MockConnection()
    mock_conn2.add_response(data=[{"id": 50, "name": "Btn2", "type": "Button"}])
    session = _make_session(mock_conn)
    session._connections["ue2"] = mock_conn2
    btn = session.find_button(id="50", connection="ue2")
    assert btn._connection_key == "ue2"
    assert len(mock_conn2._sent) == 1
