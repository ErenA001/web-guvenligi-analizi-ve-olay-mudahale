import os
import tempfile

from werkzeug.utils import secure_filename

from scripts.config import (
    ALLOWED_LOG_EXTENSIONS,
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_LABEL,
    UPLOAD_DIRECTORY,
    UPLOAD_FILE_PREFIX,
    UPLOAD_WORKSPACES_DIRECTORY,
)
from scripts.log_parser import parse_log_line
from services.workspace_service import is_valid_workspace_id


def get_file_extension(filename):
    return os.path.splitext(filename)[1].lower()


def has_allowed_extension(filename):
    return get_file_extension(filename) in ALLOWED_LOG_EXTENSIONS


def validate_log_bytes(file_bytes):
    if not file_bytes:
        return False, "Yüklenen dosya boş.", 0, 0

    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        return (
            False,
            f"Dosya boyutu {MAX_UPLOAD_SIZE_LABEL} sınırını aşıyor.",
            0,
            0,
        )

    try:
        content = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return False, "Dosya UTF-8 metin biçiminde okunamadı.", 0, 0

    if "\x00" in content:
        return False, "Dosya metin logu yerine ikili veri içeriyor.", 0, 0

    valid_line_count = 0
    skipped_line_count = 0

    for line in content.splitlines():
        if not line.strip():
            continue
        if parse_log_line(line) is None:
            skipped_line_count += 1
        else:
            valid_line_count += 1

    if valid_line_count == 0:
        return (
            False,
            "Dosyada analiz edilebilen geçerli bir log satırı bulunamadı.",
            0,
            skipped_line_count,
        )

    validation_message = f"{valid_line_count} geçerli log satırı bulundu."
    if skipped_line_count:
        validation_message += f" {skipped_line_count} hatalı satır atlandı."

    return True, validation_message, valid_line_count, skipped_line_count


def get_upload_directory(project_root, workspace_id=None):
    path_parts = [project_root, UPLOAD_DIRECTORY]
    if workspace_id is not None:
        if not is_valid_workspace_id(workspace_id):
            raise ValueError("Gecersiz workspace kimligi")
        path_parts.extend([UPLOAD_WORKSPACES_DIRECTORY, workspace_id])
    return os.path.realpath(os.path.join(*path_parts))


def remove_previous_upload(previous_file_path, project_root, workspace_id=None):
    if not previous_file_path:
        return

    upload_directory = get_upload_directory(project_root, workspace_id)
    previous_absolute_path = os.path.realpath(previous_file_path)

    try:
        is_inside = os.path.commonpath(
            [upload_directory, previous_absolute_path]
        ) == upload_directory
    except ValueError:
        is_inside = False

    if is_inside and os.path.isfile(previous_absolute_path):
        try:
            os.remove(previous_absolute_path)
        except OSError as error:
            print(
                "Onceki log dosyasi silinemedi: "
                f"{type(error).__name__}: {error}"
            )


def save_uploaded_log(
    uploaded_file,
    project_root,
    previous_file_path=None,
    workspace_id=None,
):
    if uploaded_file is None:
        return False, "Yüklenecek dosya bulunamadı.", None, None

    original_filename = uploaded_file.filename or ""
    if not original_filename.strip():
        return False, "Lütfen bir log dosyası seçin.", None, None

    if not has_allowed_extension(original_filename):
        allowed_text = ", ".join(ALLOWED_LOG_EXTENSIONS)
        return (
            False,
            f"Yalnızca {allowed_text} uzantılı dosyalar kabul edilir.",
            None,
            None,
        )

    safe_filename = secure_filename(original_filename)
    if not safe_filename or not has_allowed_extension(safe_filename):
        return False, "Dosya adı veya uzantısı doğrulanamadı.", None, None

    try:
        file_bytes = uploaded_file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    except (OSError, ValueError) as error:
        print(f"Log dosyasi okuma hatasi: {type(error).__name__}: {error}")
        return False, "Yuklenen dosya okunamadi.", None, None
    is_valid, validation_message, _, _ = validate_log_bytes(file_bytes)
    if not is_valid:
        return False, validation_message, None, None

    try:
        upload_directory = get_upload_directory(project_root, workspace_id)
    except ValueError:
        return False, "Güvenli çalışma alanı oluşturulamadı.", None, None

    os.makedirs(upload_directory, mode=0o700, exist_ok=True)
    try:
        os.chmod(upload_directory, 0o700)
    except OSError:
        pass
    destination_filename = f"{UPLOAD_FILE_PREFIX}{safe_filename}"
    destination_path = os.path.realpath(
        os.path.join(upload_directory, destination_filename)
    )

    if os.path.commonpath([upload_directory, destination_path]) != upload_directory:
        return False, "Güvenli dosya yolu oluşturulamadı.", None, None

    previous_absolute_path = (
        os.path.realpath(previous_file_path) if previous_file_path else None
    )

    temporary_path = None
    try:
        descriptor, temporary_path = tempfile.mkstemp(
            prefix=".upload-",
            suffix=".tmp",
            dir=upload_directory,
        )
        with os.fdopen(descriptor, "wb") as output_file:
            output_file.write(file_bytes)
            output_file.flush()
            os.fsync(output_file.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, destination_path)
    except OSError as error:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.remove(temporary_path)
            except OSError:
                pass
        print(f"Log dosyası kayıt hatası: {type(error).__name__}: {error}")
        return False, "Yüklenen dosya sunucuya kaydedilemedi.", None, None

    if previous_absolute_path != destination_path:
        remove_previous_upload(previous_file_path, project_root, workspace_id)

    return True, validation_message, destination_path, safe_filename
