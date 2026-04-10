"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import { StateSentinel } from "@/app/(shell)/debug/components/StateSentinel";

type Snapshot = {
  ts?: number;
  physics_tensor?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  audit_summary?: unknown;
  interaction_hub?: {
    consultation_id?: string | null;
    health?: { db_ok?: boolean; llm_ok?: boolean };
    i18n_calls?: unknown;
    audit_items?: Array<{ id?: string; step?: string; role?: string; action?: string; timestamp?: string }>;
    result_logs?: string[];
    pending_cards?: Array<{ id?: string; title?: string; card_type?: string }>;
    auditor_briefing?: {
      alignment_score?: unknown;
      structured_hit?: unknown;
      repair_mode?: unknown;
      top_anomaly?: unknown;
      causal_reasoning?: unknown;
      tuning_suggestions?: unknown;
      logic_proposal?: { param_key?: string; suggested_value?: unknown; reason?: unknown; expected_impact?: unknown };
      auto_joined_decision_box?: boolean;
    };
  };
};

export default function DebugPage() {
  const { state } = useLabStore();
  const snapshot = useMemo(() => (state.snapshot || null) as Snapshot | null, [state.snapshot]);
  const [tensorOpen, setTensorOpen] = useState(false);

  const tensor = snapshot?.physics_tensor;
  const deityAxes = (tensor?.deity_energy_axes || {}) as Record<string, { absolute_energy?: number; relative_percentage?: number }>;
  const deityEntries = Object.entries(deityAxes).filter(([, v]) => v && typeof v === "object");
  const maxAbs =
    deityEntries.length > 0
      ? Math.max(0.0001, ...deityEntries.map(([, v]) => Number(v.absolute_energy ?? 0)))
      : 1;
  const meta = (tensor?.meta || {}) as { global_entropy?: number; global_entropy_metrics?: Record<string, unknown> };
  const entropy = typeof meta.global_entropy === "number" ? meta.global_entropy : null;
  const metrics = meta.global_entropy_metrics || {};
  const pipeline = (tensor?.l1_atomic_pipeline || {}) as { steps?: unknown[] };
  const steps = Array.isArray(pipeline.steps) ? pipeline.steps : [];
  const hub = snapshot?.interaction_hub;
  const briefing = hub?.auditor_briefing;
  const hubAuditItems = Array.isArray(hub?.audit_items) ? hub.audit_items : [];
  const hubLogs = Array.isArray(hub?.result_logs) ? hub.result_logs : [];
  const hubCards = Array.isArray(hub?.pending_cards) ? hub.pending_cards : [];
  const enabledPlugins = Array.isArray((tensor?.meta as { enabled_plugins?: unknown } | undefined)?.enabled_plugins)
    ? (((tensor?.meta as { enabled_plugins?: unknown } | undefined)?.enabled_plugins || []) as unknown[]).map((item) => String(item))
    : [];
  const pluginOutputs = (tensor?.plugin_outputs && typeof tensor.plugin_outputs === "object")
    ? (tensor.plugin_outputs as Record<string, {
      ok?: unknown;
      latency_ms?: unknown;
      evidence?: unknown;
      confidence_score?: unknown;
      error?: unknown;
    }>)
    : {};
  const pluginRows = Object.entries(pluginOutputs).map(([pluginId, output]) => {
    const evidence = Array.isArray(output?.evidence) ? output.evidence.map((item) => String(item)).slice(0, 3) : [];
    const latencyMs = typeof output?.latency_ms === "number" ? output.latency_ms : null;
    const confidence = typeof output?.confidence_score === "number" ? output.confidence_score : null;
    const ok = output?.ok === false ? false : true;
    return {
      pluginId,
      ok,
      latencyMs,
      confidence,
      evidence,
      error: output?.error ? String(output.error) : "",
    };
  });

  return (
    <main className="mx-auto min-h-dvh w-full max-w-[900px] px-3 py-4">
      <header className="mb-4 border-b border-zinc-800 pb-3">
        <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">Black Box · L1</p>
        <h1 className="text-lg font-semibold text-zinc-100">黑匣子</h1>
        <p className="mt-1 text-xs text-zinc-500">审计流、物理张量快照与全局熵（最近一次主实验室排盘）。</p>
        <Link href="/" className="mt-2 inline-block text-xs text-amber-400/90 underline-offset-2 hover:underline">
          ← 返回实验室
        </Link>
      </header>

      {!snapshot ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-sm text-zinc-400">
          暂无快照。请先在「实验室」完成一次排盘，系统将自动写入本页所需数据。
        </div>
      ) : (
        <div className="space-y-4">
          <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
            <h2 className="text-sm font-medium text-zinc-200">Entropy Pulse</h2>
            <p className="mt-1 text-[11px] text-zinc-500">
              全局熵 {entropy != null ? entropy.toFixed(3) : "—"} · 快照时间{" "}
              {snapshot.ts ? new Date(snapshot.ts).toLocaleString() : "—"}
            </p>
            {entropy != null ? (
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-zinc-800">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-amber-400 to-rose-500 transition-all"
                  style={{ width: `${Math.round(entropy * 100)}%` }}
                />
              </div>
            ) : null}
            {Object.keys(metrics).length > 0 ? (
              <pre className="mt-2 max-h-32 overflow-auto rounded border border-zinc-800 bg-zinc-950 p-2 text-[10px] text-zinc-400">
                {JSON.stringify(metrics, null, 2)}
              </pre>
            ) : null}
          </section>

          {deityEntries.length > 0 ? (
            <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
              <h2 className="text-sm font-medium text-zinc-200">十神 Abs 分布（相对峰值）</h2>
              <p className="mt-1 text-[11px] text-zinc-500">来自 deity_energy_axes.absolute_energy，便于与终判/拓扑对照。</p>
              <ul className="mt-3 space-y-2">
                {deityEntries
                  .map(([name, v]) => ({ name, abs: Number(v.absolute_energy ?? 0) }))
                  .sort((a, b) => b.abs - a.abs)
                  .map(({ name, abs }) => (
                    <li key={name} className="flex items-center gap-2 text-[11px]">
                      <span className="w-10 shrink-0 font-mono text-zinc-400">{name}</span>
                      <div className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-zinc-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-sky-600/90 to-violet-500/90"
                          style={{ width: `${Math.min(100, Math.round((abs / maxAbs) * 100))}%` }}
                        />
                      </div>
                      <span className="w-14 shrink-0 text-right font-mono text-zinc-300">{abs.toFixed(2)}</span>
                    </li>
                  ))}
              </ul>
            </section>
          ) : null}

          <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
            <h2 className="text-sm font-medium text-zinc-200">L1 Atomic Trace</h2>
            <ul className="mt-2 space-y-2">
              {steps.length === 0 ? (
                <li className="text-xs text-zinc-500">无流水线步骤记录。</li>
              ) : (
                steps.slice(0, 80).map((step, idx) => (
                  <li
                    key={`${idx}-${JSON.stringify(step).slice(0, 40)}`}
                    className="rounded border border-zinc-800/80 bg-zinc-950/80 px-2 py-1.5 font-mono text-[10px] text-zinc-400"
                  >
                    {JSON.stringify(step)}
                  </li>
                ))
              )}
            </ul>
          </section>

          <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
            <h2 className="text-sm font-medium text-zinc-200">三方信息交互（原侧栏迁移）</h2>
            <p className="mt-1 text-[11px] text-zinc-500">会话主键、系统健康、审计动作与待执行冲突卡。</p>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/80 p-2 text-[11px]">
                <p className="mb-1 text-zinc-500">System Health</p>
                <p className="text-zinc-300">Session: {hub?.consultation_id || "—"}</p>
                <p className="text-zinc-300">DB: {hub?.health?.db_ok ? "OK" : "DOWN"}</p>
                <p className="text-zinc-300">LLM: {hub?.health?.llm_ok ? "OK" : "DOWN"}</p>
                <p className="mt-1 text-zinc-400">i18n calls: {hub?.i18n_calls != null ? String(hub.i18n_calls) : "—"}</p>
              </div>
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/80 p-2 text-[11px]">
                <p className="mb-1 text-zinc-500">Audit Actions</p>
                <ul className="space-y-1">
                  {hubAuditItems.length === 0 ? (
                    <li className="text-zinc-500">暂无</li>
                  ) : (
                    hubAuditItems.slice(0, 10).map((item, idx) => (
                      <li key={`${item.id || item.action || idx}`} className="text-zinc-300">
                        [{item.role || "—"}] {item.step || item.action || "unknown"}
                      </li>
                    ))
                  )}
                </ul>
              </div>
              <div className="rounded-lg border border-zinc-800 bg-zinc-950/80 p-2 text-[11px]">
                <p className="mb-1 text-zinc-500">Pending Cards</p>
                <ul className="space-y-1">
                  {hubCards.length === 0 ? (
                    <li className="text-zinc-500">暂无</li>
                  ) : (
                    hubCards.slice(0, 12).map((card, idx) => (
                      <li key={`${card.id || card.title || idx}`} className="text-zinc-300">
                        [{card.card_type || "conflict"}] {card.title || card.id || "untitled"}
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </div>
            {hubLogs.length > 0 ? (
              <pre className="mt-3 max-h-40 overflow-auto rounded border border-zinc-800 bg-zinc-950 p-2 text-[10px] text-zinc-400">
                {hubLogs.join("\n")}
              </pre>
            ) : null}
            <div className="mt-3 rounded-lg border border-cyan-700/35 bg-cyan-950/10 p-2">
              <p className="text-[11px] text-cyan-200">Plugin Trace</p>
              <p className="mt-1 text-[10px] text-zinc-500">
                Enabled: {enabledPlugins.length > 0 ? enabledPlugins.join(", ") : "—"}
              </p>
              {pluginRows.length === 0 ? (
                <p className="mt-2 text-[11px] text-zinc-500">暂无插件执行回执（请先完成一次排盘）。</p>
              ) : (
                <ul className="mt-2 space-y-2">
                  {pluginRows.map((row) => (
                    <li key={row.pluginId} className="rounded border border-zinc-800/80 bg-zinc-950/70 p-2 text-[11px]">
                      <p className="text-zinc-200">
                        {row.pluginId}
                        <span className={`ml-2 ${row.ok ? "text-emerald-300" : "text-rose-300"}`}>{row.ok ? "OK" : "ERROR"}</span>
                      </p>
                      <p className="mt-1 text-zinc-400">
                        latency={row.latencyMs != null ? `${row.latencyMs.toFixed(2)}ms` : "—"} · confidence=
                        {row.confidence != null ? row.confidence.toFixed(2) : "—"}
                      </p>
                      {row.evidence.length > 0 ? (
                        <ul className="mt-1 list-disc pl-4 text-zinc-400">
                          {row.evidence.map((item, idx) => <li key={`${row.pluginId}-${idx}`}>{item}</li>)}
                        </ul>
                      ) : null}
                      {row.error ? <p className="mt-1 text-rose-300">error: {row.error}</p> : null}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </section>

          <section className="rounded-xl border border-violet-700/35 bg-violet-950/15 p-3">
            <h2 className="text-sm font-medium text-violet-200">审计员简报（迁移）</h2>
            {!briefing ? (
              <p className="mt-1 text-xs text-zinc-500">暂无审计员简报。请在实验室完成一次排盘审计后查看。</p>
            ) : (
              <div className="mt-2 space-y-2 text-[11px] text-zinc-300">
                <p>Alignment: {String(briefing.alignment_score ?? "—")} · Structured: {String(briefing.structured_hit ?? "—")} · Mode: {String(briefing.repair_mode ?? "—")}</p>
                <p>Top Anomaly: {String(briefing.top_anomaly ?? "—")}</p>
                <p className="text-zinc-400">{String(briefing.causal_reasoning ?? "—")}</p>
                {Array.isArray(briefing.tuning_suggestions) && briefing.tuning_suggestions.length > 0 ? (
                  <ul className="list-disc pl-4 text-zinc-400">
                    {briefing.tuning_suggestions.slice(0, 6).map((item, idx) => <li key={`${idx}-${String(item)}`}>{String(item)}</li>)}
                  </ul>
                ) : null}
                {briefing.logic_proposal ? (
                  <div className="rounded border border-violet-600/30 bg-zinc-950/70 p-2">
                    <p>Proposal: {String(briefing.logic_proposal.param_key ?? "—")} → {String(briefing.logic_proposal.suggested_value ?? "—")}</p>
                    <p className="text-zinc-400">{String(briefing.logic_proposal.reason ?? briefing.logic_proposal.expected_impact ?? "—")}</p>
                    <p className="mt-1 text-emerald-300">已自动加入 Decision Box：{briefing.auto_joined_decision_box ? "是" : "否"}</p>
                  </div>
                ) : null}
              </div>
            )}
          </section>

          <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
            <button
              type="button"
              onClick={() => setTensorOpen((v) => !v)}
              className="flex w-full items-center justify-between text-sm font-medium text-zinc-200"
            >
              Tensor Inspector
              <span className="text-xs text-zinc-500">{tensorOpen ? "收起" : "展开"}</span>
            </button>
            {tensorOpen ? (
              <pre className="mt-2 max-h-[min(70vh,520px)] overflow-auto rounded border border-zinc-800 bg-zinc-950 p-2 text-[10px] text-zinc-400">
                {JSON.stringify(tensor, null, 2)}
              </pre>
            ) : null}
          </section>
          <StateSentinel />
        </div>
      )}
    </main>
  );
}
