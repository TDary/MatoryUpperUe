"""Tests for Recorder."""

from matory.elements.button import ButtonWidget
from matory.elements.widget import Widget
from matory.recorder import Recorder, Step
from matory.session import Session


def test_step_creation():
    step = Step(action="click", method="id", value="42", args={"simulate": False, "button": "left"})
    assert step.action == "click"
    assert step.method == "id"
    assert step.value == "42"


def test_recorder_records_click(mock_conn):
    mock_conn.add_response(data=None)
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0

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

    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0

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
    session = Session.__new__(Session)
    session._conn = mock_conn
    session._req_id = 0

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
    # Count descriptor lines (WidgetDescriptor lines)
    descriptor_count = code.count("WidgetDescriptor")
    assert descriptor_count == 1  # deduplicated
