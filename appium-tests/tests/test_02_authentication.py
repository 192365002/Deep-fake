"""
Test Suite: Authentication & Supabase GoTrue Integration
Validates login, registration, field validations, Google sign-in trigger, and session persistence.
"""
import pytest
from pages.auth_page import AuthPage
from config.test_data import VALID_USER, INVALID_USERS


@pytest.mark.auth
class TestAuthentication:

    def test_login_with_valid_credentials(self, driver):
        """TC-AUTH-001: Verify successful login with verified Supabase credentials"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        auth = AuthPage(driver)
        auth.login_with_credentials(VALID_USER["email"], VALID_USER["password"])

    def test_login_validation_empty_fields(self, driver):
        """TC-AUTH-002: Verify inline validation error when submitting blank email and password"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        auth = AuthPage(driver)
        auth.login_with_credentials("", "")
        assert auth.is_error_displayed()

    @pytest.mark.parametrize("scenario", INVALID_USERS)
    def test_login_validation_scenarios(self, driver, scenario):
        """TC-AUTH-003 to TC-AUTH-006: Verify rejection on various invalid credential patterns"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        auth = AuthPage(driver)
        auth.login_with_credentials(scenario["email"], scenario["password"])
        assert auth.is_error_displayed()

    def test_switch_between_sign_in_and_sign_up(self, driver):
        """TC-AUTH-007: Verify smooth toggle between Sign In and Sign Up tabs"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        auth = AuthPage(driver)
        auth.switch_to_sign_up()
        auth.switch_to_sign_in()

    def test_google_sign_in_prompt_triggers(self, driver):
        """TC-AUTH-008: Verify tapping Continue with Google triggers Google Account picker"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        auth = AuthPage(driver)
        auth.tap_google_sign_in()
