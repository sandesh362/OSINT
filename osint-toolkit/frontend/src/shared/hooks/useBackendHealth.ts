import { useEffect, useState } from "react";
import { apiClient, apiConfigurationError } from "../../api/client";

export function useBackendHealth() {
  const [status, setStatus] = useState<"checking" | "connected" | "offline">("checking");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("checking");
    const check = async () => {
      try {
        if (apiConfigurationError) throw new Error("Invalid API configuration");
        const response = await apiClient.get<{ status: string }>("/health", {
          timeout: 5_000,
          signal: controller.signal,
        });
        if (!controller.signal.aborted) setStatus(response.data.status === "ok" ? "connected" : "offline");
      } catch {
        if (!controller.signal.aborted) setStatus("offline");
      }
    };
    void check();
    const timer = window.setInterval(() => { void check(); }, 30_000);
    return () => { controller.abort(); window.clearInterval(timer); };
  }, [attempt]);

  return { status, retry: () => setAttempt(value => value + 1) };
}
