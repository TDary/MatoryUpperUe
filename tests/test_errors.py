"""Tests for error hierarchy."""

from matory.errors import MatoryError, CommandError


def test_matory_error_is_exception():
    assert issubclass(MatoryError, Exception)


def test_command_error_is_matory_error():
    assert issubclass(CommandError, MatoryError)


def test_command_error_carries_code_and_msg():
    err = CommandError(code=1, msg="widget not found")
    assert err.code == 1
    assert err.msg == "widget not found"
    assert "widget not found" in str(err)
