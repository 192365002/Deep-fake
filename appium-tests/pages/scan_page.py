"""
Multi-Modal Scanner Page Object for Social Shield
Controls file pickers, text inputs, URL inputs, and scan execution.
"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class ScanPage(BasePage):
    # Common Scan Locators
    START_SCAN_BUTTON = (AppiumBy.XPATH, "//*[@text='Start Scan' or @text='Analyze Media' or @text='Verify Now' or contains(@text, 'Scan')]")
    BACK_BUTTON = (AppiumBy.XPATH, "//android.widget.ImageButton | //*[contains(@content-desc, 'Back') or contains(@content-desc, 'Navigate up')]")
    PICK_FILE_BUTTON = (AppiumBy.XPATH, "//*[contains(@text, 'Upload') or contains(@text, 'Select File') or contains(@text, 'Choose Image')]")

    # Text Scanner Locators
    TEXT_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[contains(@hint, 'message') or contains(@hint, 'text') or contains(@text, '')]")
    PASTE_BUTTON = (AppiumBy.XPATH, "//*[contains(@text, 'Paste')]")

    # URL Scanner Locators
    URL_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[contains(@hint, 'http') or contains(@hint, 'url') or contains(@hint, 'link')]")

    # Profile Scanner Locators
    USERNAME_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[contains(@hint, 'username')]")
    FOLLOWERS_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[contains(@hint, 'followers')]")
    FOLLOWING_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[contains(@hint, 'following')]")
    BIO_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[contains(@hint, 'bio')]")

    # Processing / Scanning Indicator
    SCANNING_SPINNER = (AppiumBy.XPATH, "//*[contains(@text, 'Scanning') or contains(@text, 'Analyzing') or contains(@text, 'Processing')]")

    def enter_scam_text(self, text: str):
        self.type_text(*self.TEXT_INPUT, text)

    def enter_url(self, url: str):
        self.type_text(*self.URL_INPUT, url)

    def enter_profile_data(self, username: str, followers: str, following: str, bio: str):
        self.type_text(*self.USERNAME_INPUT, username)
        self.type_text(*self.FOLLOWERS_INPUT, followers)
        self.type_text(*self.FOLLOWING_INPUT, following)
        self.type_text(*self.BIO_INPUT, bio)

    def tap_start_scan(self):
        self.click(*self.START_SCAN_BUTTON)

    def tap_pick_file(self):
        self.click(*self.PICK_FILE_BUTTON)

    def tap_back(self):
        self.click(*self.BACK_BUTTON)

    def is_scanning_in_progress(self) -> bool:
        return self.is_visible(*self.SCANNING_SPINNER, timeout=3)
