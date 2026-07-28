import time
import random
from datetime import datetime

LOG_FILE = "logs/sample_access.log"

SAMPLE_IPS = [
    "192.168.1.11", "192.168.1.25", "192.168.1.30",
    "10.0.0.5", "10.0.0.9", "203.0.113.14", "198.51.100.23"
]

SAMPLE_PATHS = [
    "/login", "/admin", "/api/users", "/dashboard",
    "/wp-admin", "/config.php", "/.env", "/index.html"
]

SAMPLE_METHODS = ["GET", "POST"]

SAMPLE_STATUS_CODES = [200, 200, 200, 401, 403, 404]


def generate_log_line():
    ip = random.choice(SAMPLE_IPS)
    method = random.choice(SAMPLE_METHODS)
    path = random.choice(SAMPLE_PATHS)
    status = random.choice(SAMPLE_STATUS_CODES)
    timestamp = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")

    line = f'{ip} - - [{timestamp}] "{method} {path} HTTP/1.1" {status} 512\n'
    return line


def run_simulator(interval_seconds=5, max_lines=None):
    count = 0
    print(f"Trafik simulatoru baslatildi. {interval_seconds} saniyede bir yeni satir eklenecek.")

    try:
        while True:
            line = generate_log_line()

            with open(LOG_FILE, "a") as f:
                f.write(line)

            count += 1
            print(f"[{count}] eklendi: {line.strip()}")

            if max_lines and count >= max_lines:
                print("Maksimum satir sayisina ulasildi, durduruluyor.")
                break

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print(f"\nSimulator durduruldu. Toplam {count} satir eklendi.")


if __name__ == "__main__":
    run_simulator(interval_seconds=5, max_lines=20)
