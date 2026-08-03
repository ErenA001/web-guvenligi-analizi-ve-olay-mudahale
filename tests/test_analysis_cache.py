import os
import tempfile
import unittest
from unittest.mock import patch

from services.analysis_cache import AnalysisCache


class AnalysisCacheTests(unittest.TestCase):
    def test_reuses_result_and_returns_defensive_copy(self):
        with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
            temporary_file.write(b"one")
            file_path = temporary_file.name
        self.addCleanup(lambda: os.path.exists(file_path) and os.remove(file_path))

        calls = []
        cache = AnalysisCache(max_entries=4, ttl_seconds=60, schema_version="test")

        def loader():
            calls.append(1)
            return [{"value": len(calls)}]

        first = cache.get_or_load(file_path, loader)
        first[0]["value"] = 999
        second = cache.get_or_load(file_path, loader)

        self.assertEqual(len(calls), 1)
        self.assertEqual(second, [{"value": 1}])
        self.assertEqual(cache.hits, 1)
        self.assertEqual(cache.misses, 1)

    def test_file_change_invalidates_signature(self):
        with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
            temporary_file.write(b"one")
            file_path = temporary_file.name
        self.addCleanup(lambda: os.path.exists(file_path) and os.remove(file_path))

        cache = AnalysisCache(max_entries=4, ttl_seconds=60, schema_version="test")
        calls = []

        def loader():
            calls.append(1)
            return len(calls)

        self.assertEqual(cache.get_or_load(file_path, loader), 1)
        with open(file_path, "ab") as changed_file:
            changed_file.write(b"-changed")
        self.assertEqual(cache.get_or_load(file_path, loader), 2)

    def test_multiple_instances_share_sqlite_cache(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            file_path = os.path.join(temporary_directory, "access.log")
            database_path = os.path.join(temporary_directory, "cache.sqlite3")
            with open(file_path, "w", encoding="utf-8") as log_file:
                log_file.write("192.0.2.1 GET / 200\n")

            first = AnalysisCache(
                max_entries=4,
                ttl_seconds=60,
                schema_version="shared-test",
                database_path=database_path,
            )
            second = AnalysisCache(
                max_entries=4,
                ttl_seconds=60,
                schema_version="shared-test",
                database_path=database_path,
            )
            calls = []

            def loader():
                calls.append(1)
                return [{"loaded": len(calls)}]

            self.assertEqual(first.get_or_load(file_path, loader), [{"loaded": 1}])
            self.assertEqual(second.get_or_load(file_path, loader), [{"loaded": 1}])
            self.assertEqual(len(calls), 1)
            self.assertEqual(second.hits, 1)

    def test_ttl_expiration_reloads(self):
        with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
            temporary_file.write(b"one")
            file_path = temporary_file.name
        self.addCleanup(lambda: os.path.exists(file_path) and os.remove(file_path))

        cache = AnalysisCache(max_entries=4, ttl_seconds=5, schema_version="test")
        calls = []
        times = iter([100.0, 106.0])

        def loader():
            calls.append(1)
            return len(calls)

        with patch("services.analysis_cache.time.monotonic", side_effect=lambda: next(times)):
            self.assertEqual(cache.get_or_load(file_path, loader), 1)
            self.assertEqual(cache.get_or_load(file_path, loader), 2)


if __name__ == "__main__":
    unittest.main()
