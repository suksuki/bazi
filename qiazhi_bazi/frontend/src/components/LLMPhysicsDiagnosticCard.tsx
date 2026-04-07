"use client";
import { useState } from "react";

type Props = {
  loading?: boolean;
  error?: string;
  data?: {
    top_anomaly?: string;
    causal_reasoning?: string;
    tuning_suggestions?: string[];
    sql_patch?: string;
    refresh_hint?: string;
  } | null;
  onRefreshPhysics?: () => Promise<void> | void;
  onApplySqlPatch?: (sqlPatch: string) => Promise<void> | void;
};

export function LLMPhysicsDiagnosticCard({
  loading = false,
  error,
  data,
  onRefreshPhysics,
  onApplySqlPatch,
}: Props) {
  const [applyMsg, setApplyMsg] = useState("");

  async function copyText(text: string) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // ignore clipboard failures
    }
  }

  async function handleApplySql() {
    const sql = data?.sql_patch || "";
    if (!sql) return;
    const ok = window.confirm(`确认执行以下 SQL 建议？\n\n${sql}`);
    if (!ok) return;
    try {
      await onApplySqlPatch?.(sql);
      setApplyMsg("SQL 建议已执行。");
    } catch (e) {
      setApplyMsg(`执行失败：${e instanceof Error ? e.message : String(e)}`);
    }
  }

  if (!loading && !error && !data) return null;

  return (
    <section className="rounded-2xl border border-rose-500/30 bg-zinc-900/60 p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-rose-300">LLM 物理诊断卡</h3>
        {loading ? <span className="text-xs text-zinc-400">挑刺中...</span> : null}
      </div>

      {error ? <p className="mt-2 text-xs text-rose-300">{error}</p> : null}

      {data ? (
        <div className="mt-3 space-y-3 text-xs">
          <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-2">
            <div className="mb-1 text-[11px] text-rose-300">红色预警位 / top_anomaly</div>
            <p className="text-zinc-100">{data.top_anomaly || "暂无异常"}</p>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-2">
            <div className="mb-1 text-[11px] text-zinc-400">因果解释</div>
            <p className="text-zinc-300">{data.causal_reasoning || "-"}</p>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-2">
            <div className="mb-2 text-[11px] text-zinc-400">参数调优建议</div>
            <div className="space-y-2">
              {(data.tuning_suggestions || []).map((x, idx) => (
                <div key={`${idx}-${x}`} className="flex items-start justify-between gap-2">
                  <code className="block flex-1 rounded bg-zinc-900 px-2 py-1 text-[11px] text-amber-300">{x}</code>
                  <button
                    type="button"
                    onClick={() => copyText(x)}
                    className="rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-[11px] text-zinc-300"
                  >
                    复制
                  </button>
                </div>
              ))}
            </div>
          </div>

          {data.sql_patch ? (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => copyText(data.sql_patch || "")}
                className="rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-300"
              >
                复制 SQL 脚本
              </button>
              <button
                type="button"
                onClick={() => void handleApplySql()}
                className="rounded border border-emerald-500/40 bg-emerald-500/10 px-2 py-1 text-[11px] text-emerald-300"
              >
                一键应用 SQL 建议
              </button>
              <button
                type="button"
                onClick={() => void onRefreshPhysics?.()}
                className="rounded border border-sky-500/40 bg-sky-500/10 px-2 py-1 text-[11px] text-sky-300"
              >
                刷新物理参数缓存
              </button>
            </div>
          ) : null}
          {applyMsg ? <p className="text-[11px] text-zinc-400">{applyMsg}</p> : null}
        </div>
      ) : null}
    </section>
  );
}
