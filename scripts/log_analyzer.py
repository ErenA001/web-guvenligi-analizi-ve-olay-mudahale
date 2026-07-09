from collections import defaultdict
import os
import urllib.request
import urllib.error

log_file = "logs/sample_access.log"

REPORT_DATE = "20260709"

HIGH_FORBIDDEN_THRESHOLD = 5

BRUTE_FORCE_LIMIT = 5
SCANNER_PATH_LIMIT = 5
PATH_TRAVERSAL_PATTERN = "../"

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

HEADER_CHECK_TIMEOUT = 5

TARGET_URLS = [
    "https://github.com",
    "https://www.python.org",
]

SECURITY_HEADERS = [
    ("Content-Security-Policy", "Injection ve XSS Koruma Eksikligi"),
    ("Strict-Transport-Security", "Insecure Transport"),
    ("X-Content-Type-Options", "Security Misconfiguration"),
    ("X-Frame-Options", "Clickjacking Koruma Eksikligi"),
    ("Referrer-Policy", "Security Misconfiguration"),
]


def get_severity(score):
    if score <= SEVERITY_LOW_MAX:
        return "LOW"
    elif score <= SEVERITY_MEDIUM_MAX:
        return "MEDIUM"
    else:
        return "HIGH"


def classify_incident(failed_login_count, forbidden_count, brute_force, path_traversal, scanner, score):
    if brute_force:
        return "BRUTE_FORCE"
    elif failed_login_count >= FAILED_LOGIN_LIMIT:
        return "UNAUTHORIZED_ACCESS"
    elif forbidden_count >= FORBIDDEN_LIMIT:
        return "FORBIDDEN_ACCESS"
    elif path_traversal:
        return "PATH_TRAVERSAL_ATTEMPT"
    elif scanner:
        return "SCANNER_ACTIVITY"
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
    elif incident_type == "PATH_TRAVERSAL_ATTEMPT":
        return "Acil inceleme gerekli, dizin disina cikma denemesi tespit edildi"
    elif incident_type == "SCANNER_ACTIVITY":
        return "IP izlenmeli, path taramasi tespit edildi (potansiyel recon)"
    elif incident_type == "SUSPICIOUS_ACTIVITY":
        return "Izlemeye devam edilmeli (monitoring)"
    else:
        return "Aksiyon gerekmiyor"


def generate_checklist(brute_force_ips, total_forbidden, high_severity_count, scanner_ips, path_traversal_ips):

    checklist_lines = []

    if len(brute_force_ips) == 0:
        checklist_lines.append("[OK] Brute force koruması: supheli aktivite yok (OWASP: Broken Authentication)")
    else:
        checklist_lines.append("[UYARI] Brute force koruması: " + str(len(brute_force_ips)) + " IP supheli (OWASP: Broken Authentication)")

    if total_forbidden >= HIGH_FORBIDDEN_THRESHOLD:
        checklist_lines.append("[UYARI] 403 sayisi normalin uzerinde: " + str(total_forbidden) + " adet (OWASP: Broken Access Control)")
    else:
        checklist_lines.append("[OK] 403 sayisi normal seviyede: " + str(total_forbidden) + " adet (OWASP: Broken Access Control)")

    if high_severity_count == 0:
        checklist_lines.append("[OK] HIGH severity IP bulunmadi (OWASP: Security Logging and Monitoring Failures)")
    else:
        checklist_lines.append("[UYARI] " + str(high_severity_count) + " adet HIGH severity IP tespit edildi (OWASP: Security Logging and Monitoring Failures)")

    if len(scanner_ips) == 0:
        checklist_lines.append("[OK] Path taramasi (scanner) suphesi yok (OWASP: Security Misconfiguration)")
    else:
        checklist_lines.append("[UYARI] " + str(len(scanner_ips)) + " IP path taramasi yapiyor olabilir (OWASP: Security Misconfiguration)")

    if len(path_traversal_ips) == 0:
        checklist_lines.append("[OK] Path traversal denemesi yok (OWASP: Broken Access Control)")
    else:
        checklist_lines.append("[UYARI] " + str(len(path_traversal_ips)) + " IP path traversal denemesi yapmis (OWASP: Broken Access Control)")

    return checklist_lines


