import { adminHeaders } from "@/features/stream-board/constants";

export type ApplyPhysicsSqlResult =
  | { ok: true; updated?: { param_key?: string; new_value?: unknown } }
  | { ok: false; error: string };

export async function applyPhysicsSqlPatch(apiBase: string, sqlPatch: string): Promise<ApplyPhysicsSqlResult> {
  if (!sqlPatch.trim()) {
    return { ok: false, error: "缺少可执行 SQL 补丁" };
  }

  const response = await fetch(`${apiBase}/api/admin/apply-physics-sql`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...adminHeaders },
    body: JSON.stringify({ sql_patch: sqlPatch, auto_refresh: true }),
  });
  const data = await response.json().catch(() => ({}));

  if (!response.ok || !data?.ok) {
    const maybeAuthHint = response.status === 401
      ? "（请检查 NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN / QIAZHI_ADMIN_TOKEN 配置）"
      : "";
    return { ok: false, error: `${String(data?.detail ?? "apply physics sql failed")}${maybeAuthHint}` };
  }

  return { ok: true, updated: data?.updated };
}
