const API_BASE_RAW = (process.env.NEXT_PUBLIC_QIAZHI_API ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");
const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "::1"]);
const resolveApiBase = () => {
  if (!API_BASE_RAW) return "";
  if (API_BASE_RAW === "/api") return "";
  if (API_BASE_RAW.startsWith("/")) return API_BASE_RAW;
  if (typeof window === "undefined") return API_BASE_RAW;
  try {
    const apiHost = new URL(API_BASE_RAW).hostname;
    const pageHost = window.location.hostname;
    if (LOOPBACK_HOSTS.has(apiHost) && !LOOPBACK_HOSTS.has(pageHost)) return "";
  } catch {
    return "";
  }
  return API_BASE_RAW;
};
export const API_BASE = resolveApiBase();
export const ADMIN_TOKEN = process.env.NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN ?? "";
export const ADMIN_HEADERS: Record<string, string> = ADMIN_TOKEN ? { "X-Admin-Token": ADMIN_TOKEN } : {};
export const SETTINGS_KEY = "qiazhi_admin_settings_v2";
