from collections import Counter

from config import (
    BRUTE_FORCE_LIMIT,
    DETECTION_WINDOW_SECONDS,
    ENABLE_LEGACY_UNTIMED_DETECTION,
    SCANNER_PATH_LIMIT,
)


def has_event_burst(timestamps, limit, window_seconds):
    if limit <= 0:
        return True

    ordered = sorted(timestamp for timestamp in timestamps if timestamp is not None)
    left = 0

    for right, current in enumerate(ordered):
        while (
            left <= right
            and (current - ordered[left]).total_seconds() > window_seconds
        ):
            left += 1

        if right - left + 1 >= limit:
            return True

    return False


def has_unique_path_burst(path_events, limit, window_seconds):
    if limit <= 0:
        return True

    ordered = sorted(
        (timestamp, path)
        for timestamp, path in path_events
        if timestamp is not None
    )
    counts = Counter()
    left = 0

    for right, (current_time, current_path) in enumerate(ordered):
        counts[current_path] += 1

        while (
            left <= right
            and (current_time - ordered[left][0]).total_seconds() > window_seconds
        ):
            expired_path = ordered[left][1]
            counts[expired_path] -= 1
            if counts[expired_path] <= 0:
                del counts[expired_path]
            left += 1

        if len(counts) >= limit:
            return True

    return False


def find_brute_force_ips(
    failed_login_events,
    untimed_failed_login_counts=None,
    limit=BRUTE_FORCE_LIMIT,
    window_seconds=DETECTION_WINDOW_SECONDS,
):
    untimed_failed_login_counts = untimed_failed_login_counts or {}
    all_ips = set(failed_login_events) | set(untimed_failed_login_counts)
    brute_force_ips = set()

    for ip in all_ips:
        timed_detection = has_event_burst(
            failed_login_events.get(ip, []),
            limit,
            window_seconds,
        )
        legacy_detection = (
            ENABLE_LEGACY_UNTIMED_DETECTION
            and untimed_failed_login_counts.get(ip, 0) >= limit
        )

        if timed_detection or legacy_detection:
            brute_force_ips.add(ip)

    return brute_force_ips


def find_scanner_ips(
    ip_path_events,
    untimed_ip_paths=None,
    limit=SCANNER_PATH_LIMIT,
    window_seconds=DETECTION_WINDOW_SECONDS,
):
    untimed_ip_paths = untimed_ip_paths or {}
    all_ips = set(ip_path_events) | set(untimed_ip_paths)
    scanner_ips = set()

    for ip in all_ips:
        timed_detection = has_unique_path_burst(
            ip_path_events.get(ip, []),
            limit,
            window_seconds,
        )
        legacy_detection = (
            ENABLE_LEGACY_UNTIMED_DETECTION
            and len(untimed_ip_paths.get(ip, set())) >= limit
        )

        if timed_detection or legacy_detection:
            scanner_ips.add(ip)

    return scanner_ips
