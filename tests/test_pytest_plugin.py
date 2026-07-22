"""Tests for pytest plugin — using pytester to verify fixture and CLI behavior."""

import pytest


def test_plugin_registers_cli_options(pytester):
    """Plugin should add --matory-host, --matory-port, --matory-timeout.

    The matory plugin auto-registers via the pytest11 entry point.
    """
    result = pytester.runpytest("--help")
    result.stdout.fnmatch_lines(["*--matory-host*"])
    result.stdout.fnmatch_lines(["*--matory-port*"])
    result.stdout.fnmatch_lines(["*--matory-timeout*"])


def test_plugin_registers_ui_marker(pytester):
    """Plugin should register the 'ui' marker."""
    result = pytester.runpytest("--markers")
    result.stdout.fnmatch_lines(["*ui*UE UI*"])


def test_session_fixture_exists(pytester):
    """The 'session' fixture should be available (will fail to connect, but fixture must exist)."""
    pytester.makepyfile("""
        def test_session_fixture_name(session):
            # We just check the fixture is recognized — connection will fail
            # so we don't actually call anything on session
            assert session is not None
    """)
    # This will fail because no UE server is running, but the fixture
    # should be found (not "fixture 'session' not found")
    result = pytester.runpytest("--matory-host=127.0.0.1", "--matory-port=9999", "-v")
    # We expect a ConnectionError/ConnectionRefusedError, NOT a fixture-not-found error
    # Use *Connection*Error* to match both ConnectionError (Linux/macOS)
    # and ConnectionRefusedError (Windows)
    result.stdout.fnmatch_lines(["*Connection*Error*"])
