from config import BRUTE_FORCE_LIMIT, SCANNER_PATH_LIMIT


def find_brute_force_ips(failed_login_counts):
    brute_force_ips = set()
    for ip, count in failed_login_counts.items():
        if count >= BRUTE_FORCE_LIMIT:
            brute_force_ips.add(ip)
    return brute_force_ips


def find_scanner_ips(ip_paths):
    scanner_ips = set()
    for ip, paths in ip_paths.items():
        if len(paths) >= SCANNER_PATH_LIMIT:
            scanner_ips.add(ip)
    return scanner_ips
