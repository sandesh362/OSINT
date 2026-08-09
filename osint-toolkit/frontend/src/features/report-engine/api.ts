import { apiClient } from "../../api/client"; import type { HtmlReportResponse, PreviewResponse, ReportRequest } from "./types";
export const generateReport = (request: ReportRequest) => apiClient.post<HtmlReportResponse>("/report-engine/generate", request).then(r => r.data);
export const generatePdf = (request: ReportRequest) => apiClient.post("/report-engine/generate", request, { responseType: "blob" }).then(r => r.data as Blob);
export const previewReport = (reportId: string) => apiClient.get<PreviewResponse>(`/report-engine/preview/${reportId}`).then(r => r.data);
