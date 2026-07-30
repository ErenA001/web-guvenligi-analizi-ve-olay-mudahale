import os
import sys

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "scripts",
    ),
)

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.exceptions import RequestEntityTooLarge

from config import (
    CHATBOT_MAX_QUESTION_LENGTH,
    DASHBOARD_REFRESH_MILLISECONDS,
    DEFAULT_LOG_FILE,
    MAX_UPLOAD_REQUEST_BYTES,
    MAX_UPLOAD_SIZE_LABEL,
    VALID_MESSAGE_TYPES,
)
from log_analyzer import analyze_logs
from services.ai_explainer import (
    generate_incident_explanation,
)
from services.chatbot_service import answer_log_question
from services.log_upload_service import save_uploaded_log


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_REQUEST_BYTES

active_log_file = os.path.join(
    PROJECT_ROOT,
    DEFAULT_LOG_FILE,
)
active_log_name = os.path.basename(active_log_file)

VALID_INCIDENT_TYPES = [
    "BRUTE_FORCE",
    "UNAUTHORIZED_ACCESS",
    "FORBIDDEN_ACCESS",
    "PATH_TRAVERSAL_ATTEMPT",
    "SCANNER_ACTIVITY",
    "SUSPICIOUS_ACTIVITY",
    "NORMAL",
]

VALID_SEVERITIES = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]


def normalize_incident_type(incident_type):
    if incident_type in VALID_INCIDENT_TYPES:
        return incident_type

    return ""


def normalize_severity(severity):
    if severity in VALID_SEVERITIES:
        return severity

    return ""


def normalize_message_type(message_type):
    if message_type in VALID_MESSAGE_TYPES:
        return message_type

    return "info"


def calculate_severity_counts(dashboard_data):
    severity_counts = {
        "LOW": 0,
        "MEDIUM": 0,
        "HIGH": 0,
        "CRITICAL": 0,
    }

    for row in dashboard_data:
        severity = row.get("severity")

        if severity in severity_counts:
            severity_counts[severity] += 1

    return severity_counts


def filter_dashboard_data(
    dashboard_data,
    selected_incident_type,
    selected_severity,
):
    filtered_data = dashboard_data

    if selected_incident_type:
        filtered_data = [
            row
            for row in filtered_data
            if row.get("incident_type")
            == selected_incident_type
        ]

    if selected_severity:
        filtered_data = [
            row
            for row in filtered_data
            if row.get("severity") == selected_severity
        ]

    return filtered_data


def build_refresh_url(
    selected_incident_type,
    selected_severity,
):
    refresh_arguments = {}

    if selected_incident_type:
        refresh_arguments["incident_type"] = (
            selected_incident_type
        )

    if selected_severity:
        refresh_arguments["severity"] = selected_severity

    return url_for(
        "index",
        **refresh_arguments,
    )


def render_dashboard(
    dashboard_data,
    selected_incident_type="",
    selected_severity="",
    question="",
    chatbot_answer=None,
    status_message="",
    status_type="info",
):
    selected_incident_type = normalize_incident_type(
        selected_incident_type
    )
    selected_severity = normalize_severity(
        selected_severity
    )
    status_type = normalize_message_type(status_type)

    filtered_data = filter_dashboard_data(
        dashboard_data,
        selected_incident_type,
        selected_severity,
    )

    severity_counts = calculate_severity_counts(
        dashboard_data
    )

    return render_template(
        "index.html",
        data=filtered_data,
        incident_types=VALID_INCIDENT_TYPES,
        severities=VALID_SEVERITIES,
        selected_incident_type=selected_incident_type,
        selected_severity=selected_severity,
        severity_counts=severity_counts,
        question=question,
        chatbot_answer=chatbot_answer,
        status_message=status_message,
        status_type=status_type,
        active_log_name=active_log_name,
        chatbot_max_question_length=(
            CHATBOT_MAX_QUESTION_LENGTH
        ),
        max_upload_size_label=MAX_UPLOAD_SIZE_LABEL,
        dashboard_refresh_milliseconds=(
            DASHBOARD_REFRESH_MILLISECONDS
        ),
        refresh_url=build_refresh_url(
            selected_incident_type,
            selected_severity,
        ),
    )


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    print(
        "Dosya boyutu sınırı aşıldı: "
        f"{type(error).__name__}"
    )

    return redirect(
        url_for(
            "index",
            status_message=(
                "Dosya boyutu "
                f"{MAX_UPLOAD_SIZE_LABEL} sınırını aşıyor."
            ),
            status_type="error",
        )
    )


