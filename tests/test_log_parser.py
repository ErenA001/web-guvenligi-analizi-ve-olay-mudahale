import unittest
from datetime import timezone

from scripts.log_parser import has_path_traversal, parse_log_line


class LogParserTests(unittest.TestCase):
    def test_parses_apache_combined_log(self):
        entry = parse_log_line(
            '203.0.113.5 - - [04/Aug/2026:00:10:05 +0300] '
            '"POST /login HTTP/1.1" 401 123 "-" "Mozilla/5.0"'
        )
        self.assertIsNotNone(entry)
        self.assertEqual(entry.ip, "203.0.113.5")
        self.assertEqual(entry.method, "POST")
        self.assertEqual(entry.path, "/login")
        self.assertEqual(entry.status_code, "401")
        self.assertEqual(entry.timestamp.tzinfo, timezone.utc)
        self.assertEqual(entry.timestamp.hour, 21)

    def test_parses_iso_prefixed_log(self):
        entry = parse_log_line(
            "2026-08-04T00:10:05+03:00 198.51.100.10 GET /admin 403"
        )
        self.assertIsNotNone(entry)
        self.assertEqual(entry.ip, "198.51.100.10")
        self.assertEqual(entry.path, "/admin")
        self.assertIsNotNone(entry.timestamp)

    def test_parses_legacy_simple_log(self):
        entry = parse_log_line("192.0.2.4 GET /health 200")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.ip, "192.0.2.4")
        self.assertIsNone(entry.timestamp)

    def test_rejects_invalid_line(self):
        self.assertIsNone(parse_log_line("not a valid access log"))
        self.assertIsNone(parse_log_line(""))
        self.assertIsNone(parse_log_line(None))

    def test_detects_plain_and_encoded_path_traversal(self):
        self.assertTrue(has_path_traversal("/../../etc/passwd"))
        self.assertTrue(has_path_traversal("/%2e%2e/%2e%2e/etc/passwd"))
        self.assertTrue(has_path_traversal("/%252e%252e/%252e%252e/etc/passwd"))
        self.assertTrue(has_path_traversal("/%25252e%25252e/etc/passwd"))
        self.assertTrue(has_path_traversal(r"/..\..\windows\win.ini"))
        self.assertFalse(has_path_traversal("/assets/app.js"))


if __name__ == "__main__":
    unittest.main()
