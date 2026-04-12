import type { PersistedAdminSettings } from "./types";

/** 从 `DATABASE_URL` 拆向导字段（仅客户端、不入库）。密码含 % 编码时会解码。 */
export function parsePostgresUrlForWizard(dbUrl: string): {
  pgHost: string;
  pgPort: string;
  pgDatabase: string;
  pgUser: string;
  pgPassword: string;
  pgSslMode: string;
} | null {
  const trimmed = dbUrl.trim();
  if (!trimmed) return null;
  try {
    const u = new URL(trimmed);
    const proto = u.protocol.replace(":", "").toLowerCase();
    if (proto !== "postgresql" && proto !== "postgres") return null;
    const pgHost = u.hostname || "";
    if (!pgHost) return null;
    const pgPort = u.port || "5432";
    const pgDatabase = decodeURIComponent((u.pathname || "").replace(/^\//, "").split("/")[0] || "");
    const dec = (s: string) => {
      try {
        return decodeURIComponent(s);
      } catch {
        return s;
      }
    };
    const pgUser = dec(u.username || "");
    const pgPassword = dec(u.password || "");
    const pgSslMode = u.searchParams.get("sslmode") || "disable";
    return { pgHost, pgPort, pgDatabase, pgUser, pgPassword, pgSslMode };
  } catch {
    return null;
  }
}

/** 文档里的示例连接串（未替换占位符）；不应拿去请求后端做真实连通性检测。 */
export function looksLikeTutorialDatabaseUrl(raw: string): boolean {
  const trimmed = raw.trim();
  if (!trimmed) return false;
  try {
    const u = new URL(trimmed);
    const proto = u.protocol.replace(":", "").toLowerCase();
    if (proto !== "postgresql" && proto !== "postgres") return false;
    if (u.hostname.toLowerCase() !== "host") return false;
    return u.username === "user" && u.password === "password";
  } catch {
    return false;
  }
}

export type PgWizardFields = {
  host: string;
  port: string;
  database: string;
  user: string;
  password: string;
  sslMode: string;
};

export function makePgUrl(args: PgWizardFields) {
  const pwd = encodeURIComponent(args.password);
  const ssl = args.sslMode ? `?sslmode=${args.sslMode}` : "";
  return `postgresql://${args.user}:${pwd}@${args.host}:${args.port}/${args.database}${ssl}`;
}

/**
 * Test DB / Init 请求体用：避免向导里已填账号密码但 Database URL 输入框仍是旧串或未点「生成」导致连错库。
 * - `dbUrl` 为空时用向导拼串；
 * - 若 URL 与向导中的**用户名或密码**不一致（常见：向导已改正拼写，URL 框仍为 `qizzhi_admin` 等旧串），以向导为准；
 * - 若 URL 已同时含用户名与密码且与向导一致，则以输入框为准（便于只粘贴连接串；向导留空即可）。
 */
export function resolveDatabaseUrlForTest(dbUrl: string, wizard: PgWizardFields): string {
  const trimmed = dbUrl.trim();
  const fromWizard = makePgUrl(wizard);
  if (!trimmed) return fromWizard;
  const parsed = parsePostgresUrlForWizard(trimmed);
  if (!parsed) {
    if (wizard.user.trim() || wizard.password.trim()) return fromWizard;
    return trimmed;
  }
  const urlHasFullUserinfo = Boolean(parsed.pgUser.trim() && parsed.pgPassword.trim());
  const wUser = wizard.user.trim();
  const wPass = wizard.password;
  const userMismatch = Boolean(wUser && parsed.pgUser.trim() !== wUser);
  const passMismatch = Boolean(wPass && parsed.pgPassword !== wPass);
  if (userMismatch || passMismatch) return fromWizard;
  if (urlHasFullUserinfo) return trimmed;
  if (wizard.user.trim() || wizard.password.trim()) return fromWizard;
  return trimmed;
}

export function buildPersistedAdminSettings(input: PersistedAdminSettings): PersistedAdminSettings {
  return { ...input };
}

/**
 * 本地 Ollama 默认明文 HTTP；若误填 `https://127.0.0.1:11434` 会导致 TLS 握手失败，
 * 基础设施页表现为「拉不到模型 / 保存后回读失败」。仅纠正环回 + 常见 Ollama 端口。
 */
export function coerceLoopbackOllamaHttpsToHttp(raw: string): string {
  const t = raw.trim();
  if (!/^https:\/\//i.test(t)) return raw;
  try {
    const u = new URL(t.replace(/\/$/, ""));
    if (u.protocol !== "https:") return raw;
    const h = u.hostname.toLowerCase();
    if (h !== "127.0.0.1" && h !== "localhost" && h !== "::1") return raw;
    const port = u.port;
    if (port === "11434" || port === "11435") {
      return `http://${u.hostname}:${port}`;
    }
    return raw;
  } catch {
    return raw;
  }
}

/**
 * LLM 服务根地址（无 /v1）：空输入时可用 NEXT_PUBLIC_QIAZHI_OLLAMA_ORIGIN；
 * 仅主机名时可配 NEXT_PUBLIC_QIAZHI_OLLAMA_DEFAULT_PORT 补端口，否则不猜端口。
 */
export function normalizeOllamaHostInput(raw: string): string {
  const originFallback = (process.env.NEXT_PUBLIC_QIAZHI_OLLAMA_ORIGIN ?? "").trim().replace(/\/$/, "");
  const implicitPort = (process.env.NEXT_PUBLIC_QIAZHI_OLLAMA_DEFAULT_PORT ?? "").trim();
  const s0 = coerceLoopbackOllamaHttpsToHttp(raw).trim();
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
