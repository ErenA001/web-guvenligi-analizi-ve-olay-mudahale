import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIRECTORY = os.path.join(PROJECT_ROOT, "scripts")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SCRIPTS_DIRECTORY not in sys.path:
    sys.path.insert(0, SCRIPTS_DIRECTORY)
