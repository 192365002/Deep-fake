"""
Home Dashboard Page Object for Social Shield
Controls real-time Trust Score, live Scan Counter, Risk breakdown, and navigation.
"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class HomePage(BasePage):
    # Header & Metric Locators
    GREETING_TEXT = (AppiumBy.XPATH, "//android.widget.TextView[contains(@text, 'Welcome') or contains(@text, 'Shield User')]")
    TRUST_SCORE_LABEL = (AppiumBy.XPATH, "//*[contains(@text, 'Trust Score') or contains(@text, 'SHIELD SCORE')]")
    TRUST_SCORE_VALUE = (AppiumBy.XPATH, "//android.widget.TextView[string-length(@text) <= 4 and contains(@text, '%')] | //*[contains(@text, 'Trust Score')]/following-sibling::android.widget.TextView[1]")
    TOTAL_SCANS_COUNTER = (AppiumBy.XPATH, "//*[contains(@text, 'Total Scans') or contains(@text, 'SCANS ANALYZED')]")
    FAKE_DETECTED_STAT = (AppiumBy.XPATH, "//*[contains(@text, 'Fake') or contains(@text, 'THREATS')]")
    SAFE_DETECTED_STAT = (AppiumBy.XPATH, "//*[contains(@text, 'Safe') or contains(@text, 'VERIFIED')]")

    # Risk Exposure Breakdown
    RISK_BREAKDOWN_CARD = (AppiumBy.XPATH, "//*[contains(@text, 'Risk Exposure Breakdown') or contains(@text, 'Risk Breakdown')]")

    # Scanner Selection Cards
    SCAN_IMAGE_CARD = (AppiumBy.XPATH, "//*[contains(@text, 'Scan Image') or contains(@text, 'Photo Analysis')]")
    SCAN_VIDEO_CARD = (AppiumBy.XPATH, "//*[contains(@text, 'Scan Video') or contains(@text, 'Video Deepfake')]")
    SCAN_AUDIO_CARD = (AppiumBy.XPATH, "//*[contains(@text, 'Scan Audio') or contains(@text, 'Voice Clone')]")
    SCAN_TEXT_CARD = (AppiumBy.XPATH, "//*[contains(@text, 'Scan Text') or contains(@text, 'Phishing & Scam')]")
    SCAN_URL_CARD = (AppiumBy.XPATH, "//*[contains(@text, 'Scan URL') or contains(@text, 'Malicious Links')]")
    SCAN_PROFILE_CARD = (AppiumBy.XPATH, "//*[contains(@text, 'Scan Profile') or contains(@text, 'Bot Detection')]")

    # Bottom Navigation Tabs
    NAV_HOME = (AppiumBy.XPATH, "//*[contains(@text, 'Home') or @content-desc='Home']")
    NAV_HISTORY = (AppiumBy.XPATH, "//*[contains(@text, 'History') or @content-desc='History']")
    NAV_FRAUD_MAP = (AppiumBy.XPATH, "//*[contains(@text, 'Fraud Map') or @content-desc='Fraud Map']")
    NAV_SETTINGS = (AppiumBy.XPATH, "//*[contains(@text, 'Settings') or @content-desc='Settings']")

    def is_dashboard_loaded(self) -> bool:
        return self.is_visible(*self.SCAN_IMAGE_CARD, timeout=10)

    def tap_scan_image(self):
        self.click(*self.SCAN_IMAGE_CARD)

    def tap_scan_video(self):
        self.click(*self.SCAN_VIDEO_CARD)

    def tap_scan_audio(self):
        self.click(*self.SCAN_AUDIO_CARD)

    def tap_scan_text(self):
        self.click(*self.SCAN_TEXT_CARD)

    def tap_scan_url(self):
        self.click(*self.SCAN_URL_CARD)

    def tap_scan_profile(self):
        self.click(*self.SCAN_PROFILE_CARD)

    def navigate_to_history(self):
        self.click(*self.NAV_HISTORY)

    def navigate_to_fraud_map(self):
        self.click(*self.NAV_FRAUD_MAP)

    def navigate_to_settings(self):
        self.click(*self.NAV_SETTINGS)

    def navigate_to_home(self):
        self.click(*self.NAV_HOME)
