from collections import defaultdict

from config import (
    AUTHENTICATION_PATHS,
    DETECTION_WINDOW_SECONDS,
    FAILED_LOGIN_STATUS_CODES,
    SCORE_401,
    SCORE_403,
    SCORE_BRUTE_FORCE_BONUS,
    SCORE_FAILED_LOGIN,
    SCORE_PATH_TRAVERSAL,
    SCORE_SCANNER,
    TARGET_URLS,
)
from detection import find_brute_force_ips, find_scanner_ips
from headers_check import run_header_checks
from log_parser import (
    canonicalize_request_path,
    has_path_traversal,
    parse_log_line,
)
from recommendations import generate_checklist, get_recommendation
from report_writer import export_report
from scoring import classify_incident, get_severity

log_file = "logs/sample_access.log"


def _score_incident(
    unauthorized_count,
    forbidden_count,
    failed_login_count,
    brute_force,
    scanner,
    path_traversal,
):
    score = (
        unauthorized_count * SCORE_401
        + forbidden_count * SCORE_403
        + failed_login_count * SCORE_FAILED_LOGIN
    )

    if brute_force:
        score += SCORE_BRUTE_FORCE_BONUS
    if scanner:
        score += SCORE_SCANNER
    if path_traversal:
        score += SCORE_PATH_TRAVERSAL

    return score


def _empty_report(skipped_lines):
    return [
        "# Incident Classification Report",
        "",
        "Toplam okunan log satiri: 0",
        f"Atlanan satir sayisi: {skipped_lines}",
        "",
        "Gecerli veri bulunamadigi icin analiz yapilamadi.",
        "",
    ]


