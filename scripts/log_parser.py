import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote

from config import PATH_TRAVERSAL_PATTERNS


APACHE_LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<method>[A-Za-z]+)\s+(?P<path>\S+)(?:\s+[^\"]+)?"\s+'
    r'(?P<status>\d{3})(?:\s+.*)?$'
)

ISO_PREFIX_PATTERN = re.compile(
    r'^(?P<timestamp>\S+)\s+(?P<ip>\S+)\s+(?P<method>[A-Za-z]+)\s+'
    r'(?P<path>\S+)\s+(?P<status>\d{3})(?:\s+.*)?$'
)

SIMPLE_PATTERN = re.compile(
    r'^(?P<ip>\S+)\s+(?P<method>[A-Za-z]+)\s+(?P<path>\S+)\s+'
    r'(?P<status>\d{3})(?:\s+.*)?$'
)

APACHE_TIMESTAMP_PATTERN = re.compile(
    r"^(?P<day>\d{2})/(?P<month>[A-Za-z]{3})/(?P<year>\d{4}):"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2}) "
    r"(?P<offset_sign>[+-])(?P<offset_hour>\d{2})(?P<offset_minute>\d{2})$"
)

MONTH_NUMBERS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


@dataclass(frozen=True)
class LogEntry:
    ip: str
    method: str
    path: str
    status_code: str
    timestamp: datetime | None = None


def _parse_apache_timestamp(candidate):
    match = APACHE_TIMESTAMP_PATTERN.fullmatch(candidate)
    if not match:
        return None

    month = MONTH_NUMBERS.get(match.group("month").casefold())
    if month is None:
        return None

    offset_minutes = (
        int(match.group("offset_hour")) * 60
        + int(match.group("offset_minute"))
    )
    if match.group("offset_sign") == "-":
        offset_minutes *= -1

    try:
        parsed = datetime(
            year=int(match.group("year")),
            month=month,
            day=int(match.group("day")),
            hour=int(match.group("hour")),
            minute=int(match.group("minute")),
            second=int(match.group("second")),
            tzinfo=timezone(timedelta(minutes=offset_minutes)),
        )
    except ValueError:
        return None

    return parsed.astimezone(timezone.utc)


def normalize_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return None

    candidate = value.strip()
    apache_timestamp = _parse_apache_timestamp(candidate)
    if apache_timestamp is not None:
        return apache_timestamp

    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def parse_log_line(line):
    if not isinstance(line, str):
        return None

    normalized = line.strip()
    if not normalized:
        return None

    match = APACHE_LOG_PATTERN.match(normalized)
    if match:
        return LogEntry(
            ip=match.group("ip"),
            method=match.group("method").upper(),
            path=match.group("path"),
            status_code=match.group("status"),
            timestamp=normalize_timestamp(match.group("timestamp")),
        )

    match = ISO_PREFIX_PATTERN.match(normalized)
    if match:
        timestamp = normalize_timestamp(match.group("timestamp"))
        if timestamp is not None:
            return LogEntry(
                ip=match.group("ip"),
                method=match.group("method").upper(),
                path=match.group("path"),
                status_code=match.group("status"),
                timestamp=timestamp,
            )

    match = SIMPLE_PATTERN.match(normalized)
    if match:
        return LogEntry(
            ip=match.group("ip"),
            method=match.group("method").upper(),
            path=match.group("path"),
            status_code=match.group("status"),
            timestamp=None,
        )

    return None


def canonicalize_request_path(path):
    if not isinstance(path, str):
        return "/"
    path_only = path.split("?", 1)[0].split("#", 1)[0]
    return path_only or "/"


def decode_path(path):
    decoded = path
    for _ in range(5):
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    return decoded


def has_path_traversal(path):
    if not isinstance(path, str):
        return False

    decoded = decode_path(path).replace("\\", "/")
    return any(
        pattern.replace("\\", "/") in decoded
        for pattern in PATH_TRAVERSAL_PATTERNS
    )
