import { useCallback, useState } from "react";
import axios from "axios";
import type { ApiError } from "../../api/types";

export function friendlyError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "Something unexpected happened. Please try again.";
  const status = error.response?.status;
  const body = error.response?.data as ApiError | undefined;
  if (status === 422) return typeof body?.detail === "string" ? body.detail : "Please correct the input and try again.";
  if (status === 404) return "No data found for this query.";
  if (status === 429) return `Rate limited. Try again${body?.retry_after ? ` in ${body.retry_after} seconds` : " shortly"}.`;
  if (status === 500 || status === 503) return "The service is temporarily unavailable. Please try again later.";
  return typeof body?.detail === "string" ? body.detail : "The request could not be completed.";
}

export function useApiCall<T, Args extends unknown[]>() {
  const [data, setData] = useState<T | null>(null); const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(false);
  const run = useCallback(async (call: (...args: Args) => Promise<T>, ...args: Args) => { setLoading(true); setError(null); try { const result = await call(...args); setData(result); return result; } catch (err) { setError(friendlyError(err)); return null; } finally { setLoading(false); } }, []);
  return { data, error, loading, run, clear: () => { setData(null); setError(null); } };
}
