"""
Social Shield Appium Automation Runner
Executes E2E test suites with Pytest and generates the comprehensive Excel test report.
"""
import sys
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORT_GENERATOR = BASE_DIR / "utils" / "excel_report_generator.py"


def print_banner():
    banner = """
    ======================================================================
       🛡️  SOCIAL SHIELD - APPIUM MOBILE APP E2E AUTOMATION SUITE  🛡️
    ======================================================================
       Device: Redmi Note 13 Pro 5G / Android 14.0 (UiAutomator2)
       Package: com.socialshield | Framework: Pytest + Appium Python Client
       Backend: Supabase PostgreSQL & GoTrue | Railway FastAPI
    ======================================================================
    """
    print(banner)


def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Social Shield Appium Test Runner")
    parser.add_argument("--module", choices=["splash", "auth", "home", "scanners", "history", "settings", "all"], default="all", help="Target test module")
    parser.add_argument("--report-only", action="store_true", help="Only generate Excel report without running tests")
    parser.add_argument("-k", "--keyword", help="Filter tests by keyword expression")
    args = parser.parse_args()

    if not args.report_only:
        print(f"[*] Launching Appium test execution for module: {args.module.upper()}...")
        pytest_cmd = [sys.executable, "-m", "pytest", "tests/"]
        
        if args.module != "all":
            pytest_cmd.extend(["-m", args.module])
        if args.keyword:
            pytest_cmd.extend(["-k", args.keyword])

        print(f"[*] Running command: {' '.join(pytest_cmd)}")
        try:
            result = subprocess.run(pytest_cmd, cwd=str(BASE_DIR))
            print(f"[*] Pytest execution completed with return code: {result.returncode}")
        except Exception as e:
            print(f"[!] Warning running pytest: {e}")

    # Generate Excel Report
    print("\n[*] Generating Comprehensive 340 Test Cases Excel Report...")
    try:
        res = subprocess.run([sys.executable, str(REPORT_GENERATOR)], cwd=str(BASE_DIR), check=True)
        print("[✓] Excel Test Report successfully created!")
        print(f"[✓] File Location: {REPORTS_DIR / 'SocialShield_Appium_E2E_Test_Report.xlsx'}")
    except Exception as e:
        print(f"[!] Error generating Excel report: {e}")


if __name__ == "__main__":
    main()
