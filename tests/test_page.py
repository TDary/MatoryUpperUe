"""Tests for Page and WidgetDescriptor."""

from tests.helpers import MockConnection
from tests.conftest import make_session as _make_session
from matory.elements.button import ButtonWidget
from matory.elements.text import TextWidget
from matory.elements.widget import Widget
from matory.page.page import Page, WidgetDescriptor


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


def test_descriptor_connection_forwarded(mock_conn):
    """WidgetDescriptor(connection=) is forwarded to Widget."""
    class MyPage(Page):
        btn = WidgetDescriptor(id="3", connection="ue2")
    session = _make_session(mock_conn)
    session._connections["ue2"] = MockConnection()
    p = MyPage(session)
    assert p.btn._connection_key == "ue2"


def test_page_connection_forwarded(mock_conn):
    """Page(session, connection=) is forwarded to descriptors without explicit connection."""
    class MyPage(Page):
        btn = WidgetDescriptor(id="3")
    session = _make_session(mock_conn)
    session._connections["ue2"] = MockConnection()
    p = MyPage(session, connection="ue2")
    assert p.btn._connection_key == "ue2"


def test_descriptor_overrides_page(mock_conn):
    """Descriptor connection= overrides Page connection."""
    class MyPage(Page):
        btn1 = WidgetDescriptor(id="3", connection="client")
        btn2 = WidgetDescriptor(id="4")
    session = _make_session(mock_conn)
    session._connections["client"] = MockConnection()
    session._connections["host"] = MockConnection()
    p = MyPage(session, connection="host")
    assert p.btn1._connection_key == "client"  # descriptor overrides
    assert p.btn2._connection_key == "host"    # page default


def test_page_backward_compat_no_connection(mock_conn):
    """Page(session) still works without connection."""
    class MyPage(Page):
        btn = WidgetDescriptor(id="3")
    session = _make_session(mock_conn)
    p = MyPage(session)
    assert p._connection_key is None
    assert p.btn._connection_key is None


def test_widget_descriptor_rejects_unknown_kwargs():
    """WidgetDescriptor with a typo in kwargs should raise TypeError."""
    import pytest
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        WidgetDescriptor(id="3", widgt_class=ButtonWidget)


def test_page_invalidate_widgets(mock_conn):
    """invalidate_widgets clears cached widgets so they are recreated on next access."""
    class MyPage(Page):
        btn = WidgetDescriptor(id="3")
    session = _make_session(mock_conn)
    p = MyPage(session)
    w1 = p.btn
    w2 = p.btn
    assert w1 is w2  # cached
    p.invalidate_widgets()
    w3 = p.btn
    assert w3 is not w1  # new instance after invalidation
