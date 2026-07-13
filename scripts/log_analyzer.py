from collections import defaultdict

from config import (
    PATH_TRAVERSAL_PATTERN,
    SCORE_401,
    SCORE_403,
    SCORE_FAILED_LOGIN,
    SCORE_BRUTE_FORCE_BONUS,
    SCORE_SCANNER,
    SCORE_PATH_TRAVERSAL,
    TARGET_URLS,
)
from detection import find_brute_force_ips, find_scanner_ips
from scoring import get_severity, classify_incident
from recommendations import get_recommendation, generate_checklist
from headers_check import run_header_checks
from report_writer import export_report

log_file = "logs/sample_access.log"


def analyze_logs(file_path):

    ip_counts = defaultdict(int)
    status_counts = defaultdict(int)
    unauthorized_counts = defaultdict(int)
    forbidden_counts = defaultdict(int)
    failed_login_counts = defaultdict(int)
    ip_paths = defaultdict(set)
    path_traversal_ips = set()

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
                ip_paths[ip].add(path)
                total_lines += 1

                if PATH_TRAVERSAL_PATTERN in path:
                    path_traversal_ips.add(ip)

                if status_code == "401":
                    unauthorized_counts[ip] += 1
                    if path == "/login":
                        failed_login_counts[ip] += 1

                if status_code == "403":
                    forbidden_counts[ip] += 1

    except FileNotFoundError:
        print("Log dosyasi bulunamadi:", file_path)
        return

    brute_force_ips = find_brute_force_ips(failed_login_counts)
    scanner_ips = find_scanner_ips(ip_paths)

    print("\n=== DAY 16 - COK DOSYALI MIMARIYE GECIS ===\n")
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

    print("\n--- Scanner Activity Suphesi Olan IP Adresleri ---")
    if len(scanner_ips) == 0:
        print("Scanner activity suphesi bulunmadi.")
    else:
        for ip in scanner_ips:
            print(ip, "->", len(ip_paths[ip]), "farkli path -> possible scanner activity")

    print("\n--- Path Traversal Denemesi Olan IP Adresleri ---")
    if len(path_traversal_ips) == 0:
        print("Path traversal denemesi bulunmadi.")
    else:
        for ip in path_traversal_ips:
            print(ip, "-> path traversal pattern tespit edildi")

    report_lines = []
    report_lines.append("# Incident Classification Report")
    report_lines.append("")
    report_lines.append("Toplam okunan log satiri: " + str(total_lines))
    report_lines.append("Atlanan satir sayisi: " + str(skipped_lines))
    report_lines.append("")

    print("\n--- Incident Classification Summary ---")
    high_severity_count = 0
    total_forbidden = sum(forbidden_counts.values())
    for ip in sorted(ip_counts.keys()):
        unauthorized_count = unauthorized_counts[ip]
        forbidden_count = forbidden_counts[ip]
        failed_login_count = failed_login_counts[ip]
        brute_force = ip in brute_force_ips
        scanner = ip in scanner_ips
        path_traversal = ip in path_traversal_ips
        different_path_count = len(ip_paths[ip])

        score = (unauthorized_count * SCORE_401) + (forbidden_count * SCORE_403) + (failed_login_count * SCORE_FAILED_LOGIN)
        if brute_force:
            score += SCORE_BRUTE_FORCE_BONUS
        if scanner:
            score += SCORE_SCANNER
        if path_traversal:
            score += SCORE_PATH_TRAVERSAL

        severity = get_severity(score)
        if severity == "HIGH":
            high_severity_count += 1
        incident_type = classify_incident(failed_login_count, forbidden_count, brute_force, path_traversal, scanner, score)
        recommendation = get_recommendation(incident_type)

        print("\nIP:", ip)
        print("Request Count:", ip_counts[ip])
        print("Unauthorized (401):", unauthorized_count)
        print("Forbidden (403):", forbidden_count)
        print("Failed Login:", failed_login_count)
        print("Brute Force:", brute_force)
        print("Farkli Path Sayisi:", different_path_count)
        print("Scanner Activity:", scanner)
        print("Path Traversal:", path_traversal)
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
        report_lines.append("- Farkli Path Sayisi: " + str(different_path_count))
        report_lines.append("- Scanner Activity: " + str(scanner))
        report_lines.append("- Path Traversal: " + str(path_traversal))
        report_lines.append("- Score: " + str(score))
        report_lines.append("- Severity: " + severity)
        report_lines.append("- Incident Type: " + incident_type)
        report_lines.append("- Recommended Action: " + recommendation)
        report_lines.append("")

    print("\n--- Security Checklist ---")
    checklist_lines = generate_checklist(brute_force_ips, total_forbidden, high_severity_count, scanner_ips, path_traversal_ips)
    for checklist_item in checklist_lines:
        print(checklist_item)

    report_lines.append("## Security Checklist")
    for checklist_item in checklist_lines:
        report_lines.append("- " + checklist_item)
    report_lines.append("")

    header_report_lines, header_results = run_header_checks(TARGET_URLS)
    report_lines.extend(header_report_lines)

    export_report(report_lines)

    print("\nAnaliz tamamlandi.")


analyze_logs(log_file)
