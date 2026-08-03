import unittest
from datetime import datetime, timedelta, timezone

from scripts.detection import (
    find_brute_force_ips,
    find_scanner_ips,
    has_event_burst,
    has_unique_path_burst,
)


class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 8, 4, tzinfo=timezone.utc)

    def test_event_burst_detects_threshold_inside_window(self):
        events = [self.start + timedelta(seconds=offset) for offset in (0, 30, 60, 90, 120)]
        self.assertTrue(has_event_burst(events, limit=5, window_seconds=300))

    def test_event_burst_rejects_events_spread_outside_window(self):
        events = [self.start + timedelta(seconds=offset) for offset in (0, 100, 200, 300, 401)]
        self.assertFalse(has_event_burst(events, limit=5, window_seconds=300))

    def test_unique_path_burst_counts_distinct_paths_only(self):
        events = [
            (self.start + timedelta(seconds=0), "/a"),
            (self.start + timedelta(seconds=10), "/a"),
            (self.start + timedelta(seconds=20), "/b"),
            (self.start + timedelta(seconds=30), "/c"),
            (self.start + timedelta(seconds=40), "/d"),
        ]
        self.assertFalse(has_unique_path_burst(events, limit=5, window_seconds=300))
        events.append((self.start + timedelta(seconds=50), "/e"))
        self.assertTrue(has_unique_path_burst(events, limit=5, window_seconds=300))

    def test_brute_force_detection_is_per_ip(self):
        events = {
            "203.0.113.1": [self.start + timedelta(seconds=i * 20) for i in range(5)],
            "203.0.113.2": [self.start + timedelta(seconds=i * 100) for i in range(5)],
        }
        detected = find_brute_force_ips(events, limit=5, window_seconds=300)
        self.assertEqual(detected, {"203.0.113.1"})

    def test_scanner_detection_supports_legacy_untimed_logs(self):
        detected = find_scanner_ips(
            {},
            {"198.51.100.20": {"/a", "/b", "/c", "/d", "/e"}},
            limit=5,
            window_seconds=300,
        )
        self.assertEqual(detected, {"198.51.100.20"})


if __name__ == "__main__":
    unittest.main()
