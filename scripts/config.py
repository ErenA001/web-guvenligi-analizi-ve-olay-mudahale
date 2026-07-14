from datetime import datetime

REPORT_DATE = datetime.now().strftime("%Y%m%d")

HIGH_FORBIDDEN_THRESHOLD = 5

BRUTE_FORCE_LIMIT = 5
SCANNER_PATH_LIMIT = 5
PATH_TRAVERSAL_PATTERN = "../"

SCORE_401 = 2
SCORE_403 = 3
SCORE_FAILED_LOGIN = 5
SCORE_BRUTE_FORCE_BONUS = 10
SCORE_SCANNER = 4
SCORE_PATH_TRAVERSAL = 8

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
