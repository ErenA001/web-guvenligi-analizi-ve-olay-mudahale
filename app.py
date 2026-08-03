import os
import secrets
import sys
from datetime import timedelta
from urllib.parse import urlsplit

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from flask import (  # noqa: E402
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.exceptions import RequestEntityTooLarge  # noqa: E402

from config import (  # noqa: E402
    ANALYSIS_CACHE_MAX_ENTRIES,
    ANALYSIS_CACHE_SCHEMA_VERSION,
    ANALYSIS_CACHE_TTL_SECONDS,
    CHATBOT_MAX_QUESTION_LENGTH,
    CHAT_RATE_LIMIT,
    CHAT_RATE_WINDOW_SECONDS,
    DASHBOARD_REFRESH_MILLISECONDS,
    DEFAULT_LOG_FILE,
    LOGIN_RATE_LIMIT,
    LOGIN_RATE_WINDOW_SECONDS,
    MAX_UPLOAD_REQUEST_BYTES,
    MAX_UPLOAD_SIZE_LABEL,
    SESSION_LIFETIME_HOURS,
    UPLOAD_RATE_LIMIT,
    UPLOAD_RATE_WINDOW_SECONDS,
    VALID_MESSAGE_TYPES,
)
from log_analyzer import analyze_logs  # noqa: E402
from services.ai_explainer import generate_incident_explanation  # noqa: E402
from services.analysis_cache import AnalysisCache  # noqa: E402
from services.auth_service import (  # noqa: E402
    get_auth_configuration,
    get_or_create_secret_key,
    remove_initial_credentials_file,
    verify_credentials,
)
from services.chatbot_service import answer_log_question  # noqa: E402
from services.log_upload_service import save_uploaded_log  # noqa: E402
from services.rate_limiter import SQLiteRateLimiter  # noqa: E402
from services.workspace_service import (  # noqa: E402
    is_valid_workspace_id,
    load_active_log_state as load_workspace_log_state,
    save_active_log_state as save_workspace_log_state,
)


FRONTEND_DIST = os.path.join(PROJECT_ROOT, "frontend", "dist")
RUNTIME_DIRECTORY = os.path.join(PROJECT_ROOT, ".runtime")
RATE_LIMIT_DATABASE = os.path.join(RUNTIME_DIRECTORY, "rate_limits.sqlite3")
ANALYSIS_CACHE_DATABASE = os.path.join(
    RUNTIME_DIRECTORY,
    "analysis_cache.sqlite3",
)

AUTH_USERNAME, AUTH_PASSWORD_HASH = get_auth_configuration(PROJECT_ROOT)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=get_or_create_secret_key(PROJECT_ROOT),
    MAX_CONTENT_LENGTH=MAX_UPLOAD_REQUEST_BYTES,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=SESSION_LIFETIME_HOURS),
    SESSION_COOKIE_NAME="secure_ai_session",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "0") == "1",
)

analysis_cache = AnalysisCache(
    max_entries=ANALYSIS_CACHE_MAX_ENTRIES,
    ttl_seconds=ANALYSIS_CACHE_TTL_SECONDS,
    schema_version=ANALYSIS_CACHE_SCHEMA_VERSION,
    database_path=ANALYSIS_CACHE_DATABASE,
)
rate_limiter = SQLiteRateLimiter(RATE_LIMIT_DATABASE)

VALID_INCIDENT_TYPES = [
    "BRUTE_FORCE",
    "UNAUTHORIZED_ACCESS",
    "FORBIDDEN_ACCESS",
    "PATH_TRAVERSAL_ATTEMPT",
    "SCANNER_ACTIVITY",
    "SUSPICIOUS_ACTIVITY",
    "NORMAL",
]
VALID_SEVERITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
PUBLIC_ENDPOINTS = {"login", "api_health"}


def is_authenticated():
    return session.get("authenticated") is True


def get_workspace_id():
    workspace_id = session.get("workspace_id", "")
    if not is_valid_workspace_id(workspace_id):
        workspace_id = secrets.token_hex(16)
        session["workspace_id"] = workspace_id
    return workspace_id


def load_active_log_state():
    return load_workspace_log_state(
        PROJECT_ROOT,
        get_workspace_id(),
        DEFAULT_LOG_FILE,
    )


