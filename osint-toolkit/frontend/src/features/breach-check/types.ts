import type { ApiEnvelope } from "../../api/types";
export interface BreachSummary { name: string; breach_date: string | null; data_classes: string[]; reference_url: string }
export interface BreachCheckData { value: string; breached: boolean; breaches: BreachSummary[] }
export type BreachResponse = ApiEnvelope<BreachCheckData>;
