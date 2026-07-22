"""Example test demonstrating the Matory framework."""

import pytest

from matory import ButtonWidget, Page, WidgetDescriptor

from .pages.main_menu import MainMenu


@pytest.mark.ui
class TestMainMenu:
    """Tests for the main menu page.

    Run with: pytest --matory-host=127.0.0.1 --matory-port=2666
    Requires a running UE instance with the Matory SDK plugin.
    """

    def test_login_button_exists(self, session):
        main_menu = session.page(MainMenu)
        assert main_menu.login_btn.exists()

    def test_click_login(self, session):
        main_menu = session.page(MainMenu)
        main_menu.click_login()

    def test_sdk_version(self, session):
        version = session.get_sdk_version()
        assert version == "1.0.0"
