import type { ApiEnvelope } from "../../api/types";
export interface WhoisData { registrar: string | null; creation_date: string | null; expiration_date: string | null; name_servers: string[]; registrant_org: string | null }
export interface DnsData { a: string[]; aaaa: string[]; mx: string[]; ns: string[]; txt: string[] }
export type WhoisResponse = ApiEnvelope<WhoisData>; export type DnsResponse = ApiEnvelope<DnsData>;
