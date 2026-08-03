import os
import tempfile
import unittest
from unittest.mock import patch

os.environ["APP_USERNAME"] = "testuser"
os.environ["APP_PASSWORD"] = "Test-password-123!"
os.environ["APP_PASSWORD_HASH"] = ""
os.environ["APP_SECRET_KEY"] = "test-secret-key-for-unit-tests"
os.environ["NVIDIA_API_KEY"] = ""

try:
    import app as app_module
    from services.analysis_cache import AnalysisCache
    from services.rate_limiter import SQLiteRateLimiter
except ModuleNotFoundError as import_error:
    app_module = None
    APP_IMPORT_ERROR = import_error
else:
    APP_IMPORT_ERROR = None


@unittest.skipIf(
    app_module is None,
    f"Flask test bağımlılığı bu ortamda kurulu değil: {APP_IMPORT_ERROR}",
)
class ChatApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        app_module.app.config.update(TESTING=True)
        self.original_analysis_cache = app_module.analysis_cache
        app_module.analysis_cache = AnalysisCache(
            max_entries=8,
            ttl_seconds=300,
            schema_version="chat-api-test",
            database_path=os.path.join(
                self.temporary_directory.name,
                "analysis-cache.sqlite3",
            ),
        )
        app_module.rate_limiter = SQLiteRateLimiter(
            os.path.join(self.temporary_directory.name, "rate.sqlite3")
        )
        self.client = app_module.app.test_client()
        self.client.post(
            "/login",
            data={
                "username": "testuser",
                "password": "Test-password-123!",
                "next": "/",
            },
        )

    def tearDown(self):
        app_module.analysis_cache.clear()
        app_module.analysis_cache = self.original_analysis_cache

    def test_api_accepts_and_uses_history(self):
        with patch.object(
            app_module,
            "get_dashboard_data",
            return_value=[
                {
                    "ip": "192.168.1.11",
                    "request_count": 120,
                    "incident_type": "BRUTE_FORCE",
                    "severity": "CRITICAL",
                    "score": 45,
                    "recommendation": "IP engellenmeli (block)",
                }
            ],
        ):
            response = self.client.post(
                "/api/chat",
                json={
                    "question": "Buna ne yapabilirim?",
                    "history": [
                        {
                            "role": "user",
                            "content": "192.168.1.11 hakkında bilgi ver",
                        },
                        {
                            "role": "assistant",
                            "content": "BRUTE_FORCE kaydı",
                        },
                    ],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("192.168.1.11 için", response.get_json()["answer"])

    def test_api_answers_multiline_social_and_security_questions(self):
        dashboard_data = [
            {
                "ip": "192.168.1.11",
                "request_count": 120,
                "incident_type": "BRUTE_FORCE",
                "severity": "CRITICAL",
                "score": 45,
                "recommendation": "IP engellenmeli (block)",
            },
            {
                "ip": "192.168.1.1",
                "request_count": 2,
                "incident_type": "NORMAL",
                "severity": "LOW",
                "score": 0,
                "recommendation": "Aksiyon gerekmiyor",
            },
        ]

        with patch.object(
            app_module,
            "get_dashboard_data",
            return_value=dashboard_data,
        ):
            response = self.client.post(
                "/api/chat",
                json={
                    "question": (
                        "hangi ipler riskli\n"
                        "bunlara ne yapabilirim\n"
                        "risksiz ipler nedir\n"
                        "tamam sağ olasın kral"
                    ),
                    "history": [],
                },
            )

        self.assertEqual(response.status_code, 200)
        answer = response.get_json()["answer"]
        self.assertIn("IP engellenmeli", answer)
        self.assertIn("192.168.1.1", answer)
        self.assertIn("Eyvallah kral", answer)

    def test_api_rejects_invalid_json_and_oversized_question(self):
        invalid = self.client.post(
            "/api/chat",
            data="not json",
            content_type="text/plain",
        )
        self.assertEqual(invalid.status_code, 400)

        oversized = self.client.post(
            "/api/chat",
            json={"question": "x" * 301},
        )
        self.assertEqual(oversized.status_code, 400)


if __name__ == "__main__":
    unittest.main()
