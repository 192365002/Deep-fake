"""
Settings & Preferences Page Object for Social Shield
Controls dark/light theme switch, auto-scan toggles, push notifications, and sign-out.
"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class SettingsPage(BasePage):
    # Setting Switches & Locators
    DARK_MODE_SWITCH = (AppiumBy.XPATH, "//*[contains(@text, 'Dark Mode')]/following-sibling::android.widget.Switch | //*[contains(@text, 'Dark Mode')]")
    NOTIFICATIONS_SWITCH = (AppiumBy.XPATH, "//*[contains(@text, 'Notifications')]/following-sibling::android.widget.Switch | //*[contains(@text, 'Notifications')]")
    AUTO_SCAN_SWITCH = (AppiumBy.XPATH, "//*[contains(@text, 'Auto') or contains(@text, 'Real-time Guard')]")
    
    # Account & Session
    USER_EMAIL_TEXT = (AppiumBy.XPATH, "//android.widget.TextView[contains(@text, '@')]")
    SIGN_OUT_BUTTON = (AppiumBy.XPATH, "//*[@text='Sign Out' or @text='Log Out' or contains(@text, 'Sign Out')]")
    CONFIRM_LOGOUT = (AppiumBy.XPATH, "//*[@text='Confirm' or @text='Yes' or @text='Sign Out']")

    def toggle_dark_mode(self):
        self.click(*self.DARK_MODE_SWITCH)

    def toggle_notifications(self):
        self.click(*self.NOTIFICATIONS_SWITCH)

    def toggle_auto_scan(self):
        self.click(*self.AUTO_SCAN_SWITCH)

    def tap_sign_out(self):
        self.click(*self.SIGN_OUT_BUTTON)
        if self.is_visible(*self.CONFIRM_LOGOUT, timeout=3):
            self.click(*self.CONFIRM_LOGOUT)
