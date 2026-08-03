import os
import sqlite3
import threading
import time
from contextlib import closing


class SQLiteRateLimiter:
    def __init__(self, database_path, clock=None):
        self.database_path = os.path.abspath(database_path)
        self.clock = clock or time.time
        self._init_lock = threading.Lock()
        self._initialized = False

    def _connect(self):
        os.makedirs(os.path.dirname(self.database_path), mode=0o700, exist_ok=True)
        connection = sqlite3.connect(
            self.database_path,
            timeout=5.0,
            isolation_level=None,
        )
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        try:
            os.chmod(self.database_path, 0o600)
        except OSError:
            pass
        return connection

    def _ensure_schema(self):
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return
            with closing(self._connect()) as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rate_limit_events (
                        bucket TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        created_at REAL NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_rate_limit_lookup
                    ON rate_limit_events (bucket, subject, created_at)
                    """
                )
            self._initialized = True

    def allow(self, bucket, subject, limit, window_seconds):
        self._ensure_schema()
        now = float(self.clock())
        limit = max(1, int(limit))
        window_seconds = max(1, int(window_seconds))
        cutoff = now - window_seconds

        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "DELETE FROM rate_limit_events "
                    "WHERE bucket = ? AND created_at <= ?",
                    (bucket, cutoff),
                )
                rows = connection.execute(
                    "SELECT created_at FROM rate_limit_events "
                    "WHERE bucket = ? AND subject = ? "
                    "ORDER BY created_at ASC",
                    (bucket, subject),
                ).fetchall()

                if len(rows) >= limit:
                    retry_after = max(
                        1,
                        int(window_seconds - (now - rows[0][0]) + 0.999),
                    )
                    connection.execute("COMMIT")
                    return False, retry_after

                connection.execute(
                    "INSERT INTO rate_limit_events (bucket, subject, created_at) "
                    "VALUES (?, ?, ?)",
                    (bucket, subject, now),
                )
                connection.execute("COMMIT")
                return True, 0
        except sqlite3.Error as error:
            # Availability is preferred if the local limiter database is damaged.
            print(f"Rate limiter veritabani hatasi: {type(error).__name__}: {error}")
            return True, 0

    def reset(self, bucket=None, subject=None):
        self._ensure_schema()
        with closing(self._connect()) as connection:
            if bucket is None and subject is None:
                connection.execute("DELETE FROM rate_limit_events")
            elif subject is None:
                connection.execute(
                    "DELETE FROM rate_limit_events WHERE bucket = ?",
                    (bucket,),
                )
            else:
                connection.execute(
                    "DELETE FROM rate_limit_events "
                    "WHERE bucket = ? AND subject = ?",
                    (bucket, subject),
                )

    def clear(self):
        self.reset()
