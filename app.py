import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from flask import Flask, render_template, request
from log_analyzer import analyze_logs
from services.ai_explainer import generate_incident_explanation

app = Flask(__name__)

log_file = "logs/sample_access.log"

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


@app.route("/")
def index():
    dashboard_data = analyze_logs(log_file)

    selected_incident_type = request.args.get("incident_type", "")
    selected_severity = request.args.get("severity", "")

    if selected_incident_type not in VALID_INCIDENT_TYPES:
        selected_incident_type = ""

    if selected_severity not in VALID_SEVERITIES:
        selected_severity = ""

    filtered_data = dashboard_data

    if selected_incident_type:
        filtered_data = [row for row in filtered_data if row["incident_type"] == selected_incident_type]

    if selected_severity:
        filtered_data = [row for row in filtered_data if row["severity"] == selected_severity]

    return render_template(
        "index.html",
        data=filtered_data,
        incident_types=VALID_INCIDENT_TYPES,
        severities=VALID_SEVERITIES,
        selected_incident_type=selected_incident_type,
        selected_severity=selected_severity,
    )


@app.route("/ai_explain", methods=["POST"])
def ai_explain():
    ip = request.form.get("ip", "")

    dashboard_data = analyze_logs(log_file)

    incident = None
    for row in dashboard_data:
        if row["ip"] == ip:
            incident = row
            break

    if incident is None:
        explanation = "Bu IP adresine ait bir analiz sonucu bulunamadi."
    else:
        explanation = generate_incident_explanation(incident)

    return render_template(
        "ai_result.html",
        incident=incident,
        explanation=explanation,
    )


if __name__ == "__main__":
    app.run(debug=True)
