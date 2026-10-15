import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL?.trim() || "/api/v1";
export const apiConfigurationError = !baseURL.startsWith("/") && !/^https?:\/\//i.test(baseURL)
  ? "The API URL is invalid. Set VITE_API_BASE_URL to /api/v1 or a full HTTP(S) API URL, then restart the frontend."
  : null;

export const apiClient = axios.create({ baseURL, timeout: 60_000, headers: { Accept: "application/json" } });
