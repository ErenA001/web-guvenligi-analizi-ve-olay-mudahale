import json
import os
import re
import tempfile

from scripts.config import UPLOAD_DIRECTORY, UPLOAD_WORKSPACES_DIRECTORY


WORKSPACE_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


def is_valid_workspace_id(workspace_id):
    return bool(
        isinstance(workspace_id, str)
        and WORKSPACE_ID_PATTERN.fullmatch(workspace_id)
    )


def get_workspace_directory(project_root, workspace_id):
    if not is_valid_workspace_id(workspace_id):
        raise ValueError("Gecersiz workspace kimligi")

    return os.path.realpath(
        os.path.join(
            project_root,
            UPLOAD_DIRECTORY,
            UPLOAD_WORKSPACES_DIRECTORY,
            workspace_id,
        )
    )


def get_state_file(project_root, workspace_id):
    return os.path.join(
        get_workspace_directory(project_root, workspace_id),
        "active_log.json",
    )


def _default_log(project_root, default_log_file):
    default_path = os.path.realpath(os.path.join(project_root, default_log_file))
    return default_path, os.path.basename(default_path)


def _safe_display_name(value, candidate_path):
    if not isinstance(value, str) or not value.strip():
        return os.path.basename(candidate_path)
    clean_name = os.path.basename(value.strip()).replace("\x00", "")
    return clean_name[:255] or os.path.basename(candidate_path)


def load_active_log_state(project_root, workspace_id, default_log_file):
    default_path, default_name = _default_log(project_root, default_log_file)
    state_file_path = get_state_file(project_root, workspace_id)

    try:
        with open(state_file_path, "r", encoding="utf-8") as state_file:
            state = json.load(state_file)
    except (OSError, ValueError, TypeError):
        return default_path, default_name

    if not isinstance(state, dict):
        return default_path, default_name

    relative_path = state.get("relative_path", "")
    if not isinstance(relative_path, str) or not relative_path:
        return default_path, default_name

    candidate_path = os.path.realpath(os.path.join(project_root, relative_path))
    workspace_directory = get_workspace_directory(project_root, workspace_id)

    try:
        is_inside_workspace = os.path.commonpath(
            [workspace_directory, candidate_path]
        ) == workspace_directory
    except ValueError:
        is_inside_workspace = False

    if not is_inside_workspace or not os.path.isfile(candidate_path):
        return default_path, default_name

    display_name = _safe_display_name(state.get("display_name", ""), candidate_path)
    return candidate_path, display_name


def save_active_log_state(
    project_root,
    workspace_id,
    file_path,
    display_name=None,
):
    workspace_directory = get_workspace_directory(project_root, workspace_id)
    os.makedirs(workspace_directory, mode=0o700, exist_ok=True)
    try:
        os.chmod(workspace_directory, 0o700)
    except OSError:
        pass

    absolute_file_path = os.path.realpath(file_path)
    try:
        is_inside_workspace = os.path.commonpath(
            [workspace_directory, absolute_file_path]
        ) == workspace_directory
    except ValueError:
        is_inside_workspace = False

    if not is_inside_workspace:
        raise ValueError("Aktif log workspace disinda olamaz")
    if not os.path.isfile(absolute_file_path):
        raise ValueError("Aktif log dosyasi bulunamadi")

    state = {
        "relative_path": os.path.relpath(
            absolute_file_path,
            os.path.realpath(project_root),
        ),
        "display_name": _safe_display_name(display_name, absolute_file_path),
    }
    state_file_path = get_state_file(project_root, workspace_id)
    descriptor, temporary_path = tempfile.mkstemp(
        prefix=".active-log-",
        suffix=".tmp",
        dir=workspace_directory,
    )

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as state_file:
            json.dump(state, state_file, ensure_ascii=False)
            state_file.flush()
            os.fsync(state_file.fileno())
        try:
            os.chmod(temporary_path, 0o600)
        except OSError:
            pass
        os.replace(temporary_path, state_file_path)
    except Exception:
        try:
            os.remove(temporary_path)
        except OSError:
            pass
        raise
