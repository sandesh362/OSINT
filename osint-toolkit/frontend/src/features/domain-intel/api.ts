import { apiClient } from "../../api/client"; import type { DnsResponse, WhoisResponse } from "./types";
export const getWhois = (domain: string) => apiClient.get<WhoisResponse>("/domain-intel/whois", { params: { domain } }).then(r => r.data);
export const getDns = (domain: string) => apiClient.get<DnsResponse>("/domain-intel/dns", { params: { domain } }).then(r => r.data);
