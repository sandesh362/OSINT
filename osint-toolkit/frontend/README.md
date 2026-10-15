# OSINT Toolkit frontend

The dashboard is a React 18, TypeScript, and Vite single-page application.
It calls the FastAPI backend separately; start the backend before using a panel.

```powershell
cd frontend
npm ci
if (!(Test-Path .env)) { Copy-Item .env.example .env }
npm run dev
```

Set `VITE_API_BASE_URL=/api/v1` and `API_PROXY_TARGET=http://127.0.0.1:8000`
in `.env`. Vite forwards API requests to the backend in development and preview.
Open http://127.0.0.1:5173 and check the backend status in the header.
Restart the frontend after changing `.env`.

Run `npm run typecheck` to check TypeScript, `npm run build` for a production
build, and `npm run preview` to preview that build on port 4173. The backend
must keep running for API requests. `tsconfig.tsbuildinfo` is a generated cache,
not a configuration file; the build no longer generates it.

The browser must be permitted to call the backend origin (configure CORS in a
deployment if the frontend and API are hosted on different origins). No API key
is placed in the frontend; provider credentials remain on the backend.
