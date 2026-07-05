from collections import defaultdict
import os
from datetime import datetime

log_file = "logs/sample_access.log"

BRUTE_FORCE_LIMIT = 5

SCORE_401 = 2
SCORE_403 = 3
SCORE_FAILED_LOGIN = 5
SCORE_BRUTE_FORCE_BONUS = 10

SEVERITY_LOW_MAX = 4
SEVERITY_MEDIUM_MAX = 9

FAILED_LOGIN_LIMIT = 3
FORBIDDEN_LIMIT = 3
SUSPICIOUS_SCORE_LIMIT = 5

REPORTS_DIR = "reports"


def get_severity(score):
    if score <= SEVERITY_LOW_MAX:
        return "LOW"
    elif score <= SEVERITY_MEDIUM_MAX:
        return "MEDIUM"
    else:
        return "HIGH"


def classify_incident(failed_login_count, forbidden_count, brute_force, score):
    if brute_force:
        return "BRUTE_FORCE"
    elif failed_login_count >= FAILED_LOGIN_LIMIT:
        return "UNAUTHORIZED_ACCESS"
    elif forbidden_count >= FORBIDDEN_LIMIT:
        return "FORBIDDEN_ACCESS"
    elif score >= SUSPICIOUS_SCORE_LIMIT:
        return "SUSPICIOUS_ACTIVITY"
    else:
        return "NORMAL"


def get_recommendation(incident_type):
    if incident_type == "BRUTE_FORCE":
        return "IP engellenmeli (block)"
    elif incident_type == "UNAUTHORIZED_ACCESS":
        return "Rate limiting uygulanmali"
    elif incident_type == "FORBIDDEN_ACCESS":
        return "Erisim yetkileri gozden gecirilmeli"
    elif incident_type == "SUSPICIOUS_ACTIVITY":
        return "Izlemeye devam edilmeli (monitoring)"
    else:
        return "Aksiyon gerekmiyor"


def export_report(report_lines):
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    today_str = datetime.now().strftime("%Y%m%d")
    report_path = os.path.join(REPORTS_DIR, "report_" + today_str + ".md")

    with open(report_path, "w", encoding="utf-8") as report_file:
        for line in report_lines:
            report_file.write(line + "\n")

    print("\nRapor dosyaya yazildi:", report_path)


def analyze_logs(file_path):

    ip_counts = defaultdict(int)
    status_counts = defaultdict(int)
    unauthorized_counts = defaultdict(int)
    forbidden_counts = defaultdict(int)
    failed_login_counts = defaultdict(int)
    brute_force_ips = set()

    total_lines = 0
    skipped_lines = 0

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line == "":
                    continue

                parts = line.split()

                if len(parts) < 4:
                    skipped_lines += 1
                    continue

                ip = parts[0]
                path = parts[2]
                status_code = parts[3]

                ip_counts[ip] += 1
                status_counts[status_code] += 1
                total_lines += 1

                if status_code == "401":
                    unauthorized_counts[ip] += 1
                    if path == "/login":
                        failed_login_counts[ip] += 1

                if status_code == "403":
                    forbidden_counts[ip] += 1

    except FileNotFoundError:
        print("Log dosyasi bulunamadi:", file_path)
        return

    for ip, count in failed_login_counts.items():
        if count >= BRUTE_FORCE_LIMIT:
            brute_force_ips.add(ip)

    print("\n=== DAY 10 - REPORT GENERATION ===\n")
    print("Toplam okunan log satiri:", total_lines)
    print("Atlanan satir sayisi:", skipped_lines)

    print("\n--- IP Bazli Request Sayilari ---")
    for ip, count in sorted(ip_counts.items(), key=lambda item: item[1], reverse=True):
        print(ip, "->", count, "request")

    print("\n--- HTTP Status Code Dagilimi ---")
    for status, count in sorted(status_counts.items()):
        print(status, "->", count, "adet")

    print("\n--- Brute Force Suphesi Olan IP Adresleri ---")
    if len(brute_force_ips) == 0:
        print("Brute force suphesi bulunmadi.")
    else:
        for ip in brute_force_ips:
            print(ip, "-> possible brute force detected")

    # Rapor dosyasina yazilacak satirlar burada biriktiriliyor.
    report_lines = []
    report_lines.append("# Incident Classification Report")
    report_lines.append("")
    report_lines.append("Toplam okunan log satiri: " + str(total_lines))
    report_lines.append("Atlanan satir sayisi: " + str(skipped_lines))
    report_lines.append("")

    print("\n--- Incident Classification Summary ---")
    for ip in sorted(ip_counts.keys()):
        unauthorized_count = unauthorized_counts[ip]
        forbidden_count = forbidden_counts[ip]
        failed_login_count = failed_login_counts[ip]
        brute_force = ip in brute_force_ips

        score = (unauthorized_count * SCORE_401) + (forbidden_count * SCORE_403) + (failed_login_count * SCORE_FAILED_LOGIN)
        if brute_force:
            score += SCORE_BRUTE_FORCE_BONUS

        severity = get_severity(score)
        incident_type = classify_incident(failed_login_count, forbidden_count, brute_force, score)
        recommendation = get_recommendation(incident_type)

        print("\nIP:", ip)
        print("Request Count:", ip_counts[ip])
        print("Unauthorized (401):", unauthorized_count)
        print("Forbidden (403):", forbidden_count)
        print("Failed Login:", failed_login_count)
        print("Brute Force:", brute_force)
        print("Score:", score)
        print("Severity:", severity)
        print("Incident Type:", incident_type)
        print("Recommended Action:", recommendation)

        report_lines.append("## IP: " + ip)
        report_lines.append("- Request Count: " + str(ip_counts[ip]))
        report_lines.append("- Unauthorized (401): " + str(unauthorized_count))
        report_lines.append("- Forbidden (403): " + str(forbidden_count))
        report_lines.append("- Failed Login: " + str(failed_login_count))
        report_lines.append("- Brute Force: " + str(brute_force))
        report_lines.append("- Score: " + str(score))
        report_lines.append("- Severity: " + severity)
        report_lines.append("- Incident Type: " + incident_type)
        report_lines.append("- Recommended Action: " + recommendation)
        report_lines.append("")

    export_report(report_lines)

    print("\nAnaliz tamamlandi.")


analyze_logs(log_file)
