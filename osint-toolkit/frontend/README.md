# OSINT Toolkit frontend

The dashboard is a React 18, TypeScript, and Vite single-page application.
It calls the FastAPI backend separately; start the backend before using a panel.

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` in `.env` to the backend API-version base URL, normally
`http://localhost:8000/api/v1`. Run `npm run build` for a production build.

The browser must be permitted to call the backend origin (configure CORS in a
deployment if the frontend and API are hosted on different origins). No API key
is placed in the frontend; provider credentials remain on the backend.
