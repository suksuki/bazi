"use client";

import { useEffect, useMemo, useState } from "react";
import { TopologyMapV1 } from "@/components/TopologyMapV1";
import {
  DecisionTimeline,
  NarrativeProvenancePanel,
  PluginCollisionHub,
  SanheStructurePanel,
  SemanticAccordion,
  StateMonitor,
  extractSanheClusters,
} from "@/features/decision-cockpit";
import { AuditChamberPanel } from "@/features/admin/AuditChamberPanel";
import { skillIdForConflictPoint } from "@/features/decision-inbox/skillInference";
import { VerdictCertificate } from "@/features/stream-board/components/VerdictCertificate";
import { API_BASE } from "@/features/stream-board/constants";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import type { LabLlmRoundSnapshot } from "@/features/stream-board/stores/LabSessionContext";
import { buildCausalSovereigntySlice } from "@/features/stream-board/utils/causalSovereigntyFromSnapshot";
import type { ConflictPoint, TimelineSnapshot } from "@/types/bazi";

function safeJson(obj: unknown, space = 2): string {
  try {
    return JSON.stringify(obj, null, space);
  } catch {
    return String(obj);
  }
}

type DebugTabId = "overview" | "chain" | "topology" | "trace" | "court" | "llm" | "raw";

const DEBUG_TABS: { id: DebugTabId; label: string; short: string }[] = [
  { id: "overview", label: "概览", short: "会话 · 健康 · 增量" },
  { id: "chain", label: "推演链", short: "十神 · 时序 · 插件 · 判语 · 基线" },
  { id: "topology", label: "拓扑结构", short: "拓扑图 · 三合" },
  { id: "trace", label: "交互追踪", short: "Hub · 因果链 · 演化" },
  { id: "court", label: "逻辑检察院", short: "审计台全功能" },
  { id: "llm", label: "LLM 交互", short: "提示词与模型返回" },
  { id: "raw", label: "原始数据", short: "种子 · JSON" },
];

function LlmRoundPanel(props: { title: string; subtitle: string; round: LabLlmRoundSnapshot | null | undefined }) {
  const { title, subtitle, round } = props;
  if (!round || (!round.messages?.length && !(round.response_text || "").trim())) {
    return (
      <SemanticAccordion title={title} subtitle={subtitle}>
        <p className="text-xs text-zinc-500">暂无记录（需完成排盘/审计/终判且后端已返回该段 transcript）。</p>
      </SemanticAccordion>
    );
  }
  return (
    <SemanticAccordion title={title} subtitle={subtitle}>
      <div className="space-y-3 text-xs">
        {round.repair_mode ? (
          <p className="font-mono text-[10px] text-amber-200/90">repair_mode: {String(round.repair_mode)}</p>
        ) : null}
        {round.meta && Object.keys(round.meta).length > 0 ? (
          <section>
            <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">遥测 meta</p>
            <pre className="mt-1 max-h-32 overflow-auto rounded-lg border border-zinc-800 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-400">
              {safeJson(round.meta)}
            </pre>
          </section>
        ) : null}
        <section>
          <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">请求 messages（完整 role/content）</p>
          <pre className="mt-1 max-h-[min(40dvh,360px)] overflow-auto rounded-lg border border-zinc-800 bg-zinc-950/80 p-2 font-mono text-[10px] leading-relaxed text-zinc-300">
            {safeJson(round.messages ?? [])}
          </pre>
        </section>
        <section>
          <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">模型返回正文</p>
          <pre className="mt-1 max-h-[min(40dvh,360px)] overflow-auto whitespace-pre-wrap rounded-lg border border-emerald-900/40 bg-zinc-950/80 p-2 font-mono text-[10px] text-emerald-100/90">
            {(round.response_text || "").trim() || "—"}
          </pre>
        </section>
      </div>
    </SemanticAccordion>
  );
}

const tabBtnBase =
  "rounded-lg border px-3 py-2 text-left text-xs transition-colors sm:min-w-[7.5rem] sm:text-center";
