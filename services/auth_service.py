import os
import secrets
import string
import threading
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - Unix fallback
    msvcrt = None


RUNTIME_DIRECTORY_NAME = ".runtime"
SECRET_FILE_NAME = "session_secret.txt"
PASSWORD_HASH_FILE_NAME = "admin_password_hash.txt"
INITIAL_CREDENTIALS_FILE_NAME = "initial_credentials.txt"
LOCK_FILE_NAME = "runtime_config.lock"
MAX_USERNAME_LENGTH = 128
MAX_PASSWORD_LENGTH = 512
_LOCAL_LOCK = threading.RLock()


def _runtime_directory(project_root):
    path = Path(project_root) / RUNTIME_DIRECTORY_NAME
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path


def _write_private(path, content):
    temporary_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with open(temporary_path, "w", encoding="utf-8") as output_file:
        output_file.write(content)
        output_file.flush()
        os.fsync(output_file.fileno())
    try:
        os.chmod(temporary_path, 0o600)
    except OSError:
        pass
    os.replace(temporary_path, path)


def _lock_file(lock_handle):
    _LOCAL_LOCK.acquire()
    try:
        if fcntl is not None:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        elif msvcrt is not None:  # pragma: no cover - Windows only
            lock_handle.seek(0)
            if lock_handle.read(1) == "":
                lock_handle.write("0")
                lock_handle.flush()
            lock_handle.seek(0)
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_LOCK, 1)
    except Exception:
        _LOCAL_LOCK.release()
        raise


def _unlock_file(lock_handle):
    try:
        if fcntl is not None:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        elif msvcrt is not None:  # pragma: no cover - Windows only
            lock_handle.seek(0)
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        _LOCAL_LOCK.release()


def _with_runtime_lock(project_root):
    runtime_directory = _runtime_directory(project_root)
    lock_path = runtime_directory / LOCK_FILE_NAME
    lock_handle = open(lock_path, "a+", encoding="utf-8")
    _lock_file(lock_handle)
    return lock_handle, runtime_directory


def _release_runtime_lock(lock_handle):
    _unlock_file(lock_handle)
    lock_handle.close()


def get_or_create_secret_key(project_root):
    configured = os.getenv("APP_SECRET_KEY", "").strip()
    if configured:
        return configured

    lock_handle, runtime_directory = _with_runtime_lock(project_root)
    try:
        secret_path = runtime_directory / SECRET_FILE_NAME
        if secret_path.is_file():
            existing = secret_path.read_text(encoding="utf-8").strip()
            if existing:
                return existing

        secret = secrets.token_urlsafe(48)
        _write_private(secret_path, secret + "\n")
        return secret
    finally:
        _release_runtime_lock(lock_handle)


def _generate_password(length=18):
    alphabet = string.ascii_letters + string.digits + "!@#$%*-_"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(character.islower() for character in password)
            and any(character.isupper() for character in password)
            and any(character.isdigit() for character in password)
            and any(character in "!@#$%*-_" for character in password)
        ):
            return password


def get_auth_configuration(project_root):
    username = os.getenv("APP_USERNAME", "admin").strip() or "admin"
    configured_hash = os.getenv("APP_PASSWORD_HASH", "").strip()
    configured_password = os.getenv("APP_PASSWORD", "")

    if configured_hash:
        return username, configured_hash
    if configured_password:
        return username, generate_password_hash(configured_password)

    lock_handle, runtime_directory = _with_runtime_lock(project_root)
    try:
        hash_path = runtime_directory / PASSWORD_HASH_FILE_NAME
        if hash_path.is_file():
            existing_hash = hash_path.read_text(encoding="utf-8").strip()
            if existing_hash:
                return username, existing_hash

        password = _generate_password()
        password_hash = generate_password_hash(password)
        _write_private(hash_path, password_hash + "\n")

        credentials_path = runtime_directory / INITIAL_CREDENTIALS_FILE_NAME
        credentials_content = (
            "SECURE AI ILK GIRIS BILGILERI\n"
            "============================\n"
            f"Kullanici adi: {username}\n"
            f"Sifre: {password}\n\n"
            "Bu dosya ilk basarili giristen sonra otomatik silinir. "
            "Kalici sifrenizi APP_PASSWORD_HASH ortam degiskeniyle yonetin.\n"
        )
        _write_private(credentials_path, credentials_content)
        return username, password_hash
    finally:
        _release_runtime_lock(lock_handle)


def remove_initial_credentials_file(project_root):
    credentials_path = (
        Path(project_root) / RUNTIME_DIRECTORY_NAME / INITIAL_CREDENTIALS_FILE_NAME
    )
    try:
        credentials_path.unlink()
    except FileNotFoundError:
        return
    except OSError as error:
        print(
            "Ilk giris bilgileri dosyasi silinemedi: "
            f"{type(error).__name__}: {error}"
        )


def verify_credentials(username, password, configured_username, password_hash):
    if not isinstance(username, str) or not isinstance(password, str):
        return False
    if len(username) > MAX_USERNAME_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
        return False

    username_matches = secrets.compare_digest(
        username.strip(),
        configured_username,
    )
    try:
        password_matches = check_password_hash(password_hash, password)
    except (ValueError, TypeError):
        password_matches = False

    return username_matches and password_matches
