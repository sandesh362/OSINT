import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL;
if (!baseURL) throw new Error("VITE_API_BASE_URL must be set before starting the frontend.");

export const apiClient = axios.create({ baseURL, timeout: 30_000, headers: { Accept: "application/json" } });
