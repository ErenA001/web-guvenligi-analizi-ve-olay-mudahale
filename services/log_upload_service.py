import os

from werkzeug.utils import secure_filename

from scripts.config import (
    ALLOWED_LOG_EXTENSIONS,
    LOG_MIN_PART_COUNT,
    LOG_STATUS_CODE_INDEX,
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_LABEL,
    UPLOAD_DIRECTORY,
    UPLOAD_FILE_PREFIX,
)


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
        return (
            False,
            "Dosya UTF-8 metin biçiminde okunamadı.",
            0,
            0,
        )

    if "\x00" in content:
        return (
            False,
            "Dosya metin logu yerine ikili veri içeriyor.",
            0,
            0,
        )

    valid_line_count = 0
    skipped_line_count = 0

    for line in content.splitlines():
        normalized_line = line.strip()

        if not normalized_line:
            continue

        parts = normalized_line.split()

        if len(parts) < LOG_MIN_PART_COUNT:
            skipped_line_count += 1
            continue

        status_code = parts[LOG_STATUS_CODE_INDEX]

        if not status_code.isdigit():
            skipped_line_count += 1
            continue

        valid_line_count += 1

    if valid_line_count == 0:
        return (
            False,
            "Dosyada analiz edilebilen geçerli bir log satırı bulunamadı.",
            0,
            skipped_line_count,
        )

    validation_message = (
        f"{valid_line_count} geçerli log satırı bulundu."
    )

    if skipped_line_count:
        validation_message += (
            f" {skipped_line_count} hatalı satır atlandı."
        )

    return (
        True,
        validation_message,
        valid_line_count,
        skipped_line_count,
    )


def get_upload_directory(project_root):
    return os.path.abspath(
        os.path.join(
            project_root,
            UPLOAD_DIRECTORY,
        )
    )


def remove_previous_upload(previous_file_path, project_root):
    if not previous_file_path:
        return

    upload_directory = get_upload_directory(project_root)
    previous_absolute_path = os.path.abspath(previous_file_path)

    try:
        common_path = os.path.commonpath(
            [
                upload_directory,
                previous_absolute_path,
            ]
        )
    except ValueError:
        return

    if common_path != upload_directory:
        return

    if os.path.isfile(previous_absolute_path):
        os.remove(previous_absolute_path)


def save_uploaded_log(
    uploaded_file,
    project_root,
    previous_file_path=None,
):
    if uploaded_file is None:
        return (
            False,
            "Yüklenecek dosya bulunamadı.",
            None,
            None,
        )

    original_filename = uploaded_file.filename or ""

    if not original_filename.strip():
        return (
            False,
            "Lütfen bir log dosyası seçin.",
            None,
            None,
        )

    if not has_allowed_extension(original_filename):
        allowed_text = ", ".join(ALLOWED_LOG_EXTENSIONS)

        return (
            False,
            f"Yalnızca {allowed_text} uzantılı dosyalar kabul edilir.",
            None,
            None,
        )

    safe_filename = secure_filename(original_filename)

    if not safe_filename:
        return (
            False,
            "Dosya adı güvenli bir biçime dönüştürülemedi.",
            None,
            None,
        )

    if not has_allowed_extension(safe_filename):
        return (
            False,
            "Dosya uzantısı doğrulanamadı.",
            None,
            None,
        )

    file_bytes = uploaded_file.read(MAX_UPLOAD_SIZE_BYTES + 1)

    is_valid, validation_message, _, _ = validate_log_bytes(
        file_bytes
    )

    if not is_valid:
        return (
            False,
            validation_message,
            None,
            None,
        )

    upload_directory = get_upload_directory(project_root)
    os.makedirs(upload_directory, exist_ok=True)

    destination_filename = (
        f"{UPLOAD_FILE_PREFIX}{safe_filename}"
    )

    destination_path = os.path.abspath(
        os.path.join(
            upload_directory,
            destination_filename,
        )
    )

    if os.path.commonpath(
        [
            upload_directory,
            destination_path,
        ]
    ) != upload_directory:
        return (
            False,
            "Güvenli dosya yolu oluşturulamadı.",
            None,
            None,
        )

    previous_absolute_path = None

    if previous_file_path:
        previous_absolute_path = os.path.abspath(
            previous_file_path
        )

    try:
        with open(destination_path, "wb") as output_file:
            output_file.write(file_bytes)
    except OSError as error:
        print(
            "Log dosyası kayıt hatası: "
            f"{type(error).__name__}: {error}"
        )

        return (
            False,
            "Yüklenen dosya sunucuya kaydedilemedi.",
            None,
            None,
        )

    if previous_absolute_path != destination_path:
        remove_previous_upload(
            previous_file_path,
            project_root,
        )

    return (
        True,
        validation_message,
        destination_path,
        safe_filename,
    )


if __name__ == "__main__":
    valid_sample = (
        b"192.168.1.10 GET /login 401\n"
        b"192.168.1.10 POST /login 401\n"
        b"hatali satir\n"
    )

    result = validate_log_bytes(valid_sample)

    print("Doğrulama sonucu:")
    print(result)
