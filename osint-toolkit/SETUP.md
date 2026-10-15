# Local setup and troubleshooting

Use Python 3.11+ and Node.js 20.11+.

## Backend

Open a PowerShell terminal:

```powershell
cd D:\OSINT\osint-toolkit\backend
# Only create the virtual environment if it does not exist:
if (!(Test-Path .venv)) { py -3.11 -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
# Preserve existing local settings and API keys:
if (!(Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8000
```

- API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/v1/health
- Visiting the backend root redirects to the API documentation.
- Settings always load from `backend/.env`, including when launched from another directory with `--app-dir`.
- Process environment variables take precedence over `.env` values.
- Restart the backend after changing its `.env` file.

`SHODAN_API_KEY` belongs only in `backend/.env` and is needed only for network reconnaissance. Domain checks and domain-only reports work without it. DNS and WHOIS timeouts are configurable with `DNS_TIMEOUT_SECONDS`, `DNS_LIFETIME_SECONDS`, and `WHOIS_TIMEOUT_SECONDS`. Breach checks use `XON_BASE_URL` and need no key.

HTML reports use Jinja2. PDF reports use ReportLab, installed with the backend requirements; GTK and WeasyPrint system libraries are not needed.

## Frontend

Open a second PowerShell terminal:

```powershell
cd D:\OSINT\osint-toolkit\frontend
npm ci
if (!(Test-Path .env)) { Copy-Item .env.example .env }
npm run dev
```

Frontend: http://127.0.0.1:5173

The frontend environment must contain:

```dotenv
VITE_API_BASE_URL=/api/v1
API_PROXY_TARGET=http://127.0.0.1:8000
```

Vite proxies `/api` requests to the backend during development and production-build preview. Restart the frontend after editing `.env`. The header checks the real health endpoint and shows whether the backend is connected. If you change the backend port, update `API_PROXY_TARGET` too.

Never put provider API keys in a `VITE_` variable: those variables are included in the browser bundle. Both local `.env` files are ignored by Git; `.env.example` files are safe setup templates.

Ports are fixed so Vite cannot silently start on an unexpected port. If a port is occupied, reuse the running project server or stop it with Ctrl+C in its terminal before starting another copy.

## Build and verify

```powershell
cd D:\OSINT\osint-toolkit\backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
cd ..\frontend
npm run build
npm run preview
```

The build runs `tsc --noEmit` and then Vite. `tsconfig.json` is the configuration to edit; `tsconfig.tsbuildinfo` is an ignored generated cache and is no longer created by the build command. Preview runs at http://127.0.0.1:4173 and still needs the backend. For hosted deployments, configure the web server to proxy `/api` or set `VITE_API_BASE_URL` to the deployed API URL and allow its frontend origin in backend CORS settings.

Backend tests mock external providers; they do not use your API key or spend provider quota. Live results still depend on provider availability, account permissions, and rate limits.

Logs for the background servers started during repair are in `osint-toolkit/logs/`. Normal terminal launches print logs to their respective terminals.
