# Day 08 - Incident Classification

# Bu script log dosyasini okuyarak IP trafigini, basit saldiri belirtilerini,
# brute force denemelerini, risk skorlarini ve incident type siniflandirmasini analiz eder.

from collections import defaultdict

log_file = "logs/sample_access.log"

# Brute force icin esik degeri
BRUTE_FORCE_LIMIT = 5

# Severity scoring agirliklari
SCORE_401 = 2
SCORE_403 = 3
SCORE_FAILED_LOGIN = 5
SCORE_BRUTE_FORCE_BONUS = 10

# Severity seviyeleri icin esik degerleri
SEVERITY_LOW_MAX = 4
SEVERITY_MEDIUM_MAX = 9

# Incident classification icin esik degerleri
UNAUTHORIZED_ACCESS_LIMIT = 3
FORBIDDEN_ACCESS_LIMIT = 3
SUSPICIOUS_ACTIVITY_SCORE_LIMIT = 5

def get_severity(score):
    if score <= SEVERITY_LOW_MAX:
        return "LOW"
    elif score <= SEVERITY_MEDIUM_MAX:
        return "MEDIUM"
    else:
        return "HIGH"

def classify_incident(failed_login_count, unauthorized_count, forbidden_count, brute_force, score):
    if brute_force:
        return "BRUTE_FORCE"
    elif failed_login_count >= UNAUTHORIZED_ACCESS_LIMIT:
        return "UNAUTHORIZED_ACCESS"
    elif forbidden_count >= FORBIDDEN_ACCESS_LIMIT:
        return "FORBIDDEN_ACCESS"
    elif score >= SUSPICIOUS_ACTIVITY_SCORE_LIMIT:
        return "SUSPICIOUS_ACTIVITY"
    else:
        return "NORMAL"

def analyze_logs(file_path):

    ip_counts = defaultdict(int)
    status_counts = defaultdict(int)
    unauthorized_counts = defaultdict(int)
    forbidden_counts = defaultdict(int)
    failed_login_counts = defaultdict(int)

    total_lines = 0
    skipped_lines = 0

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if line == "":
                    continue

                parts = line.split()

                # Beklenen basit log formati:
                # IP METHOD PATH STATUS
                # Ornek:
                # 192.168.1.11 POST /login 401

                if len(parts) < 4:
                    skipped_lines += 1
                    continue

                ip = parts[0]
                path = parts[2]
                status_code = parts[3]

                ip_counts[ip] += 1
                status_counts[status_code] += 1
                total_lines += 1

                # 401 Unauthorized: basarisiz giris veya yetkisiz istek olabilir
                if status_code == "401":
                    unauthorized_counts[ip] += 1

                    if path == "/login":
                        failed_login_counts[ip] += 1

                # 403 Forbidden: yasakli kaynaga erisim denemesi olabilir
                if status_code == "403":
                    forbidden_counts[ip] += 1

    except FileNotFoundError:
        print("Log dosyasi bulunamadi:", file_path)
        return

    print("\n=== DAY 08 - INCIDENT CLASSIFICATION ===\n")

    print("Toplam okunan log satiri:", total_lines)
    print("Atlanan satir sayisi:", skipped_lines)

    print("\n--- IP Bazli Request Sayilari ---")
    for ip, count in sorted(ip_counts.items(), key=lambda item: item[1], reverse=True):
        print(ip, "->", count, "request")

    print("\n--- HTTP Status Code Dagilimi ---")
    for status, count in sorted(status_counts.items()):
        print(status, "->", count, "adet")

    print("\n--- 401 Unauthorized Denemeleri ---")
    if len(unauthorized_counts) == 0:
        print("401 Unauthorized denemesi bulunmadi.")
    else:
        for ip, count in sorted(unauthorized_counts.items(), key=lambda item: item[1], reverse=True):
            print(ip, "->", count, "adet 401")

    print("\n--- 403 Forbidden Denemeleri ---")
    if len(forbidden_counts) == 0:
        print("403 Forbidden denemesi bulunmadi.")
    else:
        for ip, count in sorted(forbidden_counts.items(), key=lambda item: item[1], reverse=True):
            print(ip, "->", count, "adet 403")

    print("\n--- Login Path Uzerindeki Basarisiz Denemeler ---")
    if len(failed_login_counts) == 0:
        print("/login uzerinde basarisiz deneme bulunmadi.")
    else:
        for ip, count in sorted(failed_login_counts.items(), key=lambda item: item[1], reverse=True):
            print(ip, "->", count, "basarisiz login denemesi")

    print("\n--- Brute Force Suphesi Olan IP Adresleri ---")
    brute_force_found = False
    brute_force_ips = set()

    for ip, count in sorted(failed_login_counts.items(), key=lambda item: item[1], reverse=True):
        if count >= BRUTE_FORCE_LIMIT:
            brute_force_found = True
            brute_force_ips.add(ip)
            print(ip, "-> possible brute force detected")
            print("   failed login count:", count)

    if brute_force_found == False:
        print("Brute force suphesi bulunmadi.")

    print("\n--- Incident Classification Summary ---")
    for ip in sorted(ip_counts.keys()):
        request_count = ip_counts[ip]
        unauthorized_count = unauthorized_counts[ip]
        forbidden_count = forbidden_counts[ip]
        failed_login_count = failed_login_counts[ip]
        brute_force = ip in brute_force_ips

        score = (unauthorized_count * SCORE_401) + (forbidden_count * SCORE_403) + (failed_login_count * SCORE_FAILED_LOGIN)

        if brute_force:
            score += SCORE_BRUTE_FORCE_BONUS

        severity = get_severity(score)

        incident_type = classify_incident(
            failed_login_count,
            unauthorized_count,
            forbidden_count,
            brute_force,
            score
        )

        print("\nIP:", ip)
        print("Request Count:", request_count)
        print("Unauthorized Count:", unauthorized_count)
        print("Forbidden Count:", forbidden_count)
        print("Failed Login Count:", failed_login_count)
        print("Brute Force:", brute_force)
        print("Score:", score)
        print("Severity:", severity)
        print("Incident Type:", incident_type)

    print("\nAnaliz tamamlandi.")

analyze_logs(log_file)
