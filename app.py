import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from flask import Flask, render_template, request
from log_analyzer import analyze_logs

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


if __name__ == "__main__":
    app.run(debug=True)
