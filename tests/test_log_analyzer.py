import os
import tempfile
import unittest

from scripts.log_analyzer import analyze_logs


class LogAnalyzerTests(unittest.TestCase):
    def _analyze(self, lines):
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = os.path.join(temporary_directory, "access.log")
            with open(log_path, "w", encoding="utf-8") as log_file:
                log_file.write("\n".join(lines) + "\n")
            return analyze_logs(
                log_path,
                include_header_check=False,
                write_report=False,
            )

    def test_windowed_brute_force_and_scanner_detection(self):
        lines = []
        for minute in range(5):
            lines.append(
                f'203.0.113.10 - - [04/Aug/2026:00:0{minute}:00 +0000] '
                '"POST /login HTTP/1.1" 401 12'
            )
        for index in range(5):
            lines.append(
                f'198.51.100.15 - - [04/Aug/2026:00:01:0{index} +0000] '
                f'"GET /probe-{index} HTTP/1.1" 404 0'
            )

        rows = {row["ip"]: row for row in self._analyze(lines)}
        self.assertTrue(rows["203.0.113.10"]["brute_force"])
        self.assertEqual(rows["203.0.113.10"]["incident_type"], "BRUTE_FORCE")
        self.assertTrue(rows["198.51.100.15"]["scanner_activity"])
        self.assertEqual(rows["198.51.100.15"]["incident_type"], "SCANNER_ACTIVITY")

    def test_spread_out_login_failures_are_not_brute_force(self):
        lines = [
            f'203.0.113.50 - - [04/Aug/2026:0{hour}:00:00 +0000] '
            '"POST /login HTTP/1.1" 401 12'
            for hour in range(5)
        ]
        rows = {row["ip"]: row for row in self._analyze(lines)}
        self.assertFalse(rows["203.0.113.50"]["brute_force"])
        self.assertEqual(rows["203.0.113.50"]["incident_type"], "UNAUTHORIZED_ACCESS")

    def test_encoded_path_traversal_is_detected(self):
        rows = self._analyze(
            [
                '192.0.2.99 - - [04/Aug/2026:00:00:00 +0000] '
                '"GET /%252e%252e/%252e%252e/etc/passwd HTTP/1.1" 404 0'
            ]
        )
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["path_traversal"])
        self.assertEqual(rows[0]["incident_type"], "PATH_TRAVERSAL_ATTEMPT")

    def test_query_string_variations_do_not_fake_scanner_activity(self):
        lines = [
            f'198.51.100.40 - - [04/Aug/2026:00:00:0{index} +0000] '
            f'"GET /search?q={index} HTTP/1.1" 200 10'
            for index in range(5)
        ]
        rows = {row["ip"]: row for row in self._analyze(lines)}
        self.assertFalse(rows["198.51.100.40"]["scanner_activity"])
        self.assertEqual(rows["198.51.100.40"]["different_path_count"], 1)

    def test_common_auth_endpoint_and_403_count_as_failed_login(self):
        lines = [
            f'203.0.113.70 - - [04/Aug/2026:00:00:0{index} +0000] '
            '"POST /auth/login HTTP/1.1" 403 10'
            for index in range(5)
        ]
        rows = {row["ip"]: row for row in self._analyze(lines)}
        self.assertTrue(rows["203.0.113.70"]["brute_force"])
        self.assertEqual(rows["203.0.113.70"]["failed_login_count"], 5)

    def test_invalid_lines_are_skipped_without_breaking_valid_data(self):
        rows = self._analyze(
            [
                "this line is invalid",
                "192.0.2.1 GET /health 200",
            ]
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["ip"], "192.0.2.1")
        self.assertEqual(rows[0]["incident_type"], "NORMAL")


if __name__ == "__main__":
    unittest.main()
