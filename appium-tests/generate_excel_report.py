"""
Stand-alone entrypoint to generate the 340 Test Cases Excel Report.
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.excel_report_generator import generate_excel_report

if __name__ == "__main__":
    report_path = generate_excel_report()
    print(f"\n[SUCCESS] Excel Test Report generated at:\n{report_path}")
