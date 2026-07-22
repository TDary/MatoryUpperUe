"""Tests for error hierarchy."""

from matory.errors import MatoryError, CommandError, WidgetNotFoundError, ConnectionKeyError


def test_matory_error_is_exception():
    assert issubclass(MatoryError, Exception)


def test_command_error_is_matory_error():
    assert issubclass(CommandError, MatoryError)


def test_command_error_carries_code_and_msg():
    err = CommandError(code=1, msg="widget not found")
    assert err.code == 1
    assert err.msg == "widget not found"
    assert "widget not found" in str(err)


def test_widget_not_found_error_is_matory_error():
    assert issubclass(WidgetNotFoundError, MatoryError)


def test_widget_not_found_error_carries_method_and_value():
    err = WidgetNotFoundError(method="id", value="999")
    assert err.method == "id"
    assert err.value == "999"
    assert "999" in str(err)


def test_connection_key_error_is_matory_error():
    assert issubclass(ConnectionKeyError, MatoryError)


def test_connection_key_error_carries_key_and_available():
    err = ConnectionKeyError(key="ue2", available=["default", "ue1"])
    assert err.key == "ue2"
    assert err.available == ["default", "ue1"]
    assert "ue2" in str(err)
