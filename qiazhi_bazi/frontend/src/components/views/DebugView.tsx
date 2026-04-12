"use client";

import { useEffect, useMemo, useState } from "react";
import {
  buildPluginInteractionRollup,
  DecisionTimeline,
  NarrativeProvenancePanel,
  PluginCollisionHub,
  SemanticAccordion,
  StateMonitor,
  type PluginInteractionHit,
} from "@/features/decision-cockpit";
import { AuditChamberPanel } from "@/features/admin/AuditChamberPanel";
import { VerdictCertificate } from "@/features/stream-board/components/VerdictCertificate";
import { sysCorePhysicsPayload } from "@/features/stream-board/sysCorePhysics";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import { buildCausalSovereigntySlice } from "@/features/stream-board/utils/causalSovereigntyFromSnapshot";
import type { LabLlmRoundSnapshot, LabSnapshot } from "@/features/stream-board/stores/LabSessionContext";
import type { TimelineSnapshot } from "@/types/bazi";

const DEBUG_PLUGIN_FOCUS_KEY = "qiazhi_debug_plugin_focus";

const DEBUG_TABS = [
  { id: "verdict", labelZh: "终局与断言" },
  { id: "bazi_meta", labelZh: "八字元数据" },
  { id: "physics", labelZh: "物理与博弈" },
  { id: "observe", labelZh: "时序与观测" },
  { id: "tools", labelZh: "血统与工具" },
] as const;

/** BaziMetadata 核心键；其余归入「扩展字段」便于审核对照 */
const META_CORE_KEYS = new Set([
  "version",
  "pillars",
  "conflict_matrix",
  "flow_state",
  "notes",
  "temporal_context",
]);

type DebugTabId = (typeof DEBUG_TABS)[number]["id"];

function safeJson(obj: unknown, space = 2): string {
  try {
    return JSON.stringify(obj, null, space);
  } catch {
    return String(obj);
  }
}

const LLM_ROLE_ZH: Record<string, string> = {
  system: "系统",
  user: "用户",
  assistant: "助手",
  tool: "工具",
};

function normalizeLlmMessages(raw: unknown): Array<{ role: string; content: string }> {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((m) => m && typeof m === "object" && !Array.isArray(m))
    .map((m) => {
      const r = m as Record<string, unknown>;
      return { role: String(r.role ?? ""), content: String(r.content ?? "") };
    });
}

/** 将 OpenAI 风格 messages 拼成可读的「发给模型的提示词」全文（按角色分段） */
function formatLlmMessagesAsPrompt(messages: Array<{ role: string; content: string }> | undefined): string {
  if (!messages?.length) return "";
  const parts = messages
    .map((m) => {
      const label = LLM_ROLE_ZH[m.role] ?? (m.role || "消息");
      const body = (m.content || "").trim();
      if (!body) return "";
      return `【${label}】\n${body}`;
    })
    .filter(Boolean);
  return parts.join("\n\n────────\n\n");
}