def check_security_headers(url):
    """Verilen URL'ye GET istegi atar, response header'larini kontrol eder.

    Donen deger bir sozluk: {"url", "basarili", "hata", "eksik_headerlar", "mevcut_headerlar"}
    Bu fonksiyon disariya asla exception firlatmaz; tum hatalar
    yakalanip sonuc sozlugu icinde raporlanir, boylece script
    tek bir siteye ulasilamasa bile calismaya devam eder.
    """

    result = {
        "url": url,
        "basarili": False,
        "hata": None,
        "eksik_headerlar": [],
        "mevcut_headerlar": [],
    }

    request = urllib.request.Request(url, headers={"User-Agent": "SecurityHeaderChecker/1.0"})

    try:
        with urllib.request.urlopen(request, timeout=HEADER_CHECK_TIMEOUT) as response:
            response_headers = response.headers
            result["basarili"] = True

            for header_name, owasp_category in SECURITY_HEADERS:
                if header_name in response_headers:
                    result["mevcut_headerlar"].append(header_name)
                else:
                    result["eksik_headerlar"].append((header_name, owasp_category))

    except urllib.error.HTTPError as error:
        result["hata"] = "HTTP Hatasi: " + str(error.code)
    except urllib.error.URLError as error:
        result["hata"] = "Baglanti Hatasi: " + str(error.reason)
    except TimeoutError:
        result["hata"] = "Zaman Asimi (timeout)"
    except Exception as error:
        result["hata"] = "Beklenmeyen Hata: " + str(error)

    return result


def run_header_checks(target_urls):
    """Tum hedef URL'ler icin header kontrolunu calistirir.

    Sonuclari hem terminale yazdirir hem de rapor dosyasina eklenecek
    satirlarin bir listesini dondurur.
    """

    header_report_lines = []
    header_report_lines.append("## Security Headers Check")
    header_report_lines.append("")

    print("\n--- Security Headers Check ---")

    all_results = []

    for url in target_urls:
        result = check_security_headers(url)
        all_results.append(result)

        if not result["basarili"]:
            print("\nURL:", url)
            print("Durum: BASARISIZ -", result["hata"])

            header_report_lines.append("### " + url)
            header_report_lines.append("- Durum: BASARISIZ - " + result["hata"])
            header_report_lines.append("")
            continue

        print("\nURL:", url)
        print("Durum: BASARILI")
        print("Mevcut guvenlik headerlari:", len(result["mevcut_headerlar"]), "/", len(SECURITY_HEADERS))

        header_report_lines.append("### " + url)
        header_report_lines.append("- Durum: BASARILI")
        header_report_lines.append("- Mevcut guvenlik headerlari: " + str(len(result["mevcut_headerlar"])) + "/" + str(len(SECURITY_HEADERS)))

        if len(result["eksik_headerlar"]) == 0:
            print("Tum onerilen guvenlik headerlari mevcut.")
            header_report_lines.append("- Tum onerilen guvenlik headerlari mevcut.")
        else:
            print("Eksik headerlar:")
            header_report_lines.append("- Eksik headerlar:")
            for header_name, owasp_category in result["eksik_headerlar"]:
                print(" ", header_name, "-> eksik (OWASP:", owasp_category, ")")
                header_report_lines.append("  - " + header_name + " -> eksik (OWASP: " + owasp_category + ")")

        header_report_lines.append("")

    return header_report_lines, all_results


def export_report(report_lines):
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    report_path = os.path.join(REPORTS_DIR, "report_" + REPORT_DATE + ".md")

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
    ip_paths = defaultdict(set)
    brute_force_ips = set()
    scanner_ips = set()
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

    for ip, count in failed_login_counts.items():
        if count >= BRUTE_FORCE_LIMIT:
            brute_force_ips.add(ip)

    for ip, paths in ip_paths.items():
        if len(paths) >= SCANNER_PATH_LIMIT:
            scanner_ips.add(ip)

    print("\n=== DAY 14 - PATH TRAVERSAL DETECTION ===\n")
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