const tabBtnIdle = "border-transparent bg-zinc-900/40 text-zinc-400 hover:border-zinc-700 hover:bg-zinc-800/60";
const tabBtnActive = "border-amber-500/50 bg-amber-500/10 text-amber-100";

export function DebugView() {
  const { state } = useLabStore();
  const snapshot = useMemo(() => state.snapshot ?? null, [state.snapshot]);
  const finalizationReport = state.finalizationReport;
  const metaFinal = (snapshot?.metadata as Record<string, unknown> | undefined)?.finalization as
    | { hash?: string; committed_at?: number }
    | undefined;
  const updates = state.updates;
  const lastSeed = state.lastSeedPayload;

  const [evoGeneStats, setEvoGeneStats] = useState<{ n: number; levelPct: number } | null>(null);
  const [topologyFocusDetail, setTopologyFocusDetail] = useState<string | null>(null);
  const [debugTab, setDebugTab] = useState<DebugTabId>("overview");

  /** 仅在「是否有快照 + 会话标识」变化时拉取演化热力图，避免依赖不稳定的 snapshot 引用又满足 exhaustive-deps */
  const evolutionFetchKey = useMemo(() => {
    if (!snapshot) return "";
    const ts = snapshot.ts != null ? String(snapshot.ts) : "";
    const sid = String((snapshot as { active_session_id?: unknown }).active_session_id ?? "");
    return `${ts}\0${sid}`;
  }, [snapshot]);

  useEffect(() => {
    if (!evolutionFetchKey) {
      setEvoGeneStats(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        if (!API_BASE) {
          if (!cancelled) setEvoGeneStats(null);
          return;
        }
        const r = await fetch(`${API_BASE}/api/v1/evolution/state`);
        if (!r.ok || cancelled) return;
        const data = (await r.json()) as { heatmap?: Array<{ maturity?: number }> };
        const hm = Array.isArray(data.heatmap) ? data.heatmap : [];
        const n = hm.length;
        const levelPct =
          n > 0
            ? Math.round(
                (hm.reduce((s, row) => s + Math.min(1, Math.max(0, Number(row?.maturity ?? 0))), 0) / n) * 100,
              )
            : 0;
        if (!cancelled) setEvoGeneStats({ n, levelPct });
      } catch {
        if (!cancelled) setEvoGeneStats(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [evolutionFetchKey]);

  const causalSovereigntyForCert = useMemo(
    () => buildCausalSovereigntySlice(snapshot as Record<string, unknown> | null | undefined),
    [snapshot],
  );

  const hub = snapshot?.interaction_hub;
  const physics = snapshot?.physics_tensor as Record<string, unknown> | undefined;
  const meta = (physics?.meta as Record<string, unknown> | undefined) || {};
  const fv = snapshot?.final_verdict;
  const ld = snapshot?.logic_diff;
  const baseline = snapshot?.baseline_snapshot;

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
      const impactAbs = `[Abs 修正值: ${absStr}${checked ? " [WILL_INFUSED]" : ""}]`;
      rows.push(
        `[物理匹配: ${detail}] → [Skill: ${sid}] → [Decision ID: ${did}] → [用户状态: ${checked ? "已勾选" : "未勾选"}] → ${impactAbs}`,
      );
    });

    const pierceSem = meta.mangpai_pierce_semantics;
    if (Array.isArray(pierceSem)) {
      pierceSem.forEach((raw, j) => {
        const item = raw as { detail?: string; semantic_intensity?: number; skill_id?: string };
        const si = Number(item.semantic_intensity ?? 0);
        const detailStr = String(item.detail || "—");
        const pendingMatch = pending.find((c) => {
          const title = String((c as { title?: string }).title || "");
          return title && (detailStr.includes(title.slice(0, 4)) || title.includes(detailStr.slice(0, 4)));
        }) as { id?: string } | undefined;
        const did = pendingMatch?.id ? String(pendingMatch.id) : `pierce:${j}`;
        const pierceChecked =
          did.startsWith("physics:")
            ? [...decisionIds].some((id) => id.startsWith("llm-observe"))
            : decisionIds.has(did);
        const pierceImpact = `[Abs 修正值: ${absStr}${pierceChecked ? " [WILL_INFUSED]" : ""}]`;
        rows.push(
          `[物理匹配: 穿局 ${detailStr} · semantic_intensity=${Number.isFinite(si) ? si.toFixed(4) : "—"}] → [Skill: ${String(item.skill_id || "mp_pierce_01")}] → [Decision ID: ${did}] → [用户状态: ${pierceChecked ? "已勾选" : "未勾选"}] → ${pierceImpact}`,
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
    const physics = snapshot?.physics_tensor as Record<string, unknown> | undefined;
    const auditLogPhys = (physics?.audit_log as Record<string, unknown> | undefined) || {};
    const dimensionalShieldLogs = Array.isArray(auditLogPhys.dimensional_shield_logs)
      ? (auditLogPhys.dimensional_shield_logs as unknown[]).map((x) => String(x)).filter(Boolean)
      : [];

    const decisionIdSet = new Set(
      Array.isArray(snapshot?.decision_selection_ids)
        ? snapshot.decision_selection_ids.map((x) => String(x))
        : [],
    );
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
    dimensionalShieldLogs.forEach((line) => rows.push(line));
    const auditItems = Array.isArray(hub?.audit_items) ? hub.audit_items : [];
    auditItems.forEach((item) => {
      const action = String(item?.action ?? "");
      const step = String(item?.step ?? "");
      const blob = `${step} ${action}`;
      const skill = skillFromHubBlob(blob);
      const decision = extractDecisionId(blob);
      const resolved = /决策|decision|confirm|勾选|resolved|决议|同步因果/i.test(blob);
      const actionLabel = resolved ? "Decision Resolved" : `Audit (${step || "trace"})`;
      const willInfused =
        decision !== "—" && decisionIdSet.has(decision) ? " [WILL_INFUSED]" : "";
      rows.push(
        `[Triggered]: Skill ID (${skill}) -> [Action]: ${actionLabel} (${decision !== "—" ? `ID_${decision}` : "ID_—"}) -> [Impact]: Abs Modified (${impact})${willInfused}`,
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
        const willInfused =
          decision !== "—" && decisionIdSet.has(decision) ? " [WILL_INFUSED]" : "";
        rows.push(
          `[Triggered]: Skill ID (${skill}) -> [Action]: Hub log -> (${decision !== "—" ? `ID_${decision}` : "ID_—"}) -> [Impact]: Abs Modified (${impact})${willInfused}`,
        );
      }
    });

    if (rows.length === 0) {
      rows.push(
        `[Triggered]: Skill ID (—) -> [Action]: (empty hub audit) -> [Decision]: ID_— -> [Impact]: Abs Modified (${impact})`,
      );
    }
    return rows.slice(-24);
  }, [hub?.audit_items, hub?.result_logs, ld, snapshot?.decision_selection_ids, snapshot?.physics_tensor]);

  const sanheClusters = useMemo(() => extractSanheClusters(physics), [physics]);

  const topologyGraph = useMemo(() => {
    const fv = snapshot?.final_verdict as Record<string, unknown> | undefined;
    const g = fv?.topology_graph_v1;
    return g && typeof g === "object" ? (g as Record<string, unknown>) : {};
  }, [snapshot]);

  const timelineSnap = (snapshot?.timeline ?? null) as TimelineSnapshot | null;

  return (
    <div className="mx-auto min-h-dvh w-full max-w-6xl px-3 py-4 text-zinc-200">
      {state.isFinalized && finalizationReport?.hash ? (
        <VerdictCertificate
          hash={finalizationReport.hash}
          committedAt={finalizationReport.committedAt}
          logicDiff={ld}
          effectiveSkillIds={
            finalizationReport.effectiveSkillIds ??
            (snapshot?.metadata?.verdict_effective_skill_ids as string[] | undefined)
          }
          solidGhostRatio={
            (() => {
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
            })()
          }
          causalSovereignty={causalSovereigntyForCert ?? undefined}
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

      <div className="mb-3 border-b border-zinc-800 pb-3">
        <h1 className="text-base font-semibold">决策全景审计舱</h1>
        <p className="mt-0.5 text-xs text-zinc-500">
          按 TAB 分区浏览：概览 → 推演链 → 拓扑 → 追踪 → 检察院 → LLM 交互 → 原始数据。
        </p>
      </div>

      {!snapshot ? (
        <p className="text-sm text-zinc-500">暂无数据。请先在「实验室」完成排盘或推演。</p>
      ) : (
        <div className="space-y-4">
          <div className="sticky top-0 z-10 -mx-1 border-b border-zinc-800/90 bg-zinc-950/95 px-1 pb-2 backdrop-blur-sm">
            <div className="flex gap-1 overflow-x-auto pb-1 pt-0.5">
              {DEBUG_TABS.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setDebugTab(t.id)}
                  className={`${tabBtnBase} shrink-0 ${debugTab === t.id ? tabBtnActive : tabBtnIdle}`}
                >
                  <span className="block font-medium">{t.label}</span>
                  <span className="mt-0.5 hidden text-[10px] leading-tight text-zinc-500 sm:block">{t.short}</span>
                </button>
              ))}
            </div>
          </div>

          {debugTab === "overview" ? (
            <div className="space-y-4">
              <SemanticAccordion title="会话与健康读数" subtitle="会话标识、咨询单号、快照时间、服务健康与全局熵">
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
              </SemanticAccordion>
              {evoGeneStats ? (
                <div className="rounded-xl border border-emerald-800/40 bg-emerald-950/25 p-3 text-xs text-emerald-100/90">
                  <p className="text-[10px] font-medium uppercase tracking-wide text-emerald-400/90">演化基因（摘要）</p>
                  <p className="mt-1 font-mono text-[11px]">
                    基因数 {evoGeneStats.n} · 成熟度均值约 {evoGeneStats.levelPct}%（详情见「交互追踪」）
                  </p>
                </div>
              ) : null}
              {updates.length > 0 ? (
                <SemanticAccordion title="最近因果更新" subtitle="最多保留 5 条">
                  <ul className="space-y-2 text-xs">
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
                </SemanticAccordion>
              ) : (
                <p className="rounded-lg border border-dashed border-zinc-700/80 bg-zinc-900/30 px-3 py-2 text-xs text-zinc-500">
                  暂无因果增量记录。
                </p>
              )}
            </div>
          ) : null}

          {debugTab === "chain" ? (
            <div className="space-y-4">
              <SemanticAccordion title="十神监控与岁运轨迹" subtitle="四柱激活、大运流年、|Abs| Sparkline 与变动归因">
                <StateMonitor metadata={snapshot.metadata as Record<string, unknown>} timeline={timelineSnap} physicsTensor={physics} />
              </SemanticAccordion>
              <div className="grid gap-3 lg:grid-cols-2">
                <SemanticAccordion title="决策时序轴" subtitle="物理层 → 插件 → 路由 → 终审的装配顺序">
                  <DecisionTimeline snapshot={snapshot as Record<string, unknown>} />
                </SemanticAccordion>
                <SemanticAccordion title="插件碰撞审计" subtitle="匹配插件、置信度、命中理由与 CausalRouter 摘要">
                  <PluginCollisionHub physicsTensor={physics} />
                </SemanticAccordion>
              </div>
              <SemanticAccordion title="判语血统" subtitle="系统证据链与 LLM 终审片段">
                <NarrativeProvenancePanel snapshot={snapshot as Record<string, unknown>} llmPrompt={snapshot.llm_prompt as string | undefined} />
              </SemanticAccordion>
              <SemanticAccordion title="误差与基线锚点" subtitle="logic_diff 与 baseline_snapshot">
                <div className="space-y-3">
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
                </div>
              </SemanticAccordion>
            </div>
          ) : null}

          {debugTab === "topology" ? (
            <div className="space-y-4">
              <SemanticAccordion title="拓扑图与三合结构" subtitle="点击拓扑金边联动下方三合簇面板">
                <div className="grid gap-3 lg:grid-cols-2">
                  <div className="min-w-0">
                    <TopologyMapV1
                      graph={topologyGraph}
                      activeEdgeKey={topologyFocusDetail}
                      onActivateSanheEdge={(e) => {
                        const d = String(e.detail || "").trim();
                        setTopologyFocusDetail(d || `${String(e.from)}→${String(e.to)}`);
                        requestAnimationFrame(() => {
                          document.getElementById("sanhe-cluster-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
                        });
                      }}
                    />
                  </div>
                  <SanheStructurePanel clusters={sanheClusters} activeDetail={topologyFocusDetail} />
                </div>
              </SemanticAccordion>
            </div>
          ) : null}

          {debugTab === "trace" ? (
            <div className="space-y-4">
              <SemanticAccordion title="交互中枢与因果追踪（文本）" subtitle="Hub 审计项、L1 冲突链、演化基因状态">
                <div className="space-y-4 text-xs">
                  <div>
                    <p className="text-[10px] uppercase tracking-wide text-zinc-500">interaction_hub 计数</p>
                    <p className="mt-1 text-[11px] text-zinc-400">
                      result_logs {Array.isArray(hub?.result_logs) ? hub.result_logs.length : 0} · audit_items{" "}
                      {Array.isArray(hub?.audit_items) ? hub.audit_items.length : 0} · pending_cards{" "}
                      {Array.isArray(hub?.pending_cards) ? hub.pending_cards.length : 0}
                    </p>
                    {fv?.version_id ? (
                      <p className="mt-2 font-mono text-[10px] text-zinc-500">final_verdict.version_id: {String(fv.version_id)}</p>
                    ) : null}
                  </div>
                  {Array.isArray(hub?.audit_items) && hub.audit_items.length > 0 ? (
                    <ul className="max-h-48 space-y-2 overflow-auto">
                      {hub.audit_items.map((item, idx) => (
                        <li key={String(item?.id ?? idx)} className="rounded border border-zinc-800/60 bg-zinc-950/50 px-2 py-1.5">
                          <p className="font-mono text-[10px] text-amber-200/90">
                            {String(item?.role ?? "—")} · {String(item?.step ?? "—")}
                          </p>
                          <p className="mt-0.5 text-[11px] text-zinc-300">{String(item?.action ?? "—")}</p>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  {evoGeneStats ? (
                    <p className="rounded-lg border border-emerald-800/50 bg-emerald-950/30 px-2 py-1.5 font-mono text-[10px] text-emerald-100/95">
                      [EVOLUTION_STATUS]: 基因 {evoGeneStats.n} · 成熟度 {evoGeneStats.levelPct}%
                    </p>
                  ) : null}
                  <ul className="max-h-48 space-y-2 overflow-auto">
                    {causalTraceRows.map((line, idx) => (
                      <li
                        key={`${idx}-${line.slice(0, 24)}`}
                        className="rounded border border-cyan-900/40 bg-zinc-950/70 px-2 py-1.5 font-mono text-[10px] text-cyan-100/90"
                      >
                        {line}
                      </li>
                    ))}
                  </ul>
                  <ul className="max-h-48 space-y-2 overflow-auto">
                    {hubCausalTraceLines.map((line, idx) => (
                      <li
                        key={`hub-ct-${idx}-${line.slice(0, 20)}`}
                        className="rounded border border-fuchsia-900/40 bg-zinc-950/75 px-2 py-1.5 font-mono text-[10px] text-fuchsia-100/90"
                      >
                        {line}
                      </li>
                    ))}
                  </ul>
                </div>
              </SemanticAccordion>
            </div>
          ) : null}

          {debugTab === "court" ? (
            <div className="space-y-4">
              <SemanticAccordion title="逻辑检察院（审计台）" subtitle="四柱诊断、证据瀑布、门控与对质">
                <div className="max-h-[min(90dvh,920px)] overflow-y-auto pr-1">
                  <AuditChamberPanel />
                </div>
              </SemanticAccordion>
            </div>
          ) : null}

          {debugTab === "llm" ? (
            <div className="space-y-4">
              <p className="text-xs text-zinc-500">
                下列为当前实验室快照内已持久化的 LLM 往返：首观（排盘）、物理结构化审计、终审。字段来自后端 API 与快照合并逻辑。
              </p>
              <LlmRoundPanel
                title="首观 LLM（analyze-seed / 首条判词来源）"
                subtitle="与 llm_prompt 同次的完整 messages"
                round={snapshot.first_observation_llm}
              />
              <LlmRoundPanel
                title="物理审计 LLM（audit-physics-with-llm）"
                subtitle="含 repair_mode 与原始 JSON 诊断"
                round={snapshot.physics_auditor_llm}
              />
              <SemanticAccordion title="终审 LLM（final-verdict）" subtitle="终判 Markdown 与模型原始 JSON 包裹">
                {fv &&
                ((fv.llm_request_messages && fv.llm_request_messages.length > 0) ||
                  (fv.llm_raw_response && fv.llm_raw_response.trim())) ? (
                  <div className="space-y-3 text-xs">
                    {fv.llm_meta && Object.keys(fv.llm_meta).length > 0 ? (
                      <section>
                        <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">遥测 meta</p>
                        <pre className="mt-1 max-h-32 overflow-auto rounded-lg border border-zinc-800 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-400">
                          {safeJson(fv.llm_meta)}
                        </pre>
                      </section>
                    ) : null}
                    <section>
                      <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">请求 messages</p>
                      <pre className="mt-1 max-h-[min(40dvh,360px)] overflow-auto rounded-lg border border-zinc-800 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
                        {safeJson(fv.llm_request_messages ?? [])}
                      </pre>
                    </section>
                    <section>
                      <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">模型原始返回（多为 JSON）</p>
                      <pre className="mt-1 max-h-[min(40dvh,360px)] overflow-auto whitespace-pre-wrap rounded-lg border border-violet-900/40 bg-zinc-950/80 p-2 font-mono text-[10px] text-violet-100/90">
                        {(fv.llm_raw_response || "").trim() || "—"}
                      </pre>
                    </section>
                    <section>
                      <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">解析后的判词正文（final_verdict.body）</p>
                      <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-900/40 p-2 text-[11px] text-zinc-300">
                        {(fv.body || "").trim() || "—"}
                      </pre>
                    </section>
                  </div>
                ) : (
                  <p className="text-xs text-zinc-500">暂无终审 LLM 记录（需发起全局裁决且接口返回 llm_request_messages / llm_raw_response）。</p>
                )}
              </SemanticAccordion>
            </div>
          ) : null}

          {debugTab === "raw" ? (
            <div className="space-y-4">
              {lastSeed ? (
                <SemanticAccordion title="最后种子 The Seed" subtitle="最近一次 analyze 请求体">
                  <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded-xl border border-zinc-800 bg-zinc-900/40 p-3 font-mono text-[11px] text-zinc-400">
                    {safeJson(lastSeed)}
                  </pre>
                </SemanticAccordion>
              ) : null}
              <SemanticAccordion title="原始张量（完整 JSON）" subtitle="展开后可查看或自行复制">
                <section className="rounded-xl border border-amber-900/40 bg-zinc-950/80 p-3">
                  <pre className="max-h-[min(70dvh,720px)] overflow-auto text-[11px] leading-relaxed text-zinc-400">
                    {safeJson(snapshot)}
                  </pre>
                </section>
              </SemanticAccordion>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
