import type { ApiEnvelope } from "../../api/types";
export type ProfileStatus = "found" | "not_found" | "uncertain";
export interface PlatformResult { platform: string; url: string; status: ProfileStatus; checked_at: string; profile_title: string | null; profile_description: string | null }
export interface UsernameLookupData { username: string; results: PlatformResult[] }
export type SocialResponse = ApiEnvelope<UsernameLookupData>;
