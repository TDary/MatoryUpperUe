"""Tests for Page and WidgetDescriptor."""

from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.elements.widget import Widget
from matory.page.page import Page, WidgetDescriptor
from matory.session import Session


def _make_session(mock_conn):
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0
    return session


def test_widget_descriptor_by_id(mock_conn):
    class MyPage(Page):
        btn = WidgetDescriptor(id="42")

    session = _make_session(mock_conn)
    p = MyPage(session)
    w = p.btn
    assert isinstance(w, Widget)
    assert w._method == "id"
    assert w._value == "42"


def test_widget_descriptor_by_name(mock_conn):
    class MyPage(Page):
        btn = WidgetDescriptor(name="LoginBtn")

    session = _make_session(mock_conn)
    p = MyPage(session)
    w = p.btn
    assert w._method == "name"
    assert w._value == "LoginBtn"


def test_widget_descriptor_by_path(mock_conn):
    class MyPage(Page):
        panel = WidgetDescriptor(path="/Canvas/Panel")

    session = _make_session(mock_conn)
    p = MyPage(session)
    w = p.panel
    assert w._method == "path"
    assert w._value == "/Canvas/Panel"


def test_widget_descriptor_widget_class(mock_conn):
    class MyPage(Page):
        btn = WidgetDescriptor(id="42", widget_class=ButtonWidget)
        title = WidgetDescriptor(id="10", widget_class=TextWidget)

    session = _make_session(mock_conn)
    p = MyPage(session)
    assert isinstance(p.btn, ButtonWidget)
    assert isinstance(p.title, TextWidget)


def test_widget_descriptor_caches(mock_conn):
    """Accessing the same descriptor twice returns the same Widget instance."""
    class MyPage(Page):
        btn = WidgetDescriptor(id="42")

    session = _make_session(mock_conn)
    p = MyPage(session)
    w1 = p.btn
    w2 = p.btn
    assert w1 is w2


def test_widget_descriptor_class_access_returns_descriptor():
    """Accessing on the class (not instance) returns the descriptor itself."""
    class MyPage(Page):
        btn = WidgetDescriptor(id="42")

    assert isinstance(MyPage.btn, WidgetDescriptor)


def test_page_session_property(mock_conn):
    session = _make_session(mock_conn)
    p = Page(session)
    assert p.session is session


def test_page_custom_method(mock_conn):
    mock_conn.add_response(data=None)

    class MainMenu(Page):
        login_btn = WidgetDescriptor(id="1", widget_class=ButtonWidget)

        def click_login(self):
            self.login_btn.click()
            return self

    session = _make_session(mock_conn)
    p = MainMenu(session)
    result = p.click_login()
    assert result is p