function DebugSubTabBar(props: { active: DebugTabId; onChange: (id: DebugTabId) => void }) {
  const { active, onChange } = props;
  return (
    <div
      role="tablist"
      aria-label="黑匣子分区"
      className="flex w-full max-w-5xl flex-wrap rounded-2xl border border-zinc-800 bg-zinc-950 p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:flex-nowrap"
    >
      {DEBUG_TABS.map((tab) => {
        const isActive = active === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            className={`relative flex min-h-[2.5rem] min-w-[4.5rem] flex-1 items-center justify-center rounded-xl px-1 py-2 text-center text-[10px] font-medium transition-colors sm:min-w-0 sm:px-2 sm:text-xs ${
              isActive
                ? "bg-cyan-900/75 text-cyan-50 shadow-[0_1px_8px_rgba(6,78,95,0.45)]"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
            onClick={() => onChange(tab.id)}
          >
            {tab.labelZh}
          </button>
        );
      })}
    </div>
  );
}

/** 模型交互：展示「发给模型的提示词」+ 返回；原始 JSON 折叠 */
function LlmRoundCompact(props: {
  title: string;
  subtitle: string;
  round: LabLlmRoundSnapshot | null | undefined;
  /** 无 messages 时回退（如首观仅顶层 llm_prompt） */
  promptFallback?: string;
}) {
  const { title, subtitle, round, promptFallback } = props;
  const messagesNorm = normalizeLlmMessages(round?.messages);
  const promptFormatted = formatLlmMessagesAsPrompt(messagesNorm) || (typeof promptFallback === "string" ? promptFallback.trim() : "");
  const responseBody = (round?.response_text || "").trim();
  const hasMeta = !!(round?.meta && typeof round.meta === "object" && Object.keys(round.meta).length > 0);
  const hasRound = !!round;

  if (!hasRound || (!promptFormatted && !responseBody && !hasMeta)) {
    return (
      <SemanticAccordion title={title} subtitle={subtitle} defaultOpen={false}>
        <p className="text-xs text-zinc-500">暂无记录。</p>
      </SemanticAccordion>
    );
  }

  return (
    <SemanticAccordion title={title} subtitle={subtitle} defaultOpen={false}>
      <div className="space-y-3 text-xs">
        {promptFormatted ? (
          <div>
            <p className="text-[10px] uppercase tracking-wide text-sky-400/90">发给模型的提示词（messages）</p>
            <div className="mt-1 max-h-[min(42dvh,380px)] overflow-auto whitespace-pre-wrap rounded-lg border border-sky-900/40 bg-sky-950/20 p-3 text-[11px] leading-relaxed text-sky-50/95">
              {promptFormatted}
            </div>
            {!messagesNorm.length && promptFallback ? (
              <p className="mt-1 text-[10px] text-zinc-600">（messages 未返回，已用快照顶层 llm_prompt 回退）</p>
            ) : null}
          </div>
        ) : (
          <p className="text-[10px] text-zinc-600">本轮无可用 messages 文本（可展开下方「原始 messages JSON」核对）。</p>
        )}
        <div>
          <p className="text-[10px] uppercase tracking-wide text-zinc-500">模型返回（主张摘录）</p>
          <div className="mt-1 max-h-[min(36dvh,320px)] overflow-auto whitespace-pre-wrap rounded-lg border border-emerald-900/35 bg-zinc-950/80 p-3 text-[11px] leading-relaxed text-emerald-100/90">
            {responseBody || "—"}
          </div>
        </div>
        <details className="rounded border border-zinc-800/80 bg-zinc-950/50">
          <summary className="cursor-pointer px-2 py-1.5 text-[10px] text-zinc-500">原始 messages JSON / 遥测（技术复核）</summary>
          <div className="space-y-2 border-t border-zinc-800/80 p-2">
            {hasMeta ? (
              <pre className="max-h-28 overflow-auto rounded bg-zinc-950 p-2 font-mono text-[9px] text-zinc-500">{safeJson(round!.meta)}</pre>
            ) : null}
            <pre className="max-h-40 overflow-auto rounded bg-zinc-950 p-2 font-mono text-[9px] text-zinc-400">{safeJson(round?.messages ?? [])}</pre>
          </div>
        </details>
      </div>
    </SemanticAccordion>
  );
}

function hitRemarkChips(hit: PluginInteractionHit): string[] {
  const chips: string[] = [];
  if (hit.traceFirstStep !== null) chips.push(`L0 流水线·步 #${hit.traceFirstStep + 1} 首见`);
  if (hit.hasPluginOutput) chips.push("physics_tensor.plugin_outputs");
  if (hit.lifecycleHitCount > 0) chips.push(`Inbox 生命周期 ×${hit.lifecycleHitCount}`);
  if (hit.hasMatchScore) chips.push("MatchScore");
  return chips;
}

/** L0 physics_trace + L1–L4 Inbox：命中插件总表 + 三个默认可收起小节 */
function LayerAuditTrails({ physics }: { physics: Record<string, unknown> | undefined }) {
  const meta = (physics?.meta as Record<string, unknown> | undefined) || {};
  const inbox = meta.decision_inbox_v1 as Record<string, unknown> | undefined;
  const po = (physics?.plugin_outputs as Record<string, unknown> | undefined) || {};
  const corePl = sysCorePhysicsPayload(po);
  const trace = Array.isArray(corePl?.physics_trace) ? (corePl.physics_trace as Record<string, unknown>[]) : [];
  const scores = Array.isArray(inbox?.match_scores) ? (inbox.match_scores as Record<string, unknown>[]) : [];
  const lifecycles = Array.isArray(inbox?.lifecycle_traces) ? (inbox.lifecycle_traces as Record<string, unknown>[]) : [];
  const pluginHits = useMemo(() => buildPluginInteractionRollup(physics), [physics]);

  return (
    <div className="space-y-3">
      <SemanticAccordion
        title="交互命中插件一览"
        subtitle="按 L0 流水线先后，并并入张量输出与 Inbox 中的全部插件 ID（去重）"
        defaultOpen={false}
      >
        {pluginHits.length === 0 ? (
          <p className="text-[11px] text-zinc-600">
            暂无插件级命中记录（需完整 analyze-seed，且 plugin_outputs / 流水线非空）。
          </p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-zinc-800/90 bg-black/25">
            <table className="w-full min-w-[320px] border-collapse text-left text-[11px]">
              <thead>
                <tr className="border-b border-zinc-800 bg-zinc-900/80 text-[10px] uppercase tracking-wide text-zinc-500">
                  <th className="px-2 py-2 font-medium">#</th>
                  <th className="px-2 py-2 font-medium">名称</th>
                  <th className="hidden px-2 py-2 font-medium sm:table-cell">技术 ID</th>
                  <th className="px-2 py-2 font-medium">来源摘要</th>
                </tr>
              </thead>
              <tbody>
                {pluginHits.map((hit, i) => (
                  <tr key={hit.id} className="border-b border-zinc-800/60 last:border-0 hover:bg-zinc-900/40">
                    <td className="align-top px-2 py-2 font-mono text-zinc-500">{i + 1}</td>
                    <td className="align-top px-2 py-2">
                      <span className="font-medium text-zinc-100">{hit.displayName}</span>
                      <span className="mt-0.5 block font-mono text-[10px] leading-snug text-cyan-200/75 sm:hidden">{hit.id}</span>
                    </td>
                    <td className="hidden align-top px-2 py-2 font-mono text-[10px] text-cyan-200/80 sm:table-cell">{hit.id}</td>
                    <td className="align-top px-2 py-2">
                      <div className="flex flex-wrap gap-1">
                        {hitRemarkChips(hit).map((c) => (
                          <span
                            key={c}
                            className="inline-block rounded border border-zinc-700/80 bg-zinc-950/80 px-1.5 py-0.5 text-[10px] text-zinc-400"
                          >
                            {c}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="border-t border-zinc-800/80 px-2 py-1.5 text-[10px] text-zinc-600">
              共 {pluginHits.length} 个插件条目；细粒度步进见下方「L0 物理轨迹」。
            </p>
          </div>
        )}
      </SemanticAccordion>
      <p className="text-[11px] text-zinc-500">
        轨迹 A：<code className="text-zinc-400">sys.core.physics.physics_trace</code>；轨迹 B/C：Inbox v1（默认自动确认）。
      </p>
      <SemanticAccordion title="L0 物理轨迹（前 12 步）" subtitle="physics_trace 抽样" defaultOpen={false}>
        {trace.length === 0 ? (
          <p className="text-[11px] text-zinc-600">无 physics_trace（需完整 analyze-seed）。</p>
        ) : (
          <ul className="max-h-48 space-y-1 overflow-auto font-mono text-[10px] text-cyan-100/85">
            {trace.slice(0, 12).map((t, i) => (
              <li key={`tr-${i}`}>
                #{String(t.step_index ?? i)} {String(t.plugin || "—")} · {String(t.reason || "").slice(0, 120)}
                {String(t.delta_summary || "").trim() ? (
                  <span className="text-zinc-500"> · Δ {String(t.delta_summary).slice(0, 80)}</span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </SemanticAccordion>
      <SemanticAccordion title="PluginMatchScore（L1–L3）" subtitle="decision_inbox_v1.match_scores" defaultOpen={false}>
        {scores.length === 0 ? (
          <p className="text-[11px] text-zinc-600">暂无 match_scores。</p>
        ) : (
          <ul className="max-h-40 space-y-1 overflow-auto text-[10px] text-amber-100/90">
            {scores.map((s, i) => (
              <li key={`sc-${i}`}>
                <span className="font-medium text-zinc-200">{String(s.plugin_id)}</span>{" "}
                <span className="text-zinc-500">L{String(s.layer_id).replace(/^L/, "")}</span> score=
                {String(s.score)} <span className="text-zinc-500">({(s.reasons as string[])?.join(", ")})</span>
              </li>
            ))}
          </ul>
        )}
      </SemanticAccordion>
      <SemanticAccordion title="Inbox 生命周期（末 16 条）" subtitle="lifecycle_traces" defaultOpen={false}>
        {lifecycles.length === 0 ? (
          <p className="text-[11px] text-zinc-600">无 lifecycle_traces。</p>
        ) : (
          <ul className="max-h-36 space-y-0.5 overflow-auto font-mono text-[9px] leading-relaxed text-violet-100/80">
            {lifecycles.slice(-16).map((e, i) => (
              <li key={`lc-${i}`}>
                {String(e.event)} · {String(e.plugin_id)} · {String(e.detail || "").slice(0, 100)}
              </li>
            ))}
          </ul>
        )}
      </SemanticAccordion>
    </div>
  );
}

function asLooseRecord(x: unknown): Record<string, unknown> {
  return x && typeof x === "object" && !Array.isArray(x) ? (x as Record<string, unknown>) : {};
}

function parsePillarCell(p: unknown): { stem: string; branch: string; energy?: number } | null {
  if (!p || typeof p !== "object" || Array.isArray(p)) return null;
  const o = p as Record<string, unknown>;
  const stem = String(o.stem ?? "");
  const branch = String(o.branch ?? "");
  if (!stem && !branch) return null;
  const ev = o.energy_value;
  const energy = typeof ev === "number" && Number.isFinite(ev) ? ev : undefined;
  return { stem, branch, energy };
}

/** 黑匣子：八字元数据（BaziMetadata + 快照审计键）专页 */
function DebugBaziMetadataPanel({ snapshot }: { snapshot: LabSnapshot }) {
  const md = asLooseRecord(snapshot.metadata);
  const pillars = asLooseRecord(md.pillars);
  const cm = asLooseRecord(md.conflict_matrix);
  const pointsRaw = cm.points;
  const points = Array.isArray(pointsRaw) ? pointsRaw : [];
  const temporal = md.temporal_context;
  const timeline = snapshot.timeline as Record<string, unknown> | null | undefined;
  const extraKeys = Object.keys(md).filter((k) => !META_CORE_KEYS.has(k));
  const extraObj: Record<string, unknown> = {};
  for (const k of extraKeys) extraObj[k] = md[k];

  const pillarOrder = ["year", "month", "day", "hour"] as const;
  const pillarLabels: Record<(typeof pillarOrder)[number], string> = {
    year: "年柱",
    month: "月柱",
    day: "日柱",
    hour: "时柱",
  };

  return (
    <div className="space-y-4" role="tabpanel" aria-label="八字元数据">
      <p className="text-[11px] leading-relaxed text-zinc-500">
        与后端 <code className="font-mono text-zinc-400">BaziMetadata</code> 对齐：四柱、矛盾矩阵、流向与{" "}
        <code className="font-mono text-zinc-400">temporal_context</code>；并附岁运快照与完整 JSON，供下一步证据与提示词锚点审核。
      </p>

      <SemanticAccordion title="快照标识" subtitle="seed_signature · ts · 会话" defaultOpen={false}>
        <dl className="grid gap-2 text-[11px] sm:grid-cols-2">
          <div>
            <dt className="text-zinc-500">seed_signature</dt>
            <dd className="mt-0.5 break-all font-mono text-zinc-200">{snapshot.seed_signature ? String(snapshot.seed_signature) : "—"}</dd>
          </div>
          <div>
            <dt className="text-zinc-500">ts（快照时间戳）</dt>
            <dd className="mt-0.5 font-mono text-zinc-200">{snapshot.ts != null ? String(snapshot.ts) : "—"}</dd>
          </div>
          <div className="sm:col-span-2">
            <dt className="text-zinc-500">active_session_id</dt>
            <dd className="mt-0.5 break-all font-mono text-zinc-200">
              {snapshot.active_session_id != null ? String(snapshot.active_session_id) : "—"}
            </dd>
          </div>
        </dl>
      </SemanticAccordion>

      <SemanticAccordion title="四柱与盘面摘要" subtitle="version · flow_state · notes" defaultOpen={false}>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {pillarOrder.map((key) => {
              const cell = parsePillarCell(pillars[key]);
              return (
                <div
                  key={key}
                  className="rounded-lg border border-zinc-800/90 bg-zinc-900/40 px-2 py-2 text-center"
                >
                  <p className="text-[10px] uppercase tracking-wide text-zinc-500">{pillarLabels[key]}</p>
                  {cell ? (
                    <>
                      <p className="mt-1 text-lg font-semibold tracking-wide text-amber-100/95">
                        {cell.stem}
                        {cell.branch}
                      </p>
                      {cell.energy != null ? (
                        <p className="mt-0.5 text-[10px] text-zinc-500">能量 {cell.energy}</p>
                      ) : null}
                    </>
                  ) : (
                    <p className="mt-1 text-xs text-zinc-600">—</p>
                  )}
                </div>
              );
            })}
          </div>
          <dl className="grid gap-2 border-t border-zinc-800/80 pt-3 text-[11px] sm:grid-cols-3">
            <div>
              <dt className="text-zinc-500">version</dt>
              <dd className="mt-0.5 font-mono text-zinc-200">{md.version != null ? String(md.version) : "—"}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">flow_state</dt>
              <dd className="mt-0.5 font-mono text-zinc-200">{md.flow_state != null ? String(md.flow_state) : "—"}</dd>
            </div>
            <div className="sm:col-span-3">
              <dt className="text-zinc-500">notes</dt>
              <dd className="mt-0.5 whitespace-pre-wrap text-zinc-300">{md.notes != null ? String(md.notes) : "—"}</dd>
            </div>
          </dl>
        </div>
      </SemanticAccordion>

      <SemanticAccordion title="矛盾矩阵（扫描点）" subtitle="conflict_matrix.points" defaultOpen={false}>
        {points.length === 0 ? (
          <p className="text-xs text-zinc-600">无扫描点（或尚未写入 conflict_matrix）。</p>
        ) : (
          <ul className="max-h-[min(50dvh,420px)] space-y-2 overflow-auto text-[11px]">
            {points.map((pt, i) => {
              const row = asLooseRecord(pt);
              return (
                <li
                  key={i}
                  className="rounded-lg border border-zinc-800/80 bg-black/25 px-2 py-2"
                >
                  <span className="font-mono text-[10px] text-cyan-300/90">{String(row.kind ?? "—")}</span>
                  <span className="mx-2 text-zinc-600">·</span>
                  <span className="text-zinc-400">{Array.isArray(row.positions) ? row.positions.join(", ") : "—"}</span>
                  <p className="mt-1 text-zinc-200">{String(row.detail ?? "")}</p>
                </li>
              );
            })}
          </ul>
        )}
      </SemanticAccordion>

      <SemanticAccordion title="时空上下文（temporal_context）" subtitle="大运 / 流年 / 参考年等 Chronos 审计锚点" defaultOpen={false}>
        {!temporal || (typeof temporal === "object" && temporal !== null && !Array.isArray(temporal) && Object.keys(temporal as object).length === 0) ? (
          <p className="text-xs text-zinc-600">无 temporal_context。</p>
        ) : (
          <pre className="max-h-[min(40dvh,360px)] overflow-auto whitespace-pre-wrap rounded-lg border border-amber-900/25 bg-amber-950/10 p-3 font-mono text-[10px] leading-relaxed text-amber-100/90">
            {safeJson(temporal)}
          </pre>
        )}
      </SemanticAccordion>

      <SemanticAccordion title="岁运时间轴快照" subtitle="snapshot.timeline（与实验室岁运展示同源）" defaultOpen={false}>
        {!timeline || Object.keys(timeline).length === 0 ? (
          <p className="text-xs text-zinc-600">无 timeline。</p>
        ) : (
          <dl className="grid gap-2 text-[11px] sm:grid-cols-2">
            {(["dayun", "liunian", "reference_year"] as const).map((k) => (
              <div key={k}>
                <dt className="text-zinc-500">{k}</dt>
                <dd className="mt-0.5 font-mono text-zinc-200">{timeline[k] != null ? String(timeline[k]) : "—"}</dd>
              </div>
            ))}
          </dl>
        )}
      </SemanticAccordion>

      {extraKeys.length > 0 ? (
        <SemanticAccordion
          title="metadata 扩展字段"
          subtitle={`与 BaziMetadata 核心键并列的其余键（${extraKeys.length} 项）`}
          defaultOpen={false}
        >
          <pre className="max-h-[min(44dvh,400px)] overflow-auto rounded-lg border border-violet-900/25 bg-violet-950/10 p-3 font-mono text-[10px] text-violet-100/85">
            {safeJson(extraObj)}
          </pre>
        </SemanticAccordion>
      ) : null}

      <SemanticAccordion title="metadata 完整 JSON" subtitle="整对象复制 / 与后端对拍" defaultOpen={false}>
        <pre className="max-h-[min(56dvh,520px)] overflow-auto rounded-lg border border-zinc-800 bg-black/40 p-3 font-mono text-[10px] text-zinc-400">
          {safeJson(Object.keys(md).length ? md : {})}
        </pre>
      </SemanticAccordion>
    </div>
  );
}

export function DebugView() {
  const { state } = useLabStore();
  const snapshot = useMemo(() => state.snapshot ?? null, [state.snapshot]);
  const [pluginFocusId, setPluginFocusId] = useState<string | null>(null);
  const [debugTab, setDebugTab] = useState<DebugTabId>("verdict");
  const finalizationReport = state.finalizationReport;
  const metaFinal = (snapshot?.metadata as Record<string, unknown> | undefined)?.finalization as
    | { hash?: string; committed_at?: number }
    | undefined;

  const physics = snapshot?.physics_tensor as Record<string, unknown> | undefined;
  const fv = snapshot?.final_verdict as Record<string, unknown> | undefined;
  const ld = snapshot?.logic_diff;

  const causalSovereigntyForCert = useMemo(
    () => buildCausalSovereigntySlice(snapshot as Record<string, unknown> | null | undefined),
    [snapshot],
  );

  const timelineSnap = (snapshot?.timeline ?? null) as TimelineSnapshot | null;
  const verdictBody = typeof fv?.body === "string" ? fv.body.trim() : "";
  const llmPrompt = typeof snapshot?.llm_prompt === "string" ? snapshot.llm_prompt.trim() : "";

  const solidGhostRatio = useMemo(() => {
    const m = snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined;
    const raw = m?.solid_ghost_ratio as Record<string, unknown> | undefined;
    if (!raw || typeof raw.solid_fraction !== "number" || !Number.isFinite(raw.solid_fraction)) return null;
    return {
      solid_fraction: raw.solid_fraction as number,
      ghost_fraction:
        typeof raw.ghost_fraction === "number" && Number.isFinite(raw.ghost_fraction)
          ? (raw.ghost_fraction as number)
          : 1 - (raw.solid_fraction as number),
      avg_effective_conductivity:
        typeof raw.avg_effective_conductivity === "number" && Number.isFinite(raw.avg_effective_conductivity)
          ? (raw.avg_effective_conductivity as number)
          : undefined,
    };
  }, [snapshot?.physics_tensor?.meta]);

  useEffect(() => {
    if (!snapshot || typeof window === "undefined") return;
    const pid = sessionStorage.getItem(DEBUG_PLUGIN_FOCUS_KEY);
    if (!pid) return;
    sessionStorage.removeItem(DEBUG_PLUGIN_FOCUS_KEY);
    setPluginFocusId(pid);
    setDebugTab("physics");
  }, [snapshot?.ts, snapshot]);

  useEffect(() => {
    if (!pluginFocusId) return;
    const tid = window.setTimeout(() => {
      document.getElementById(`plugin-audit-row-${pluginFocusId}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 120);
    return () => window.clearTimeout(tid);
  }, [pluginFocusId]);

  return (
    <div className="mx-auto min-h-dvh w-full max-w-5xl px-3 py-4 text-zinc-200">
      <header className="mb-4 border-b border-zinc-800 pb-4">
        <h1 className="text-lg font-semibold tracking-tight text-zinc-50">裁决舱 · 调试视图</h1>
        <p className="mt-1 text-xs leading-relaxed text-zinc-500">
          与顶栏「实验室 / 黑匣子 / 机房」同系分段 Tab；含「八字元数据」专页供锚点审核；其余各小节默认收起。
        </p>
      </header>

      {!snapshot ? (
        <p className="text-sm text-zinc-500">暂无数据。请先在「实验室」完成排盘或推演。</p>
      ) : (
        <div className="space-y-5">
          <div className="flex flex-col items-stretch gap-3 sm:items-center">
            <DebugSubTabBar active={debugTab} onChange={setDebugTab} />
          </div>

          {debugTab === "verdict" ? (
            <div className="space-y-4" role="tabpanel" aria-label="终局与断言">
              <SemanticAccordion
                title="终审存证"
                subtitle="已签发证书、logic_diff 遥测、因果主权摘要"
                defaultOpen={false}
              >
                {state.isFinalized && finalizationReport?.hash ? (
                  <VerdictCertificate
                    hash={finalizationReport.hash}
                    committedAt={finalizationReport.committedAt}
                    logicDiff={ld}
                    showAbsTelemetry={true}
                    effectiveSkillIds={
                      finalizationReport.effectiveSkillIds ??
                      (snapshot?.metadata?.verdict_effective_skill_ids as string[] | undefined)
                    }
                    solidGhostRatio={solidGhostRatio ?? undefined}
                    causalSovereignty={causalSovereigntyForCert ?? undefined}
                  />
                ) : (
                  <p className="text-xs text-zinc-500">当前未签发终审证书（终判完成后将显示完整存证）。</p>
                )}
              </SemanticAccordion>

              <SemanticAccordion title="终审指纹（简）" subtitle="未签发完整证书时仍可查看哈希" defaultOpen={false}>
                {!state.isFinalized && (finalizationReport || metaFinal?.hash) ? (
                  <div className="rounded-lg border border-violet-500/35 bg-violet-950/25 p-3 text-xs text-violet-100">
                    <p className="text-[10px] font-medium uppercase tracking-wide text-violet-300">SHA-256</p>
                    <p className="mt-2 font-mono text-[11px] break-all">
                      {String(finalizationReport?.hash ?? metaFinal?.hash ?? "—")}
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-zinc-500">暂无独立指纹条（与完整存证二选一展示）。</p>
                )}
              </SemanticAccordion>

              <SemanticAccordion
                title="LLM 智能断言"
                subtitle="终审正文优先；否则回退展示提示词头部"
                defaultOpen={false}
              >
                <div className="overflow-hidden rounded-xl border border-fuchsia-900/35 bg-gradient-to-b from-zinc-950 to-zinc-900/90 p-4 shadow-[0_0_24px_rgba(192,38,211,0.08)]">
                  {verdictBody ? (
                    <article className="max-h-[min(52dvh,560px)] overflow-auto whitespace-pre-wrap text-sm leading-relaxed text-zinc-100">
                      {verdictBody}
                    </article>
                  ) : llmPrompt ? (
                    <article className="max-h-[min(40dvh,400px)] overflow-auto whitespace-pre-wrap text-sm leading-relaxed text-zinc-300">
                      {llmPrompt}
                    </article>
                  ) : (
                    <p className="text-sm text-zinc-500">暂无终判正文；完成终判或首观后将显示于此。</p>
                  )}
                </div>
              </SemanticAccordion>
            </div>
          ) : null}

          {debugTab === "bazi_meta" ? <DebugBaziMetadataPanel snapshot={snapshot} /> : null}

          {debugTab === "physics" ? (
            <div className="space-y-4" role="tabpanel" aria-label="物理与博弈">
              <SemanticAccordion title="分层轨迹审计（L0 / Inbox）" subtitle="physics_trace 与 Inbox v1" defaultOpen={false}>
                <LayerAuditTrails physics={physics} />
              </SemanticAccordion>
              <SemanticAccordion title="插件博弈证据" subtitle="插件输出、置信度与路由文案" defaultOpen={false}>
                <PluginCollisionHub physicsTensor={physics} highlightPluginId={pluginFocusId} />
              </SemanticAccordion>
            </div>
          ) : null}

          {debugTab === "observe" ? (
            <div className="space-y-4" role="tabpanel" aria-label="时序与观测">
              <SemanticAccordion title="决策时序轴" subtitle="物理 → 插件 → 路由 → 终审装配顺序" defaultOpen={false}>
                <DecisionTimeline snapshot={snapshot as Record<string, unknown>} />
              </SemanticAccordion>
              <SemanticAccordion title="实时状态仪表盘" subtitle="四柱激活、岁运与场强摘要" defaultOpen={false}>
                <StateMonitor metadata={snapshot.metadata as Record<string, unknown>} timeline={timelineSnap} physicsTensor={physics} />
              </SemanticAccordion>
            </div>
          ) : null}

          {debugTab === "tools" ? (
            <div className="space-y-4" role="tabpanel" aria-label="血统与工具">
              <SemanticAccordion title="血统证明链" subtitle="系统证据与插件输出如何支撑 LLM 断言" defaultOpen={false}>
                <NarrativeProvenancePanel snapshot={snapshot as Record<string, unknown>} llmPrompt={snapshot.llm_prompt as string | undefined} />
              </SemanticAccordion>
              <SemanticAccordion
                title="逻辑检察院"
                subtitle="POST /audit/diagnose；可载入实验室四柱"
                defaultOpen={false}
              >
                <div className="max-h-[min(85dvh,720px)] overflow-auto pr-1">
                  <AuditChamberPanel />
                </div>
              </SemanticAccordion>
              <SemanticAccordion title="模型交互记录" subtitle="首观 / 物理审计 / 终审 LLM" defaultOpen={false}>
                <div className="space-y-3">
                  <LlmRoundCompact
                    title="首观 LLM"
                    subtitle="analyze-seed / 首条判词来源"
                    round={snapshot.first_observation_llm}
                    promptFallback={typeof snapshot.llm_prompt === "string" ? snapshot.llm_prompt : undefined}
                  />
                  <LlmRoundCompact title="物理审计 LLM" subtitle="audit-physics-with-llm" round={snapshot.physics_auditor_llm} />
                  <SemanticAccordion title="终审 LLM 往返" subtitle="messages 与模型原始返回" defaultOpen={false}>
                    {(() => {
                      const finalMsgs = normalizeLlmMessages(fv?.llm_request_messages);
                      const finalPrompt = formatLlmMessagesAsPrompt(finalMsgs);
                      const finalRaw =
                        fv && typeof fv.llm_raw_response === "string" ? fv.llm_raw_response.trim() : "";
                      if (!fv || (!finalPrompt && !finalRaw)) {
                        return <p className="text-xs text-zinc-500">暂无终审 LLM 记录。</p>;
                      }
                      return (
                        <div className="space-y-3 text-xs">
                          {finalPrompt ? (
                            <div>
                              <p className="text-[10px] uppercase tracking-wide text-sky-400/90">发给模型的提示词（messages）</p>
                              <div className="mt-1 max-h-[min(42dvh,380px)] overflow-auto whitespace-pre-wrap rounded-lg border border-sky-900/40 bg-sky-950/20 p-3 text-[11px] leading-relaxed text-sky-50/95">
                                {finalPrompt}
                              </div>
                            </div>
                          ) : null}
                          <div>
                            <p className="text-[10px] uppercase tracking-wide text-zinc-500">模型原始返回</p>
                            <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap rounded-lg border border-violet-900/35 bg-zinc-950/80 p-2 font-mono text-[10px] text-violet-100/90">
                              {finalRaw || "—"}
                            </pre>
                          </div>
                          <details className="rounded border border-zinc-800 bg-zinc-950/60">
                            <summary className="cursor-pointer px-2 py-1.5 text-[10px] text-zinc-500">原始 llm_request_messages JSON</summary>
                            <pre className="max-h-48 overflow-auto border-t border-zinc-800 p-2 font-mono text-[9px] text-zinc-400">
                              {safeJson(fv.llm_request_messages ?? [])}
                            </pre>
                          </details>
                        </div>
                      );
                    })()}
                  </SemanticAccordion>
                </div>
              </SemanticAccordion>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
