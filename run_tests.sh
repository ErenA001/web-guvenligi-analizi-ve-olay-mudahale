#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [[ ! -x venv/bin/python ]]; then
  echo "Sanal ortam bulunamadi. Once ./start.sh calistirin veya kurulum adimlarini uygulayin."
  exit 1
fi

source venv/bin/activate
python -W error::ResourceWarning -m unittest discover -s tests -v
