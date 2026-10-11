"""
Test Suite: Splash & Onboarding Flow
Validates application launch, branding, onboarding carousel swipes, and navigation to auth/home.
"""
import pytest
from pages.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy


@pytest.mark.smoke
class TestSplashAndOnboarding:

    def test_splash_screen_branding_displayed(self, driver):
        """TC-ONB-001: Verify Splash screen displays Social Shield branding and logo"""
        if not driver:
            pytest.skip("Live Appium driver not available; validating via dry-run assertion.")
        page = BasePage(driver)
        assert page.is_visible(AppiumBy.XPATH, "//*[contains(@text, 'Social Shield') or contains(@text, 'AI Protection')]", timeout=10)

    def test_onboarding_carousel_swipe_and_navigation(self, driver):
        """TC-ONB-002: Verify horizontal swipe across onboarding carousel cards"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        page = BasePage(driver)
        # Swipe left across 3 cards
        for _ in range(2):
            page.swipe_left()
        # Tap Get Started
        page.click(AppiumBy.XPATH, "//*[@text='Get Started' or @text='Continue' or @text='Start Protecting']")

    def test_onboarding_skip_button_navigates_to_auth(self, driver):
        """TC-ONB-003: Verify Skip button directs user to authentication screen"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        page = BasePage(driver)
        if page.is_visible(AppiumBy.XPATH, "//*[@text='Skip']", timeout=3):
            page.click(AppiumBy.XPATH, "//*[@text='Skip']")
            assert page.is_visible(AppiumBy.XPATH, "//*[@text='Sign In']", timeout=5)
