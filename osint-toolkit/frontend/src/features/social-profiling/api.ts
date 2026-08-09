import { apiClient } from "../../api/client"; import type { SocialResponse } from "./types";
export const lookupUsername = (value: string) => apiClient.get<SocialResponse>("/social-profiling/username", { params: { value } }).then(r => r.data);
