"""Tests for Recorder."""

from tests.helpers import MockConnection
from tests.conftest import make_session as _make_session
from matory.elements.button import ButtonWidget
from matory.elements.widget import Widget
from matory.recorder import Recorder, Step


def test_step_creation():
    step = Step(action="click", method="id", value="42", args={"simulate": False, "button": "left"})
    assert step.action == "click"
    assert step.method == "id"
    assert step.value == "42"


def test_recorder_records_click(mock_conn):
    mock_conn.add_response(data=None)
    session = _make_session(mock_conn)

    rec = Recorder(session)
    rec.start()

    btn = ButtonWidget(session, "id", "42")
    btn.click()

    rec.stop()
    assert len(rec.steps) == 1
    assert rec.steps[0].action == "click"
    assert rec.steps[0].method == "id"
    assert rec.steps[0].value == "42"


def test_recorder_records_multiple_actions(mock_conn):
    for _ in range(3):
        mock_conn.add_response(data=None)

    session = _make_session(mock_conn)

    rec = Recorder(session)
    rec.start()

    w = Widget(session, "id", "1")
    w.click()
    w.press("left")
    w.release("left")

    rec.stop()
    assert len(rec.steps) == 3
    assert rec.steps[0].action == "click"
    assert rec.steps[1].action == "press"
    assert rec.steps[2].action == "release"


def test_recorder_not_recording_when_stopped(mock_conn):
    mock_conn.add_response(data=None)
    session = _make_session(mock_conn)

    rec = Recorder(session)
    # Don't call start()
    w = Widget(session, "id", "1")
    w.click()

    assert len(rec.steps) == 0


def test_recorder_generate_code(tmp_path):
    steps = [
        Step(action="click", method="id", value="LoginBtn", args={"simulate": False, "button": "left"}),
        Step(action="click", method="id", value="SettingsBtn", args={"simulate": False, "button": "left"}),
    ]

    rec = Recorder.__new__(Recorder)
    rec._steps = steps
    rec._recording = False

    output = tmp_path / "test_recorded.py"
    rec.generate_code("RecordedPage", str(output))

    code = output.read_text(encoding="utf-8")
    assert "class RecordedPage(Page)" in code
    assert "LoginBtn" in code
    assert "SettingsBtn" in code
    assert "def test_recorded_flow" in code
    assert "click" in code
    # Should use explicit imports, not wildcard
    assert "from matory.page.page import Page, WidgetDescriptor" in code


def test_recorder_generate_code_aggregates_widgets(tmp_path):
    """Two clicks on the same widget should produce one descriptor."""
    steps = [
        Step(action="click", method="id", value="LoginBtn", args={"simulate": False, "button": "left"}),
        Step(action="click", method="id", value="LoginBtn", args={"simulate": True, "button": "left"}),
    ]

    rec = Recorder.__new__(Recorder)
    rec._steps = steps
    rec._recording = False

    output = tmp_path / "test_recorded.py"
    rec.generate_code("RecordedPage", str(output))

    code = output.read_text(encoding="utf-8")
    # Should have exactly one descriptor for LoginBtn
    assert code.count("LoginBtn") >= 2  # descriptor + usage(s)
    # Should have exactly one descriptor line for LoginBtn (not counting import)
    descriptor_lines = [l for l in code.splitlines() if "WidgetDescriptor" in l and "=" in l and "import" not in l]
    assert len(descriptor_lines) == 1  # deduplicated


def test_recorder_generate_code_numeric_id(tmp_path):
    """Numeric widget IDs should generate valid Python attribute names."""
    steps = [
        Step(action="click", method="id", value="3", args={"simulate": False, "button": "left"}),
    ]

    rec = Recorder.__new__(Recorder)
    rec._steps = steps
    rec._recording = False

    output = tmp_path / "test_recorded.py"
    rec.generate_code("RecordedPage", str(output))

    code = output.read_text(encoding="utf-8")
    # Should prefix with "widget_" for numeric IDs
    assert "widget_3" in code
    # The generated code should be valid Python
    compile(code, str(output), "exec")


def test_recorder_stop_restores_send_cmd(mock_conn):
    """After stop(), the send hook should be unregistered and session functional."""
    mock_conn.add_response(data=None)
    session = _make_session(mock_conn)

    rec = Recorder(session)
    rec.start()
    assert rec._hook in session._send_hooks

    # Use the click that consumes the mock response above
    btn = ButtonWidget(session, "id", "1")
    btn.click()

    rec.stop()
    assert rec._hook not in session._send_hooks

    # Verify it still works after stop
    mock_conn.add_response(data="1.0.0")
    resp = session.get_sdk_version()
    assert resp == "1.0.0"


def test_step_has_connection_field():
    step = Step(action="click", method="id", value="42", connection="ue2")
    assert step.connection == "ue2"


def test_step_connection_defaults_none():
    step = Step(action="click", method="id", value="42")
    assert step.connection is None


def test_recorder_records_connection(mock_conn):
    """Recording a widget with connection_key records it in Step."""
    mock_conn2 = MockConnection()
    mock_conn2.add_response(data=None)
    session = _make_session(mock_conn)
    session._connections["ue2"] = mock_conn2
    rec = Recorder(session)
    rec.start()
    btn = ButtonWidget(session, "id", "42", connection_key="ue2")
    btn.click()
    rec.stop()
    assert len(rec.steps) == 1
    assert rec.steps[0].connection == "ue2"


def test_recorder_generate_code_with_connection(tmp_path):
    """Generated code includes connection= on descriptors."""
    steps = [
        Step(action="click", method="id", value="LoginBtn", connection="ue2",
             args={"simulate": False, "button": "left"}),
    ]
    rec = Recorder.__new__(Recorder)
    rec._steps = steps
    rec._recording = False
    output = tmp_path / "test_recorded.py"
    rec.generate_code("RecordedPage", str(output))
    code = output.read_text(encoding="utf-8")
    assert 'connection="ue2"' in code


def test_recorder_double_start_no_op(mock_conn):
    """Calling start() twice without stop() should be a no-op."""
    mock_conn.add_response(data=None)
    session = _make_session(mock_conn)

    rec = Recorder(session)
    rec.start()
    hook_count = len(session._send_hooks)

    # Second start() should be a no-op — hook not added twice
    rec.start()
    assert len(session._send_hooks) == hook_count

    rec.stop()
    assert rec._hook not in session._send_hooks
