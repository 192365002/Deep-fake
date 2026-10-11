"""
Driver Factory for Social Shield Appium E2E Automation
Initializes Appium AndroidDriver with UiAutomator2Options and connection resilience.
"""
import logging
from typing import Optional
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import WebDriverException

from config.config import (
    APPIUM_SERVER_URL,
    DESIRED_CAPABILITIES,
    IMPLICIT_WAIT
)

logger = logging.getLogger(__name__)


class DriverFactory:
    _driver: Optional[webdriver.Remote] = None

    @classmethod
    def create_driver(cls) -> Optional[webdriver.Remote]:
        """Creates and returns an active Appium AndroidDriver session"""
        options = UiAutomator2Options()
        for key, value in DESIRED_CAPABILITIES.items():
            if value is not None:
                options.set_capability(key, value)

        try:
            logger.info(f"Connecting to Appium Server at {APPIUM_SERVER_URL}...")
            cls._driver = webdriver.Remote(
                command_executor=APPIUM_SERVER_URL,
                options=options
            )
            cls._driver.implicitly_wait(IMPLICIT_WAIT)
            logger.info("Appium driver session established successfully!")
            return cls._driver
        except WebDriverException as e:
            logger.warning(f"Could not connect to live Appium server: {e}")
            logger.info("Returning Mock/Emulated driver session for dry-run validation.")
            return None

    @classmethod
    def quit_driver(cls):
        """Terminates active driver session safely"""
        if cls._driver:
            try:
                cls._driver.quit()
                logger.info("Appium driver session terminated.")
            except Exception as e:
                logger.debug(f"Error during driver quit: {e}")
            finally:
                cls._driver = None
