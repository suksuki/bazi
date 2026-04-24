"use client";

import { t, translateTerm, translateTermList, type AppLanguage } from "@/lib/i18n";

/**
 * V17.23 — V17_TracePanel
 *
 * 因果链路调试面板（原 OraclePage 第 365–505 行）。
 * Props 由 useOracleSession 直接传入，完全无状态。
 */

interface TracePanelProps {
  collapsed: boolean;
  onToggle: () => void;
  surfaceMode?: "sidebar" | "tab";
  contentMode?: "full" | "insight_only" | "debug_only";
  showChrome?: boolean;
  focusedDecisionId?: string;
  llmMeta: Record<string, unknown>;
  llmLifecyclePhase:
    | "idle"
    | "connecting"
    | "awaiting_first_token"
    | "streaming"
    | "completed"
    | "failed"
    | "closed_without_output";
  llmStatusText: string;
  llmStatusDetail: string;
  modelLabel: string;
  connectTickMs: number;
  lastHeartbeatStep: string;
  heartbeatHistory: Array<{ stepPosition: string; idleSec: number; timestamp?: string }>;
  streamClosed: boolean;
  fullTrace: Record<string, unknown> | undefined;
  llmAuditSnapshot: unknown;
  latestNarrator: { payload?: Record<string, unknown> } | undefined;
  traceHits: unknown[];
  traceFacts: unknown[];
  birthTimeISO: string;
  natalGender: string | undefined;
  natalCalendar: string | undefined;
  selectedLuckYear: number;
  streamEndpoint: string | null;
  streamBody: Record<string, unknown> | null;
  streamQuery: { will_proxy: string; birth_time: string; gender: string; flow_year: string };
  lang?: AppLanguage;
  physicsSnapshot?: {
    payload?: {
      causal_anchor?: unknown;
      physics_fingerprint?: unknown;
      ten_gods_base_l0?: Record<string, number>;
      ten_gods_decomposition_l0?: Record<
        string,
        {
          manifest?: number;
          root?: number;
          momentum?: number;
          momentum_month_order?: number;
          momentum_stage?: number;
          momentum_stage_lu?: number;
          momentum_stage_blade?: number;
          momentum_stage_general?: number;
          momentum_structure?: number;
          momentum_auxiliary?: number;
          momentum_other?: number;
          hidden?: number;
          total?: number;
        }
      >;
      ten_gods_runtime?: Record<string, number>;
      ten_gods_narrative?: Record<string, number>;
      deity_scores?: Record<string, number>;
      ten_gods_absolute_intensity?: Record<string, number>;
      total_energy_index?: number;
      ten_gods?: unknown[];
      ten_gods_ledger?: Record<
        string,
        Array<{
          step: string;
          val: number;
          delta?: number;
          reason: string;
          source?: string;
          highlight_type?: string;
          ratio_applied?: number;
          original_value?: number;
          final_value?: number;
          visible_ratio_change?: boolean;
        }>
      >;
      flow_topology?: Array<{ from_el: string; to_el: string; current: number; rel: string; resistance?: number; stress?: number }>;
      physics_tension?: number;
      four_pillars?: Record<string, unknown>;
      luck_pillar?: unknown;
      flow_pillar?: unknown;
      flow_year?: unknown;
      plugins?: {
        hits?: unknown[];
        rows?: Array<Record<string, unknown>>;
        statuses?: Array<Record<string, unknown>>;
        claims?: Array<Record<string, unknown>>;
        conflicts?: Array<Record<string, unknown>>;
        conflict_resolutions?: Array<Record<string, unknown>>;
        knowledge_snapshot?: Record<string, unknown>;
        brain_action_queue?: Array<Record<string, unknown>>;
      };
      manual_inbox?: Array<Record<string, unknown>>;
      auto_decisions?: Array<Record<string, unknown>>;
      manual_decisions?: Array<Record<string, unknown>>;
      auto_resolutions?: Array<Record<string, unknown>>;
      llm_arbitration_context?: Array<Record<string, unknown>>;
      debug_trace?: {
        facts?: unknown[];
      };
    };
  };
}

function traceImpactText(row: Record<string, unknown>): string {
  const impact =
    row.physical_impact && typeof row.physical_impact === "object"
      ? (row.physical_impact as Record<string, unknown>)
      : {};
  const ratio = Math.abs(Number(impact.impact_ratio || 0));
  const level = Number(impact.intensity_level || 0);
  if (ratio > 0) return `位移 ${(ratio * 100).toFixed(1)}% · L${level || "?"}`;
  if (level > 0) return `烈度 L${level}`;
  return "诊断参考";
}

function tracePromptPreview(row: Record<string, unknown>): string {
  const impact =
    row.physical_impact && typeof row.physical_impact === "object"
      ? (row.physical_impact as Record<string, unknown>)
      : {};
  const target = String(row.target_god || impact.target_god || "未定目标").trim();
  const source = String(row.source || row.plugin_id || "unknown").trim();
  const ratio = Math.abs(Number(impact.impact_ratio || 0));
  const movement = ratio > 0 ? `${(ratio * 100).toFixed(1)}% 位移` : "诊断引用";
  return `${target} · ${movement} · ${source}`;
}

function traceBiasPairs(value: unknown): Array<{ name: string; score: number }> {
  return Object.entries((value && typeof value === "object" ? (value as Record<string, unknown>) : {}))
    .map(([name, raw]) => ({ name: String(name || "").trim(), score: Number(raw || 0) }))
    .filter((row) => row.name && Number.isFinite(row.score) && row.score > 0)
    .sort((a, b) => b.score - a.score);
}

function traceBiasSummary(row: Record<string, unknown>): { useText: string; tabooText: string } | null {
  const impact =
    row.physical_impact && typeof row.physical_impact === "object"
      ? (row.physical_impact as Record<string, unknown>)
      : {};
  const bias =
    impact.god_ring_bias && typeof impact.god_ring_bias === "object"
      ? (impact.god_ring_bias as Record<string, unknown>)
      : {};
  const usePairs = traceBiasPairs(bias.use_bias).slice(0, 3);
  const tabooPairs = traceBiasPairs(bias.taboo_bias).slice(0, 3);
  if (!usePairs.length && !tabooPairs.length) return null;
  return {
    useText: usePairs.map((item) => `${item.name} +${item.score.toFixed(2)}`).join(" · "),
    tabooText: tabooPairs.map((item) => `${item.name} +${item.score.toFixed(2)}`).join(" · "),
  };
}

function traceArbitrationChain(row: Record<string, unknown>, fallbackMode: "手动" | "自动" | "LLM"): string {
  const explicit = String(row.arbitration_trace || "").trim();
  if (explicit) return explicit;
  const impact =
    row.physical_impact && typeof row.physical_impact === "object"
      ? (row.physical_impact as Record<string, unknown>)
      : {};
  const source = String(row.source_label || row.source || row.plugin_id || "unknown").trim();
  const level = Number(impact.intensity_level || 0);
  return `${source} -> L${level > 0 ? level : "?"} -> ${fallbackMode}`;
}

function scoreEntries(map: Record<string, number> | undefined): Array<{ name: string; score: number }> {
  return Object.entries(map || {})
    .map(([name, score]) => ({ name: String(name), score: Number(score || 0) }))
    .filter((row) => row.name && Number.isFinite(row.score))
    .sort((a, b) => b.score - a.score);
}

function conflictTone(severity: string): string {
  const value = String(severity || "").trim().toUpperCase();
  if (value === "P1") return "text-rose-200 border-rose-500/25 bg-rose-950/20";
  if (value === "P2") return "text-amber-200 border-amber-500/25 bg-amber-950/20";
  return "text-cyan-200 border-cyan-500/25 bg-cyan-950/20";
}

function brainStepTone(kind: string): string {
  const value = String(kind || "").trim().toLowerCase();
  if (value.includes("manual") || value === "user") return "text-violet-200";
  if (value.includes("system")) return "text-amber-200";
  if (value.includes("llm")) return "text-cyan-200";
  return "text-zinc-300";
}

function compactProjection(projection: unknown): string {
  if (!projection || typeof projection !== "object") return "";
  const entries = Object.entries(projection as Record<string, unknown>)
    .map(([key, value]) => [key, Number(value || 0)] as const)
    .filter(([, value]) => Number.isFinite(value) && value > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);
  return entries.map(([key, value]) => `${key} ${Math.round(value * 100)}%`).join(" · ");
}

