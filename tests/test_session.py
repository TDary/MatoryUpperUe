"""Tests for Session."""

import json

from matory.client.protocol import Cmd, Key, Method
from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.elements.widget import Widget
from matory.errors import CommandError
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
    assert btn.id == "42"


def test_find_button_by_name(mock_conn):
    mock_conn.add_response(data=[{"id": 42, "name": "LoginBtn", "type": "Button"}])
    session = _make_session(mock_conn)
    btn = session.find_button(name="LoginBtn")
    assert isinstance(btn, ButtonWidget)


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


def test_find_button_no_match_raises(mock_conn):
    mock_conn.add_response(data=[])
    session = _make_session(mock_conn)
    try:
        session.find_button(id="999")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "999" in str(e)


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
    assert session._next_req_id() == 1
    assert session._next_req_id() == 2
