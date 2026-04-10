"use client";

import { useMemo, useState } from "react";
import { useActiveView } from "@/components/layout/ActiveViewContext";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";

function safeJson(obj: unknown, space = 2): string {
  try {
    return JSON.stringify(obj, null, space);
  } catch {
    return String(obj);
  }
}

export function DebugView() {
  const { setActiveView } = useActiveView();
  const { state } = useLabStore();
  const snapshot = useMemo(() => state.snapshot ?? null, [state.snapshot]);
  const updates = state.updates;
  const lastSeed = state.lastSeedPayload;

  const [showRaw, setShowRaw] = useState(false);

  const hub = snapshot?.interaction_hub;
  const physics = snapshot?.physics_tensor as Record<string, unknown> | undefined;
  const meta = (physics?.meta as Record<string, unknown> | undefined) || {};
  const fv = snapshot?.final_verdict;
  const ld = snapshot?.logic_diff;
  const baseline = snapshot?.baseline_snapshot;

  const verdictPreview = fv?.body ? String(fv.body).slice(0, 800) : "";
  const entropy =
    typeof meta.global_entropy === "number" && Number.isFinite(meta.global_entropy)
      ? meta.global_entropy
      : null;

  const copyAll = async () => {
    if (!snapshot) return;
    try {
      await navigator.clipboard.writeText(safeJson(snapshot));
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="mx-auto min-h-dvh w-full max-w-4xl px-3 py-4 text-zinc-200">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-3">
        <div>
          <h1 className="text-base font-semibold">黑匣子（调试）</h1>
          <p className="mt-0.5 text-xs text-zinc-500">
            实验室会话摘要、最近合并键、因果更新流水与完整快照 JSON。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setShowRaw((v) => !v)}
            className="rounded border border-zinc-600 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 hover:bg-zinc-800"
          >
            {showRaw ? "收起原始 JSON" : "展开原始 JSON"}
          </button>
          <button
            type="button"
            disabled={!snapshot}
            onClick={() => void copyAll()}
            className="rounded border border-amber-600/50 bg-amber-950/40 px-3 py-1.5 text-xs text-amber-100 hover:bg-amber-950/60 disabled:cursor-not-allowed disabled:opacity-40"
          >
            复制快照 JSON
          </button>
          <button
            type="button"
            onClick={() => setActiveView("lab")}
            className="rounded border border-zinc-600 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 hover:bg-zinc-800"
          >
            回实验室
          </button>
        </div>
      </div>

      {!snapshot ? (
        <p className="text-sm text-zinc-500">暂无数据。请先在「实验室」完成排盘或推演。</p>
      ) : (
        <div className="space-y-4">
          <section className="grid gap-2 sm:grid-cols-2">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3 text-xs">
              <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">会话</p>
              <p className="mt-1 font-mono text-zinc-200">
                active_session_id: {String(snapshot.active_session_id ?? "—")}
              </p>
              <p className="mt-1 font-mono text-zinc-400">consultation: {hub?.consultation_id ?? "—"}</p>
              <p className="mt-1 text-zinc-500">
                快照时间: {snapshot.ts ? new Date(snapshot.ts).toLocaleString() : "—"}
              </p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3 text-xs">
              <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">健康 / 熵</p>
              <p className="mt-1 text-zinc-300">
                DB: {hub?.health?.db_ok === true ? "ok" : hub?.health?.db_ok === false ? "fail" : "—"} · LLM:{" "}
                {hub?.health?.llm_ok === true ? "ok" : hub?.health?.llm_ok === false ? "fail" : "—"}
              </p>
              <p className="mt-1 text-cyan-200/90">
                global_entropy: {entropy != null ? entropy.toFixed(4) : "—"}
              </p>
            </div>
          </section>

          <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3 text-xs">
            <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">logic_diff</p>
            <div className="mt-2 grid gap-1 font-mono text-[11px] text-zinc-400 sm:grid-cols-2">
              <span>abs_delta: {ld?.abs_delta != null ? String(ld.abs_delta) : "—"}</span>
              <span>entropy_delta: {ld?.entropy_delta != null ? String(ld.entropy_delta) : "—"}</span>
              <span>baseline_abs: {ld?.baseline_abs_loss_total != null ? String(ld.baseline_abs_loss_total) : "—"}</span>
              <span>current_abs: {ld?.current_abs_loss_total != null ? String(ld.current_abs_loss_total) : "—"}</span>
            </div>
          </section>

          <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3 text-xs">
            <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">基线锚点 baseline_snapshot</p>
            {!baseline ? (
              <p className="mt-2 text-zinc-500">尚未固化基线。</p>
            ) : (
              <div className="mt-2 space-y-1 font-mono text-[11px] text-zinc-400">
                <p>at: {baseline.at ? new Date(baseline.at).toLocaleString() : "—"}</p>
                <p>
                  abs_loss_total:{" "}
                  {typeof baseline.abs_loss_total === "number" ? baseline.abs_loss_total.toFixed(4) : "—"}
                </p>
                <p>
                  global_entropy:{" "}
                  {typeof baseline.global_entropy === "number" ? baseline.global_entropy.toFixed(4) : "—"}
                </p>
              </div>
            )}
          </section>

          {lastSeed ? (
            <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3 text-xs">
              <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">最后种子 The Seed</p>
              <pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap font-mono text-[11px] text-zinc-400">
                {safeJson(lastSeed)}
              </pre>
            </section>
          ) : null}

          <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3 text-xs">
            <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">终极判词摘要</p>
            {verdictPreview ? (
              <p className="mt-2 whitespace-pre-wrap text-[13px] leading-relaxed text-zinc-300">{verdictPreview}</p>
            ) : (
              <p className="mt-2 text-zinc-500">尚无 final_verdict.body。</p>
            )}
            {fv?.version_id ? (
              <p className="mt-2 font-mono text-[11px] text-zinc-500">version_id: {String(fv.version_id)}</p>
            ) : null}
          </section>

          <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3 text-xs">
            <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">交互中枢 interaction_hub</p>
            <div className="mt-2 space-y-1 text-[11px] text-zinc-400">
              <p>result_logs 条数: {Array.isArray(hub?.result_logs) ? hub.result_logs.length : 0}</p>
              <p>audit_items 条数: {Array.isArray(hub?.audit_items) ? hub.audit_items.length : 0}</p>
              <p>pending_cards 条数: {Array.isArray(hub?.pending_cards) ? hub.pending_cards.length : 0}</p>
            </div>
          </section>

          {updates.length > 0 ? (
            <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3 text-xs">
              <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">最近因果更新（最多 5 条）</p>
              <ul className="mt-2 space-y-2">
                {updates.map((u) => (
                  <li
                    key={u.id}
                    className="rounded border border-zinc-800/80 bg-zinc-950/60 px-2 py-1.5 font-mono text-[10px] text-zinc-400"
                  >
                    <span className="text-zinc-500">{new Date(u.ts).toLocaleTimeString()}</span> · keys:{" "}
                    {u.keys.join(", ") || "—"} · Δabs {u.abs_delta ?? "—"}
                    {u.overload ? " · overload" : ""}
                    {u.decisionMutation ? " · decision" : ""}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {showRaw ? (
            <section className="rounded-xl border border-amber-900/40 bg-zinc-950/80 p-3">
              <p className="text-[10px] font-medium uppercase tracking-wide text-amber-600/90">完整快照 JSON</p>
              <pre className="mt-2 max-h-[min(70dvh,720px)] overflow-auto text-[11px] leading-relaxed text-zinc-400">
                {safeJson(snapshot)}
              </pre>
            </section>
          ) : null}
        </div>
      )}
    </div>
  );
}
