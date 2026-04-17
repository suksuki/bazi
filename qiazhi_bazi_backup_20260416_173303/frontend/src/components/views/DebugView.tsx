"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import { ArbiterAuditPanel, type ArbiterAuditEntry } from "@/components/views/ArbiterAuditPanel";
import { LogicPulseStream } from "@/components/views/LogicPulseStream";
import { sysCorePhysicsPayload } from "@/features/stream-board/sysCorePhysics";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import { buildCausalSovereigntySlice } from "@/features/stream-board/utils/causalSovereigntyFromSnapshot";
import type { LabSnapshot } from "@/features/stream-board/stores/LabSessionContext";
import type { TimelineSnapshot } from "@/types/bazi";

const DEBUG_PLUGIN_FOCUS_KEY = "qiazhi_debug_plugin_focus";
const DEBUG_TABS = [
  { id: "tools", label: "LLM 对话总览" },
  { id: "verdict", label: "终局与断言" },
  { id: "physics", label: "物理与博弈" },
  { id: "bazi_meta", label: "八字元数据" },
  { id: "observe", label: "时序与观测" },
] as const;
type DebugTabId = (typeof DEBUG_TABS)[number]["id"];


/** BaziMetadata 核心键；其余归入「扩展字段」便于审核对照 */
const META_CORE_KEYS = new Set([
  "version",
  "memory_schema_version",
  "pillars",
  "conflict_matrix",
  "flow_state",
  "notes",
  "temporal_context",
  "plugin_selection_trace",
  "history_context",
  "inference_trace",
  "verdict_anchor_layer",
]);

const EARTHLY_BRANCHES = "子丑寅卯辰巳午未申酉戌亥";

function firstEarthlyInString(s: string): string | null {
  for (const ch of s) {
    if (EARTHLY_BRANCHES.includes(ch)) return ch;
  }
  return null;
}


function safeJson(obj: unknown, space = 2): string {
  try {
    return JSON.stringify(obj, null, space);
  } catch {
    return String(obj);
  }
}

