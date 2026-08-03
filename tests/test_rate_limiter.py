import os
import tempfile
import unittest

from services.rate_limiter import SQLiteRateLimiter


class MutableClock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value


class RateLimiterTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = os.path.join(self.temporary_directory.name, "rate.sqlite3")
        self.clock = MutableClock()

    def test_blocks_after_limit_and_allows_after_window(self):
        limiter = SQLiteRateLimiter(self.database_path, clock=self.clock)
        self.assertEqual(limiter.allow("chat", "user", 2, 60), (True, 0))
        self.clock.value += 1
        self.assertEqual(limiter.allow("chat", "user", 2, 60), (True, 0))
        self.clock.value += 1
        allowed, retry_after = limiter.allow("chat", "user", 2, 60)
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)

        self.clock.value += 60
        self.assertEqual(limiter.allow("chat", "user", 2, 60), (True, 0))

    def test_multiple_instances_share_the_same_database(self):
        first = SQLiteRateLimiter(self.database_path, clock=self.clock)
        second = SQLiteRateLimiter(self.database_path, clock=self.clock)
        self.assertEqual(first.allow("upload", "same", 1, 300), (True, 0))
        self.assertFalse(second.allow("upload", "same", 1, 300)[0])

    def test_subjects_and_buckets_are_isolated(self):
        limiter = SQLiteRateLimiter(self.database_path, clock=self.clock)
        self.assertTrue(limiter.allow("chat", "user-a", 1, 60)[0])
        self.assertTrue(limiter.allow("chat", "user-b", 1, 60)[0])
        self.assertTrue(limiter.allow("upload", "user-a", 1, 60)[0])


if __name__ == "__main__":
    unittest.main()
