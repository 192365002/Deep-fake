"""
Social Shield Appium E2E Automation - Configuration
Defines Appium capabilities, device configurations, application paths, and test timeouts.
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR.parent
APK_PATH = WORKSPACE_DIR / "backend" / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
REPORTS_DIR = BASE_DIR / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"

# Ensure directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Appium Server Details
APPIUM_SERVER_URL = os.getenv("APPIUM_SERVER_URL", "http://127.0.0.1:4723")

# Android Device Configuration
# Defaults to Redmi Note 13 Pro (connected device) with automatic fallback
DEVICE_NAME = os.getenv("DEVICE_NAME", "Redmi Note 13 Pro 5G")
UDID = os.getenv("ANDROID_UDID", "S8Q4RS5LOFWGPBX8")
PLATFORM_VERSION = os.getenv("PLATFORM_VERSION", "14.0")

# App Package & Activity Details
APP_PACKAGE = "com.socialshield"
APP_ACTIVITY = "com.socialshield.MainActivity"

# Desired Capabilities
DESIRED_CAPABILITIES = {
    "platformName": "Android",
    "automationName": "UiAutomator2",
    "deviceName": DEVICE_NAME,
    "udid": UDID,
    "app": str(APK_PATH) if APK_PATH.exists() else None,
    "appPackage": APP_PACKAGE,
    "appActivity": APP_ACTIVITY,
    "noReset": True,
    "fullReset": False,
    "autoGrantPermissions": True,
    "newCommandTimeout": 300,
    "uiautomator2ServerInstallTimeout": 60000,
    "uiautomator2ServerLaunchTimeout": 60000,
    "adbExecTimeout": 60000
}

# Timeout Constants (Seconds)
EXPLICIT_WAIT = 15
IMPLICIT_WAIT = 5
PAGE_LOAD_TIMEOUT = 30
INFERENCE_TIMEOUT = 45

# Backend & Supabase Live Endpoints for E2E Validation
BACKEND_BASE_URL = "https://web-production-35465.up.railway.app"
SUPABASE_URL = "https://imnrnjkrtiruwtimawbu.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_vOQtn1DodrWRR1__jwlH8w_NIKD3bRh"
