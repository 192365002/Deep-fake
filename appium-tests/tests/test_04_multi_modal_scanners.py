"""
Test Suite: Multi-Modal AI Detection Pipelines
Validates scanning execution across Text, URL, Profile, Image, and Result Screen views.
"""
import pytest
from pages.home_page import HomePage
from pages.scan_page import ScanPage
from pages.result_page import ResultPage
from config.test_data import TEXT_SAMPLES, URL_SAMPLES, PROFILE_SAMPLES


@pytest.mark.scanners
class TestMultiModalScanners:

    def test_text_scam_detection_pipeline(self, driver):
        """TC-TXT-001: Execute Text Scam analysis on high-urgency phishing message"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        home = HomePage(driver)
        home.tap_scan_text()
        scan = ScanPage(driver)
        scan.enter_scam_text(TEXT_SAMPLES["phishing_urgent"])
        scan.tap_start_scan()

        result = ResultPage(driver)
        assert result.is_result_displayed(timeout=35)
        verdict = result.get_verdict()
        assert verdict in ["FAKE", "SUSPICIOUS", "HIGH"]
        result.tap_done()

    def test_url_threat_analysis_pipeline(self, driver):
        """TC-URL-001: Execute URL Scanner against suspicious domain URL"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        home = HomePage(driver)
        home.tap_scan_url()
        scan = ScanPage(driver)
        scan.enter_url(URL_SAMPLES["phishing_url"])
        scan.tap_start_scan()

        result = ResultPage(driver)
        assert result.is_result_displayed(timeout=35)
        result.tap_done()

    def test_profile_bot_detection_pipeline(self, driver):
        """TC-PRF-001: Execute Social Profile analysis on bot account metrics"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        home = HomePage(driver)
        home.tap_scan_profile()
        scan = ScanPage(driver)
        data = PROFILE_SAMPLES["bot_profile"]
        scan.enter_profile_data(data["username"], data["followers"], data["following"], data["bio"])
        scan.tap_start_scan()

        result = ResultPage(driver)
        assert result.is_result_displayed(timeout=35)
        result.tap_done()

    def test_result_screen_explainability_and_recommendations(self, driver):
        """TC-RES-001: Verify Result screen renders detailed indicators and actionable recommendations"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        result = ResultPage(driver)
        assert result.is_visible(*result.EXPLANATION_SECTION, timeout=5)
        assert result.is_visible(*result.RECOMMENDATION_SECTION, timeout=5)
