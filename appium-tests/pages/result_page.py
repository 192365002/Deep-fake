"""
Scan Result Page Object for Social Shield
Validates deepfake verdicts, confidence meters, XAI explanations, and recommendations.
"""
from appium.webdriver.common.appiumby import AppiumBy
from pages.base_page import BasePage


class ResultPage(BasePage):
    # Verdict & Confidence Locators
    VERDICT_BADGE = (AppiumBy.XPATH, "//*[@text='FAKE' or @text='REAL' or @text='SUSPICIOUS' or @text='SAFE']")
    CONFIDENCE_LABEL = (AppiumBy.XPATH, "//android.widget.TextView[contains(@text, '%')]")
    RISK_LEVEL_BADGE = (AppiumBy.XPATH, "//*[contains(@text, 'HIGH') or contains(@text, 'MEDIUM') or contains(@text, 'LOW')]")

    # Explainable AI & Recommendations
    EXPLANATION_SECTION = (AppiumBy.XPATH, "//*[contains(@text, 'Explanation') or contains(@text, 'Indicators') or contains(@text, 'Analysis Details')]")
    RECOMMENDATION_SECTION = (AppiumBy.XPATH, "//*[contains(@text, 'Recommendation') or contains(@text, 'Action Steps')]")

    # Action Buttons
    DONE_BUTTON = (AppiumBy.XPATH, "//*[@text='Done' or @text='Close' or @text='Back to Dashboard']")
    SHARE_BUTTON = (AppiumBy.XPATH, "//*[contains(@text, 'Share') or contains(@content-desc, 'Share')]")

    def get_verdict(self) -> str:
        return self.get_text(*self.VERDICT_BADGE)

    def is_result_displayed(self, timeout: int = 40) -> bool:
        return self.is_visible(*self.VERDICT_BADGE, timeout=timeout)

    def tap_done(self):
        if self.is_visible(*self.DONE_BUTTON, timeout=5):
            self.click(*self.DONE_BUTTON)
        else:
            self.driver.back()

    def tap_share(self):
        self.click(*self.SHARE_BUTTON)
