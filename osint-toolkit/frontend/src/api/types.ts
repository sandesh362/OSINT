export interface ResponseMeta { queried_at: string }
export interface ApiEnvelope<T> { success: boolean; data: T; meta: ResponseMeta }
export interface ApiError { success?: boolean; error?: string; detail?: unknown; retry_after?: number }