function DebugTabs(props: { active: DebugTabId; onChange: (id: DebugTabId) => void }) {
  const { active, onChange } = props;
  return (
    <div className="flex flex-wrap gap-1 rounded-xl border border-zinc-800/90 bg-zinc-950/90 p-1">
      {DEBUG_TABS.map((tab) => {
        const on = active === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            className={`rounded-lg px-2 py-1 text-[11px] transition-colors ${
              on ? "bg-cyan-900/70 text-cyan-100" : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
            }`}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

/** V12.94：静默智能裁决历史（physics meta / 断言树侧车） */
function collectSilentArbiterHistory(snapshot: LabSnapshot): Record<string, unknown>[] {
  const pt = snapshot.physics_tensor as Record<string, unknown> | undefined;
  const meta = pt?.meta as Record<string, unknown> | undefined;
  const fromPhysics = meta?.silent_arbiter_history_v1;
  if (Array.isArray(fromPhysics) && fromPhysics.length > 0) {
    return fromPhysics.filter((x): x is Record<string, unknown> => x !== null && typeof x === "object");
  }
  const md = snapshot.metadata as Record<string, unknown> | undefined;
  const val = md?.verdict_anchor_layer as Record<string, unknown> | undefined;
  const tree = val?.assertion_tree as Record<string, unknown> | undefined;
  const fromTree = tree?.silent_arbiter_history_v1;
  if (Array.isArray(fromTree) && fromTree.length > 0) {
    return fromTree.filter((x): x is Record<string, unknown> => x !== null && typeof x === "object");
  }
  const fv = snapshot.final_verdict as Record<string, unknown> | undefined;
  const fvTree = fv?.assertion_tree as Record<string, unknown> | undefined;
  const fromFv = fvTree?.silent_arbiter_history_v1;
  if (Array.isArray(fromFv) && fromFv.length > 0) {
    return fromFv.filter((x): x is Record<string, unknown> => x !== null && typeof x === "object");
  }
  return [];
}

/** V12.95：完整裁决审计（含 prompt / raw_response，与 DB arbitration_logs 同源字段） */
function collectArbitrationAuditFeed(snapshot: LabSnapshot): ArbiterAuditEntry[] {
  const pt = snapshot.physics_tensor as Record<string, unknown> | undefined;
  const meta = pt?.meta as Record<string, unknown> | undefined;
  const feed = meta?.arbitration_audit_feed_v1;
  if (!Array.isArray(feed) || feed.length === 0) return [];
  return feed.filter((x): x is ArbiterAuditEntry => x !== null && typeof x === "object");
}

/** V13.03：物理引擎自治（锚点毙稿 / 权力否决 / 二段跳强收） */
function collectPhysicsAutonomyLog(snapshot: LabSnapshot): Record<string, unknown>[] {
  const pt = snapshot.physics_tensor as Record<string, unknown> | undefined;
  const meta = pt?.meta as Record<string, unknown> | undefined;
  const raw = meta?.physics_autonomy_log_v1;
  if (!Array.isArray(raw) || raw.length === 0) return [];
  return raw.filter((x): x is Record<string, unknown> => x !== null && typeof x === "object");
}

/** V13.06：物理自治单行人话（与 ``decision_hub.append_physics_autonomy_log`` 结构对齐） */
function physicsAutonomyHumanLine(row: Record<string, unknown>): string {
  const kind = String(row.kind ?? "");
  const reason = String(row.reason ?? "");
  if (kind === "SILENT_REJECT" && reason === "physical_anchor_deviation") {
    const pid = String(row.plugin_id ?? "插件");
    const anchor = row.anchor;
    const hint = row.hint_effective;
    const dev = row.deviation;
    const thr = row.threshold;
    return `由于当前物理场强锚（约 ${anchor}）与插件「${pid}」的合成先验（约 ${hint}）偏差 ${dev}，已超过自治阈值 ${thr}，已静默剔除该候选分，避免与真值锚点冲突（例如：场强已偏一侧时，不再采纳与之相悖的「木旺」类意象偏差）。`;
  }
  if (kind === "SILENT_REJECT" && reason === "plugin_authority_veto") {
    const pid = String(row.plugin_id ?? "—");
    const lv = row.authority_level;
    const mx = row.max_authority_level;
    return `存在更高权力等级（峰值 ${mx}）的插件结论；等级 ${lv} 的「${pid}」已被一票否决，仅保留最高等级参与后续博弈（古法格局类插件往往在此占优）。`;
  }
  if (kind === "TWO_STAGE_FORCE" && reason === "fact_stalemate_exhausted") {
    const win = String(row.winner_plugin_id ?? "—");
    return `同一事实点在多轮高分僵持后触发二段跳：已强制采纳当前最高分插件「${win}」，并将全局冲突张力抹零以闭合事实链。`;
  }
  return "";
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

/** 从 evidence_refs 解析 UI 高亮集合（与后端锚点字符串约定对齐） */
function collectEvidenceHighlights(refs: string[]) {
  const conflictIds = new Set<string>();
  const pluginIds = new Set<string>();
  const pillarKeys = new Set<string>();
  const branches = new Set<string>();
  for (const raw of refs) {
    const r = String(raw || "").trim();
    if (!r) continue;
    if (r.startsWith("conflict_matrix.")) conflictIds.add(r.slice("conflict_matrix.".length));
    else if (r.endsWith(".pillar")) pillarKeys.add(r.replace(/\.pillar$/, ""));
    else if (r.endsWith(".branch")) pillarKeys.add(r.replace(/\.branch$/, ""));
    else if (r.endsWith(".stem")) pillarKeys.add(r.replace(/\.stem$/, ""));
    else if (r.startsWith("branch.")) branches.add(r.slice("branch.".length));
    else if (r.startsWith("plugin.")) pluginIds.add(r.slice("plugin.".length));
    else if (
      r.includes(".") &&
      (r.includes("v1") || r.includes("sys.") || r.includes("classical.") || r.includes("modern.") || r.includes("base_physics"))
    ) {
      pluginIds.add(r);
    }
  }
  return { conflictIds, pluginIds, pillarKeys, branches };
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

/** 黑匣子：八字元数据（BaziMetadata + 快照审计键）专页；地支点击联动终判段落 */
function DebugBaziMetadataPanel(props: {
  snapshot: LabSnapshot;
  focusBranch: string | null;
  onBranchSelect: (branch: string | null) => void;
}) {
  const { snapshot, focusBranch, onBranchSelect } = props;
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
  const pstRaw = md.plugin_selection_trace;
  const pluginTrace = Array.isArray(pstRaw) ? pstRaw : [];
  const [timeTravelSel, setTimeTravelSel] = useState<{ id: string; refs: string[] } | null>(null);
  const ttHl = useMemo(() => collectEvidenceHighlights(timeTravelSel?.refs || []), [timeTravelSel]);

  const infRaw = md.inference_trace;
  const infRec = infRaw && typeof infRaw === "object" && !Array.isArray(infRaw) ? asLooseRecord(infRaw) : {};
  const inferenceSteps = Array.isArray(infRec.steps) ? infRec.steps : [];

  const anchorLayerRaw = md.verdict_anchor_layer;
  const anchorLayer =
    anchorLayerRaw && typeof anchorLayerRaw === "object" && !Array.isArray(anchorLayerRaw) ? asLooseRecord(anchorLayerRaw) : {};
  const anchorAssertionsRaw = anchorLayer.assertions;
  const anchorAssertions = Array.isArray(anchorAssertionsRaw)
    ? anchorAssertionsRaw.map((x) => asLooseRecord(x)).filter((x) => Object.keys(x).length > 0)
    : [];
  const coreAnchorAssertions = anchorAssertions.filter((row) => Array.isArray(row.evidence_refs) && row.evidence_refs.length > 0);
  const orphanAnchorAssertions = anchorAssertions.filter((row) => !Array.isArray(row.evidence_refs) || row.evidence_refs.length === 0);

  const hcRaw = md.history_context;
  const hcRec = hcRaw && typeof hcRaw === "object" && !Array.isArray(hcRaw) ? asLooseRecord(hcRaw) : {};
  const confirmedVerdicts = Array.isArray(hcRec.confirmed_verdicts) ? hcRec.confirmed_verdicts.map(asLooseRecord) : [];
  const regenerationEvents = Array.isArray(hcRec.regeneration_events) ? hcRec.regeneration_events.map(asLooseRecord) : [];
  const modelStamps = Array.isArray(hcRec.verdict_model_stamps) ? hcRec.verdict_model_stamps.map(asLooseRecord) : [];

  const fv = snapshot.final_verdict as Record<string, unknown> | undefined;
  const narrativeChunks = useMemo(() => {
    const raw = fv?.narrative_chunks;
    return Array.isArray(raw) ? raw.filter((x): x is Record<string, unknown> => !!x && typeof x === "object") : [];
  }, [fv?.narrative_chunks]);
  const matchedNarrative = useMemo(() => {
    if (!focusBranch) return [] as Record<string, unknown>[];
    return narrativeChunks.filter((c) => {
      const bc = c.branch_chars;
      return Array.isArray(bc) && bc.includes(focusBranch);
    });
  }, [narrativeChunks, focusBranch]);
  const fallbackNarrative = useMemo(() => {
    if (!focusBranch || matchedNarrative.length > 0) return [] as string[];
    const body = typeof fv?.body === "string" ? fv.body : "";
    if (!body.trim()) return [];
    return body
      .split(/\n\s*\n+/)
      .map((p) => p.trim())
      .filter((p) => p.includes(focusBranch))
      .slice(0, 12);
  }, [focusBranch, matchedNarrative.length, fv?.body]);

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
        与后端 <code className="font-mono text-zinc-400">BaziMetadata</code> 对齐；矛盾矩阵含 L1 流水线回写；点击柱上{" "}
        <strong className="text-zinc-300">地支</strong> 可高亮下方「关联智能断言」。柱能数值与{" "}
        <code className="font-mono text-zinc-400">by_pillar.raw_energy</code> 归一化同步。
      </p>
      {focusBranch ? (
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-amber-800/50 bg-amber-950/20 px-2 py-1.5 text-[11px] text-amber-100/90">
          <span>已选地支锚点：</span>
          <span className="font-mono text-lg font-semibold">{focusBranch}</span>
          <button type="button" className="rounded border border-zinc-600 px-2 py-0.5 text-[10px] text-zinc-300 hover:bg-zinc-800" onClick={() => onBranchSelect(null)}>
            清除
          </button>
        </div>
      ) : null}

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

      <SemanticAccordion title="插件入选轨迹" subtitle="metadata.plugin_selection_trace" defaultOpen={false}>
        {pluginTrace.length === 0 ? (
          <p className="text-xs text-zinc-600">暂无轨迹（需 analyze-seed 且 Inbox 管线成功）。</p>
        ) : (
          <ul className="max-h-[min(44dvh,400px)] space-y-1.5 overflow-auto text-[11px]">
            {pluginTrace.map((row, i) => {
              const r = asLooseRecord(row);
              return (
                <li key={i} className="rounded border border-zinc-800/80 bg-black/25 px-2 py-1.5">
                  <span className="font-mono text-cyan-200/90">{String(r.plugin_id)}</span>
                  <span className="mx-1 text-zinc-600">·</span>
                  <span className="text-zinc-400">{String(r.layer_id)}</span>
                  <span className="mx-1 text-zinc-600">·</span>
                  <span className="text-amber-200/85">{String(r.status)}</span>
                  <p className="mt-0.5 text-[10px] leading-snug text-zinc-400">{String(r.reason || "")}</p>
                </li>
              );
            })}
          </ul>
        )}
      </SemanticAccordion>

      <SemanticAccordion title="决策回溯（Time-Travel Audit）" subtitle="核心断言 · 签发记忆 · inference_trace 联动高亮" defaultOpen={false}>
        <div className="space-y-3 text-[11px] leading-relaxed">
          <p className="text-zinc-500">
            仅带 <code className="font-mono text-zinc-400">evidence_refs</code> 的断言进入「核心断言区」；点击一条可高亮下方四柱、矛盾矩阵行及因果轨迹中的插件步。
          </p>
          {timeTravelSel ? (
            <div className="flex flex-wrap items-center gap-2 rounded-lg border border-violet-800/50 bg-violet-950/20 px-2 py-1.5 text-violet-100/90">
              <span className="font-mono text-[10px]">选中：{timeTravelSel.id}</span>
              <button
                type="button"
                className="rounded border border-zinc-600 px-2 py-0.5 text-[10px] text-zinc-300 hover:bg-zinc-800"
                onClick={() => setTimeTravelSel(null)}
              >
                清除高亮
              </button>
            </div>
          ) : null}

          <div>
            <p className="mb-1 font-medium text-zinc-300">核心断言区（可溯源）</p>
            {coreAnchorAssertions.length === 0 ? (
              <p className="text-zinc-600">暂无（需终判回写 metadata.verdict_anchor_layer）。</p>
            ) : (
              <ul className="max-h-[min(36dvh,320px)] space-y-1.5 overflow-auto">
                {coreAnchorAssertions.map((row, i) => {
                  const aid = String(row.assertion_id ?? `a${i}`);
                  const selected = timeTravelSel?.id === aid;
                  const refs = Array.isArray(row.evidence_refs) ? row.evidence_refs.map((x) => String(x)) : [];
                  return (
                    <li key={aid}>
                      <button
                        type="button"
                        className={`w-full rounded-lg border px-2 py-2 text-left transition-colors ${
                          selected ? "border-violet-500/70 bg-violet-950/30" : "border-zinc-800/80 bg-black/25 hover:border-violet-800/40"
                        }`}
                        onClick={() => setTimeTravelSel(selected ? null : { id: aid, refs })}
                      >
                        <span className="font-mono text-[9px] text-zinc-500">{aid}</span>
                        <p className="mt-1 line-clamp-4 whitespace-pre-wrap text-zinc-200">{String(row.text ?? "")}</p>
                        <p className="mt-1 font-mono text-[9px] text-cyan-300/80">{refs.join(" · ")}</p>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          {orphanAnchorAssertions.length > 0 ? (
            <div>
              <p className="mb-1 text-zinc-500">非溯源断言（不进入核心区）</p>
              <ul className="max-h-[min(20dvh,200px)] space-y-1 overflow-auto text-[10px] text-zinc-500">
                {orphanAnchorAssertions.map((row, i) => (
                  <li key={String(row.assertion_id ?? `o${i}`)} className="line-clamp-2">
                    {String(row.text ?? "").slice(0, 160)}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div>
            <p className="mb-1 font-medium text-zinc-300">已签发记忆（history_context）</p>
            {confirmedVerdicts.length === 0 ? (
              <p className="text-zinc-600">暂无签发归档。</p>
            ) : (
              <ul className="max-h-[min(28dvh,260px)] space-y-1.5 overflow-auto">
                {confirmedVerdicts.map((row, i) => {
                  const vid = String(row.verdict_id ?? `cv${i}`);
                  const refs = Array.isArray(row.evidence_refs) ? row.evidence_refs.map((x) => String(x)) : [];
                  const selected = timeTravelSel?.id === `hist:${vid}`;
                  return (
                    <li key={vid}>
                      <button
                        type="button"
                        className={`w-full rounded-lg border px-2 py-2 text-left ${
                          selected ? "border-amber-500/60 bg-amber-950/25" : "border-zinc-800/80 bg-black/20 hover:border-amber-900/35"
                        }`}
                        onClick={() => setTimeTravelSel(selected ? null : { id: `hist:${vid}`, refs })}
                      >
                        <span className="font-mono text-[9px] text-zinc-500">{vid}</span>
                        <span className="mx-1 text-zinc-600">·</span>
                        <span className="text-[9px] text-zinc-500">{String(row.confirmed_at ?? "")}</span>
                        <p className="mt-1 line-clamp-2 text-zinc-300">{String(row.body_excerpt ?? "")}</p>
                        <p className="mt-0.5 font-mono text-[8px] text-zinc-600">hash {String(row.source_metadata_hash ?? "").slice(0, 20)}…</p>
                        {row.model_id ? (
                          <p className="mt-0.5 font-mono text-[8px] text-cyan-600/90">model {String(row.model_id)}</p>
                        ) : null}
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <div>
            <p className="mb-1 font-medium text-zinc-300">模型指纹链（verdict_model_stamps）</p>
            {modelStamps.length === 0 ? (
              <p className="text-zinc-600">暂无（需终判成功且已合并 metadata_memory_patch）。</p>
            ) : (
              <ul className="max-h-[min(24dvh,220px)] space-y-1 overflow-auto font-mono text-[10px]">
                {modelStamps.map((row, i) => (
                  <li key={`${String(row.version_id ?? i)}-${String(row.occurred_at ?? i)}`} className="text-cyan-200/85">
                    {String(row.occurred_at ?? "")} · <span className="text-amber-200/90">{String(row.model_id ?? "unknown")}</span> ·{" "}
                    {String(row.version_id ?? "—")}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <p className="mb-1 font-medium text-zinc-300">再生记录（regeneration_events）</p>
            {regenerationEvents.length === 0 ? (
              <p className="text-zinc-600">暂无（终判请求未带 regeneration_context 或未合并进 metadata）。</p>
            ) : (
              <ul className="max-h-[min(28dvh,260px)] space-y-1.5 overflow-auto text-[10px]">
                {regenerationEvents.map((row, i) => (
                  <li key={`${String(row.version_id ?? i)}-${String(row.occurred_at ?? i)}`} className="rounded border border-zinc-800/80 bg-black/20 px-2 py-1.5">
                    <span className="font-mono text-cyan-300/85">{String(row.trigger ?? "—")}</span>
                    <span className="mx-1 text-zinc-600">·</span>
                    <span className="text-zinc-500">{String(row.occurred_at ?? "")}</span>
                    <p className="mt-0.5 text-zinc-300">{String(row.reason ?? "")}</p>
                    <p className="mt-0.5 font-mono text-[9px] text-zinc-500">
                      model {String(row.model_id ?? "—")} · ver {String(row.version_id ?? "—")} ← prev{" "}
                      {String(row.previous_version_id ?? "—")}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <p className="mb-1 font-medium text-zinc-300">因果轨迹（metadata.inference_trace）</p>
            {inferenceSteps.length === 0 ? (
              <p className="text-zinc-600">暂无（需 analyze 写入 L0 physics_trace + Inbox MatchScore）。</p>
            ) : (
              <ul className="max-h-[min(40dvh,380px)] space-y-1 overflow-auto font-mono text-[10px]">
                {inferenceSteps.map((st, idx) => {
                  const s = asLooseRecord(st);
                  const pid = String(s.plugin_id ?? "");
                  const stepHit =
                    ttHl.pluginIds.has(pid) ||
                    Array.from(ttHl.pluginIds).some((p) => p === pid || pid.includes(p) || p.includes(pid));
                  return (
                    <li
                      key={`${pid}-${idx}`}
                      className={`rounded border px-2 py-1.5 ${stepHit ? "border-violet-500/60 bg-violet-950/20" : "border-zinc-800/60 bg-black/20"}`}
                    >
                      <span className="text-cyan-300/90">{String(s.layer_id ?? "")}</span>
                      <span className="mx-1 text-zinc-600">·</span>
                      <span className="text-amber-200/85">{pid}</span>
                      {s.match_score != null && typeof s.match_score === "number" ? (
                        <>
                          <span className="mx-1 text-zinc-600">·</span>
                          <span className="text-zinc-400">score {String(s.match_score)}</span>
                        </>
                      ) : null}
                      <p className="mt-0.5 whitespace-pre-wrap text-zinc-400">{String(s.output_summary || s.input_summary || "")}</p>
                      {s.arbitration_note ? <p className="mt-0.5 text-violet-300/80">{String(s.arbitration_note)}</p> : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
      </SemanticAccordion>

      <SemanticAccordion title="四柱与盘面摘要" subtitle="version · flow_state · notes · 点击地支联动断言" defaultOpen={false}>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {pillarOrder.map((key) => {
              const cell = parsePillarCell(pillars[key]);
              const br = cell?.branch ?? "";
              const selectedBranch = Boolean(br && focusBranch === br);
              const pillarAudit = ttHl.pillarKeys.has(key);
              const branchAudit = Boolean(br && ttHl.branches.has(br));
              const pillarAccent = selectedBranch || pillarAudit || branchAudit;
              return (
                <div
                  key={key}
                  className={`rounded-lg border px-2 py-2 text-center ${
                    pillarAccent ? "border-violet-500/70 bg-violet-950/25" : "border-zinc-800/90 bg-zinc-900/40"
                  }`}
                >
                  <p className="text-[10px] uppercase tracking-wide text-zinc-500">{pillarLabels[key]}</p>
                  {cell ? (
                    <>
                      <p className="mt-1 text-lg font-semibold tracking-wide text-amber-100/95">
                        {cell.stem}
                        {br ? (
                          <button
                            type="button"
                            title="点击以高亮终判中引用该地支的段落"
                            className={`ml-0.5 rounded px-0.5 underline decoration-dotted decoration-amber-500/60 underline-offset-2 hover:bg-amber-950/50 ${selectedBranch ? "text-amber-200" : "text-amber-100/95"}`}
                            onClick={() => onBranchSelect(selectedBranch ? null : br)}
                          >
                            {br}
                          </button>
                        ) : null}
                      </p>
                      {cell.energy != null ? (
                        <p className="mt-0.5 text-[10px] text-zinc-500">柱能 {cell.energy}</p>
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
              <dt className="text-zinc-500">memory_schema_version</dt>
              <dd className="mt-0.5 font-mono text-zinc-200">{md.memory_schema_version != null ? String(md.memory_schema_version) : "—"}</dd>
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

      <SemanticAccordion title="矛盾矩阵（扫描点 + L1 回写）" subtitle="conflict_matrix.points · 点击行可拾取地支锚点" defaultOpen={false}>
        {points.length === 0 ? (
          <p className="text-xs text-zinc-600">无扫描点（或尚未写入 conflict_matrix）。</p>
        ) : (
          <ul className="max-h-[min(50dvh,420px)] space-y-2 overflow-auto text-[11px]">
            {points.map((pt, i) => {
              const row = asLooseRecord(pt);
              const pid = String(row.id ?? `cp_${i}`);
              const hitB = firstEarthlyInString(String(row.detail ?? "") + (Array.isArray(row.positions) ? row.positions.join("") : ""));
              const rowHit = ttHl.conflictIds.has(pid);
              return (
                <li key={pid}>
                  <button
                    type="button"
                    className={`w-full rounded-lg border px-2 py-2 text-left hover:border-amber-800/50 ${
                      rowHit ? "border-violet-500/70 bg-violet-950/25" : "border-zinc-800/80 bg-black/25"
                    }`}
                    onClick={() => onBranchSelect(hitB ? (focusBranch === hitB ? null : hitB) : null)}
                  >
                    <span className="font-mono text-[9px] text-zinc-500">{pid}</span>
                    <span className="mx-1 text-zinc-600">·</span>
                    <span className="font-mono text-[10px] text-cyan-300/90">{String(row.kind ?? "—")}</span>
                    {row.source ? (
                      <>
                        <span className="mx-1 text-zinc-600">·</span>
                        <span className="text-[9px] text-violet-300/80">{String(row.source)}</span>
                      </>
                    ) : null}
                    <span className="mx-2 text-zinc-600">·</span>
                    <span className="text-zinc-400">{Array.isArray(row.positions) ? row.positions.join(", ") : "—"}</span>
                    <p className="mt-1 text-zinc-200">{String(row.detail ?? "")}</p>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </SemanticAccordion>

      <SemanticAccordion title="关联智能断言（终判段落）" subtitle="narrative_chunks 或正文启发式匹配" defaultOpen={false}>
        {!focusBranch ? (
          <p className="text-xs text-zinc-600">请先在上方四柱或矛盾矩阵中点选地支。</p>
        ) : matchedNarrative.length === 0 && fallbackNarrative.length === 0 ? (
          <p className="text-xs text-zinc-600">终判正文中未检出含「{focusBranch}」的段落（或尚未终判）。</p>
        ) : (
          <ul className="max-h-[min(48dvh,440px)] space-y-2 overflow-auto">
            {matchedNarrative.map((c, i) => (
              <li
                key={String(c.chunk_id ?? i)}
                className="rounded-lg border border-fuchsia-900/35 bg-fuchsia-950/15 px-2 py-2 text-[11px] leading-relaxed text-fuchsia-50/95"
              >
                <span className="font-mono text-[9px] text-zinc-500">{String(c.chunk_id ?? "")}</span>
                <p className="mt-1 whitespace-pre-wrap">{String(c.text ?? "")}</p>
                {Array.isArray(c.conflict_point_ids) && c.conflict_point_ids.length > 0 ? (
                  <p className="mt-1 text-[9px] text-zinc-500">锚点 ID：{(c.conflict_point_ids as string[]).join(", ")}</p>
                ) : null}
              </li>
            ))}
            {matchedNarrative.length === 0
              ? fallbackNarrative.map((text, i) => (
                  <li
                    key={`fb-${i}`}
                    className="rounded-lg border border-zinc-700/80 bg-zinc-900/40 px-2 py-2 text-[11px] leading-relaxed text-zinc-200"
                  >
                    <span className="text-[9px] text-amber-600/90">启发式段落</span>
                    <p className="mt-1 whitespace-pre-wrap">{text}</p>
                  </li>
                ))
              : null}
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
  const { state, mergeSnapshot } = useLabStore();
  const snapshot = useMemo(() => state.snapshot ?? null, [state.snapshot]);
  const [pluginFocusId, setPluginFocusId] = useState<string | null>(null);
  const [debugTab, setDebugTab] = useState<DebugTabId>("tools");
  const [metaBranchFocus, setMetaBranchFocus] = useState<string | null>(null);
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
  const [hoverFactIds, setHoverFactIds] = useState<string[]>([]);
  const fullTraceRows = useMemo(() => {
    const md = (snapshot?.metadata || {}) as Record<string, unknown>;
    const li = (md.logic_introspection || {}) as Record<string, unknown>;
    const rows = li.full_trace;
    const base = Array.isArray(rows)
      ? rows.filter((x): x is Record<string, unknown> => Boolean(x && typeof x === "object"))
      : [];

    const fallbackRows: Record<string, unknown>[] = [];
    const rounds = Array.isArray(snapshot?.llm_rounds) ? snapshot.llm_rounds : [];
    for (const r of rounds) {
      if (!r || typeof r !== "object" || Array.isArray(r)) continue;
      const rr = r as Record<string, unknown>;
      const scenario = String(rr.scenario || "").toLowerCase();
      let stage = "LLM_ROUND";
      if (scenario.includes("first_observation")) stage = "FIRST_OBSERVATION";
      else if (scenario.includes("physics_audit")) stage = "ARBITRATION";
      else if (scenario.includes("final_verdict")) stage = "FINAL_VERDICT";
      const messages = Array.isArray(rr.messages)
        ? (rr.messages as Array<Record<string, unknown>>)
            .map((m) => ({ role: String(m?.role || ""), content: String(m?.content || "") }))
            .filter((m) => m.role && m.content)
        : [];
      const responseText = String(rr.response_text || "");
      if (!messages.length && !responseText.trim()) continue;
      fallbackRows.push({
        trace_id: String(rr.id || `round-${fallbackRows.length + 1}`),
        stage,
        at: typeof rr.at === "number" ? rr.at : Date.now(),
        messages,
        response_text: responseText,
        llm_meta: {
          ...(rr.meta && typeof rr.meta === "object" && !Array.isArray(rr.meta) ? (rr.meta as Record<string, unknown>) : {}),
          prompt_scenario: String(rr.scenario || ""),
          title_zh: String(rr.title_zh || ""),
          source: "snapshot.llm_rounds",
        },
      });
    }

    const hasFinalTrace = base.some((x) => String(x.stage || "").toUpperCase() === "FINAL_VERDICT");
    const llmPromptText = typeof snapshot?.llm_prompt === "string" ? snapshot.llm_prompt : "";
    const finalBody = typeof (snapshot?.final_verdict as Record<string, unknown> | undefined)?.body === "string"
      ? String((snapshot?.final_verdict as Record<string, unknown>).body || "")
      : "";
    const merged = [...base, ...fallbackRows];
    if (!hasFinalTrace && (llmPromptText.trim() || finalBody.trim())) {
      merged.push({
        trace_id: "fv-fallback-debug",
        stage: "FINAL_VERDICT",
        at: Date.now(),
        messages: [
          { role: "system", content: "FINAL_VERDICT_SYSTEM" },
          { role: "user", content: llmPromptText || "（无 llm_prompt）" },
        ],
        response_text: finalBody || "（无 final_verdict.body）",
        rendered_verdict_body: finalBody || "",
        llm_meta: {
          source: "debug_fallback_snapshot",
          note: "metadata.logic_introspection.full_trace 缺失 FINAL_VERDICT，已用快照补齐展示",
        },
      });
    }

    const seen = new Set<string>();
    return merged.filter((r) => {
      const key = `${String(r.trace_id || "")}|${String(r.stage || "")}|${String(r.at || "")}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [snapshot]);
  const physicalFactRows = useMemo(() => {
    const out: Array<{ factId: string; text: string }> = [];
    const tree = (snapshot?.final_verdict as Record<string, unknown> | undefined)?.assertion_tree as Record<string, unknown> | undefined;
    const nodes = Array.isArray(tree?.nodes) ? tree?.nodes : [];
    for (const n of nodes) {
      if (!n || typeof n !== "object" || Array.isArray(n)) continue;
      const r = n as Record<string, unknown>;
      const nodeType = String(r.node_type || "").toUpperCase();
      if (nodeType !== "FACT") continue;
      const factId = String(r.node_id || "").trim();
      const text = String(r.text || "").trim();
      if (factId) out.push({ factId, text });
    }
    return out;
  }, [snapshot?.final_verdict]);

  const silentArbiterHistory = useMemo(
    () => (snapshot ? collectSilentArbiterHistory(snapshot as LabSnapshot) : []),
    [snapshot],
  );
  const physicsAutonomyLog = useMemo(
    () => (snapshot ? collectPhysicsAutonomyLog(snapshot as LabSnapshot) : []),
    [snapshot],
  );
  const arbiterAuditEntries = useMemo(
    () => (snapshot ? collectArbitrationAuditFeed(snapshot as LabSnapshot) : []),
    [snapshot],
  );
  const [arbiterAuditEpoch, setArbiterAuditEpoch] = useState(0);
  const arbiterAuditLenRef = useRef<number | null>(null);
  useEffect(() => {
    const n = arbiterAuditEntries.length;
    if (arbiterAuditLenRef.current === null) {
      arbiterAuditLenRef.current = n;
      return;
    }
    if (n > arbiterAuditLenRef.current) {
      arbiterAuditLenRef.current = n;
      setArbiterAuditEpoch((e) => e + 1);
    }
  }, [arbiterAuditEntries.length]);

  const consultationIdForAudit = useMemo(() => {
    const hub = snapshot?.interaction_hub as Record<string, unknown> | undefined;
    const raw = hub?.consultation_id ?? snapshot?.active_session_id;
    const n = typeof raw === "number" ? raw : Number(raw || 0);
    return Number.isFinite(n) && n > 0 ? n : null;
  }, [snapshot?.active_session_id, snapshot?.interaction_hub]);

  const handleArbitrationOverrule = useCallback(
    async (auditId: string) => {
      const snap = state.snapshot;
      if (!snap) throw new Error("无实验室快照，无法否决。");
      const md = { ...(snap.metadata || {}) } as Record<string, unknown>;
      const valLayer = md.verdict_anchor_layer;
      let assertionTree: Record<string, unknown> = {};
      if (typeof valLayer === "object" && valLayer !== null) {
        const va = valLayer as Record<string, unknown>;
        const at0 = va.assertion_tree;
        if (at0 && typeof at0 === "object" && !Array.isArray(at0)) {
          assertionTree = at0 as Record<string, unknown>;
        }
      }
      if (!Array.isArray(assertionTree.nodes)) {
        const fv = snap.final_verdict as Record<string, unknown> | undefined;
        const at1 = fv?.assertion_tree;
        if (at1 && typeof at1 === "object" && !Array.isArray(at1)) {
          assertionTree = at1 as Record<string, unknown>;
        }
      }
      const feed = collectArbitrationAuditFeed(snap as LabSnapshot);
      const physMeta = (snap.physics_tensor as Record<string, unknown> | undefined)?.meta as
        | Record<string, unknown>
        | undefined;
      const res = await fetch("/api/v1/brain/arbitration-overrule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          audit_id: auditId,
          consultation_id: consultationIdForAudit ?? undefined,
          assertion_tree: assertionTree,
          metadata: md,
          arbitration_audit_feed: feed,
          physics_meta: physMeta || {},
        }),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `HTTP ${res.status}`);
      }
      const data = (await res.json()) as {
        metadata?: Record<string, unknown>;
        assertion_tree?: Record<string, unknown>;
        physics_meta_patch?: Record<string, unknown>;
      };
      const patMd = data.metadata || {};
      const nextMeta = { ...md, ...patMd };
      const vacRaw = nextMeta.verdict_anchor_layer;
      const atree = (data.assertion_tree || {}) as Record<string, unknown>;
      if (typeof vacRaw === "object" && vacRaw !== null) {
        nextMeta.verdict_anchor_layer = { ...(vacRaw as Record<string, unknown>), assertion_tree: atree };
      } else {
        nextMeta.verdict_anchor_layer = { assertion_tree: atree };
      }
      const prevPt = (snap.physics_tensor || {}) as Record<string, unknown>;
      const prevInner = (prevPt.meta || {}) as Record<string, unknown>;
      const patch = (data.physics_meta_patch || {}) as Record<string, unknown>;
      const nextInner = { ...prevInner, ...patch };
      mergeSnapshot({ metadata: nextMeta, physics_tensor: { ...prevPt, meta: nextInner } });
      window.dispatchEvent(new CustomEvent("qiazhi:verdict-flow-conflict"));
    },
    [consultationIdForAudit, mergeSnapshot, state.snapshot],
  );

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
          <DebugTabs active={debugTab} onChange={setDebugTab} />
          {/* V13.09: Kill the tabs，统一纵向审计流 */}
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
                    <article className="max-h-[min(52dvh,560px)] min-w-0 max-w-full overflow-x-hidden overflow-y-auto whitespace-pre-wrap break-words text-sm leading-relaxed text-zinc-100 [overflow-wrap:anywhere]">
                      {verdictBody}
                    </article>
                  ) : llmPrompt ? (
                    <article className="max-h-[min(40dvh,400px)] min-w-0 max-w-full overflow-x-hidden overflow-y-auto whitespace-pre-wrap break-words text-sm leading-relaxed text-zinc-300 [overflow-wrap:anywhere]">
                      {llmPrompt}
                    </article>
                  ) : (
                    <p className="text-sm text-zinc-500">暂无终判正文；完成终判或首观后将显示于此。</p>
                  )}
                </div>
              </SemanticAccordion>

              <SemanticAccordion
                title="LLM 裁决透明化（V12.95）"
                subtitle="自动裁决审计：Prompt / 原始回复 / 物理证据上下文；条目写入 BrainHtnSnapshot.arbitration_logs 并镜像到 meta"
                defaultOpen={false}
              >
                <ArbiterAuditPanel
                  entries={arbiterAuditEntries}
                  silentHistoryRows={silentArbiterHistory}
                  feedEpoch={arbiterAuditEpoch}
                  consultationId={consultationIdForAudit}
                  onOverrule={handleArbitrationOverrule}
                />
              </SemanticAccordion>
            </div>
          ) : null}

          {debugTab === "bazi_meta" ? (
            <DebugBaziMetadataPanel snapshot={snapshot} focusBranch={metaBranchFocus} onBranchSelect={setMetaBranchFocus} />
          ) : null}

          {debugTab === "physics" ? (
            <div className="space-y-4" role="tabpanel" aria-label="物理与博弈">
              <SemanticAccordion title="物理层 · 事实（Fact_ID）" subtitle="悬停 LogicPulseStream 自动联动高亮" defaultOpen={false}>
                {physicalFactRows.length === 0 ? (
                  <p className="text-xs text-zinc-500">暂无 FACT 节点。</p>
                ) : (
                  <ul className="space-y-1 text-[11px]">
                    {physicalFactRows.map((row) => {
                      const on = hoverFactIds.includes(row.factId);
                      return (
                        <li
                          key={row.factId}
                          className={`rounded border px-2 py-1 ${on ? "border-amber-500/70 bg-amber-950/25 text-amber-100" : "border-zinc-800/70 bg-black/25 text-zinc-300"}`}
                        >
                          <span className="font-mono text-[10px]">{row.factId}</span>
                          <span className="mx-2 text-zinc-600">·</span>
                          <span>{row.text || "—"}</span>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </SemanticAccordion>
              <SemanticAccordion title="分层轨迹审计（L0 / Inbox）" subtitle="physics_trace 与 Inbox v1" defaultOpen={false}>
                <LayerAuditTrails physics={physics} />
              </SemanticAccordion>
              <SemanticAccordion
                title="物理自治记录（V13.03）"
                subtitle="锚点偏差 SILENT_REJECT、插件权力否决、二段跳张力抹零"
                defaultOpen={false}
              >
                <div className="space-y-2 text-xs text-zinc-300">
                  {physicsAutonomyLog.length === 0 ? (
                    <p className="text-zinc-500">暂无自治记录（尚未触发毙稿或强收）。</p>
                  ) : (
                    <ol className="list-decimal space-y-3 pl-4">
                      {physicsAutonomyLog.map((row, i) => {
                        const human = physicsAutonomyHumanLine(row);
                        return (
                        <li key={i} className="min-w-0 break-words">
                          <span className="font-semibold text-amber-200/95">{String(row.kind ?? "—")}</span>
                          {row.reason != null ? <span className="text-zinc-400"> · {String(row.reason)}</span> : null}
                          {row.plugin_id != null ? (
                            <span className="font-mono text-[10px] text-cyan-200/85"> · {String(row.plugin_id)}</span>
                          ) : null}
                          {human ? (
                            <p className="mt-1 rounded border border-emerald-900/40 bg-emerald-950/25 px-2 py-1.5 text-[11px] leading-snug text-emerald-100/95">
                              {human}
                            </p>
                          ) : null}
                          <pre className="mt-1 max-h-36 overflow-auto rounded border border-zinc-800/80 bg-zinc-950/80 p-2 font-mono text-[10px] leading-snug text-zinc-400">
                            {safeJson(row, 0)}
                          </pre>
                        </li>
                        );
                      })}
                    </ol>
                  )}
                </div>
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
              <div className="rounded-lg border border-cyan-900/35 bg-cyan-950/10 p-2 text-[11px] text-cyan-100/85">
                全量 LLM 对话流：每条均可查看标题（议题）、完整 Prompt、完整回复；终判支持原始/渲染双视图。
              </div>
              <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/45 p-2">
                <LogicPulseStream rows={fullTraceRows} onHoverFacts={setHoverFactIds} />
              </div>
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
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
