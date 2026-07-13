import os

from config import REPORTS_DIR, REPORT_DATE


def export_report(report_lines):
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    report_path = os.path.join(REPORTS_DIR, "report_" + REPORT_DATE + ".md")

    with open(report_path, "w", encoding="utf-8") as report_file:
        for line in report_lines:
            report_file.write(line + "\n")

    print("\nRapor dosyaya yazildi:", report_path)
