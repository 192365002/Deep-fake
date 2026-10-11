"""
Authentication Page Object for Social Shield
Manages login, registration, password recovery, and error feedback elements.
"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class AuthPage(BasePage):
    # Locators (Jetpack Compose texts and accessibility descriptions)
    EMAIL_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[contains(@text, 'Email') or contains(@hint, 'Email')] | //android.widget.EditText[1]")
    PASSWORD_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[contains(@hint, 'Password')] | //android.widget.EditText[2]")
    SIGN_IN_BUTTON = (AppiumBy.XPATH, "//*[@text='Sign In' or @text='SIGN IN']")
    SIGN_UP_BUTTON = (AppiumBy.XPATH, "//*[@text='Sign Up' or @text='SIGN UP' or @text='Create Account']")
    SIGN_UP_TAB = (AppiumBy.XPATH, "//*[@text='Sign Up' or @text='Create an Account']")
    SIGN_IN_TAB = (AppiumBy.XPATH, "//*[@text='Sign In' or @text='Already have an account? Sign In']")
    GOOGLE_BUTTON = (AppiumBy.XPATH, "//*[contains(@text, 'Google') or contains(@content-desc, 'Google')]")
    FORGOT_PASSWORD_LINK = (AppiumBy.XPATH, "//*[contains(@text, 'Forgot Password')]")
    ERROR_MESSAGE = (AppiumBy.XPATH, "//android.widget.TextView[contains(@text, 'required') or contains(@text, 'failed') or contains(@text, 'Invalid') or contains(@text, 'error')]")

    def enter_email(self, email: str):
        self.type_text(*self.EMAIL_INPUT, email)

    def enter_password(self, password: str):
        self.type_text(*self.PASSWORD_INPUT, password)

    def tap_sign_in(self):
        self.click(*self.SIGN_IN_BUTTON)

    def tap_sign_up(self):
        self.click(*self.SIGN_UP_BUTTON)

    def tap_google_sign_in(self):
        self.click(*self.GOOGLE_BUTTON)

    def tap_forgot_password(self):
        self.click(*self.FORGOT_PASSWORD_LINK)

    def switch_to_sign_up(self):
        if self.is_visible(*self.SIGN_UP_TAB, timeout=3):
            self.click(*self.SIGN_UP_TAB)

    def switch_to_sign_in(self):
        if self.is_visible(*self.SIGN_IN_TAB, timeout=3):
            self.click(*self.SIGN_IN_TAB)

    def get_error_text(self) -> str:
        return self.get_text(*self.ERROR_MESSAGE)

    def is_error_displayed(self) -> bool:
        return self.is_visible(*self.ERROR_MESSAGE, timeout=4)

    def login_with_credentials(self, email: str, password: str):
        """Helper to execute full login sequence"""
        self.enter_email(email)
        self.enter_password(password)
        self.tap_sign_in()
