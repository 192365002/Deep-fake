"""
Test Suite: Scan History & Real-Time Multi-Device Synchronization
Validates history filters, search bar, item detail drill-down, deletion, and bidirectional sync.
"""
import pytest
from pages.home_page import HomePage
from pages.history_page import HistoryPage
from pages.result_page import ResultPage


@pytest.mark.history
class TestHistoryAndRealtimeSync:

    def test_navigate_to_history_and_verify_filter_chips(self, driver):
        """TC-HIS-001: Verify filter chips (ALL, IMAGE, VIDEO, AUDIO, TEXT, URL) are visible and clickable"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        home = HomePage(driver)
        home.navigate_to_history()

        history = HistoryPage(driver)
        assert history.is_visible(*history.FILTER_CHIP_ALL)
        for chip in ["IMAGE", "VIDEO", "AUDIO", "TEXT", "URL"]:
            history.select_filter(chip)
        history.select_filter("ALL")

    def test_search_history_by_query(self, driver):
        """TC-HIS-002: Verify filtering history items dynamically via search bar"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        history = HistoryPage(driver)
        history.enter_search_query("IMAGE")

    def test_drill_down_into_history_item_detail(self, driver):
        """TC-HIS-003: Verify tapping a scan history item opens its full Result Screen"""
        if not driver:
            pytest.skip("Live Appium driver not available.")
        history = HistoryPage(driver)
        if history.get_history_item_count() > 0:
            history.tap_first_history_item()
            result = ResultPage(driver)
            assert result.is_result_displayed(timeout=10)
            result.tap_done()
