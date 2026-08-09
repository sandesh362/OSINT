import type { ApiEnvelope } from "../../api/types";
export interface Location { country_name: string | null; city: string | null; latitude: number | null; longitude: number | null }
export interface ServiceBanner { port: number | null; transport: string | null; product: string | null; version: string | null; banner: string | null }
export interface HostData { ip: string; open_ports: number[]; services: ServiceBanner[]; org: string | null; isp: string | null; location: Location; os_guess: string | null; last_updated: string | null }
export interface SearchHost { ip: string; port: number | null; org: string | null; location: Location }
export interface SearchData { total: number; page: number; results: SearchHost[] }
export type HostResponse = ApiEnvelope<HostData>; export type SearchResponse = ApiEnvelope<SearchData>;
