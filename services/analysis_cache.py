import copy
import hashlib
import json
import os
import sqlite3
import threading
import time
from collections import OrderedDict
from contextlib import closing


class AnalysisCache:
    def __init__(
        self,
        max_entries=64,
        ttl_seconds=300,
        schema_version="1",
        database_path=None,
    ):
        self.max_entries = max(1, int(max_entries))
        self.ttl_seconds = max(1, int(ttl_seconds))
        self.schema_version = str(schema_version)
        self.database_path = (
            os.path.abspath(database_path) if database_path else None
        )
        self._entries = OrderedDict()
        self._lock = threading.RLock()
        self._database_init_lock = threading.Lock()
        self._database_initialized = False
        self.hits = 0
        self.misses = 0

    def _signature(self, file_path):
        stat_result = os.stat(file_path)
        return (
            os.path.abspath(file_path),
            stat_result.st_mtime_ns,
            getattr(stat_result, "st_ctime_ns", 0),
            stat_result.st_size,
            getattr(stat_result, "st_ino", 0),
            self.schema_version,
        )

    @staticmethod
    def _cache_key(signature):
        serialized = json.dumps(signature, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _connect(self):
        os.makedirs(os.path.dirname(self.database_path), mode=0o700, exist_ok=True)
        connection = sqlite3.connect(
            self.database_path,
            timeout=15.0,
            isolation_level=None,
        )
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        try:
            os.chmod(self.database_path, 0o600)
        except OSError:
            pass
        return connection

    def _ensure_database(self):
        if self.database_path is None or self._database_initialized:
            return

        with self._database_init_lock:
            if self._database_initialized:
                return
            with closing(self._connect()) as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analysis_cache_entries (
                        cache_key TEXT PRIMARY KEY,
                        file_path TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        payload_json TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_analysis_cache_file
                    ON analysis_cache_entries (file_path)
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_analysis_cache_created
                    ON analysis_cache_entries (created_at)
                    """
                )
            self._database_initialized = True

    def _memory_get(self, signature, now_monotonic):
        with self._lock:
            cached = self._entries.get(signature)
            if cached is None:
                return None
            created_at, payload = cached
            if now_monotonic - created_at > self.ttl_seconds:
                self._entries.pop(signature, None)
                return None
            self._entries.move_to_end(signature)
            self.hits += 1
            return copy.deepcopy(payload)

    def _memory_set(self, signature, payload, now_monotonic):
        with self._lock:
            self._entries[signature] = (now_monotonic, copy.deepcopy(payload))
            self._entries.move_to_end(signature)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)

    def _load_with_shared_database(
        self,
        signature,
        loader,
        now_monotonic,
    ):
        self._ensure_database()
        cache_key = self._cache_key(signature)
        file_path = signature[0]
        now_wall = time.time()
        cutoff = now_wall - self.ttl_seconds

        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT created_at, payload_json "
                    "FROM analysis_cache_entries WHERE cache_key = ?",
                    (cache_key,),
                ).fetchone()

                if row is not None and row[0] >= cutoff:
                    try:
                        payload = json.loads(row[1])
                    except (TypeError, ValueError, json.JSONDecodeError):
                        connection.execute(
                            "DELETE FROM analysis_cache_entries WHERE cache_key = ?",
                            (cache_key,),
                        )
                    else:
                        connection.execute("COMMIT")
                        with self._lock:
                            self.hits += 1
                        self._memory_set(signature, payload, now_monotonic)
                        return copy.deepcopy(payload)

                payload = loader()
                payload_json = json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                connection.execute(
                    """
                    INSERT INTO analysis_cache_entries
                        (cache_key, file_path, created_at, payload_json)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(cache_key) DO UPDATE SET
                        file_path = excluded.file_path,
                        created_at = excluded.created_at,
                        payload_json = excluded.payload_json
                    """,
                    (cache_key, file_path, now_wall, payload_json),
                )
                connection.execute(
                    "DELETE FROM analysis_cache_entries WHERE created_at < ?",
                    (cutoff,),
                )
                connection.execute(
                    """
                    DELETE FROM analysis_cache_entries
                    WHERE cache_key NOT IN (
                        SELECT cache_key FROM analysis_cache_entries
                        ORDER BY created_at DESC LIMIT ?
                    )
                    """,
                    (self.max_entries,),
                )
                connection.execute("COMMIT")

            with self._lock:
                self.misses += 1
            self._memory_set(signature, payload, now_monotonic)
            return copy.deepcopy(payload)
        except sqlite3.Error as error:
            print(
                "Analiz cache veritabani hatasi: "
                f"{type(error).__name__}: {error}"
            )
            payload = loader()
            with self._lock:
                self.misses += 1
            self._memory_set(signature, payload, now_monotonic)
            return copy.deepcopy(payload)

    def get_or_load(self, file_path, loader):
        try:
            signature = self._signature(file_path)
        except OSError:
            with self._lock:
                self.misses += 1
            return loader()

        now_monotonic = time.monotonic()
        memory_payload = self._memory_get(signature, now_monotonic)
        if memory_payload is not None:
            return memory_payload

        if self.database_path is not None:
            return self._load_with_shared_database(
                signature,
                loader,
                now_monotonic,
            )

        payload = loader()
        with self._lock:
            self.misses += 1
        self._memory_set(signature, payload, now_monotonic)
        return copy.deepcopy(payload)

    def invalidate(self, file_path=None):
        absolute_path = os.path.abspath(file_path) if file_path else None
        with self._lock:
            if absolute_path is None:
                self._entries.clear()
            else:
                stale_keys = [
                    key for key in self._entries if key[0] == absolute_path
                ]
                for key in stale_keys:
                    self._entries.pop(key, None)

        if self.database_path is None:
            return

        try:
            self._ensure_database()
            with closing(self._connect()) as connection:
                if absolute_path is None:
                    connection.execute("DELETE FROM analysis_cache_entries")
                else:
                    connection.execute(
                        "DELETE FROM analysis_cache_entries WHERE file_path = ?",
                        (absolute_path,),
                    )
        except sqlite3.Error as error:
            print(
                "Analiz cache invalidation hatasi: "
                f"{type(error).__name__}: {error}"
            )

    def clear(self):
        self.invalidate()
        with self._lock:
            self.hits = 0
            self.misses = 0