def save_active_log_state(file_path, display_name=None):
    save_workspace_log_state(
        PROJECT_ROOT,
        get_workspace_id(),
        file_path,
        display_name,
    )


def get_active_log():
    return load_active_log_state()


def get_dashboard_data(file_path):
    return analysis_cache.get_or_load(
        file_path,
        lambda: analyze_logs(
            file_path,
            include_header_check=False,
            write_report=False,
        ),
    )


def normalize_incident_type(incident_type):
    return incident_type if incident_type in VALID_INCIDENT_TYPES else ""


def normalize_severity(severity):
    return severity if severity in VALID_SEVERITIES else ""


def normalize_message_type(message_type):
    return message_type if message_type in VALID_MESSAGE_TYPES else "info"


def calculate_severity_counts(dashboard_data):
    severity_counts = {severity: 0 for severity in VALID_SEVERITIES}
    for row in dashboard_data:
        severity = row.get("severity")
        if severity in severity_counts:
            severity_counts[severity] += 1
    return severity_counts


def filter_dashboard_data(dashboard_data, selected_incident_type, selected_severity):
    filtered_data = dashboard_data
    if selected_incident_type:
        filtered_data = [
            row
            for row in filtered_data
            if row.get("incident_type") == selected_incident_type
        ]
    if selected_severity:
        filtered_data = [
            row for row in filtered_data if row.get("severity") == selected_severity
        ]
    return filtered_data


def build_refresh_url(selected_incident_type, selected_severity):
    refresh_arguments = {}
    if selected_incident_type:
        refresh_arguments["incident_type"] = selected_incident_type
    if selected_severity:
        refresh_arguments["severity"] = selected_severity
    return url_for("index", **refresh_arguments)


def render_dashboard(
    dashboard_data,
    selected_incident_type="",
    selected_severity="",
    question="",
    chatbot_answer=None,
    status_message="",
    status_type="info",
):
    selected_incident_type = normalize_incident_type(selected_incident_type)
    selected_severity = normalize_severity(selected_severity)
    _, active_log_name = get_active_log()

    return render_template(
        "index.html",
        data=filter_dashboard_data(
            dashboard_data,
            selected_incident_type,
            selected_severity,
        ),
        incident_types=VALID_INCIDENT_TYPES,
        severities=VALID_SEVERITIES,
        selected_incident_type=selected_incident_type,
        selected_severity=selected_severity,
        severity_counts=calculate_severity_counts(dashboard_data),
        question=question,
        chatbot_answer=chatbot_answer,
        status_message=status_message,
        status_type=normalize_message_type(status_type),
        active_log_name=active_log_name,
        chatbot_max_question_length=CHATBOT_MAX_QUESTION_LENGTH,
        max_upload_size_label=MAX_UPLOAD_SIZE_LABEL,
        dashboard_refresh_milliseconds=DASHBOARD_REFRESH_MILLISECONDS,
        refresh_url=build_refresh_url(selected_incident_type, selected_severity),
    )


def get_client_ip():
    # Proxy headers are deliberately ignored unless the deployment adds a trusted
    # ProxyFix layer. This prevents clients from spoofing their limiter identity.
    return request.remote_addr or "unknown"


def get_rate_limit_subject(include_workspace=True):
    parts = [get_client_ip()]
    if is_authenticated():
        parts.append(str(session.get("username", "authenticated")))
        if include_workspace:
            parts.append(get_workspace_id())
    return ":".join(parts)


def enforce_rate_limit(bucket, limit, window_seconds, include_workspace=True):
    subject = get_rate_limit_subject(include_workspace=include_workspace)
    allowed, retry_after = rate_limiter.allow(
        bucket,
        subject,
        limit,
        window_seconds,
    )
    if allowed:
        return None

    message = (
        "Çok fazla istek gönderildi. "
        f"Lütfen {retry_after} saniye sonra tekrar deneyin."
    )
    if request.path.startswith("/api/"):
        payload = {"success": False, "message": message, "answer": message}
        response = app.json.response(payload)
        response.status_code = 429
    else:
        response = app.make_response((message, 429))
    response.headers["Retry-After"] = str(retry_after)
    return response


