file_path = "../logs/sample_access.log"

ip_count = {}
failed_login = {}

with open(file_path, "r") as file:
    for line in file:
        parts = line.split()

        ip = parts[0]
        status = parts[-1]

        if ip in ip_count:
            ip_count[ip] += 1
        else:
            ip_count[ip] = 1

        if status == "401":
            if ip in failed_login:
                failed_login[ip] += 1
            else:
                failed_login[ip] = 1

print("\n=== IP TRAFFIC ===")
for ip, count in ip_count.items():
    print(ip, "->", count)

print("\n=== SUSPICIOUS IPS ===")
for ip, count in failed_login.items():
    if count >= 2:
        print(ip, "-> BRUTE FORCE RISK")
