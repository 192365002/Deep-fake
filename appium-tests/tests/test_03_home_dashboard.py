"""
Test Suite: Home Dashboard & Real-Time Metrics
Validates live Trust Score display, total scan counter, risk distribution card, and quick stats.
"""
import pytest
from pages.home_page import HomePage
from pages.scan_page import ScanPage


@pytest.mark.home
class TestHomeDashboard:

    def test_dashboard_elements_rendered(self, driver):
        """TC-HOM-001: Verify all core home dashboard widgets are visible"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        home = HomePage(driver)
        assert home.is_dashboard_loaded()

    def test_trust_score_meter_presence(self, driver):
        """TC-HOM-002: Verify Trust Score circular gauge or numeric percentage is rendered"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        home = HomePage(driver)
        assert home.is_visible(*home.TRUST_SCORE_LABEL, timeout=5)

    def test_risk_exposure_breakdown_card_visible(self, driver):
        """TC-HOM-003: Verify Risk Exposure breakdown card with segmented bars is visible"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        home = HomePage(driver)
        home.scroll_down()
        assert home.is_visible(*home.RISK_BREAKDOWN_CARD, timeout=5)

    def test_navigate_to_image_scanner(self, driver):
        """TC-HOM-004: Verify tapping Scan Image card routes to Image Scanner screen"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        home = HomePage(driver)
        home.scroll_up()
        home.tap_scan_image()
        scan = ScanPage(driver)
        assert scan.is_visible(*scan.START_SCAN_BUTTON, timeout=5)
        scan.tap_back()

    def test_bottom_navigation_bar_routes(self, driver):
        """TC-HOM-005: Verify switching between History, Fraud Map, and Home via bottom nav bar"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        home = HomePage(driver)
        home.navigate_to_history()
        home.navigate_to_fraud_map()
        home.navigate_to_settings()
        home.navigate_to_home()