@app.route("/")
def index():
    selected_incident_type = normalize_incident_type(
        request.args.get("incident_type", "")
    )
    selected_severity = normalize_severity(
        request.args.get("severity", "")
    )

    status_message = request.args.get(
        "status_message",
        "",
    )
    status_type = normalize_message_type(
        request.args.get(
            "status_type",
            "info",
        )
    )

    dashboard_data = analyze_logs(active_log_file)

    return render_dashboard(
        dashboard_data,
        selected_incident_type=selected_incident_type,
        selected_severity=selected_severity,
        status_message=status_message,
        status_type=status_type,
    )


@app.route("/chat", methods=["POST"])
def chat():
    question = request.form.get("question", "")

    selected_incident_type = normalize_incident_type(
        request.form.get("incident_type", "")
    )
    selected_severity = normalize_severity(
        request.form.get("severity", "")
    )

    dashboard_data = analyze_logs(active_log_file)

    chatbot_answer = answer_log_question(
        question,
        dashboard_data,
    )

    return render_dashboard(
        dashboard_data,
        selected_incident_type=selected_incident_type,
        selected_severity=selected_severity,
        question=question.strip(),
        chatbot_answer=chatbot_answer,
    )


@app.route("/upload_log", methods=["POST"])
def upload_log():
    global active_log_file
    global active_log_name

    uploaded_file = request.files.get("log_file")

    (
        is_successful,
        upload_message,
        uploaded_path,
        uploaded_name,
    ) = save_uploaded_log(
        uploaded_file,
        PROJECT_ROOT,
        previous_file_path=active_log_file,
    )

    if not is_successful:
        return redirect(
            url_for(
                "index",
                status_message=upload_message,
                status_type="error",
            )
        )

    active_log_file = uploaded_path
    active_log_name = uploaded_name

    return redirect(
        url_for(
            "index",
            status_message=(
                f"{uploaded_name} yüklendi. "
                f"{upload_message}"
            ),
            status_type="success",
        )
    )


@app.route("/ai_explain", methods=["POST"])
def ai_explain():
    ip_address = request.form.get("ip", "")

    dashboard_data = analyze_logs(active_log_file)

    incident = None

    for row in dashboard_data:
        if row.get("ip") == ip_address:
            incident = row
            break

    if incident is None:
        explanation = (
            "Bu IP adresine ait bir analiz sonucu "
            "bulunamadı."
        )
    else:
        explanation = generate_incident_explanation(
            incident
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
    selected_severity = normalize_severity(
        request.args.get("severity", "")
    )

    dashboard_data = analyze_logs(active_log_file)

    filtered_data = filter_dashboard_data(
        dashboard_data,
        selected_incident_type,
        selected_severity,
    )

    return {
        "data": filtered_data,
        "severity_counts": calculate_severity_counts(
            dashboard_data
        ),
        "active_log_name": active_log_name,
    }


@app.route("/api/chat", methods=["POST"])
def api_chat():
    request_body = request.get_json(silent=True) or {}

    question = request_body.get("question", "")

    dashboard_data = analyze_logs(active_log_file)

    chatbot_answer = answer_log_question(
        question,
        dashboard_data,
    )

    return {"answer": chatbot_answer}


@app.route("/api/upload", methods=["POST"])
def api_upload():
    global active_log_file
    global active_log_name

    uploaded_file = request.files.get("log_file")

    (
        is_successful,
        upload_message,
        uploaded_path,
        uploaded_name,
    ) = save_uploaded_log(
        uploaded_file,
        PROJECT_ROOT,
        previous_file_path=active_log_file,
    )

    if not is_successful:
        return {"success": False, "message": upload_message}, 400

    active_log_file = uploaded_path
    active_log_name = uploaded_name

    return {
        "success": True,
        "message": upload_message,
        "active_log_name": active_log_name,
    }


if __name__ == "__main__":
    app.run(debug=True)
