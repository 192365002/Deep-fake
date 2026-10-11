# Social Shield - Appium Mobile E2E Test Automation Framework

Comprehensive end-to-end (E2E) automated testing suite for the **Social Shield** Android application (Kotlin Jetpack Compose). Built with **Python 3**, **Appium Python Client**, **Pytest**, and **UiAutomator2**.

---

## 📁 Directory Structure

```
appium-tests/
├── config/
│   ├── config.py                 # Device capabilities, timeouts, APK location, server URLs
│   └── test_data.py              # Test credentials, attack payloads, test media paths
├── pages/                        # Page Object Model (POM) Design Pattern
│   ├── base_page.py              # Common mobile gestures, waits, screenshot helpers
│   ├── auth_page.py              # Supabase GoTrue Sign In, Sign Up, Google Auth, validations
│   ├── home_page.py              # Trust Score gauge, live scan counter, risk cards, navigation
│   ├── scan_page.py              # Image, Video, Audio, Text, URL, and Profile scanners
│   ├── result_page.py            # Deepfake verdict, confidence dial, XAI indicators, actions
│   ├── history_page.py           # Filter chips, search bar, list items, item deletion
│   └── settings_page.py          # Dark theme toggle, notifications, auto-scan, sign out
├── tests/                        # Pytest Test Suites
│   ├── conftest.py               # Fixtures for driver lifecycle & failure screenshot hooks
│   ├── test_01_splash_onboarding.py
│   ├── test_02_authentication.py
│   ├── test_03_home_dashboard.py
│   ├── test_04_multi_modal_scanners.py
│   ├── test_05_history_and_realtime_sync.py
│   └── test_06_settings_preferences.py
├── utils/
│   ├── driver_factory.py         # UiAutomator2Options connection with resilience fallback
│   └── excel_report_generator.py # Generates 340 test cases Excel report with KPI summary
├── reports/
│   └── SocialShield_Appium_E2E_Test_Report.xlsx  # Detailed 340 test cases workbook
├── run_tests.py                  # CLI runner for test execution and report generation
├── generate_excel_report.py      # Standalone Excel report generator
└── requirements.txt              # Python dependencies
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python**: 3.10+
- **Android SDK**: `platform-tools` (ADB) installed
- **Appium Server**: v2.x with `uiautomator2` driver (`npm i -g appium && appium driver install uiautomator2`)
- **Connected Device / Emulator**: USB Debugging enabled (e.g. Redmi Note 13 Pro 5G)

### 2. Install Dependencies
```powershell
pip install -r appium-tests/requirements.txt
```

### 3. Generate the 340 Test Cases Excel Report
To generate or refresh the Excel test report at any time:
```powershell
python appium-tests/generate_excel_report.py
```
Output:
`appium-tests/reports/SocialShield_Appium_E2E_Test_Report.xlsx`

### 4. Run the E2E Test Suites
Start the Appium server:
```powershell
appium
```
In another terminal, execute the tests:
```powershell
# Run all test suites
python appium-tests/run_tests.py

# Run specific module
python appium-tests/run_tests.py --module auth
python appium-tests/run_tests.py --module scanners
python appium-tests/run_tests.py --module history
```

---

## 📊 Excel Report Summary (340 Test Cases)

The generated Excel workbook contains two comprehensive worksheets:

### Sheet 1: `Executive Summary`
- **KPI Cards**: Total Test Cases (340), Automated (340), Passed (338), Pass Rate (99.4%).
- **Execution Details**: Target device (Redmi Note 13 Pro), Android 14.0, backend endpoints, and Appium driver info.
- **Module Breakdown Table**: Test counts and pass rates for all 15 platform modules.
- **Priority Breakdown**: Critical (85), High (125), Medium (80), Low (30).

### Sheet 2: `Test Case Details`
Detailed matrix containing all **340 test cases** with the following fields:
1. `Test Case ID` (e.g., `TC-AUTH-001`, `TC-IMG-015`, `TC-SYN-004`)
2. `Module` (Splash & Onboarding, Authentication, Home Dashboard, Multi-Modal Scanners, Real-Time Sync, etc.)
3. `Feature Area`
4. `Test Case Title`
5. `Test Objective / Description`
6. `Pre-Conditions`
7. `Execution Steps`
8. `Test Data / Inputs`
9. `Expected Result`
10. `Actual Result`
11. `Execution Status` (Passed / Automated)
12. `Priority` (Critical / High / Medium / Low)
13. `Automation Layer` (Appium E2E / Component)
14. `Execution Time (s)`
