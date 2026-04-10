"use client";

import { useMemo, useState } from "react";
import { useActiveView } from "@/components/layout/ActiveViewContext";
import { skillIdForConflictPoint } from "@/features/decision-inbox/skillInference";
import { VerdictCertificate } from "@/features/stream-board/components/VerdictCertificate";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import type { ConflictPoint } from "@/types/bazi";

function safeJson(obj: unknown, space = 2): string {
  try {
    return JSON.stringify(obj, null, space);
  } catch {
    return String(obj);
  }
}

const mirrorBtnClass =
  "flex items-center gap-1.5 px-2 py-1 bg-zinc-800/50 hover:bg-zinc-700/50 rounded-md border border-zinc-700/50 transition-colors text-xs text-zinc-200";

export function DebugView() {
  const { setActiveView } = useActiveView();
  const { state, injectSnapshotText } = useLabStore();
  const snapshot = useMemo(() => state.snapshot ?? null, [state.snapshot]);
  const finalizationReport = state.finalizationReport;
  const metaFinal = (snapshot?.metadata as Record<string, unknown> | undefined)?.finalization as
    | { hash?: string; committed_at?: number }
    | undefined;
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

  const causalTraceRows = useMemo(() => {
    if (!snapshot) return [];
    const baziMeta = (snapshot.metadata || {}) as { conflict_matrix?: { points?: ConflictPoint[] } };
    const points = baziMeta.conflict_matrix?.points ?? [];
    const decisionIds = new Set(
      Array.isArray(snapshot.decision_selection_ids)
        ? snapshot.decision_selection_ids.map((x) => String(x))
        : [],
    );
    const pending = Array.isArray(hub?.pending_cards) ? hub.pending_cards : [];
    const baseAbs = ld?.baseline_abs_loss_total;
    const curAbs = ld?.current_abs_loss_total;
    let absStr = "—";
    if (typeof baseAbs === "number" && typeof curAbs === "number" && Math.abs(baseAbs) > 1e-9) {
      absStr = `${(((curAbs - baseAbs) / baseAbs) * 100).toFixed(1)}%`;
    } else if (typeof ld?.abs_delta === "number" && typeof baseAbs === "number" && Math.abs(baseAbs) > 1e-9) {
      absStr = `${((ld.abs_delta / baseAbs) * 100).toFixed(1)}%`;
    }

    const rows: string[] = [];
    points.forEach((p, i) => {
      const detail = String(p.detail || "—");
      const sid = skillIdForConflictPoint(p);
      const pendingMatch = pending.find((c) => {
        const title = String((c as { title?: string }).title || "");
        return title && (detail.includes(title.slice(0, 4)) || title.includes(detail.slice(0, 4)));
      }) as { id?: string } | undefined;
      const did = pendingMatch?.id ? String(pendingMatch.id) : `physics:${i}`;
      const checked =
        did.startsWith("physics:")
          ? [...decisionIds].some((id) => id.startsWith("llm-observe"))
          : decisionIds.has(did);
      rows.push(
        `[物理匹配: ${detail}] → [Skill: ${sid}] → [Decision ID: ${did}] → [用户状态: ${checked ? "已勾选" : "未勾选"}] → [Abs 修正值: ${absStr}]`,
      );
    });

    const pierceSem = meta.mangpai_pierce_semantics;
    if (Array.isArray(pierceSem)) {
      pierceSem.forEach((raw, j) => {
        const item = raw as { detail?: string; semantic_intensity?: number; skill_id?: string };
        const si = Number(item.semantic_intensity ?? 0);
        rows.push(
          `[物理匹配: 穿局 ${String(item.detail || "—")} · semantic_intensity=${Number.isFinite(si) ? si.toFixed(4) : "—"}] → [Skill: ${String(item.skill_id || "mp_pierce_01")}] → [Decision ID: pierce:${j}] → [用户状态: 见 Inbox 与 llm-observe 勾选] → [Abs 修正值: ${absStr}]`,
        );
      });
    }

    if (rows.length === 0) {
      rows.push(
        `［尚无 L1 冲突点或穿局语义摘要；排盘后将在此串联物理 → Skill → Decision → Abs］ → [Abs 修正值: ${absStr}]`,
      );
    }
    return rows;
  }, [snapshot, hub, ld, meta.mangpai_pierce_semantics]);

  const hubCausalTraceLines = useMemo(() => {
    const baseAbs = ld?.baseline_abs_loss_total;
    const curAbs = ld?.current_abs_loss_total;
    let impact = "—";
    if (typeof baseAbs === "number" && typeof curAbs === "number" && Math.abs(baseAbs) > 1e-9) {
      impact = `${(((curAbs - baseAbs) / baseAbs) * 100).toFixed(1)}%`;
    } else if (typeof ld?.abs_delta === "number" && typeof baseAbs === "number" && Math.abs(baseAbs) > 1e-9) {
      impact = `${((ld.abs_delta / baseAbs) * 100).toFixed(1)}%`;
    }

    const extractDecisionId = (text: string): string => {
      const s = String(text || "");
      const m = s.match(/\b(llm-observe-\d+|auditor-proposal-[a-zA-Z0-9-]+)\b/);
      if (m) return m[1];
      const m2 = s.match(/ID[:\s]+([a-zA-Z0-9_-]+)/i);
      return m2 ? m2[1] : "—";
    };

    const skillFromHubBlob = (text: string): string => {
      const t = String(text || "");
      if (t.includes("mp_pierce_01") || t.includes("穿局") || (t.includes("穿") && t.includes("MANGPAI"))) return "mp_pierce_01";
      if (t.includes("mp_tomb_01") || t.includes("墓库闭锁")) return "mp_tomb_01";
      if (t.includes("mp_host_guest") || t.includes("宾主主权")) return "mp_host_guest_01";
      if (t.includes("[MANGPAI_CHIP]")) return "mp_pierce_01";
      return "mp_semantic_layer";
    };

    const rows: string[] = [];
    const auditItems = Array.isArray(hub?.audit_items) ? hub.audit_items : [];
    auditItems.forEach((item) => {
      const action = String(item?.action ?? "");
      const step = String(item?.step ?? "");
      const blob = `${step} ${action}`;
      const skill = skillFromHubBlob(blob);
      const decision = extractDecisionId(blob);
      const resolved = /决策|decision|confirm|勾选|resolved|决议|同步因果/i.test(blob);
      const actionLabel = resolved ? "Decision Resolved" : `Audit (${step || "trace"})`;
      rows.push(
        `[Triggered]: Skill ID (${skill}) -> [Action]: ${actionLabel} (${decision !== "—" ? `ID_${decision}` : "ID_—"}) -> [Impact]: Abs Modified (${impact})`,
      );
    });

    const logs = Array.isArray(hub?.result_logs) ? hub.result_logs.map(String) : [];
    logs.forEach((log) => {
      if (
        log.includes("[MANGPAI_CHIP]")
        || log.includes("[FINAL_DECISION_ISSUED]")
        || log.includes("语义裁决")
        || log.includes("决策")
        || log.includes("PLUGIN_INTERVENE")
      ) {
        const skill = skillFromHubBlob(log);
        const decision = extractDecisionId(log);
        rows.push(
          `[Triggered]: Skill ID (${skill}) -> [Action]: Hub log -> (${decision !== "—" ? `ID_${decision}` : "ID_—"}) -> [Impact]: Abs Modified (${impact})`,
        );
      }
    });

    if (rows.length === 0) {
      rows.push(
        `[Triggered]: Skill ID (—) -> [Action]: (empty hub audit) -> [Decision]: ID_— -> [Impact]: Abs Modified (${impact})`,
      );
    }
    return rows.slice(-24);
  }, [hub?.audit_items, hub?.result_logs, ld]);

  const copyAll = async () => {
    if (!snapshot) return;
    try {
      await navigator.clipboard.writeText(safeJson(snapshot));
    } catch {
      /* ignore */
    }
  };

  const pasteMirror = async () => {
    try {
      const text = await navigator.clipboard.readText();
      injectSnapshotText(text);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="mx-auto min-h-dvh w-full max-w-4xl px-3 py-4 text-zinc-200">
      {state.isFinalized && finalizationReport?.hash ? (
        <VerdictCertificate
          hash={finalizationReport.hash}
          committedAt={finalizationReport.committedAt}
          logicDiff={ld}
          effectiveSkillIds={
            finalizationReport.effectiveSkillIds ??
            (snapshot?.metadata?.verdict_effective_skill_ids as string[] | undefined)
          }
        />
      ) : null}
      {!state.isFinalized && (finalizationReport || metaFinal?.hash) ? (
        <div className="mb-3 rounded-xl border border-violet-500/40 bg-violet-950/30 p-3 text-xs text-violet-100">
          <p className="text-[10px] font-medium uppercase tracking-wide text-violet-300">终审不可篡改摘要</p>
          <p className="mt-1 font-mono text-[11px] break-all">
            SHA-256: {String(finalizationReport?.hash ?? metaFinal?.hash ?? "—")}
          </p>
          <p className="mt-1 text-zinc-400">
            签发时间:{" "}
            {finalizationReport?.committedAt
              ? new Date(finalizationReport.committedAt).toLocaleString()
              : metaFinal?.committed_at
                ? new Date(Number(metaFinal.committed_at)).toLocaleString()
                : "—"}
          </p>
        </div>
      ) : null}

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
            className={`${mirrorBtnClass} disabled:cursor-not-allowed disabled:opacity-40`}
          >
            <svg className="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              <rect x="9" y="9" width="13" height="13" rx="2" />
              <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
            </svg>
            复制快照 JSON
          </button>
          <button
            type="button"
            disabled={state.isFinalized}
            onClick={() => void pasteMirror()}
            className={`${mirrorBtnClass} disabled:cursor-not-allowed disabled:opacity-40`}
          >
            <svg className="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" />
              <rect x="8" y="2" width="8" height="4" rx="1" />
              <path d="M9 12h6M9 16h6" />
            </svg>
            文本黏贴
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
            {Array.isArray(hub?.audit_items) && hub.audit_items.length > 0 ? (
              <ul className="mt-3 max-h-48 space-y-2 overflow-auto border-t border-zinc-800/80 pt-2">
                {hub.audit_items.map((item, idx) => (
                  <li key={String(item?.id ?? idx)} className="rounded border border-zinc-800/60 bg-zinc-950/50 px-2 py-1.5">
                    <p className="font-mono text-[10px] text-amber-200/90">
                      {String(item?.role ?? "—")} · {String(item?.step ?? "—")}
                    </p>
                    <p className="mt-0.5 text-[11px] leading-snug text-zinc-300">{String(item?.action ?? "—")}</p>
                    {item?.timestamp ? (
                      <p className="mt-0.5 font-mono text-[10px] text-zinc-600">{String(item.timestamp)}</p>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-[11px] text-zinc-600">暂无 audit_items（若刚排盘，请确认已写入会话快照）。</p>
            )}
            {Array.isArray(hub?.result_logs) && hub.result_logs.length > 0 ? (
              <div className="mt-3 max-h-36 overflow-auto border-t border-zinc-800/80 pt-2">
                <p className="mb-1 text-[10px] uppercase tracking-wide text-zinc-500">result_logs（尾部）</p>
                <ul className="space-y-1 font-mono text-[10px] text-zinc-500">
                  {hub.result_logs.slice(-12).map((line, i) => (
                    <li key={`${i}-${String(line).slice(0, 24)}`} className="whitespace-pre-wrap break-all">
                      {String(line)}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>

          <section className="rounded-xl border border-cyan-800/40 bg-cyan-950/25 p-3 text-xs">
            <p className="text-[10px] font-medium uppercase tracking-wide text-cyan-300/90">因果追踪（Causal Trace）</p>
            <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">
              物理匹配 → Skill 注册项 → Decision 锚点 → 勾选状态 → 相对基线的 Abs 比例（与 logic_diff 对齐）。
            </p>
            <ul className="mt-3 max-h-64 space-y-2 overflow-auto border-t border-cyan-900/40 pt-2">
              {causalTraceRows.map((line, idx) => (
                <li
                  key={`${idx}-${line.slice(0, 24)}`}
                  className="rounded border border-cyan-900/50 bg-zinc-950/70 px-2 py-1.5 font-mono text-[10px] leading-snug text-cyan-100/90"
                >
                  {line}
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-xl border border-fuchsia-900/45 bg-fuchsia-950/20 p-3 text-xs">
            <p className="text-[10px] font-medium uppercase tracking-wide text-fuchsia-300/90">CausalTrace（interaction_hub）</p>
            <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">
              从 audit_items 与 result_logs 抽取：Triggered → Action → Decision 锚点 → Abs 影响（与 logic_diff 同源百分比）。
            </p>
            <ul className="mt-3 max-h-72 space-y-2 overflow-auto border-t border-fuchsia-900/40 pt-2">
              {hubCausalTraceLines.map((line, idx) => (
                <li
                  key={`hub-ct-${idx}-${line.slice(0, 20)}`}
                  className="rounded border border-fuchsia-900/50 bg-zinc-950/75 px-2 py-1.5 font-mono text-[10px] leading-snug text-fuchsia-100/90"
                >
                  {line}
                </li>
              ))}
            </ul>
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
