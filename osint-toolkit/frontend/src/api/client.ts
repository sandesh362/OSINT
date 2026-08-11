import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL;
export const apiConfigurationError = !baseURL
  ? "Backend connection is not configured. Create frontend/.env with VITE_API_BASE_URL=http://localhost:8000/api/v1, then restart npm run dev."
  : null;

export const apiClient = axios.create({ baseURL: baseURL ?? "/api/v1", timeout: 30_000, headers: { Accept: "application/json" } });
