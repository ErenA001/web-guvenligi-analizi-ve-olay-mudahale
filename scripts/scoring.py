from config import (
    SEVERITY_LOW_MAX,
    SEVERITY_MEDIUM_MAX,
    SEVERITY_HIGH_MAX,
    FAILED_LOGIN_LIMIT,
    FORBIDDEN_LIMIT,
    SUSPICIOUS_SCORE_LIMIT,
)


def get_severity(score):
    if score <= SEVERITY_LOW_MAX:
        return "LOW"
    elif score <= SEVERITY_MEDIUM_MAX:
        return "MEDIUM"
    elif score <= SEVERITY_HIGH_MAX:
        return "HIGH"
    else:
        return "CRITICAL"


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