def safe_next_url(candidate):
    if not isinstance(candidate, str) or not candidate:
        return url_for("index")
    parsed = urlsplit(candidate)
    if (
        parsed.scheme
        or parsed.netloc
        or not candidate.startswith("/")
        or "\\" in candidate
        or "\r" in candidate
        or "\n" in candidate
    ):
        return url_for("index")
    return candidate


@app.before_request
def require_authentication():
    if request.endpoint in PUBLIC_ENDPOINTS:
        return None
    if is_authenticated():
        return None
    if request.path.startswith("/api/"):
        return {
            "success": False,
            "message": "Oturum açmanız gerekiyor.",
            "login_url": url_for("login"),
        }, 401
    return redirect(url_for("login", next=request.full_path.rstrip("?")))


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-XSS-Protection", "0")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )
    if request.is_secure:
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=63072000; includeSubDomains",
        )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; font-src 'self' data:; "
        "object-src 'none'; frame-ancestors 'none'; base-uri 'self'; "
        "form-action 'self'",
    )
    if request.path.startswith("/api/") or request.endpoint in {"login", "logout"}:
        response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    print(f"Dosya boyutu sınırı aşıldı: {type(error).__name__}")
    message = f"Dosya boyutu {MAX_UPLOAD_SIZE_LABEL} sınırını aşıyor."
    if request.path.startswith("/api/"):
        return {"success": False, "message": message}, 413
    return redirect(
        url_for("index", status_message=message, status_type="error")
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated():
        return redirect(url_for("index"))

    error_message = ""
    next_url = safe_next_url(request.values.get("next", ""))

    if request.method == "POST":
        limited_response = enforce_rate_limit(
            "login",
            LOGIN_RATE_LIMIT,
            LOGIN_RATE_WINDOW_SECONDS,
            include_workspace=False,
        )
        if limited_response is not None:
            return render_template(
                "login.html",
                error_message="Çok fazla başarısız giriş denemesi. Daha sonra tekrar deneyin.",
                next_url=next_url,
            ), 429

        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if verify_credentials(
            username,
            password,
            AUTH_USERNAME,
            AUTH_PASSWORD_HASH,
        ):
            rate_limiter.reset("login", get_client_ip())
            remove_initial_credentials_file(PROJECT_ROOT)
            session.clear()
            session["authenticated"] = True
            session["username"] = AUTH_USERNAME
            session["workspace_id"] = secrets.token_hex(16)
            session.permanent = True
            return redirect(next_url)

        error_message = "Kullanıcı adı veya şifre hatalı."

    return render_template(
        "login.html",
        error_message=error_message,
        next_url=next_url,
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


def serve_react_index():
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if not os.path.isfile(index_path):
        return (
            "React production build bulunamadı. "
            "Önce 'cd frontend && npm install && npm run build' komutlarını çalıştırın.",
            503,
        )
    return send_from_directory(FRONTEND_DIST, "index.html")


@app.route("/")
def index():
    return serve_react_index()


@app.route("/react")
def react_dashboard():
    return redirect(url_for("index"), code=302)


@app.route("/assets/<path:filename>")
def react_assets(filename):
    return send_from_directory(os.path.join(FRONTEND_DIST, "assets"), filename)


@app.route("/<path:filename>")
def react_static(filename):
    requested_path = os.path.join(FRONTEND_DIST, filename)
    if os.path.isfile(requested_path):
        return send_from_directory(FRONTEND_DIST, filename)
    return serve_react_index()


@app.route("/chat", methods=["POST"])
def chat():
    limited_response = enforce_rate_limit(
        "chat",
        CHAT_RATE_LIMIT,
        CHAT_RATE_WINDOW_SECONDS,
    )
    if limited_response is not None:
        return limited_response

    question = request.form.get("question", "")
    selected_incident_type = normalize_incident_type(
        request.form.get("incident_type", "")
    )
    selected_severity = normalize_severity(request.form.get("severity", ""))
    current_log_file, _ = get_active_log()
    dashboard_data = get_dashboard_data(current_log_file)

    return render_dashboard(
        dashboard_data,
        selected_incident_type=selected_incident_type,
        selected_severity=selected_severity,
        question=question.strip(),
        chatbot_answer=answer_log_question(question, dashboard_data),
    )


def process_upload(api_response):
    limited_response = enforce_rate_limit(
        "upload",
        UPLOAD_RATE_LIMIT,
        UPLOAD_RATE_WINDOW_SECONDS,
    )
    if limited_response is not None:
        return limited_response

    uploaded_file = request.files.get("log_file")
    current_log_file, _ = get_active_log()
    workspace_id = get_workspace_id()

    result = save_uploaded_log(
        uploaded_file,
        PROJECT_ROOT,
        previous_file_path=current_log_file,
        workspace_id=workspace_id,
    )
    is_successful, upload_message, uploaded_path, uploaded_name = result

    if not is_successful:
        if api_response:
            return {"success": False, "message": upload_message}, 400
        return redirect(
            url_for("index", status_message=upload_message, status_type="error")
        )

    analysis_cache.invalidate(current_log_file)
    analysis_cache.invalidate(uploaded_path)
    save_active_log_state(uploaded_path, uploaded_name)

    if api_response:
        return {
            "success": True,
            "message": upload_message,
            "active_log_name": uploaded_name,
        }
    return redirect(
        url_for(
            "index",
            status_message=f"{uploaded_name} yüklendi. {upload_message}",
            status_type="success",
        )
    )


@app.route("/upload_log", methods=["POST"])
def upload_log():
    return process_upload(api_response=False)


@app.route("/ai_explain", methods=["POST"])
def ai_explain():
    ip_address = request.form.get("ip", "")
    current_log_file, _ = get_active_log()
    dashboard_data = get_dashboard_data(current_log_file)
    incident = next(
        (row for row in dashboard_data if row.get("ip") == ip_address),
        None,
    )
    explanation = (
        generate_incident_explanation(incident)
        if incident is not None
        else "Bu IP adresine ait bir analiz sonucu bulunamadı."
    )
    return render_template(
        "ai_result.html",
        incident=incident,
        explanation=explanation,
    )


@app.route("/api/dashboard")
def api_dashboard():
    selected_incident_type = normalize_incident_type(
        request.args.get("incident_type", "")
    )
    selected_severity = normalize_severity(request.args.get("severity", ""))
    current_log_file, current_log_name = get_active_log()
    dashboard_data = get_dashboard_data(current_log_file)

    return {
        "data": filter_dashboard_data(
            dashboard_data,
            selected_incident_type,
            selected_severity,
        ),
        "severity_counts": calculate_severity_counts(dashboard_data),
        "active_log_name": current_log_name,
        "username": session.get("username", ""),
    }


@app.route("/api/health")
def api_health():
    active_log_name = None
    if is_authenticated():
        _, active_log_name = get_active_log()
    return {
        "status": "ok",
        "service": "secure-ai-web-monitor",
        "active_log_name": active_log_name,
        "authenticated": is_authenticated(),
    }


@app.route("/api/chat", methods=["POST"])
def api_chat():
    limited_response = enforce_rate_limit(
        "chat",
        CHAT_RATE_LIMIT,
        CHAT_RATE_WINDOW_SECONDS,
    )
    if limited_response is not None:
        return limited_response

    request_body = request.get_json(silent=True)
    if not isinstance(request_body, dict):
        return {"answer": "Geçerli bir JSON isteği gönderin."}, 400

    question = request_body.get("question", "")
    conversation_history = request_body.get("history", [])
    if not isinstance(question, str):
        return {"answer": "Soru metin biçiminde olmalıdır."}, 400
    if len(question) > CHATBOT_MAX_QUESTION_LENGTH:
        return {
            "answer": (
                f"Soru en fazla {CHATBOT_MAX_QUESTION_LENGTH} karakter olabilir."
            )
        }, 400
    if not isinstance(conversation_history, list):
        conversation_history = []

    current_log_file, _ = get_active_log()
    dashboard_data = get_dashboard_data(current_log_file)
    chatbot_answer = answer_log_question(
        question,
        dashboard_data,
        conversation_history=conversation_history,
    )
    return {"answer": chatbot_answer}


@app.route("/api/upload", methods=["POST"])
def api_upload():
    return process_upload(api_response=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
