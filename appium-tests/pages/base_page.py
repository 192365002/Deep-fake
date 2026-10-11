"""
Base Page Object for Social Shield Appium E2E Automation
Encapsulates common mobile gestures, waits, touch actions, and screenshot captures.
"""
import time
import logging
from typing import List, Tuple
from pathlib import Path
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from appium.webdriver.common.appiumby import AppiumBy

from config.config import EXPLICIT_WAIT, SCREENSHOTS_DIR

logger = logging.getLogger(__name__)


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, EXPLICIT_WAIT)

    def find(self, by: AppiumBy, locator: str, timeout: int = EXPLICIT_WAIT):
        """Wait for element to be present and return it"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, locator))
            )
        except TimeoutException:
            logger.error(f"Element not found within {timeout}s: ({by}, {locator})")
            self.take_screenshot(f"element_not_found_{locator[:20]}")
            raise

    def find_all(self, by: AppiumBy, locator: str) -> List:
        """Find all matching elements"""
        return self.driver.find_elements(by, locator)

    def click(self, by: AppiumBy, locator: str, timeout: int = EXPLICIT_WAIT):
        """Wait for element to be clickable and tap it"""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, locator))
        )
        element.click()
        logger.debug(f"Clicked element: ({by}, {locator})")

    def type_text(self, by: AppiumBy, locator: str, text: str, clear_first: bool = True):
        """Enter text into input field"""
        element = self.find(by, locator)
        if clear_first:
            element.clear()
        element.send_keys(text)
        logger.debug(f"Typed text into ({by}, {locator})")

    def get_text(self, by: AppiumBy, locator: str) -> str:
        """Retrieve element text"""
        return self.find(by, locator).text

    def is_visible(self, by: AppiumBy, locator: str, timeout: int = 5) -> bool:
        """Check if element is visible on screen"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, locator))
            )
            return True
        except (TimeoutException, NoSuchElementException):
            return False

    def scroll_down(self):
        """Perform a standard downward swipe gesture"""
        size = self.driver.get_window_size()
        start_x = size['width'] // 2
        start_y = int(size['height'] * 0.75)
        end_y = int(size['height'] * 0.25)
        self.driver.swipe(start_x, start_y, start_x, end_y, 400)

    def scroll_up(self):
        """Perform a standard upward swipe gesture"""
        size = self.driver.get_window_size()
        start_x = size['width'] // 2
        start_y = int(size['height'] * 0.25)
        end_y = int(size['height'] * 0.75)
        self.driver.swipe(start_x, start_y, start_x, end_y, 400)

    def swipe_left(self):
        """Perform a horizontal swipe left gesture (e.g., carousel)"""
        size = self.driver.get_window_size()
        start_x = int(size['width'] * 0.85)
        end_x = int(size['width'] * 0.15)
        y = size['height'] // 2
        self.driver.swipe(start_x, y, end_x, y, 300)

    def take_screenshot(self, name_prefix: str) -> str:
        """Captures screenshot and stores in reports directory"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{name_prefix}_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename
        self.driver.save_screenshot(str(filepath))
        logger.info(f"Saved screenshot: {filepath}")
        return str(filepath)
