"use client";

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
  /** @deprecated 保留签名以兼容旧调用；SQL 直改已废弃 */
  onApplySqlPatch?: (sqlPatch: string) => Promise<void> | void;
};

export function LLMPhysicsDiagnosticCard({
  loading = false,
  error,
  data,
  onRefreshPhysics,
  onApplySqlPatch: _onApplySqlPatch,
}: Props) {
  async function copyText(text: string) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // ignore clipboard failures
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
            <div className="space-y-2 rounded-lg border border-zinc-700 bg-zinc-950/80 p-2">
              <p className="text-[11px] leading-relaxed text-zinc-400">
                全局 <code className="text-zinc-300">UPDATE physics_interaction_params</code>{" "}
                路径已废弃。请将 LLM 建议转为 Decision Inbox 的「个人能量补丁」卡片，勾选后执行裁决以写入{" "}
                <code className="text-zinc-300">manual_energy_patch</code>（仅影响当前命盘展示）。
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => copyText(data.sql_patch || "")}
                  className="rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-300"
                >
                  复制 SQL（审计留档）
                </button>
                <button
                  type="button"
                  disabled
                  title="已废弃：请使用 Inbox 个人能量补丁"
                  className="cursor-not-allowed rounded border border-zinc-700 bg-zinc-800/60 px-2 py-1 text-[11px] text-zinc-500"
                >
                  一键应用 SQL（已禁用）
                </button>
                <button
                  type="button"
                  onClick={() => void onRefreshPhysics?.()}
                  className="rounded border border-sky-500/40 bg-sky-500/10 px-2 py-1 text-[11px] text-sky-300"
                >
                  刷新物理参数缓存
                </button>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
