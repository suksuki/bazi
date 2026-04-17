import { resolveQiazhiApiBase } from "@/lib/qiazhiApiBase";

export const API_BASE = resolveQiazhiApiBase();
export const ADMIN_TOKEN = process.env.NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN ?? "";
export const ADMIN_HEADERS: Record<string, string> = ADMIN_TOKEN ? { "X-Admin-Token": ADMIN_TOKEN } : {};
export const SETTINGS_KEY = "qiazhi_admin_settings_v2";
