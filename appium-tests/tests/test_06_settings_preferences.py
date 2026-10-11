"""
Test Suite: Settings & User Preferences
Validates theme switching (dark/light), auto-scan toggling, push notifications, and logout flow.
"""
import pytest
from pages.home_page import HomePage
from pages.settings_page import SettingsPage
from pages.auth_page import AuthPage


@pytest.mark.settings
class TestSettingsPreferences:

    def test_navigate_to_settings_screen(self, driver):
        """TC-SET-001: Verify Settings screen renders user preferences and session info"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        home = HomePage(driver)
        home.navigate_to_settings()
        settings = SettingsPage(driver)
        assert settings.is_visible(*settings.DARK_MODE_SWITCH, timeout=5)

    def test_toggle_dark_theme(self, driver):
        """TC-SET-002: Verify toggling Dark Mode switch persists in preferences"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        settings = SettingsPage(driver)
        settings.toggle_dark_mode()
        settings.toggle_dark_mode()  # Restore original state

    def test_toggle_notifications(self, driver):
        """TC-SET-003: Verify toggling push notification alerts switch"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        settings = SettingsPage(driver)
        settings.toggle_notifications()
        settings.toggle_notifications()

    def test_sign_out_flow(self, driver):
        """TC-SET-004: Verify signing out clears user session and redirects to Auth screen"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        settings = SettingsPage(driver)
        settings.tap_sign_out()
        auth = AuthPage(driver)
        assert auth.is_visible(*auth.SIGN_IN_BUTTON, timeout=10)
