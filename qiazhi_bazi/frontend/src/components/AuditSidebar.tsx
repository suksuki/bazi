"use client";

import type { ReactNode } from "react";
import { useState } from "react";

export type AuditRole = "Arbiter" | "Core" | "Auditor";

export type AuditItem = {
  id: string;
  step?: string;
  role: AuditRole;
  action: string;
  timestamp: string;
  payload?: unknown;
};

type Props = {
  items: AuditItem[];
  dbOk: boolean;
  llmOk: boolean;
  llmModelName?: string;
  i18nCalls?: number;
  sessionId?: number | null;
  t?: (s: string) => string;
  topSlot?: ReactNode;
  middleSlot?: ReactNode;
};

const ROLE_STYLE: Record<AuditRole, string> = {
  Arbiter: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  Core: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  Auditor: "bg-violet-500/15 text-violet-300 border-violet-500/30",
};

export function AuditSidebar({
  items,
  dbOk,
  llmOk,
  llmModelName = "LLM",
  i18nCalls = 0,
  sessionId = null,
  t = (s) => s,
  topSlot,
  middleSlot,
}: Props) {
  const [openId, setOpenId] = useState<string | null>(null);
  return (
    <aside className="w-full rounded-2xl border border-zinc-800 bg-zinc-900/70 p-3 md:w-[420px] md:shrink-0">
      <h3 className="text-sm font-semibold">{t("Audit Sidebar")}</h3>
      <p className="mt-1 text-xs text-zinc-500">{t("权力三角：Arbiter / Core / Auditor")}</p>
      <div className="mt-3 flex gap-3 text-xs">
        <span className={`rounded-full px-2 py-1 ${dbOk ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"}`}>
          {t("DB(本地)")} {dbOk ? "🟢" : "🔴"}
        </span>
        <span className={`rounded-full px-2 py-1 ${llmOk ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"}`}>
          {`LLM(${llmModelName || "N/A"})`} {llmOk ? "🟢" : "🔴"}
        </span>
      </div>
      {topSlot ? <div className="mt-3 rounded-xl border border-zinc-800/90 bg-zinc-950/40 p-2">{topSlot}</div> : null}
      {middleSlot ? <div className="mt-3 rounded-xl border border-zinc-800/90 bg-zinc-950/40 p-2">{middleSlot}</div> : null}
      <div className="mt-4 space-y-2">
        {items.length === 0 ? <p className="text-xs text-zinc-500">{t("等待交互步骤…")}</p> : null}
        {items.map((x) => (
          <article key={x.id} className="rounded-xl border border-zinc-800 bg-zinc-950 p-3">
            <button type="button" onClick={() => setOpenId((p) => (p === x.id ? null : x.id))} className="w-full text-left">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {x.step ? <span className="rounded-md bg-zinc-800 px-2 py-0.5 text-[11px] text-zinc-300">{t("Step")} {x.step}</span> : null}
                  <span className={`rounded-md border px-2 py-0.5 text-[11px] ${ROLE_STYLE[x.role]}`}>{x.role}</span>
                  {x.role === "Auditor" && typeof x.payload === "object" && x.payload !== null && "model_name" in x.payload ? (
                    <span className="rounded-md border border-zinc-700 bg-zinc-900 px-2 py-0.5 text-[10px] text-zinc-400">
                      {String((x.payload as { model_name?: string }).model_name || "LLM")}
                    </span>
                  ) : null}
                </div>
                <span className="text-[11px] text-zinc-500">{new Date(x.timestamp).toLocaleTimeString()}</span>
              </div>
              <p className="mt-1 text-xs text-zinc-300">{x.action}</p>
              {typeof x.payload === "object" && x.payload !== null && "param_version_id" in x.payload ? (
                <p className="mt-1 text-[10px] text-zinc-500">
                  param: {String((x.payload as { param_version_id?: string }).param_version_id || "--")}
                </p>
              ) : null}
              {typeof x.payload === "object" && x.payload !== null && "llm_elapsed_ms" in x.payload ? (
                <p className="mt-1 text-[10px] text-zinc-500">
                  llm: {String((x.payload as { llm_elapsed_ms?: number }).llm_elapsed_ms || 0)}ms
                  {` / ~${String((x.payload as { llm_approx_tokens?: number }).llm_approx_tokens || 0)} tok`}
                </p>
              ) : null}
              {typeof x.payload === "object" && x.payload !== null && "snapshot_summary" in x.payload ? (
                <p className="mt-1 text-[10px] text-zinc-500">
                  {String((x.payload as { snapshot_summary?: string }).snapshot_summary || "")}
                </p>
              ) : null}
              {x.role === "Core"
                && typeof x.payload === "object"
                && x.payload !== null
                && ("local_decay_applied" in x.payload || "self_deity_only" in x.payload) ? (
                  <p className="mt-1 text-[10px] text-zinc-500">
                    Local Decay Applied: {String((x.payload as { local_decay_applied?: boolean }).local_decay_applied ?? false)}
                    {" | "}
                    Self_Deity_Only: {String((x.payload as { self_deity_only?: boolean }).self_deity_only ?? false)}
                  </p>
                ) : null}
              {x.role === "Core"
                && typeof x.payload === "object"
                && x.payload !== null
                && "hard_route_logs" in x.payload
                && Array.isArray((x.payload as { hard_route_logs?: unknown[] }).hard_route_logs)
                && ((x.payload as { hard_route_logs?: unknown[] }).hard_route_logs || []).length > 0 ? (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {((x.payload as { hard_route_logs?: unknown[] }).hard_route_logs || []).slice(0, 3).map((log, idx) => {
                      const text = String(log || "");
                      const m = text.match(/Param '([^']+)'.*=>\\s*([0-9.]+)/);
                      return (
                        <span
                          key={`${x.id}-hr-${idx}`}
                          className="rounded-md border border-sky-500/40 bg-sky-500/15 px-2 py-0.5 text-[10px] text-sky-200"
                          title={text}
                        >
                          强制覆盖: {m ? `${m[1]}=${m[2]}` : text}
                        </span>
                      );
                    })}
                  </div>
                ) : null}
            </button>
            {openId === x.id ? (
              <pre className="mt-2 max-h-48 overflow-auto rounded-lg border border-zinc-800 bg-zinc-900 p-2 text-[11px] text-zinc-400">
                {JSON.stringify(x.payload ?? {}, null, 2)}
              </pre>
            ) : null}
          </article>
        ))}
      </div>
      <p className="mt-3 text-[10px] text-zinc-500">
        {`[Sess: #${sessionId ?? "--"}] [DB: ${dbOk ? "OK" : "FAIL"}] [I18N Calls: ${i18nCalls}${i18nCalls === 0 ? " (Cached)" : ""}]`}
      </p>
    </aside>
  );
}
