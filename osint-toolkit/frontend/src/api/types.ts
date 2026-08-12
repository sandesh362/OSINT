export interface ResponseMeta { queried_at: string }
export interface ApiEnvelope<T> { success: true; data: T; meta: ResponseMeta; error: null }
export interface ApiError { success: false; data: null; meta: ResponseMeta; error: { code: string; message: string; retry_after?: number } }