export function V17_TracePanel({
  collapsed,
  onToggle,
  surfaceMode = "sidebar",
  contentMode = "full",
  showChrome = true,
  focusedDecisionId,
  llmMeta,
  llmLifecyclePhase,
  llmStatusText,
  llmStatusDetail,
  modelLabel,
  connectTickMs,
  lastHeartbeatStep,
  heartbeatHistory,
  streamClosed,
  fullTrace,
  llmAuditSnapshot,
  latestNarrator,
  traceHits,
  traceFacts,
  birthTimeISO,
  natalGender,
  natalCalendar,
  selectedLuckYear,
  streamEndpoint,
  streamBody,
  streamQuery,
  physicsSnapshot,
  lang = "zh",
}: TracePanelProps) {
  const ui = (zh: string, en: string, ko: string) =>
    lang === "en" ? en : lang === "ko" ? ko : zh;
  const compactInsightMode = contentMode === "insight_only";
  const showInsightSections = contentMode !== "debug_only";
  const showDebugSections = contentMode !== "insight_only";
  const physicsPayload = (physicsSnapshot?.payload ?? {}) as Record<string, unknown>;
  const auditPayload =
    llmAuditSnapshot && typeof llmAuditSnapshot === "object"
      ? (((llmAuditSnapshot as { payload?: Record<string, unknown> }).payload ?? {}) as Record<string, unknown>)
      : {};
  const baseScoreMap = physicsSnapshot?.payload?.ten_gods_base_l0 || {};
  const decompositionScoreMap = physicsSnapshot?.payload?.ten_gods_decomposition_l0 || {};
  const runtimeScoreMap =
    physicsSnapshot?.payload?.ten_gods_runtime ||
    physicsSnapshot?.payload?.ten_gods_absolute_intensity ||
    physicsSnapshot?.payload?.deity_scores ||
    {};
  const narrativeScoreMap = physicsSnapshot?.payload?.ten_gods_narrative || {};
  const ledgerRaw = physicsSnapshot?.payload?.ten_gods_ledger || {};
  const deityScores = Object.entries(runtimeScoreMap)
    .map(([name, score]) => {
      const history = ledgerRaw[name] || [];
      const currentVal = Number(score || 0);
      // V17.36: 相比上一次操作的变化 (Ledger 倒数第二条)
      const prevVal = history.length > 1 ? history[history.length - 2].val : (history.length > 0 ? history[0].val : currentVal);
      const deltaLast = currentVal - prevVal;
      const ratioLastRaw =
        history.length > 0 && typeof history[history.length - 1]?.ratio_applied === "number"
          ? Number(history[history.length - 1]?.ratio_applied || 0)
          : deltaLast / Math.max(Math.abs(prevVal), 1);
      const ratioLast = Math.abs(ratioLastRaw) >= 0.005 ? ratioLastRaw : 0;
      const initialVal = history.length > 0 ? history[0].val : currentVal;
      const deltaTotal = currentVal - initialVal;

      return { 
        name: String(name), 
        score: currentVal, 
        prevScore: prevVal,
        delta: deltaLast, // 默认显示单步变动
        ratioDelta: ratioLast,
        deltaTotal,
        history 
      };
    })
    .filter((row) => row.name && Number.isFinite(row.score))
    .sort((a, b) => b.score - a.score);
  const baseScores = scoreEntries(baseScoreMap);
  const narrativeScores = scoreEntries(narrativeScoreMap);
  const decompositionRows = Object.entries(decompositionScoreMap)
    .map(([name, row]) => ({
      name: String(name || ""),
      manifest: Number((row as { manifest?: number } | undefined)?.manifest || 0),
      root: Number((row as { root?: number } | undefined)?.root || 0),
      momentum: Number((row as { momentum?: number } | undefined)?.momentum || 0),
      momentumMonthOrder: Number((row as { momentum_month_order?: number } | undefined)?.momentum_month_order || 0),
      momentumStage: Number((row as { momentum_stage?: number } | undefined)?.momentum_stage || 0),
      momentumStageLu: Number((row as { momentum_stage_lu?: number } | undefined)?.momentum_stage_lu || 0),
      momentumStageBlade: Number((row as { momentum_stage_blade?: number } | undefined)?.momentum_stage_blade || 0),
      momentumStageGeneral: Number((row as { momentum_stage_general?: number } | undefined)?.momentum_stage_general || 0),
      momentumStructure: Number((row as { momentum_structure?: number } | undefined)?.momentum_structure || 0),
      momentumAuxiliary: Number((row as { momentum_auxiliary?: number } | undefined)?.momentum_auxiliary || 0),
      momentumOther: Number((row as { momentum_other?: number } | undefined)?.momentum_other || 0),
      hidden: Number((row as { hidden?: number } | undefined)?.hidden || 0),
      total: Number((row as { total?: number } | undefined)?.total || 0),
    }))
    .filter((row) => row.name && Number.isFinite(row.total) && row.total > 0)
    .sort((a, b) => b.total - a.total)
    .slice(0, 6);
  const decompositionSummary = Object.values(decompositionScoreMap).reduce<{
    manifest: number;
    root: number;
    momentum: number;
    hidden: number;
  }>(
    (acc, raw) => {
      const row = raw as {
        manifest?: number;
        root?: number;
        momentum?: number;
        hidden?: number;
      };
      acc.manifest += Number(row?.manifest || 0);
      acc.root += Number(row?.root || 0);
      acc.momentum += Number(row?.momentum || 0);
      acc.hidden += Number(row?.hidden || 0);
      return acc;
    },
    { manifest: 0, root: 0, momentum: 0, hidden: 0 },
  );
  const baseTotal = baseScores.reduce((sum, row) => sum + row.score, 0);
  const runtimeTotal = deityScores.reduce((sum, row) => sum + row.score, 0);
  const narrativeTotal = narrativeScores.reduce((sum, row) => sum + row.score, 0);
  const momentumShare =
    runtimeTotal > 0 ? Math.min(100, Math.max(0, (decompositionSummary.momentum / runtimeTotal) * 100)) : 0;
  const runtimeTopRows = deityScores.slice(0, 6);
  const layerCards = [
    {
      key: "base",
      title: ui("L0 基线", "L0 Base", "L0 기준"),
      subtitle: ui("冻结基线", "Frozen baseline", "고정 기준선"),
      rows: baseScores,
      accent: "text-zinc-200",
      border: "border-zinc-700/70",
      bg: "bg-zinc-900/70",
    },
    {
      key: "runtime",
      title: ui("L1 运行态", "L1 Runtime", "L1 운행"),
      subtitle: ui("客观运行态", "Objective runtime", "객관 운행 상태"),
      rows: deityScores.map((row) => ({ name: row.name, score: row.score })),
      accent: "text-cyan-200",
      border: "border-cyan-500/30",
      bg: "bg-cyan-950/20",
    },
    {
      key: "narrative",
      title: ui("L2 叙事态", "L2 Narrative", "L2 서사"),
      subtitle: ui("主观镜头", "Narrative lens", "서사 렌즈"),
      rows: narrativeScores,
      accent: "text-fuchsia-200",
      border: "border-fuchsia-500/30",
      bg: "bg-fuchsia-950/20",
    },
  ];
  const tenGods = Array.isArray(physicsSnapshot?.payload?.ten_gods)
    ? physicsSnapshot?.payload?.ten_gods.map((x) => String(x || "").trim()).filter(Boolean)
    : [];
  const pillars = physicsSnapshot?.payload?.four_pillars || {};
  const pillarText = ["year", "month", "day", "hour"]
    .map((k) => String((pillars as Record<string, unknown>)[k] || "").trim())
    .filter(Boolean)
    .join(" / ");
  const pluginRows = Array.isArray((physicsPayload.plugins as { rows?: unknown[] } | undefined)?.rows)
    ? (((physicsPayload.plugins as { rows?: unknown[] }).rows ?? []) as Array<Record<string, unknown>>)
    : [];
  const pluginStatuses = Array.isArray((physicsPayload.plugins as { statuses?: unknown[] } | undefined)?.statuses)
    ? (((physicsPayload.plugins as { statuses?: unknown[] }).statuses ?? []) as Array<Record<string, unknown>>)
    : [];
  const pluginClaims = Array.isArray((physicsPayload.plugins as { claims?: unknown[] } | undefined)?.claims)
    ? (((physicsPayload.plugins as { claims?: unknown[] }).claims ?? []) as Array<Record<string, unknown>>)
    : [];
  const pluginConflicts = Array.isArray((physicsPayload.plugins as { conflicts?: unknown[] } | undefined)?.conflicts)
    ? (((physicsPayload.plugins as { conflicts?: unknown[] }).conflicts ?? []) as Array<Record<string, unknown>>)
    : [];
  const pluginConflictResolutions = Array.isArray((physicsPayload.plugins as { conflict_resolutions?: unknown[] } | undefined)?.conflict_resolutions)
    ? (((physicsPayload.plugins as { conflict_resolutions?: unknown[] }).conflict_resolutions ?? []) as Array<Record<string, unknown>>)
    : [];
  const knowledgeSnapshot =
    (physicsPayload.plugins as { knowledge_snapshot?: Record<string, unknown> } | undefined)?.knowledge_snapshot || {};
  const brainActionQueue = Array.isArray((physicsPayload.plugins as { brain_action_queue?: unknown[] } | undefined)?.brain_action_queue)
    ? (((physicsPayload.plugins as { brain_action_queue?: unknown[] }).brain_action_queue ?? []) as Array<Record<string, unknown>>)
    : [];
  const brainTimeline = pluginConflicts.slice(0, 8).map((conflict) => {
    const conflictId = String(conflict.conflict_id || "").trim();
    const resolution = pluginConflictResolutions.find((item) => String(item.conflict_id || "").trim() === conflictId);
    const action = brainActionQueue.find((item) => String(item.conflict_id || "").trim() === conflictId);
    return { conflict, resolution, action };
  }).filter((row) => String(row.conflict.conflict_id || "").trim());
  const manualDecisions = Array.isArray(physicsPayload.manual_inbox)
    ? (physicsPayload.manual_inbox as Array<Record<string, unknown>>)
    : Array.isArray(physicsPayload.manual_decisions)
      ? (physicsPayload.manual_decisions as Array<Record<string, unknown>>)
      : [];
  const autoDecisions = Array.isArray(physicsPayload.auto_decisions)
    ? (physicsPayload.auto_decisions as Array<Record<string, unknown>>)
    : [];
  const autoResolutions = autoDecisions.length
    ? autoDecisions.filter((row) => {
        const bucket = String(row.auto_bucket || "").trim().toLowerCase();
        return bucket === "system" || bucket === "llm";
      })
    : Array.isArray(physicsPayload.auto_resolutions)
      ? (physicsPayload.auto_resolutions as Array<Record<string, unknown>>)
      : [];
  const llmArbitrationContext = autoDecisions.length
    ? autoDecisions.filter((row) => String(row.auto_bucket || "").trim().toLowerCase() === "context")
    : [];
  if (!autoDecisions.length && Array.isArray(physicsPayload.llm_arbitration_context)) {
    llmArbitrationContext.push(...(physicsPayload.llm_arbitration_context as Array<Record<string, unknown>>));
  }
  const godRings =
    physicsPayload.god_rings && typeof physicsPayload.god_rings === "object"
      ? (physicsPayload.god_rings as Record<string, unknown>)
      : {};
  const judgementBias =
    godRings.judgement_bias && typeof godRings.judgement_bias === "object"
      ? (godRings.judgement_bias as Record<string, unknown>)
      : {};
  const judgementUseBias = traceBiasPairs(judgementBias.use_bias).slice(0, 6);
  const judgementTabooBias = traceBiasPairs(judgementBias.taboo_bias).slice(0, 6);
  const judgementBiasEntries = Array.isArray(godRings.judgement_bias_entries)
    ? (godRings.judgement_bias_entries as Array<Record<string, unknown>>)
        .map((row) => {
          const sourceLabel = String(row.source_label || row.decision_label || row.plugin_id || "").trim();
          const decisionId = String(row.decision_id || "").trim();
          const reason = String(row.reason || "").trim();
          const usePairs = traceBiasPairs(row.use_bias);
          const tabooPairs = traceBiasPairs(row.taboo_bias);
          if (!sourceLabel || (!usePairs.length && !tabooPairs.length)) return null;
          return { sourceLabel, decisionId, reason, usePairs, tabooPairs };
        })
        .filter(Boolean) as Array<{
          sourceLabel: string;
          decisionId: string;
          reason: string;
          usePairs: Array<{ name: string; score: number }>;
          tabooPairs: Array<{ name: string; score: number }>;
        }>
    : [];
  const groupedPlugins = pluginRows.reduce<Record<string, string[]>>((acc, row) => {
    const plugin = String(row.plugin || row.source || "unknown").trim() || "unknown";
    const fact = String(row.fact || row.label || row.title || "").trim();
    if (!fact) return acc;
    acc[plugin] = [...(acc[plugin] || []), fact];
    return acc;
  }, {});
  const pluginClaimById = pluginClaims.reduce<Record<string, Record<string, unknown>>>((acc, row) => {
    const key = String(row.plugin_id || "").trim();
    if (!key) return acc;
    const current = acc[key];
    if (!current || Number(row.match_ratio || 0) > Number(current.match_ratio || 0)) acc[key] = row;
    return acc;
  }, {});
  const causalPhysicsAnchor = String(physicsPayload.causal_anchor || "—");
  const causalAuditAnchor = String(auditPayload.causal_anchor || "—");
  const causalPhysicsFp = String(physicsPayload.physics_fingerprint || "—");
  const causalAuditFp = String(
    auditPayload.physics_fingerprint ||
      (fullTrace?.physics_fingerprint as string | undefined) ||
      (llmMeta.physics_fingerprint as string | undefined) ||
      "—",
  );
  const causalAligned =
    causalPhysicsAnchor !== "—" &&
    causalAuditAnchor !== "—" &&
    causalPhysicsFp !== "—" &&
    causalAuditFp !== "—" &&
    causalPhysicsAnchor !== "" &&
    causalAuditAnchor !== "" &&
    causalPhysicsFp === causalAuditFp;
  const connectPhase =
    llmLifecyclePhase === "connecting" || llmLifecyclePhase === "awaiting_first_token";
  const collapsePhase = llmLifecyclePhase === "streaming";
  const timelineItems = [
    {
      label: "SNAPSHOT",
      state: pillarText ? "已显影" : "未显影",
      meta: `${causalPhysicsAnchor} · ${causalPhysicsFp}`,
    },
    {
      label: "AUDIT_PREVIEW",
      state: Object.keys(auditPayload).length > 0 ? "已派发" : "未到达",
      meta: `${causalAuditAnchor} · ${causalAuditFp}`,
    },
    {
      label: "LLM",
      state: llmStatusText,
      meta: `${String(llmMeta.model || llmMeta.llm_endpoint_host || "叙事引擎")} · ${llmStatusDetail}`,
    },
    {
      label: "TERMINAL",
      state:
        llmLifecyclePhase === "failed"
          ? "失败/降级"
          : llmLifecyclePhase === "completed"
            ? "完成"
            : llmLifecyclePhase === "closed_without_output"
              ? "已关闭"
              : "未终结",
      meta:
        llmMeta.error != null && String(llmMeta.error).trim()
          ? String(llmMeta.error)
          : streamClosed
            ? lastHeartbeatStep || "stream_eof"
            : `${Number(llmMeta.elapsed_ms || 0)} ms`,
    },
  ];

  if (surfaceMode === "tab" && collapsed) {
    return null;
  }

  if (collapsed) {
    return (
      <aside className="sticky top-6 flex h-fit min-h-[28rem] w-14 flex-col items-center rounded-2xl border border-cyan-500/25 bg-zinc-900/70 py-3 shadow-[0_18px_60px_rgba(8,145,178,0.12)]">
        <button
          type="button"
          onClick={onToggle}
          className="rounded-full border border-cyan-400/35 bg-cyan-950/55 px-3 py-2 text-[10px] tracking-[0.35em] text-cyan-200 transition hover:bg-cyan-900/70"
          title="展开系统观测"
        >
          观测
        </button>
        <div className="mt-4 flex flex-1 items-center">
          <span className="[writing-mode:vertical-rl] text-[10px] tracking-[0.4em] text-zinc-500">
            系统观测
          </span>
        </div>
      </aside>
    );
  }

  return (
    <aside
      className={
        surfaceMode === "tab"
          ? "rounded-2xl border border-cyan-500/40 bg-[linear-gradient(180deg,rgba(10,18,24,0.96),rgba(9,14,19,0.88))] p-3 shadow-[0_22px_70px_rgba(8,145,178,0.16)]"
          : "sticky top-6 h-fit rounded-2xl border border-cyan-500/40 bg-[linear-gradient(180deg,rgba(10,18,24,0.96),rgba(9,14,19,0.88))] p-3 shadow-[0_22px_70px_rgba(8,145,178,0.16)]"
      }
    >
      {showChrome ? (
        <div className="mb-3 flex items-center justify-between gap-2">
          <div>
            <p className="text-xs tracking-[0.28em] text-cyan-200">
              {contentMode === "debug_only" ? "BACKEND OBSERVATORY" : "SYSTEM OBSERVATORY"}
            </p>
            <p className="mt-1 text-[11px] text-zinc-500">
              {contentMode === "debug_only"
                ? "后台链路 / Prompt / LLM / payload 调试观测"
                : "元数据 / 十神账本 / 决策与 LLM 观测"}
            </p>
          </div>
          <button
            type="button"
            onClick={onToggle}
            className="rounded-full border border-cyan-400/35 bg-cyan-950/50 px-3 py-1 text-[10px] text-cyan-200 transition hover:bg-cyan-900/70"
          >
            {surfaceMode === "tab" ? "返回" : "收起"}
          </button>
        </div>
      ) : null}
      {showChrome && focusedDecisionId ? (
        <div className="mb-3 rounded-xl border border-emerald-500/20 bg-emerald-950/15 px-3 py-2 text-[10px] text-emerald-200">
          当前聚焦决策：{focusedDecisionId}
        </div>
      ) : null}

      {showInsightSections ? (
        <>
      <div className="space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
            <p className="text-[11px] text-cyan-300">{ui("八字元数据", "BaZi Metadata", "사주 메타데이터")}</p>
            <div className="space-y-1 text-[11px] text-zinc-200">
          <p>{ui("张力", "Tension", "장력")}：{Number(physicsSnapshot?.payload?.physics_tension || 0).toFixed(2)}</p>
          <p>{ui("六柱", "Six pillars", "육주")}：{pillarText || "—"}</p>
          <p>
            {ui("运势", "Luck / Flow", "운세")}：
            {String(physicsSnapshot?.payload?.luck_pillar || "—")} / {String(physicsSnapshot?.payload?.flow_pillar || "—")}
          </p>
          <p>{ui("流年锚年", "Flow year anchor", "세운 기준연")}：{String(physicsSnapshot?.payload?.flow_year || "—")}</p>
          <p>{ui("十神主轴", "Ten-god axis", "십신 주축")}：{tenGods.length ? translateTermList(lang, tenGods) : "—"}</p>
          <p>{ui("总能量指数", "Total energy index", "총 에너지 지수")}：{Number(physicsSnapshot?.payload?.total_energy_index || 0).toFixed(2)}</p>
        </div>
        <div className="mt-2 space-y-1">
          <div className="flex items-center justify-between gap-2">
            <p className="text-[10px] uppercase tracking-[0.24em] text-zinc-500">{ui("三层能量", "Three-Layer Energy", "삼층 에너지")}</p>
            <span className="rounded-full border border-cyan-500/20 bg-cyan-950/30 px-2 py-0.5 text-[9px] tracking-[0.2em] text-cyan-200">
              {ui("主图: 运行态", "Primary: Runtime", "주 도표: Runtime")}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {layerCards.map((layer) => {
              const total = layer.rows.reduce((sum, row) => sum + row.score, 0);
              const leads = layer.rows.slice(0, 2).map((row) => `${row.name} ${row.score.toFixed(1)}`);
              return (
                <div key={layer.key} className={`rounded-lg border px-2 py-2 ${layer.border} ${layer.bg}`}>
                  <p className={`text-[10px] tracking-[0.18em] ${layer.accent}`}>{layer.title}</p>
                  <p className="mt-1 text-[10px] text-zinc-500">{layer.subtitle}</p>
                  <p className="mt-2 font-mono text-[11px] text-zinc-100">{total.toFixed(2)}</p>
                  <p className="mt-1 text-[10px] leading-relaxed text-zinc-400">
                    {leads.length ? leads.map((lead) => {
                      const [name, score] = lead.split(" ");
                      return `${translateTerm(lang, name)} ${score}`;
                    }).join(" / ") : ui("暂无样本", "No samples yet", "샘플 없음")}
                  </p>
                </div>
              );
            })}
          </div>
          <p className="text-[10px] uppercase tracking-[0.24em] text-zinc-500">{ui("运行总览", "Runtime Overview", "운행 개요")}</p>
          {runtimeTopRows.length ? (
            <div className="space-y-2">
              <div className="grid gap-2 md:grid-cols-3">
                <div className="rounded-lg border border-cyan-500/15 bg-cyan-950/20 p-2">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-cyan-300">{ui("当前运行总分", "Current runtime total", "현재 운행 총점")}</p>
                  <p className="mt-2 font-mono text-lg text-cyan-100">{runtimeTotal.toFixed(2)}</p>
                  <p className="mt-1 text-[10px] text-zinc-500">{ui("L1 运行态总量", "L1 runtime total", "L1 운행 총량")}</p>
                </div>
                <div className="rounded-lg border border-zinc-700/40 bg-zinc-900/80 p-2">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-zinc-300">{ui("基线总分", "Baseline total", "기준선 총점")}</p>
                  <p className="mt-2 font-mono text-lg text-zinc-100">{baseTotal.toFixed(2)}</p>
                  <p className="mt-1 text-[10px] text-zinc-500">{ui("L0 冻结基线", "L0 frozen baseline", "L0 고정 기준선")}</p>
                </div>
                <div className="rounded-lg border border-amber-500/15 bg-amber-950/20 p-2">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-amber-300">{ui("势能占比", "Momentum share", "세력 비중")}</p>
                  <p className="mt-2 font-mono text-lg text-amber-100">{momentumShare.toFixed(1)}%</p>
                  <p className="mt-1 text-[10px] text-zinc-500">{ui("势能 / 运行总分", "Momentum / runtime total", "세력 / 운행 총점")}</p>
                </div>
              </div>
              <div className="grid gap-2 md:grid-cols-2">
                <div className="rounded-lg border border-fuchsia-500/15 bg-fuchsia-950/20 p-2">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-fuchsia-300">{ui("叙事总分", "Narrative total", "서사 총점")}</p>
                  <p className="mt-2 font-mono text-lg text-fuchsia-100">{narrativeTotal.toFixed(2)}</p>
                  <p className="mt-1 text-[10px] text-zinc-500">{ui("L2 叙事总量", "L2 narrative total", "L2 서사 총량")}</p>
                </div>
                <div className="rounded-lg border border-emerald-500/15 bg-emerald-950/20 p-2">
                  <p className="text-[10px] uppercase tracking-[0.16em] text-emerald-300">{ui("运行偏移", "Runtime drift", "운행 편차")}</p>
                  <p className="mt-2 font-mono text-lg text-emerald-100">
                    {(runtimeTotal - baseTotal >= 0 ? "+" : "") + (runtimeTotal - baseTotal).toFixed(2)}
                  </p>
                  <p className="mt-1 text-[10px] text-zinc-500">Runtime - Base</p>
                </div>
              </div>
              <div className="rounded-lg border border-cyan-500/15 bg-zinc-900/80 p-2">
                <p className="text-[10px] uppercase tracking-[0.16em] text-cyan-300">Top Runtime Scores</p>
                <div className="mt-2 space-y-1 text-[10px] text-zinc-300">
                  {runtimeTopRows.map((row) => (
                    <div key={row.name} className="flex items-center justify-between gap-2 rounded border border-zinc-800 bg-zinc-950/60 px-2 py-1">
                      <span className="text-zinc-100">{translateTerm(lang, row.name)}</span>
                      <span className="font-mono text-cyan-200">{row.score.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg border border-fuchsia-500/15 bg-zinc-900/80 p-2">
                <p className="text-[10px] uppercase tracking-[0.16em] text-fuchsia-300">Source Totals</p>
                <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] text-zinc-300">
                  <div className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-1">
                    {ui("显化", "Manifest", "현출")} <span className="ml-1 font-mono text-fuchsia-100">{decompositionSummary.manifest.toFixed(2)}</span>
                  </div>
                  <div className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-1">
                    {ui("根气", "Root", "근기")} <span className="ml-1 font-mono text-emerald-100">{decompositionSummary.root.toFixed(2)}</span>
                  </div>
                  <div className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-1">
                    {ui("势能", "Momentum", "세력")} <span className="ml-1 font-mono text-amber-100">{decompositionSummary.momentum.toFixed(2)}</span>
                  </div>
                  <div className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-1">
                    {ui("潜藏", "Hidden", "잠장")} <span className="ml-1 font-mono text-zinc-100">{decompositionSummary.hidden.toFixed(2)}</span>
                  </div>
                </div>
                <p className="mt-2 text-[10px] leading-relaxed text-zinc-500">
                  {ui(
                    "这里仅展示当前运行态总览，不再保留旧版单步 `was` 条形图。",
                    "This block shows only the current runtime overview and no longer keeps the legacy step-by-step `was` bars.",
                    "이 영역은 현재 운행 개요만 보여 주며, 예전 `was` 막대는 더 이상 유지하지 않습니다.",
                  )}
                </p>
              </div>
            </div>
          ) : (
            <p className="text-[11px] text-zinc-500">{ui("暂无运行态总览", "No runtime overview yet", "운행 개요 없음")}</p>
          )}
          {decompositionRows.length ? (
            <div className="mt-3">
              <p className="text-[10px] uppercase tracking-[0.24em] text-zinc-500">{ui("L0 十神来源分解", "L0 Decomposition", "L0 십신 분해")}</p>
              <div className="mt-2 space-y-1">
                {decompositionRows.map((row) => (
                  <div key={row.name} className="rounded-lg border border-fuchsia-500/15 bg-zinc-900/80 px-2 py-1.5 text-[10px] text-zinc-300">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-fuchsia-100">{translateTerm(lang, row.name)}</span>
                      <span className="font-mono text-fuchsia-200">{row.total.toFixed(2)}</span>
                    </div>
                    <div className="mt-1 grid grid-cols-2 gap-1 lg:grid-cols-4">
                      <span>{ui("显化", "Manifest", "현출")} {row.manifest.toFixed(2)}</span>
                      <span>{ui("根气", "Root", "근기")} {row.root.toFixed(2)}</span>
                      <span>{ui("势能", "Momentum", "세력")} {row.momentum.toFixed(2)}</span>
                      <span>{ui("潜藏", "Hidden", "잠장")} {row.hidden.toFixed(2)}</span>
                    </div>
                    <div className="mt-1 flex flex-wrap gap-2 text-[10px] text-zinc-500">
                      <span>{ui("月令势", "Month order", "월령세")} {row.momentumMonthOrder.toFixed(2)}</span>
                      <span>{ui("阶段势", "Stage", "단계세")} {row.momentumStage.toFixed(2)}</span>
                      <span>{ui("禄势", "Lu", "록세")} {row.momentumStageLu.toFixed(2)}</span>
                      <span>{ui("刃势", "Blade", "인세")} {row.momentumStageBlade.toFixed(2)}</span>
                      <span>{ui("长生势", "Growth", "장생세")} {row.momentumStageGeneral.toFixed(2)}</span>
                      <span>{ui("结构势", "Structure", "구조세")} {row.momentumStructure.toFixed(2)}</span>
                      <span>{ui("辅助势", "Auxiliary", "보조세")} {row.momentumAuxiliary.toFixed(2)}</span>
                      <span>{ui("其他势", "Other", "기타세")} {row.momentumOther.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-cyan-300">{ui("体用判定账本", "Body/Use Authority Ledger", "체용 판정 장부")}</p>
          <span className="text-[10px] text-zinc-500">
            {ui("用侧", "Use", "용측")} {judgementUseBias.length} / {ui("忌侧", "Taboo", "기측")} {judgementTabooBias.length} / {ui("来源", "Sources", "출처")} {judgementBiasEntries.length}
          </span>
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          <div className="rounded-lg border border-emerald-500/15 bg-zinc-900/60 p-2">
            <p className="text-[10px] tracking-[0.2em] text-emerald-200">USE BIAS</p>
            <div className="mt-2 flex flex-wrap gap-2 text-[10px]">
              {judgementUseBias.length ? judgementUseBias.map((row) => (
                <span key={`trace_judgement_use_${row.name}`} className="rounded-full border border-emerald-500/20 bg-emerald-950/20 px-2 py-1 text-emerald-200">
                  {translateTerm(lang, row.name)} +{row.score.toFixed(2)}
                </span>
              )) : <span className="text-zinc-500">{ui("暂无。", "None.", "없음.")}</span>}
            </div>
          </div>
          <div className="rounded-lg border border-rose-500/15 bg-zinc-900/60 p-2">
            <p className="text-[10px] tracking-[0.2em] text-rose-200">TABOO BIAS</p>
            <div className="mt-2 flex flex-wrap gap-2 text-[10px]">
              {judgementTabooBias.length ? judgementTabooBias.map((row) => (
                <span key={`trace_judgement_taboo_${row.name}`} className="rounded-full border border-rose-500/20 bg-rose-950/20 px-2 py-1 text-rose-200">
                  {translateTerm(lang, row.name)} +{row.score.toFixed(2)}
                </span>
              )) : <span className="text-zinc-500">{ui("暂无。", "None.", "없음.")}</span>}
            </div>
          </div>
        </div>
        <div className="space-y-2">
          {judgementBiasEntries.length ? judgementBiasEntries.slice(0, 8).map((row, idx) => (
            <div
              key={`judgement_entry_${idx}_${row.sourceLabel}`}
              className={`rounded-lg border bg-zinc-900/60 px-2 py-2 ${
                row.decisionId && row.decisionId === focusedDecisionId
                  ? "border-emerald-500/35 shadow-[0_0_0_1px_rgba(16,185,129,0.22)]"
                  : "border-cyan-500/10"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-[10px] tracking-[0.18em] text-cyan-200 uppercase">{row.sourceLabel}</p>
                {row.decisionId ? <span className="font-mono text-[10px] text-zinc-400">{row.decisionId}</span> : null}
              </div>
              {row.reason ? <p className="mt-1 text-[10px] text-zinc-400">{row.reason}</p> : null}
              {row.usePairs.length ? (
                <p className="mt-1 text-[10px] text-emerald-200/90">
                  {ui("用侧", "Use", "용측")}：{row.usePairs.map((item) => `${translateTerm(lang, item.name)} +${item.score.toFixed(2)}`).join(" · ")}
                </p>
              ) : null}
              {row.tabooPairs.length ? (
                <p className="mt-1 text-[10px] text-rose-200/90">
                  {ui("忌侧", "Taboo", "기측")}：{row.tabooPairs.map((item) => `${translateTerm(lang, item.name)} +${item.score.toFixed(2)}`).join(" · ")}
                </p>
              ) : null}
            </div>
          )) : (
            <p className="text-[11px] text-zinc-500">{ui("暂无体用判定账本；当前没有插件向体用裁决提供额外偏置。", "No body/use authority ledger is available yet; no plugin is currently adding extra bias into the authority judgement.", "체용 판정 장부가 아직 없습니다. 현재 체용 판정에 추가 편향을 제공하는 플러그인이 없습니다.")}</p>
          )}
        </div>
      </div>

      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-cyan-300">{ui("插件执行状态", "Plugin Execution Status", "플러그인 실행 상태")}</p>
          <span className="text-[10px] text-zinc-500">{pluginStatuses.length} {ui("条", "rows", "건")}</span>
        </div>
        <div className="space-y-1">
          {pluginStatuses.length ? pluginStatuses.slice(0, 10).map((row, idx) => {
            const status = String(row.status || "fact_only").trim();
            const statusTone =
              status === "auto_applied"
                ? "text-emerald-200 border-emerald-500/20 bg-emerald-950/20"
                : status === "proposal_pending"
                  ? "text-amber-200 border-amber-500/20 bg-amber-950/20"
                  : status === "clamped"
                    ? "text-fuchsia-200 border-fuchsia-500/20 bg-fuchsia-950/20"
                    : status.startsWith("skipped")
                      ? "text-rose-200 border-rose-500/20 bg-rose-950/20"
                      : "text-zinc-200 border-zinc-700/60 bg-zinc-900/70";
            return (
              <div key={`plugin_status_${idx}`} className={`min-w-0 rounded-lg border px-2 py-2 ${statusTone}`}>
                <div className="flex min-w-0 items-center justify-between gap-2">
                  <p className="min-w-0 break-all text-[10px] tracking-[0.18em]">{String(row.plugin_id || "unknown")}</p>
                  <span className="font-mono text-[10px] uppercase">{status}</span>
                </div>
                <p className="mt-1 break-words text-[10px] text-zinc-300">{String(row.reason || "—")}</p>
                  <p className="mt-1 text-[10px] text-zinc-500">
                    facts {Number(row.fact_count || 0)} / proposals {Number(row.proposal_count || 0)}
                    {String(row.target_god || "").trim() ? ` / ${ui("target", "target", "대상")} ${translateTerm(lang, String(row.target_god))}` : ""}
                  </p>
                  {(() => {
                    const claim = pluginClaimById[String(row.plugin_id || "").trim()];
                    if (!claim) return null;
                    const projectionText = compactProjection(claim.cluster_projection);
                    return (
                      <p className="mt-1 break-words text-[10px] text-zinc-400">
                        {ui("主落点", "Primary target", "주 낙점")} {translateTerm(lang, String(claim.target_god || row.target_god || "未定目标"))}
                        {Number(claim.projection_share || 0) > 0 ? ` · ${ui("占比", "share", "비중")} ${Math.round(Number(claim.projection_share || 0) * 100)}%` : ""}
                        {projectionText ? ` · ${projectionText}` : ""}
                      </p>
                    );
                  })()}
                </div>
              );
            }) : (
            <p className="text-[11px] text-zinc-500">{ui("暂无插件状态标签", "No plugin status labels yet", "플러그인 상태 라벨 없음")}</p>
          )}
        </div>
      </div>

      <details className="mt-3 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3" open>
        <summary className="cursor-pointer text-[11px] text-cyan-300">{ui("插件 / Fact 分组", "Plugin / Fact Groups", "플러그인 / Fact 그룹")}</summary>
        <div className="mt-3">
        <p className="text-[11px] text-cyan-300">{ui("命中插件", "Matched Plugins", "적중 플러그인")}</p>
        <p className="mt-1 text-[11px] text-zinc-200">
          {traceHits.length ? (traceHits as string[]).join(" / ") : ui("暂无命中", "No matched plugins yet", "적중 없음")}
        </p>
        </div>
        <div className="mt-3">
        <p className="text-[11px] text-cyan-300">{ui("织造 Fact", "Weaving Facts", "직조 Fact")}</p>
        <div className="mt-1 space-y-1">
          {traceFacts.length ? (
            (traceFacts as string[]).map((x, idx) => (
              <p key={`${idx}_${x}`} className="text-[11px] text-zinc-200">
                {idx + 1}. {String(x)}
              </p>
            ))
          ) : (
            <p className="text-[11px] text-zinc-500">{ui("暂无 Fact", "No facts yet", "Fact 없음")}</p>
          )}
        </div>
        </div>
        <div className="mt-3 space-y-2">
          <p className="text-[11px] text-cyan-300">{ui("插件分组", "Plugin Groups", "플러그인 그룹")}</p>
          {Object.keys(groupedPlugins).length ? (
            Object.entries(groupedPlugins).map(([plugin, facts]) => (
              <details key={plugin} className="rounded-lg border border-cyan-500/15 bg-zinc-900/70 p-2">
                <summary className="cursor-pointer text-[11px] text-zinc-100">{plugin}</summary>
                <div className="mt-2 space-y-1">
                  {facts.map((fact, idx) => (
                    <p key={`${plugin}_${idx}`} className="text-[10px] text-zinc-300">
                      {idx + 1}. {fact}
                    </p>
                  ))}
                </div>
              </details>
            ))
          ) : (
            <p className="text-[11px] text-zinc-500">{ui("暂无插件分组", "No plugin groups yet", "플러그인 그룹 없음")}</p>
          )}
        </div>
      </details>

      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-cyan-300">{ui("裁决摘要", "Decision Summary", "결정 요약")}</p>
          <span className="text-[10px] text-zinc-500">
            {ui("手动", "Manual", "수동")} {manualDecisions.length} / {ui("自动", "Auto", "자동")} {autoResolutions.length} / {ui("上下文", "Context", "컨텍스트")} {llmArbitrationContext.length}
          </span>
        </div>
        {compactInsightMode ? (
          <div className="grid gap-2 md:grid-cols-3">
            <div className="rounded-lg border border-violet-500/15 bg-zinc-900/60 p-2">
              <p className="text-[10px] tracking-[0.18em] text-violet-200">MANUAL</p>
              <p className="mt-2 font-mono text-base text-violet-50">{manualDecisions.length}</p>
              <p className="mt-1 text-[10px] text-zinc-500">{ui("命理师待确认裁决", "Pending practitioner decisions", "명리사 확인 대기")}</p>
            </div>
            <div className="rounded-lg border border-amber-500/15 bg-zinc-900/60 p-2">
              <p className="text-[10px] tracking-[0.18em] text-amber-200">AUTO</p>
              <p className="mt-2 font-mono text-base text-amber-50">{autoResolutions.length}</p>
              <p className="mt-1 text-[10px] text-zinc-500">{ui("系统静默处理项", "System silent resolutions", "시스템 자동 처리")}</p>
            </div>
            <div className="rounded-lg border border-cyan-500/15 bg-zinc-900/60 p-2">
              <p className="text-[10px] tracking-[0.18em] text-cyan-200">CONTEXT</p>
              <p className="mt-2 font-mono text-base text-cyan-50">{llmArbitrationContext.length}</p>
              <p className="mt-1 text-[10px] text-zinc-500">{ui("仅作上下文缓存", "Context-only cache", "컨텍스트 전용 캐시")}</p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="rounded-lg border border-violet-500/15 bg-zinc-900/60 p-2">
              <p className="text-[10px] tracking-[0.2em] text-violet-200">MANUAL INBOX</p>
              <div className="mt-2 space-y-1 text-[10px] text-zinc-300">
                {manualDecisions.length ? manualDecisions.slice(0, 8).map((row, idx) => {
                  const biasSummary = traceBiasSummary(row);
                  return (
                    <div
                      key={`manual_${idx}`}
                      className={`rounded border bg-zinc-950/60 px-2 py-1 ${
                        String(row.id || "").trim() === focusedDecisionId
                          ? "border-emerald-500/35 shadow-[0_0_0_1px_rgba(16,185,129,0.22)]"
                          : "border-violet-500/10"
                      }`}
                    >
                      <p className="text-violet-100">{String(row.label || row.title || "—")}</p>
                      <p className="mt-0.5 text-zinc-500">
                        {String(row.source || row.plugin_id || "unknown")} · {String(row.target_god || (row.physical_impact as Record<string, unknown> | undefined)?.target_god || "无目标神")}
                      </p>
                      <p className="mt-0.5 font-mono text-violet-200/80">{traceArbitrationChain(row, "手动")}</p>
                      {row.resolved_from_llm ? <p className="mt-0.5 text-cyan-200/80">来自 LLM 仲裁 · {String(row.llm_resolution_state || "promoted_to_manual")}</p> : null}
                      <p className="mt-0.5 text-zinc-400">{traceImpactText(row)}</p>
                      {biasSummary ? (
                        <div className="mt-1 space-y-0.5 text-[10px]">
                          {biasSummary.useText ? <p className="text-emerald-200/90">用侧推动：{biasSummary.useText}</p> : null}
                          {biasSummary.tabooText ? <p className="text-rose-200/90">忌侧推动：{biasSummary.tabooText}</p> : null}
                        </div>
                      ) : null}
                    </div>
                  );
                }) : <p className="text-zinc-500">{ui("暂无手动裁决项", "No manual decisions", "수동 결정 없음")}</p>}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-cyan-300">{ui("因果锚点", "Causal Anchors", "인과 앵커")}</p>
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] ${
              causalAligned ? "bg-emerald-950/80 text-emerald-200" : "bg-amber-950/80 text-amber-200"
            }`}
          >
            {causalAligned ? ui("已对齐", "Aligned", "정렬됨") : ui("待核对", "Pending review", "검토 대기")}
          </span>
        </div>
        <div className="space-y-1 text-[11px] text-zinc-200">
          <p>{ui("物理快照", "Physics snapshot", "물리 스냅샷")}：{causalPhysicsAnchor}</p>
          <p className="font-mono text-[10px] text-cyan-200/90 break-all">fp={causalPhysicsFp}</p>
          <p>{ui("审计快照", "Audit snapshot", "감사 스냅샷")}：{causalAuditAnchor}</p>
          <p className="font-mono text-[10px] text-cyan-200/90 break-all">fp={causalAuditFp}</p>
        </div>
      </div>

        </>
      ) : null}

      {showDebugSections ? (
        <>
      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-cyan-300">主张与冲突层</p>
          <span className="text-[10px] text-zinc-500">
            claims {pluginClaims.length} / conflicts {pluginConflicts.length} / resolutions {pluginConflictResolutions.length}
          </span>
        </div>
        <div className="rounded-lg border border-zinc-800/80 bg-zinc-900/60 px-2 py-2 text-[10px] text-zinc-400">
          <div className="flex flex-wrap items-center gap-3">
            <span>claims {Number((knowledgeSnapshot.claim_history as Record<string, unknown> | undefined)?.total_claims || 0)}</span>
            <span>conflicts {Number((knowledgeSnapshot.conflict_history as Record<string, unknown> | undefined)?.total_conflicts || 0)}</span>
            <span>suggestions {Number((knowledgeSnapshot.resolution_preview as Record<string, unknown> | undefined)?.total_suggestions || 0)}</span>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-zinc-500">
            <span>arbiter bias system {Number(((knowledgeSnapshot.conflict_history as Record<string, unknown> | undefined)?.recommended_arbiters as Record<string, unknown> | undefined)?.system || 0)}</span>
            <span>llm {Number(((knowledgeSnapshot.conflict_history as Record<string, unknown> | undefined)?.recommended_arbiters as Record<string, unknown> | undefined)?.llm || 0)}</span>
            <span>user {Number(((knowledgeSnapshot.conflict_history as Record<string, unknown> | undefined)?.recommended_arbiters as Record<string, unknown> | undefined)?.user || 0)}</span>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-zinc-400">
            <span>feedback system {Number(((knowledgeSnapshot.conflict_history as Record<string, unknown> | undefined)?.feedback_arbiters as Record<string, unknown> | undefined)?.system || 0)}</span>
            <span>llm {Number(((knowledgeSnapshot.conflict_history as Record<string, unknown> | undefined)?.feedback_arbiters as Record<string, unknown> | undefined)?.llm || 0)}</span>
            <span>user {Number(((knowledgeSnapshot.conflict_history as Record<string, unknown> | undefined)?.feedback_arbiters as Record<string, unknown> | undefined)?.user || 0)}</span>
            <span>score system {Number(((knowledgeSnapshot.conflict_history as Record<string, unknown> | undefined)?.feedback_arbiter_scores as Record<string, unknown> | undefined)?.system || 0).toFixed(2)}</span>
            <span>llm {Number(((knowledgeSnapshot.conflict_history as Record<string, unknown> | undefined)?.feedback_arbiter_scores as Record<string, unknown> | undefined)?.llm || 0).toFixed(2)}</span>
            <span>user {Number(((knowledgeSnapshot.conflict_history as Record<string, unknown> | undefined)?.feedback_arbiter_scores as Record<string, unknown> | undefined)?.user || 0).toFixed(2)}</span>
          </div>
        </div>
        <div className="space-y-2">
          {pluginConflicts.length ? (
            pluginConflicts.slice(0, 8).map((row, idx) => {
              const conflictId = String(row.conflict_id || `conflict_${idx}`).trim();
              const resolution = pluginConflictResolutions.find((item) => String(item.conflict_id || "").trim() === conflictId);
              const claims = Array.isArray(row.claims) ? row.claims : [];
              const plugins = Array.isArray(row.plugins) ? row.plugins : [];
              return (
                <div key={conflictId} className={`min-w-0 rounded-lg border px-2 py-2 ${conflictTone(String(row.severity || "P3"))}`}>
                  <div className="flex min-w-0 items-center justify-between gap-2">
                    <p className="min-w-0 break-all text-[10px] tracking-[0.18em] uppercase">
                      {String(row.conflict_type || "unknown")}
                    </p>
                    <span className="font-mono text-[10px] uppercase">
                      {String(row.severity || "P3")} · {String(row.recommended_arbiter || "system")}
                    </span>
                  </div>
                  <p className="mt-1 break-words text-[10px] text-zinc-300">{String(row.why_conflict || "—")}</p>
                  <p className="mt-1 text-[10px] text-zinc-500">
                    {String(row.target_god || "").trim() ? `target ${String(row.target_god)} / ` : ""}
                    plugins {plugins.length} / claims {claims.length}
                  </p>
                  {plugins.length ? (
                    <p className="mt-1 break-all text-[10px] text-zinc-400">{plugins.slice(0, 4).join(" / ")}</p>
                  ) : null}
                  {resolution ? (
                    <p className="mt-1 break-all text-[10px] text-cyan-200/90">
                      system suggestion: {String(resolution.policy || "—")} · keep {String(resolution.winner_claim_id || "—")}
                    </p>
                  ) : null}
                </div>
              );
            })
          ) : (
            <p className="text-[11px] text-zinc-500">暂无挂起冲突；当前主张之间未检测到显著冲突。</p>
          )}
        </div>
      </div>

      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-cyan-300">大脑动作队列</p>
          <span className="text-[10px] text-zinc-500">{brainActionQueue.length} 条</span>
        </div>
        <div className="space-y-1">
          {brainActionQueue.length ? (
            brainActionQueue.slice(0, 8).map((row, idx) => (
              <div key={`brain_action_${idx}`} className="rounded-lg border border-sky-500/15 bg-zinc-900/60 px-2 py-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[10px] tracking-[0.18em] text-sky-200 uppercase">{String(row.action_type || "brain_action")}</p>
                  <span className="font-mono text-[10px] text-sky-100 uppercase">{String(row.queue || "llm")}</span>
                </div>
                <p className="mt-1 text-[10px] text-zinc-300">{String(row.reason || "—")}</p>
                <p className="mt-1 text-[10px] text-zinc-500">
                  conflict {String(row.conflict_id || "—")} / confidence {Number(row.confidence || 0).toFixed(2)}
                </p>
                {Array.isArray(row.source_plugins) && row.source_plugins.length ? (
                  <p className="mt-1 text-[10px] text-zinc-400">{(row.source_plugins as string[]).slice(0, 4).join(" / ")}</p>
                ) : null}
              </div>
            ))
          ) : (
            <p className="text-[11px] text-zinc-500">暂无脑动作；当前未形成可执行的后续路由建议。</p>
          )}
        </div>
      </div>

      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-cyan-300">脑流时间线</p>
          <span className="text-[10px] text-zinc-500">{brainTimeline.length} 条</span>
        </div>
        <div className="space-y-2">
          {brainTimeline.length ? (
            brainTimeline.map((row, idx) => (
              <div key={`brain_timeline_${idx}`} className="min-w-0 rounded-lg border border-cyan-500/15 bg-zinc-900/60 px-2 py-2">
                <p className="break-all text-[10px] uppercase tracking-[0.18em] text-cyan-200">
                  {String(row.conflict.conflict_type || "conflict")} · {String(row.conflict.conflict_id || "—")}
                </p>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] text-zinc-400">
                  <span className="rounded border border-rose-500/15 bg-rose-950/20 px-2 py-1">
                    Conflict · {String(row.conflict.severity || "P?")}
                  </span>
                  <span className={`rounded border border-zinc-700 px-2 py-1 ${brainStepTone(String(row.resolution?.resolved_by || row.conflict.recommended_arbiter || "llm"))}`}>
                    Resolution · {String(row.resolution?.resolved_by || row.conflict.recommended_arbiter || "pending")}
                  </span>
                  <span className={`rounded border border-zinc-700 px-2 py-1 ${brainStepTone(String(row.action?.queue || row.resolution?.next_queue || "llm"))}`}>
                    Brain Action · {String(row.action?.action_type || row.resolution?.policy || "waiting")}
                  </span>
                  <span className={`rounded border border-zinc-700 px-2 py-1 ${brainStepTone(String(row.action?.queue || row.resolution?.next_queue || "llm"))}`}>
                    Queue · {String(row.action?.queue || row.resolution?.next_queue || "pending")}
                  </span>
                </div>
                <p className="mt-2 break-words text-[10px] text-zinc-500">
                  {String(row.action?.reason || row.resolution?.reason || row.conflict.why_conflict || "—")}
                </p>
              </div>
            ))
          ) : (
            <p className="text-[11px] text-zinc-500">暂无脑流时间线；当前尚未形成从冲突到路由的完整链路。</p>
          )}
        </div>
      </div>

      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <p className="text-[11px] text-cyan-300">LLM 链路时间线</p>
        <div className="space-y-2">
          {timelineItems.map((item) => (
            <div key={item.label} className="rounded-lg border border-cyan-500/10 bg-zinc-900/70 px-2 py-2">
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] tracking-[0.24em] text-cyan-200">{item.label}</span>
                <span className="text-[11px] text-zinc-100">{item.state}</span>
              </div>
              <p className="mt-1 break-all text-[10px] text-zinc-500">{item.meta}</p>
            </div>
          ))}
        </div>
        {heartbeatHistory.length ? (
          <div className="mt-3 rounded-lg border border-cyan-500/10 bg-zinc-900/60 p-2">
            <p className="text-[10px] tracking-[0.22em] text-zinc-500">HEARTBEAT TRACE</p>
            <div className="mt-2 space-y-1 font-mono text-[10px] text-zinc-400">
              {heartbeatHistory.slice().reverse().map((beat, idx) => (
                <div key={`${beat.timestamp || idx}_${beat.stepPosition}`} className="flex items-center justify-between gap-2">
                  <span className="truncate text-cyan-200/90">{beat.stepPosition}</span>
                  <span className="shrink-0 text-zinc-500">
                    {beat.idleSec.toFixed(1)}s
                    {beat.timestamp ? ` · ${String(beat.timestamp).slice(11, 19)}` : ""}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      {/* ── LLM 状态概览 ── */}
      <div className="mt-3 space-y-1 text-[11px] text-zinc-200 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <p className="text-[11px] text-cyan-300">LLM 状态概览</p>
        <p>
          模型：
          {connectPhase
            ? `${modelLabel}（待首字）`
            : String(llmMeta.model || llmMeta.llm_endpoint_host || "叙事引擎")}
        </p>
        <p>
          耗时：
          {connectPhase
            ? `${modelLabel} · ${connectTickMs} ms`
            : collapsePhase
              ? "计时中…"
              : llmLifecyclePhase === "closed_without_output"
                ? "流已结束"
                : `${Number(llmMeta.elapsed_ms || 0)} ms`}
        </p>
        <p>
          状态：
          {llmStatusText}
        </p>
        {llmStatusDetail ? <p>步进：{llmStatusDetail}</p> : null}
        {lastHeartbeatStep ? <p>Heartbeat：{lastHeartbeatStep}</p> : null}
        {llmMeta.http_timeout_sec != null ? (
          <p>HTTP 超时：{String(llmMeta.http_timeout_sec)} s</p>
        ) : null}
        {llmMeta.fuse_wait_timeout_sec != null ? (
          <p>Fuse 等待：{String(llmMeta.fuse_wait_timeout_sec)} s</p>
        ) : null}
        {llmMeta.error ? <p className="text-rose-300/90">错误：{String(llmMeta.error)}</p> : null}
      </div>

      {/* ── 初始请求参数 ── */}
      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <p className="text-[11px] text-cyan-300">初始请求参数</p>
        <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md border border-cyan-500/20 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
          {JSON.stringify(
            {
              birth_time: streamQuery.birth_time || birthTimeISO || null,
              gender: streamQuery.gender || natalGender || null,
              calendar_type:
                natalCalendar ||
                (streamBody as { calendar_type?: string } | null)?.calendar_type ||
                null,
              flow_year: streamQuery.flow_year || String(selectedLuckYear),
              will_proxy: streamQuery.will_proxy || null,
              stream_endpoint: streamEndpoint,
              session_id: (streamBody as { session_id?: string } | null)?.session_id || null,
            },
            null,
            2,
          )}
        </pre>
      </div>

      <details className="mt-3 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3" open>
        <summary className="cursor-pointer text-[11px] text-cyan-300">full_prompt_trace 审计</summary>
        <div className="mt-3 space-y-2">
        {fullTrace ? (
          <p className="text-[10px] text-amber-200/90">
            full_prompt_trace：decision_anchor 位于 System Role —{" "}
            {fullTrace.decision_anchor_literal_in_system_role ? "已验证" : "未命中（锚点为空或未写入 System）"}
            {typeof fullTrace.decision_anchor_len === "number"
              ? `（锚点长度 ${String(fullTrace.decision_anchor_len)}）`
              : ""}
          </p>
        ) : collapsePhase || connectPhase || llmLifecyclePhase === "closed_without_output" ? (
          <p className="text-[10px] text-zinc-500">
            {llmAuditSnapshot
              ? "full_prompt_trace：已由 SNAPSHOT（llm_audit_preview）在 fuse 前下发…"
              : "full_prompt_trace：终帧到达后解锁审计字段…"}
          </p>
        ) : null}

        <p className="text-[11px] text-cyan-300">LLM 系统提示词</p>
        <pre className="max-h-32 overflow-auto whitespace-pre-wrap break-words rounded-md border border-cyan-500/20 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
          {String(
            fullTrace?.system_role ??
              llmMeta.llm_system_prompt ??
              "（本期帧未携带，可能为缓存帧或非 LLM 路径）",
          )}
        </pre>
        <p className="text-[11px] text-cyan-300">LLM 用户提示词</p>
        <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md border border-cyan-500/20 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
          {String(fullTrace?.user_role ?? llmMeta.llm_user_prompt ?? "（同上）")}
        </pre>

        {Array.isArray(llmMeta.llm_request_messages) ? (
          <details className="text-[11px] text-zinc-400">
            <summary className="cursor-pointer text-cyan-300/90">完整 messages JSON</summary>
            <pre className="mt-1 max-h-36 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-400">
              {JSON.stringify(llmMeta.llm_request_messages, null, 2)}
            </pre>
          </details>
        ) : null}

        <p className="text-[11px] text-cyan-300">LLM 返回（模型正文，未经 Sanitizer）</p>
        <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md border border-cyan-500/20 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
          {(() => {
            const raw = String(llmMeta.llm_reply ?? "").trim();
            if (raw) return raw;
            if (llmMeta.ok === false) return "（LLM 调用失败，无模型正文；界面判词可能为降级拼接）";
            return String(latestNarrator?.payload?.render_text || "").trim() || "（空）";
          })()}
        </pre>

        <p className="text-[11px] text-cyan-300">上游原始 JSON / SSE（截断）</p>
        <pre className="max-h-32 overflow-auto whitespace-pre-wrap break-words rounded-md border border-cyan-500/20 bg-zinc-950/80 p-2 font-mono text-[9px] text-zinc-400">
          {String(llmMeta.llm_raw_response_json || "").trim() || "（无）"}
        </pre>
        </div>
      </details>

      <details className="mt-3 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <summary className="cursor-pointer text-[11px] text-cyan-300">四柱原始 payload</summary>
        <div className="mt-3 space-y-2">
          <p className="text-[10px] uppercase tracking-[0.22em] text-zinc-500">Physics SNAPSHOT</p>
          <pre className="max-h-56 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
            {JSON.stringify(physicsPayload, null, 2)}
          </pre>
          <p className="text-[10px] uppercase tracking-[0.22em] text-zinc-500">Audit SNAPSHOT</p>
          <pre className="max-h-56 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
            {JSON.stringify(auditPayload, null, 2)}
          </pre>
        </div>
      </details>

      {/* ── 展开式提示词 / 原始回复 ── */}
      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <details className="text-[11px] text-zinc-300">
          <summary className="cursor-pointer text-cyan-300/90">[查看完整提示词 (Prompt)]</summary>
          <p className="mt-1 text-[10px] text-cyan-400/80">System</p>
          <pre className="mt-0.5 max-h-36 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
            {String(fullTrace?.system_role ?? llmMeta.llm_system_prompt ?? "（等待终帧 llm_meta）")}
          </pre>
          <p className="mt-2 text-[10px] text-cyan-400/80">User</p>
          <pre className="mt-0.5 max-h-36 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
            {String(fullTrace?.user_role ?? llmMeta.llm_user_prompt ?? "（等待终帧 llm_meta）")}
          </pre>
        </details>
        <details className="text-[11px] text-zinc-300">
          <summary className="cursor-pointer text-cyan-300/90">[查看原始回复 (Raw)]</summary>
          <p className="mt-1 text-[10px] text-zinc-500">模型正文（未经 Sanitizer）</p>
          <pre className="mt-0.5 max-h-28 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[10px] text-zinc-300">
            {String(llmMeta.llm_reply || "").trim() || "（空）"}
          </pre>
          <p className="mt-2 text-[10px] text-zinc-500">上游 JSON / SSE</p>
          <pre className="mt-0.5 max-h-28 overflow-auto whitespace-pre-wrap break-words rounded-md border border-zinc-700 bg-zinc-950/80 p-2 font-mono text-[9px] text-zinc-400">
            {String(llmMeta.llm_raw_response_json || "").trim() || "（无）"}
          </pre>
        </details>
      </div>
        </>
      ) : null}
    </aside>
  );
}
