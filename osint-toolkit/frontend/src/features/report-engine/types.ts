import type { ApiEnvelope } from "../../api/types";
export type ModuleName = "domain_intel" | "network_recon" | "social_profiling" | "breach_check";
export type ReportFormat = "html" | "pdf";
export interface ReportRequest { domain?: string; email?: string; username?: string; ip?: string; modules: ModuleName[]; format: ReportFormat }
export interface HtmlReportData { report_id: string; html: string }
export type HtmlReportResponse = ApiEnvelope<HtmlReportData>;
export interface PreviewData { report_id: string; html: string }
export type PreviewResponse = ApiEnvelope<PreviewData>;
