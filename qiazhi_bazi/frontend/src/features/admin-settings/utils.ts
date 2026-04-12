import type { PersistedAdminSettings } from "./types";

export function makePgUrl(args: {
  host: string;
  port: string;
  database: string;
  user: string;
  password: string;
  sslMode: string;
}) {
  const pwd = encodeURIComponent(args.password);
  const ssl = args.sslMode ? `?sslmode=${args.sslMode}` : "";
  return `postgresql://${args.user}:${pwd}@${args.host}:${args.port}/${args.database}${ssl}`;
}

export function buildPersistedAdminSettings(input: PersistedAdminSettings): PersistedAdminSettings {
  return { ...input };
}

/**
 * LLM 服务根地址（无 /v1）：空输入时可用 NEXT_PUBLIC_QIAZHI_OLLAMA_ORIGIN；
 * 仅主机名时可配 NEXT_PUBLIC_QIAZHI_OLLAMA_DEFAULT_PORT 补端口，否则不猜端口。
 */
export function normalizeOllamaHostInput(raw: string): string {
  const originFallback = (process.env.NEXT_PUBLIC_QIAZHI_OLLAMA_ORIGIN ?? "").trim().replace(/\/$/, "");
  const implicitPort = (process.env.NEXT_PUBLIC_QIAZHI_OLLAMA_DEFAULT_PORT ?? "").trim();
  const s0 = raw.trim();
  if (!s0) return originFallback;
  let s = s0;
  if (!/^https?:\/\//i.test(s)) {
    s = `http://${s}`;
  }
  s = s.replace(/\/$/, "");
  try {
    const u = new URL(s);
    const host = u.hostname;
    if (!host) return originFallback;
    if (u.protocol === "http:" && (!u.port || u.port === "80")) {
      if (implicitPort) return `http://${host}:${implicitPort}`;
      return `http://${host}`;
    }
    if (u.protocol === "https:" && (!u.port || u.port === "443")) {
      if (implicitPort) return `https://${host}:${implicitPort}`;
      return `https://${host}`;
    }
    return u.origin;
  } catch {
    if (implicitPort) return `http://${s0.replace(/^\/+/, "")}:${implicitPort}`;
    return `http://${s0.replace(/^\/+/, "")}`;
  }
}
