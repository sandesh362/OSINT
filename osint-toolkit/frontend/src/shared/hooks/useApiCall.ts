import { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import type { ApiError } from "../../api/types";

export function friendlyError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "Something unexpected happened. Please try again.";
  if (error.code === "ECONNABORTED" || error.code === "ETIMEDOUT") return "The lookup timed out. Please try again or check the provider's availability.";
  if (!error.response) return "Cannot reach the backend. Check the connection status and make sure the backend is running.";
  const status = error.response?.status;
  const body = error.response?.data as ApiError | undefined;
  const message = body?.error?.message;
  if (status === 422) return message ?? "Please correct the input and try again.";
  if (status === 403) return message ?? "This account is not permitted to perform that lookup.";
  if (status === 404) return "No data found for this query.";
  if (status === 429) return `Rate limited. Try again${body?.error?.retry_after ? ` in ${body.error.retry_after} seconds` : " shortly"}.`;
  if (status === 504) return message ?? "The provider took too long to respond. Please try again.";
  if (status === 500 || status === 502 || status === 503) return message ?? "The service is temporarily unavailable. Please try again later.";
  return message ?? "The request could not be completed.";
}

export function useApiCall<T, Args extends unknown[]>() {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const latest = useRef(0);
  useEffect(() => () => { latest.current += 1; }, []);
  const run = useCallback(async (call: (...args: Args) => Promise<T>, ...args: Args) => {
    const requestId = ++latest.current;
    setLoading(true);
    setData(null);
    setError(null);
    try {
      const result = await call(...args);
      if (requestId !== latest.current) return null;
      setData(result);
      return result;
    } catch (err) {
      // PDF endpoints return JSON errors as blobs because the request expects a file.
      if (axios.isAxiosError(err) && err.response?.data instanceof Blob) {
        try { err.response.data = JSON.parse(await err.response.data.text()); } catch { /* Fall back to the HTTP status. */ }
      }
      if (requestId === latest.current) setError(friendlyError(err));
      return null;
    } finally {
      if (requestId === latest.current) setLoading(false);
    }
  }, []);
  const clear = useCallback(() => { latest.current += 1; setData(null); setError(null); setLoading(false); }, []);
  return { data, error, loading, run, clear };
}
