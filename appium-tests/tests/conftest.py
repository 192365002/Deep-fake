"""
Pytest Fixtures for Social Shield Appium Automation
Handles driver setup, teardown, test session hooks, and failure screenshots.
"""
import pytest
import logging
from utils.driver_factory import DriverFactory

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def appium_driver():
    """Session-scoped fixture providing the Appium WebDriver"""
    driver = DriverFactory.create_driver()
    yield driver
    DriverFactory.quit_driver()


@pytest.fixture(scope="function")
def driver(appium_driver):
    """Function-scoped fixture ensuring clean state between tests"""
    yield appium_driver


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture failure screenshots automatically"""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        driver = item.funcargs.get("driver")
        if driver:
            try:
                screenshot_name = f"fail_{item.name}"
                driver.save_screenshot(f"reports/screenshots/{screenshot_name}.png")
                logger.error(f"Captured failure screenshot for {item.name}")
            except Exception as e:
                logger.warning(f"Could not take screenshot on test failure: {e}")
