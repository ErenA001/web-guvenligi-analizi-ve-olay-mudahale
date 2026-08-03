import json
import os
import tempfile
import unittest
from io import BytesIO
from unittest.mock import patch

from werkzeug.datastructures import FileStorage
from werkzeug.security import generate_password_hash

from services.auth_service import (
    get_auth_configuration,
    get_or_create_secret_key,
    remove_initial_credentials_file,
    verify_credentials,
)
from services.log_upload_service import save_uploaded_log, validate_log_bytes
from services.workspace_service import (
    get_state_file,
    get_workspace_directory,
    load_active_log_state,
    save_active_log_state,
)


class AuthServiceTests(unittest.TestCase):
    def test_configured_password_is_verified(self):
        with tempfile.TemporaryDirectory() as project_root:
            with patch.dict(
                os.environ,
                {
                    "APP_USERNAME": "analyst",
                    "APP_PASSWORD": "Strong-test-123!",
                    "APP_PASSWORD_HASH": "",
                },
            ):
                username, password_hash = get_auth_configuration(project_root)

        self.assertEqual(username, "analyst")
        self.assertTrue(
            verify_credentials(
                "analyst",
                "Strong-test-123!",
                username,
                password_hash,
            )
        )
        self.assertFalse(
            verify_credentials("analyst", "wrong", username, password_hash)
        )
        self.assertFalse(
            verify_credentials("other", "Strong-test-123!", username, password_hash)
        )

    def test_generated_credentials_and_secret_are_persistent(self):
        with tempfile.TemporaryDirectory() as project_root:
            with patch.dict(
                os.environ,
                {
                    "APP_USERNAME": "admin",
                    "APP_PASSWORD": "",
                    "APP_PASSWORD_HASH": "",
                    "APP_SECRET_KEY": "",
                },
            ):
                username, first_hash = get_auth_configuration(project_root)
                credentials_path = os.path.join(
                    project_root,
                    ".runtime",
                    "initial_credentials.txt",
                )
                with open(credentials_path, encoding="utf-8") as credentials_file:
                    credentials = credentials_file.read()
                password = credentials.split("Sifre: ", 1)[1].splitlines()[0]
                _, second_hash = get_auth_configuration(project_root)
                first_secret = get_or_create_secret_key(project_root)
                second_secret = get_or_create_secret_key(project_root)

                self.assertEqual(first_hash, second_hash)
                self.assertEqual(first_secret, second_secret)
                self.assertTrue(
                    verify_credentials(username, password, username, first_hash)
                )
                remove_initial_credentials_file(project_root)
                self.assertFalse(os.path.exists(credentials_path))

    def test_oversized_credentials_are_rejected(self):
        password_hash = generate_password_hash("valid")
        self.assertFalse(
            verify_credentials("admin", "x" * 1000, "admin", password_hash)
        )


class WorkspaceAndUploadTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.project_root = self.temporary_directory.name
        os.makedirs(os.path.join(self.project_root, "logs"), exist_ok=True)
        self.default_log = os.path.join(self.project_root, "logs", "sample_access.log")
        with open(self.default_log, "w", encoding="utf-8") as log_file:
            log_file.write("127.0.0.1 GET /health 200\n")
        self.workspace_a = "a" * 32
        self.workspace_b = "b" * 32

    def _file_storage(self, content, filename="access.log"):
        return FileStorage(
            stream=BytesIO(content.encode("utf-8")),
            filename=filename,
            content_type="text/plain",
        )

    def test_uploads_and_state_are_isolated_per_workspace(self):
        first = save_uploaded_log(
            self._file_storage("192.0.2.1 GET /one 200\n", "one.log"),
            self.project_root,
            workspace_id=self.workspace_a,
        )
        second = save_uploaded_log(
            self._file_storage("192.0.2.2 GET /two 200\n", "two.log"),
            self.project_root,
            workspace_id=self.workspace_b,
        )
        self.assertTrue(first[0])
        self.assertTrue(second[0])
        self.assertNotEqual(first[2], second[2])

        save_active_log_state(self.project_root, self.workspace_a, first[2], first[3])
        save_active_log_state(self.project_root, self.workspace_b, second[2], second[3])
        self.assertEqual(
            load_active_log_state(
                self.project_root,
                self.workspace_a,
                "logs/sample_access.log",
            )[1],
            "one.log",
        )
        self.assertEqual(
            load_active_log_state(
                self.project_root,
                self.workspace_b,
                "logs/sample_access.log",
            )[1],
            "two.log",
        )

    def test_workspace_rejects_external_active_file(self):
        with self.assertRaises(ValueError):
            save_active_log_state(
                self.project_root,
                self.workspace_a,
                self.default_log,
            )

    def test_tampered_state_falls_back_to_default(self):
        os.makedirs(get_workspace_directory(self.project_root, self.workspace_a), exist_ok=True)
        with open(get_state_file(self.project_root, self.workspace_a), "w", encoding="utf-8") as state_file:
            json.dump({"relative_path": "../../etc/passwd"}, state_file)
        active_path, active_name = load_active_log_state(
            self.project_root,
            self.workspace_a,
            "logs/sample_access.log",
        )
        self.assertEqual(
            os.path.realpath(active_path),
            os.path.realpath(self.default_log),
        )
        self.assertEqual(active_name, "sample_access.log")

    def test_symlink_state_cannot_escape_workspace(self):
        workspace_directory = get_workspace_directory(
            self.project_root,
            self.workspace_a,
        )
        os.makedirs(workspace_directory, exist_ok=True)
        external_path = os.path.join(self.project_root, "external.log")
        with open(external_path, "w", encoding="utf-8") as external_file:
            external_file.write("192.0.2.200 GET /external 200\n")
        link_path = os.path.join(workspace_directory, "linked.log")
        try:
            os.symlink(external_path, link_path)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink bu platformda desteklenmiyor")

        with open(
            get_state_file(self.project_root, self.workspace_a),
            "w",
            encoding="utf-8",
        ) as state_file:
            json.dump(
                {
                    "relative_path": os.path.relpath(link_path, self.project_root),
                    "display_name": "linked.log",
                },
                state_file,
            )

        active_path, active_name = load_active_log_state(
            self.project_root,
            self.workspace_a,
            "logs/sample_access.log",
        )
        self.assertEqual(
            os.path.realpath(active_path),
            os.path.realpath(self.default_log),
        )
        self.assertEqual(active_name, "sample_access.log")
        with self.assertRaises(ValueError):
            save_active_log_state(
                self.project_root,
                self.workspace_a,
                link_path,
            )

    def test_upload_validation_accepts_apache_and_rejects_binary(self):
        valid = (
            b'203.0.113.1 - - [04/Aug/2026:00:00:00 +0000] '
            b'"GET / HTTP/1.1" 200 10\n'
        )
        self.assertTrue(validate_log_bytes(valid)[0])
        self.assertFalse(validate_log_bytes(b"abc\x00def")[0])

    def test_upload_rejects_disallowed_extension(self):
        result = save_uploaded_log(
            self._file_storage("192.0.2.1 GET / 200\n", "payload.exe"),
            self.project_root,
            workspace_id=self.workspace_a,
        )
        self.assertFalse(result[0])


if __name__ == "__main__":
    unittest.main()
