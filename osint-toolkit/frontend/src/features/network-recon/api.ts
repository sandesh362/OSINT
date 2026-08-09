import { apiClient } from "../../api/client"; import type { HostResponse, SearchResponse } from "./types";
export const getHost = (ip: string) => apiClient.get<HostResponse>("/network-recon/host", { params: { ip } }).then(r => r.data);
export const searchHosts = (query: string, page: number) => apiClient.get<SearchResponse>("/network-recon/search", { params: { query, page } }).then(r => r.data);
