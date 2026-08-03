# Secure AI — Web Security Analysis & Incident Response

Secure AI is a React + Flask security operations dashboard for Apache/Nginx and educational access logs. It performs IP-based incident classification, severity scoring, secure log ingestion, and analysis-grounded AI assistance.

🇹🇷 Full documentation: [README_TR.md](README_TR.md)

![Secure AI dashboard](docs/screenshots/dashboard-desktop.png)

## Hardened release

- Session-based authentication with persistent secret management
- Per-session upload workspaces and active-log isolation
- SQLite-backed, multi-worker rate limiting for login, chat, and upload routes
- Shared SQLite file-signature analysis cache with TTL and automatic invalidation across Gunicorn workers
- Five-minute sliding-window brute-force and scanner detection
- Apache Common/Combined, ISO timestamp, and legacy simple-log parsers
- Atomic, validated `.log` / `.txt` uploads
- Security headers, safe redirects, hardened cookies, and restricted AI output
- Comprehensive standard-library test suite (**56/56 passing**)

The NVIDIA NIM base URL, model selection, and `NVIDIA_API_KEY` integration remain unchanged.

## Quick start

```bash
cd web-guvenligi-analizi-ve-olay-mudahale
./start.sh
```

Open `http://localhost:5001` and use the initial credentials printed by the startup script. When no password is configured, credentials are generated in `.runtime/initial_credentials.txt` and the plaintext file is deleted after the first successful login.

Preserve your existing `.env` when upgrading. A new installation can start from:

```bash
cp .env.example .env
```

## API

`/api/health` is public. The remaining endpoints require an authenticated browser session.

- `GET /api/health`
- `GET /api/dashboard`
- `POST /api/chat`
- `POST /api/upload`

Rate-limit responses use HTTP `429` and include `Retry-After`.

## Tests

```bash
./run_tests.sh
```

See [docs/reports/FINAL_TEST_REPORT.md](docs/reports/FINAL_TEST_REPORT.md) for the final verification summary.

## Frontend development

The delivery includes a ready production build. To rebuild from source, use Node.js 20.19+:

```bash
cd frontend
npm install
npm run lint
npm run build
```

## Developer

Developed by **@JhreX**  
Website: **jhrex.com.tr**  
WhatsApp: **+44 7441 900754**

> For educational and authorized security analysis only. Incident classifications are analytical indicators, not definitive proof of an attack.
