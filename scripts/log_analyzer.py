# Day 04 - IP Traffic Analysis
# Bu script log dosyasini okuyarak IP bazli trafik analizi yapar.

from collections import defaultdict


log_file = "logs/sample_access.log"


def analyze_ip_traffic(file_path):
    ip_counts = defaultdict(int)
    status_counts = defaultdict(int)
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
                # 192.168.1.10 GET /home 200
                if len(parts) < 4:
                    skipped_lines += 1
                    continue

                ip = parts[0]
                status_code = parts[3]

                ip_counts[ip] += 1
                status_counts[status_code] += 1
                total_lines += 1

    except FileNotFoundError:
        print("Log dosyasi bulunamadi:", file_path)
        return

    print("\n=== DAY 04 - IP TRAFFIC ANALYSIS ===\n")

    print("Toplam okunan log satiri:", total_lines)
    print("Atlanan satir sayisi:", skipped_lines)

    print("\n--- IP Bazli Request Sayilari ---")

    for ip, count in sorted(ip_counts.items(), key=lambda item: item[1], reverse=True):
        print(ip, "->", count, "request")

    print("\n--- HTTP Status Code Dagilimi ---")

    for status, count in sorted(status_counts.items()):
        print(status, "->", count, "adet")

    print("\nAnaliz tamamlandi.")


analyze_ip_traffic(log_file)
