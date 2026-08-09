import { apiClient } from "../../api/client"; import type { BreachResponse } from "./types";
export const checkEmail = (value: string) => apiClient.get<BreachResponse>("/breach-check/email", { params: { value } }).then(r => r.data);
