#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3 bulunamadi. Python 3.11 veya daha yeni bir surum kurun."
  exit 1
fi

if [[ -d venv ]] && { [[ ! -x venv/bin/python ]] || ! venv/bin/python -c "import sys" >/dev/null 2>&1; }; then
  echo "Bu bilgisayarla uyumsuz eski sanal ortam kaldiriliyor..."
  rm -rf venv
fi

if [[ ! -x venv/bin/python ]]; then
  echo "Python sanal ortami olusturuluyor..."
  "$PYTHON_BIN" -m venv venv
fi

source venv/bin/activate

if ! python -c "import flask, dotenv, httpx, gunicorn" >/dev/null 2>&1; then
  echo "Python bagimliliklari kuruluyor..."
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo ".env dosyasi olusturuldu. Mevcut NVIDIA_API_KEY degerinizi buraya ekleyebilirsiniz."
fi

if [[ ! -f frontend/dist/index.html ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Frontend build eksik ve npm bulunamadi. Node.js 20.19+ kurun."
    exit 1
  fi
  echo "React production build hazirlaniyor..."
  (cd frontend && npm install && npm run build)
fi

python - <<'PY'
import os
from dotenv import load_dotenv
from services.auth_service import get_auth_configuration, get_or_create_secret_key

project_root = os.getcwd()
load_dotenv(os.path.join(project_root, ".env"))
get_auth_configuration(project_root)
get_or_create_secret_key(project_root)
PY

if [[ -f .runtime/initial_credentials.txt ]]; then
  echo
  echo "Ilk giris bilgileri:"
  sed -n '1,5p' .runtime/initial_credentials.txt
  echo "Bu dosya ilk basarili giristen sonra otomatik silinir."
  echo
fi

exec gunicorn -c gunicorn.conf.py app:app
