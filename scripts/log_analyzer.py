from collections import defaultdict

log_file = "../logs/sample_access.log"

failed_logins = defaultdict(int)
ip_requests = defaultdict(int)

with open(log_file, "r") as file:
    for line in file:
        parts = line.split()
        ip = parts[0]
        status_code = parts[-2]

        ip_requests[ip] += 1

        if status_code == "401":
            failed_logins[ip] += 1

print("\n=== IP Request Count ===")
for ip, count in ip_requests.items():
    print(ip, "->", count)

print("\n=== Suspicious IPs ===")
for ip, count in failed_logins.items():
    if count >= 2:
        print(ip, "-> POSSIBLE BRUTE FORCE")
