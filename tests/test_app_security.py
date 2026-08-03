import io
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ["APP_USERNAME"] = "testuser"
os.environ["APP_PASSWORD"] = "Test-password-123!"
os.environ["APP_PASSWORD_HASH"] = ""
os.environ["APP_SECRET_KEY"] = "test-secret-key-for-unit-tests"
os.environ["NVIDIA_API_KEY"] = ""

import app as app_module
from services.analysis_cache import AnalysisCache
from services.rate_limiter import SQLiteRateLimiter


class AppSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.project_root = self.temporary_directory.name
        os.makedirs(os.path.join(self.project_root, "logs"), exist_ok=True)
        with open(
            os.path.join(self.project_root, "logs", "sample_access.log"),
            "w",
            encoding="utf-8",
        ) as log_file:
            log_file.write("127.0.0.1 GET /health 200\n")

        self.original_project_root = app_module.PROJECT_ROOT
        self.original_analysis_cache = app_module.analysis_cache
        app_module.PROJECT_ROOT = self.project_root
        app_module.analysis_cache = AnalysisCache(
            max_entries=16,
            ttl_seconds=300,
            schema_version="app-test",
            database_path=os.path.join(
                self.project_root,
                ".runtime",
                "analysis_cache.sqlite3",
            ),
        )
        app_module.rate_limiter = SQLiteRateLimiter(
            os.path.join(self.project_root, ".runtime", "rate_limits.sqlite3")
        )
        app_module.app.config.update(TESTING=True)
        self.client = app_module.app.test_client()

    def tearDown(self):
        app_module.analysis_cache.clear()
        app_module.analysis_cache = self.original_analysis_cache
        app_module.PROJECT_ROOT = self.original_project_root

    def login(self, client=None, next_url="/"):
        client = client or self.client
        return client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "Test-password-123!",
                "next": next_url,
            },
            follow_redirects=False,
        )

    def test_health_is_public_but_dashboard_requires_authentication(self):
        health_response = self.client.get("/api/health")
        self.assertEqual(health_response.status_code, 200)
        self.assertFalse(health_response.get_json()["authenticated"])

        dashboard_response = self.client.get("/api/dashboard")
        self.assertEqual(dashboard_response.status_code, 401)
        self.assertIn("login_url", dashboard_response.get_json())

    def test_login_sets_hardened_cookie_and_allows_dashboard(self):
        login_response = self.login()
        self.assertEqual(login_response.status_code, 302)
        cookie = login_response.headers.get("Set-Cookie", "")
        self.assertIn("secure_ai_session=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)

        dashboard_response = self.client.get("/api/dashboard")
        self.assertEqual(dashboard_response.status_code, 200)
        payload = dashboard_response.get_json()
        self.assertEqual(payload["username"], "testuser")
        self.assertEqual(payload["active_log_name"], "sample_access.log")

    def test_external_next_url_is_not_used(self):
        response = self.login(next_url="https://evil.example/phish")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

    def test_backslash_next_url_is_not_used(self):
        response = self.login(next_url="/\\evil.example")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

    def test_security_headers_are_present(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-XSS-Protection"], "0")
        self.assertEqual(response.headers["Cross-Origin-Opener-Policy"], "same-origin")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_chat_rate_limit_returns_429_and_retry_after(self):
        self.login()
        with (
            patch.object(app_module, "CHAT_RATE_LIMIT", 2),
            patch.object(app_module, "CHAT_RATE_WINDOW_SECONDS", 60),
            patch.object(app_module, "get_dashboard_data", return_value=[]),
        ):
            first = self.client.post("/api/chat", json={"question": "selam"})
            second = self.client.post("/api/chat", json={"question": "selam"})
            third = self.client.post("/api/chat", json={"question": "selam"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 429)
        self.assertIn("Retry-After", third.headers)
        self.assertFalse(third.get_json()["success"])

    def test_login_rate_limit_blocks_repeated_failures(self):
        with (
            patch.object(app_module, "LOGIN_RATE_LIMIT", 2),
            patch.object(app_module, "LOGIN_RATE_WINDOW_SECONDS", 300),
        ):
            first = self.client.post(
                "/login",
                data={"username": "testuser", "password": "wrong"},
            )
            second = self.client.post(
                "/login",
                data={"username": "testuser", "password": "wrong"},
            )
            third = self.client.post(
                "/login",
                data={"username": "testuser", "password": "wrong"},
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 429)

    def test_upload_rate_limit_is_enforced(self):
        self.login()
        with (
            patch.object(app_module, "UPLOAD_RATE_LIMIT", 1),
            patch.object(app_module, "UPLOAD_RATE_WINDOW_SECONDS", 300),
        ):
            first = self.client.post(
                "/api/upload",
                data={
                    "log_file": (
                        io.BytesIO(b"192.0.2.1 GET /one 200\n"),
                        "one.log",
                    )
                },
                content_type="multipart/form-data",
            )
            second = self.client.post(
                "/api/upload",
                data={
                    "log_file": (
                        io.BytesIO(b"192.0.2.2 GET /two 200\n"),
                        "two.log",
                    )
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)

    def test_dashboard_analysis_is_cached_until_file_changes(self):
        self.login()
        calls = []

        def fake_analyzer(*_args, **_kwargs):
            calls.append(1)
            return []

        with patch.object(app_module, "analyze_logs", side_effect=fake_analyzer):
            self.assertEqual(self.client.get("/api/dashboard").status_code, 200)
            self.assertEqual(self.client.get("/api/dashboard").status_code, 200)

            log_path = os.path.join(self.project_root, "logs", "sample_access.log")
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write("192.0.2.8 GET /changed 200\n")
            self.assertEqual(self.client.get("/api/dashboard").status_code, 200)

        self.assertEqual(len(calls), 2)

    def test_two_sessions_keep_uploaded_logs_separate(self):
        client_a = app_module.app.test_client()
        client_b = app_module.app.test_client()
        self.login(client_a)
        self.login(client_b)

        upload_a = client_a.post(
            "/api/upload",
            data={
                "log_file": (
                    io.BytesIO(b"192.0.2.11 GET /alpha 200\n"),
                    "alpha.log",
                )
            },
            content_type="multipart/form-data",
        )
        upload_b = client_b.post(
            "/api/upload",
            data={
                "log_file": (
                    io.BytesIO(b"192.0.2.22 GET /beta 200\n"),
                    "beta.log",
                )
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(upload_a.status_code, 200)
        self.assertEqual(upload_b.status_code, 200)

        dashboard_a = client_a.get("/api/dashboard").get_json()
        dashboard_b = client_b.get("/api/dashboard").get_json()
        self.assertEqual(dashboard_a["active_log_name"], "alpha.log")
        self.assertEqual(dashboard_b["active_log_name"], "beta.log")
        self.assertEqual(dashboard_a["data"][0]["ip"], "192.0.2.11")
        self.assertEqual(dashboard_b["data"][0]["ip"], "192.0.2.22")

        with client_a.session_transaction() as session_a:
            workspace_a = session_a["workspace_id"]
        with client_b.session_transaction() as session_b:
            workspace_b = session_b["workspace_id"]
        self.assertNotEqual(workspace_a, workspace_b)

    def test_logout_clears_session(self):
        self.login()
        response = self.client.post("/logout", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")
        self.assertEqual(self.client.get("/api/dashboard").status_code, 401)


if __name__ == "__main__":
    unittest.main()
