import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from flask import Flask, render_template
from log_analyzer import analyze_logs

app = Flask(__name__)

log_file = "logs/sample_access.log"


@app.route("/")
def index():
    dashboard_data = analyze_logs(log_file)
    return render_template("index.html", data=dashboard_data)


if __name__ == "__main__":
    app.run(debug=True)
