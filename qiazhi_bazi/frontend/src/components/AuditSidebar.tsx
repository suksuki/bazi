"use client";

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
  i18nCalls?: number;
  sessionId?: number | null;
  t?: (s: string) => string;
};

const ROLE_STYLE: Record<AuditRole, string> = {
  Arbiter: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  Core: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  Auditor: "bg-violet-500/15 text-violet-300 border-violet-500/30",
};

export function AuditSidebar({ items, dbOk, llmOk, i18nCalls = 0, sessionId = null, t = (s) => s }: Props) {
  const [openId, setOpenId] = useState<string | null>(null);
  return (
    <aside className="w-full rounded-2xl border border-zinc-800 bg-zinc-900/60 p-3 md:w-72 md:shrink-0">
      <h3 className="text-sm font-semibold">{t("Audit Sidebar")}</h3>
      <p className="mt-1 text-xs text-zinc-500">{t("权力三角：Arbiter / Core / Auditor")}</p>
      <div className="mt-3 flex gap-3 text-xs">
        <span className={`rounded-full px-2 py-1 ${dbOk ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"}`}>
          {t("DB(0.13)")} {dbOk ? "🟢" : "🔴"}
        </span>
        <span className={`rounded-full px-2 py-1 ${llmOk ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"}`}>
          {t("LLM(0.10)")} {llmOk ? "🟢" : "🔴"}
        </span>
      </div>
      <div className="mt-4 space-y-2">
        {items.length === 0 ? <p className="text-xs text-zinc-500">{t("等待交互步骤…")}</p> : null}
        {items.map((x) => (
          <article key={x.id} className="rounded-xl border border-zinc-800 bg-zinc-950 p-3">
            <button type="button" onClick={() => setOpenId((p) => (p === x.id ? null : x.id))} className="w-full text-left">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {x.step ? <span className="rounded-md bg-zinc-800 px-2 py-0.5 text-[11px] text-zinc-300">{t("Step")} {x.step}</span> : null}
                  <span className={`rounded-md border px-2 py-0.5 text-[11px] ${ROLE_STYLE[x.role]}`}>{x.role}</span>
                </div>
                <span className="text-[11px] text-zinc-500">{new Date(x.timestamp).toLocaleTimeString()}</span>
              </div>
              <p className="mt-1 text-xs text-zinc-300">{x.action}</p>
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