def analyze_logs(file_path, include_header_check=True, write_report=True):
    ip_counts = defaultdict(int)
    status_counts = defaultdict(int)
    unauthorized_counts = defaultdict(int)
    forbidden_counts = defaultdict(int)
    failed_login_counts = defaultdict(int)
    failed_login_events = defaultdict(list)
    untimed_failed_login_counts = defaultdict(int)
    ip_paths = defaultdict(set)
    ip_path_events = defaultdict(list)
    untimed_ip_paths = defaultdict(set)
    path_traversal_ips = set()

    total_lines = 0
    skipped_lines = 0
    timestamped_lines = 0
    untimestamped_lines = 0

    try:
        with open(file_path, "r", encoding="utf-8") as log_handle:
            for raw_line in log_handle:
                if not raw_line.strip():
                    continue

                entry = parse_log_line(raw_line)
                if entry is None:
                    skipped_lines += 1
                    continue

                ip = entry.ip
                path = entry.path
                canonical_path = canonicalize_request_path(path)
                status_code = entry.status_code

                ip_counts[ip] += 1
                status_counts[status_code] += 1
                ip_paths[ip].add(canonical_path)
                total_lines += 1

                if entry.timestamp is None:
                    untimestamped_lines += 1
                    untimed_ip_paths[ip].add(canonical_path)
                else:
                    timestamped_lines += 1
                    ip_path_events[ip].append((entry.timestamp, canonical_path))

                if has_path_traversal(path):
                    path_traversal_ips.add(ip)

                if status_code == "401":
                    unauthorized_counts[ip] += 1

                normalized_auth_path = canonical_path.casefold().rstrip("/") or "/"
                if (
                    status_code in FAILED_LOGIN_STATUS_CODES
                    and normalized_auth_path in AUTHENTICATION_PATHS
                ):
                    failed_login_counts[ip] += 1
                    if entry.timestamp is None:
                        untimed_failed_login_counts[ip] += 1
                    else:
                        failed_login_events[ip].append(entry.timestamp)

                if status_code == "403":
                    forbidden_counts[ip] += 1

    except (FileNotFoundError, OSError) as error:
        print(f"Log dosyasi okunamadi: {file_path} ({type(error).__name__})")
        return []

    if total_lines == 0:
        print("\nGecerli log satiri bulunamadi (dosya bos veya tum satirlar hatali).")
        print("Atlanan satir sayisi:", skipped_lines)
        if write_report:
            export_report(_empty_report(skipped_lines))
        return []

    brute_force_ips = find_brute_force_ips(
        failed_login_events,
        untimed_failed_login_counts,
    )
    scanner_ips = find_scanner_ips(
        ip_path_events,
        untimed_ip_paths,
    )

    print("\n=== SECURE AI LOG ANALYSIS ===\n")
    print("Toplam okunan log satiri:", total_lines)
    print("Zaman damgali satir:", timestamped_lines)
    print("Zaman damgasiz satir:", untimestamped_lines)
    print("Atlanan satir sayisi:", skipped_lines)
    print("Tespit zaman penceresi (saniye):", DETECTION_WINDOW_SECONDS)

    report_lines = [
        "# Incident Classification Report",
        "",
        f"Toplam okunan log satiri: {total_lines}",
        f"Zaman damgali satir sayisi: {timestamped_lines}",
        f"Zaman damgasiz satir sayisi: {untimestamped_lines}",
        f"Atlanan satir sayisi: {skipped_lines}",
        f"Brute force/scanner zaman penceresi: {DETECTION_WINDOW_SECONDS} saniye",
        "",
    ]

    high_severity_count = 0
    total_forbidden = sum(forbidden_counts.values())
    dashboard_data = []

    for ip in sorted(ip_counts):
        unauthorized_count = unauthorized_counts[ip]
        forbidden_count = forbidden_counts[ip]
        failed_login_count = failed_login_counts[ip]
        brute_force = ip in brute_force_ips
        scanner = ip in scanner_ips
        path_traversal = ip in path_traversal_ips
        different_path_count = len(ip_paths[ip])

        score = _score_incident(
            unauthorized_count,
            forbidden_count,
            failed_login_count,
            brute_force,
            scanner,
            path_traversal,
        )
        severity = get_severity(score)
        if severity in {"HIGH", "CRITICAL"}:
            high_severity_count += 1

        incident_type = classify_incident(
            failed_login_count,
            forbidden_count,
            brute_force,
            path_traversal,
            scanner,
            score,
        )
        recommendation = get_recommendation(incident_type)

        detection_basis = []
        if brute_force:
            detection_basis.append("windowed_or_legacy_brute_force")
        if scanner:
            detection_basis.append("windowed_or_legacy_scanner")
        if path_traversal:
            detection_basis.append("path_traversal")

        report_lines.extend(
            [
                f"## IP: {ip}",
                f"- Request Count: {ip_counts[ip]}",
                f"- Unauthorized (401): {unauthorized_count}",
                f"- Forbidden (403): {forbidden_count}",
                f"- Failed Login: {failed_login_count}",
                f"- Brute Force: {brute_force}",
                f"- Farkli Path Sayisi: {different_path_count}",
                f"- Scanner Activity: {scanner}",
                f"- Path Traversal: {path_traversal}",
                f"- Score: {score}",
                f"- Severity: {severity}",
                f"- Incident Type: {incident_type}",
                f"- Recommended Action: {recommendation}",
                "",
            ]
        )

        dashboard_data.append(
            {
                "ip": ip,
                "request_count": ip_counts[ip],
                "score": score,
                "severity": severity,
                "incident_type": incident_type,
                "recommendation": recommendation,
                "unauthorized_count": unauthorized_count,
                "forbidden_count": forbidden_count,
                "failed_login_count": failed_login_count,
                "different_path_count": different_path_count,
                "brute_force": brute_force,
                "scanner_activity": scanner,
                "path_traversal": path_traversal,
                "detection_basis": detection_basis,
            }
        )

    checklist_lines = generate_checklist(
        brute_force_ips,
        total_forbidden,
        high_severity_count,
        scanner_ips,
        path_traversal_ips,
    )
    report_lines.append("## Security Checklist")
    report_lines.extend(f"- {item}" for item in checklist_lines)
    report_lines.append("")

    if include_header_check:
        header_report_lines, _ = run_header_checks(TARGET_URLS)
        report_lines.extend(header_report_lines)

    if write_report:
        export_report(report_lines)

    print("Analiz tamamlandi.")
    return dashboard_data


if __name__ == "__main__":
    analyze_logs(log_file)
