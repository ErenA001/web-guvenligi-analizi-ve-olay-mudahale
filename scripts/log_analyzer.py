# Day 05 - Basic Attack Detection
# Bu script log dosyasini okuyarak IP trafigini ve basit saldiri belirtilerini analiz eder.

from collections import defaultdict


log_file = "logs/sample_access.log"


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

    print("\n=== DAY 05 - BASIC ATTACK DETECTION ===\n")

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

    print("\n--- Supheli IP Listesi ---")

    suspicious_ip_found = False

    for ip in sorted(ip_counts.keys()):
        unauthorized_count = unauthorized_counts[ip]
        forbidden_count = forbidden_counts[ip]
        failed_login_count = failed_login_counts[ip]

        # Gun 5 icin basit kural:
        # Ayni IP birden fazla 401 veya 403 aliyorsa supheli olarak gosterilir.
        if unauthorized_count > 1 or forbidden_count > 1:
            suspicious_ip_found = True
            print(ip, "-> suspicious activity detected")
            print("   401 count:", unauthorized_count)
            print("   403 count:", forbidden_count)
            print("   failed login count:", failed_login_count)

    if suspicious_ip_found == False:
        print("Supheli IP bulunmadi.")

    print("\nAnaliz tamamlandi.")


analyze_logs(log_file)
