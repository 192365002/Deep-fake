"""
Scan History Page Object for Social Shield
Controls history filtering, item search, detail drill-down, and item deletion.
"""
from typing import List
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class HistoryPage(BasePage):
    # Search & Filter Locators
    SEARCH_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[contains(@hint, 'Search') or contains(@text, 'Search')]")
    FILTER_CHIP_ALL = (AppiumBy.XPATH, "//*[@text='ALL' or contains(@text, 'All')]")
    FILTER_CHIP_IMAGE = (AppiumBy.XPATH, "//*[@text='IMAGE' or contains(@text, 'Image')]")
    FILTER_CHIP_VIDEO = (AppiumBy.XPATH, "//*[@text='VIDEO' or contains(@text, 'Video')]")
    FILTER_CHIP_AUDIO = (AppiumBy.XPATH, "//*[@text='AUDIO' or contains(@text, 'Audio')]")
    FILTER_CHIP_TEXT = (AppiumBy.XPATH, "//*[@text='TEXT' or contains(@text, 'Text')]")
    FILTER_CHIP_URL = (AppiumBy.XPATH, "//*[@text='URL' or contains(@text, 'Url')]")

    # History List Items
    HISTORY_ITEMS = (AppiumBy.XPATH, "//android.widget.TextView[contains(@text, 'Scan') or contains(@text, 'Image') or contains(@text, 'Text')]/ancestor::android.view.View[1]")
    DELETE_BUTTON = (AppiumBy.XPATH, "//*[contains(@content-desc, 'Delete') or contains(@text, 'Delete')]")
    EMPTY_STATE_TEXT = (AppiumBy.XPATH, "//*[contains(@text, 'No scans') or contains(@text, 'No history')]")

    def enter_search_query(self, query: str):
        self.type_text(*self.SEARCH_INPUT, query)

    def select_filter(self, filter_name: str):
        mapping = {
            "ALL": self.FILTER_CHIP_ALL,
            "IMAGE": self.FILTER_CHIP_IMAGE,
            "VIDEO": self.FILTER_CHIP_VIDEO,
            "AUDIO": self.FILTER_CHIP_AUDIO,
            "TEXT": self.FILTER_CHIP_TEXT,
            "URL": self.FILTER_CHIP_URL,
        }
        chip = mapping.get(filter_name.upper(), self.FILTER_CHIP_ALL)
        self.click(*chip)

    def get_history_item_count(self) -> int:
        return len(self.find_all(*self.HISTORY_ITEMS))

    def tap_first_history_item(self):
        items = self.find_all(*self.HISTORY_ITEMS)
        if items:
            items[0].click()

    def is_empty_state_visible(self) -> bool:
        return self.is_visible(*self.EMPTY_STATE_TEXT, timeout=3)
