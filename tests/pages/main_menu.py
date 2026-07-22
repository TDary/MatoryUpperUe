"""Example Page Object for the main menu."""

from matory import ButtonWidget, Page, TextWidget, WidgetDescriptor


class MainMenu(Page):
    """The main menu page of the UE application."""

    login_btn = WidgetDescriptor(id="LoginBtn", widget_class=ButtonWidget)
    settings_btn = WidgetDescriptor(id="SettingsBtn", widget_class=ButtonWidget)
    title_text = WidgetDescriptor(id="TitleLabel", widget_class=TextWidget)

    def click_login(self) -> MainMenu:
        self.login_btn.click()
        return self

    def click_settings(self) -> MainMenu:
        self.settings_btn.click()
        return self
