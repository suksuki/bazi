"use client";

/**
 * V17.23 — V17_TracePanel
 *
 * 因果链路调试面板（原 OraclePage 第 365–505 行）。
 * Props 由 useOracleSession 直接传入，完全无状态。
 */

interface TracePanelProps {
  collapsed: boolean;
  onToggle: () => void;
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
  physicsSnapshot?: {
    payload?: {
      causal_anchor?: unknown;
      physics_fingerprint?: unknown;
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
      pattern?: string;
      physics_tension?: number;
      four_pillars?: Record<string, unknown>;
      luck_pillar?: unknown;
      flow_pillar?: unknown;
      flow_year?: unknown;
      plugins?: {
        hits?: unknown[];
        rows?: Array<Record<string, unknown>>;
      };
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

export function V17_TracePanel({
  collapsed,
  onToggle,
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
}: TracePanelProps) {
  const physicsPayload = (physicsSnapshot?.payload ?? {}) as Record<string, unknown>;
  const auditPayload =
    llmAuditSnapshot && typeof llmAuditSnapshot === "object"
      ? (((llmAuditSnapshot as { payload?: Record<string, unknown> }).payload ?? {}) as Record<string, unknown>)
      : {};
  const scoreMap =
    physicsSnapshot?.payload?.ten_gods_absolute_intensity || physicsSnapshot?.payload?.deity_scores || {};
  const ledgerRaw = physicsSnapshot?.payload?.ten_gods_ledger || {};
  const deityScores = Object.entries(scoreMap)
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
  const maxDeityScore = deityScores.length ? Math.max(...deityScores.map((row) => row.score), 1) : 1;
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
  const manualDecisions = Array.isArray(physicsPayload.manual_decisions)
    ? (physicsPayload.manual_decisions as Array<Record<string, unknown>>)
    : [];
  const autoResolutions = Array.isArray(physicsPayload.auto_resolutions)
    ? (physicsPayload.auto_resolutions as Array<Record<string, unknown>>)
    : [];
  const llmArbitrationContext = Array.isArray(physicsPayload.llm_arbitration_context)
    ? (physicsPayload.llm_arbitration_context as Array<Record<string, unknown>>)
    : [];
  const groupedPlugins = pluginRows.reduce<Record<string, string[]>>((acc, row) => {
    const plugin = String(row.plugin || row.source || "unknown").trim() || "unknown";
    const fact = String(row.fact || row.label || row.title || "").trim();
    if (!fact) return acc;
    acc[plugin] = [...(acc[plugin] || []), fact];
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

  if (collapsed) {
    return (
      <aside className="sticky top-6 flex h-fit min-h-[28rem] w-14 flex-col items-center rounded-2xl border border-cyan-500/25 bg-zinc-900/70 py-3 shadow-[0_18px_60px_rgba(8,145,178,0.12)]">
        <button
          type="button"
          onClick={onToggle}
          className="rounded-full border border-cyan-400/35 bg-cyan-950/55 px-3 py-2 text-[10px] tracking-[0.35em] text-cyan-200 transition hover:bg-cyan-900/70"
          title="展开调试边栏"
        >
          DEBUG
        </button>
        <div className="mt-4 flex flex-1 items-center">
          <span className="[writing-mode:vertical-rl] text-[10px] tracking-[0.4em] text-zinc-500">
            元数据 / 链路
          </span>
        </div>
      </aside>
    );
  }

  return (
    <aside className="sticky top-6 h-fit rounded-2xl border border-cyan-500/40 bg-[linear-gradient(180deg,rgba(10,18,24,0.96),rgba(9,14,19,0.88))] p-3 shadow-[0_22px_70px_rgba(8,145,178,0.16)]">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div>
          <p className="text-xs tracking-[0.28em] text-cyan-200">DEBUG SIDEBAR</p>
          <p className="mt-1 text-[11px] text-zinc-500">元数据 / 因果链路 / LLM 调试</p>
        </div>
        <button
          type="button"
          onClick={onToggle}
          className="rounded-full border border-cyan-400/35 bg-cyan-950/50 px-3 py-1 text-[10px] text-cyan-200 transition hover:bg-cyan-900/70"
        >
          收起
        </button>
      </div>

      <div className="space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <p className="text-[11px] text-cyan-300">八字元数据</p>
        <div className="space-y-1 text-[11px] text-zinc-200">
          <p>格局：{String(physicsSnapshot?.payload?.pattern || "—")}</p>
          <p>张力：{Number(physicsSnapshot?.payload?.physics_tension || 0).toFixed(2)}</p>
          <p>六柱：{pillarText || "—"}</p>
          <p>
            运势：
            {String(physicsSnapshot?.payload?.luck_pillar || "—")} / {String(physicsSnapshot?.payload?.flow_pillar || "—")}
          </p>
          <p>流年锚年：{String(physicsSnapshot?.payload?.flow_year || "—")}</p>
          <p>十神主轴：{tenGods.length ? tenGods.join(" / ") : "—"}</p>
          <p>总能量指数：{Number(physicsSnapshot?.payload?.total_energy_index || 0).toFixed(2)}</p>
        </div>
        <div className="mt-2 space-y-1">
          <p className="text-[10px] uppercase tracking-[0.24em] text-zinc-500">Absolute Intensity</p>
          {deityScores.length ? (
            <div className="space-y-1">
              {deityScores.map((row) => (
                <div key={row.name} className="group relative rounded-lg border border-cyan-500/15 bg-zinc-900/80 px-2 py-1.5 transition hover:border-cyan-500/40">
                  <div className="mb-1 flex items-center justify-between text-[11px] text-zinc-200">
                    <span className="flex items-center gap-1">
                      {row.name}
                      {Math.abs(row.ratioDelta) >= 0.005 && (
                        <span className={`text-[9px] font-bold ${row.delta > 0 ? "text-[#10B981]" : "text-[#EF4444]"}`}>
                          {row.delta > 0 ? "↑" : "↓"} {(Math.abs(row.ratioDelta) * 100).toFixed(1)}%
                        </span>
                      )}
                    </span>
                    <span className="font-mono text-cyan-200">
                      {row.score.toFixed(2)}
                      {Math.abs(row.ratioDelta) >= 0.005 && (
                         <span className="ml-1 text-[9px] text-zinc-500">
                           (was {row.prevScore.toFixed(0)})
                         </span>
                      )}
                    </span>
                  </div>
                  <div className="relative h-2 overflow-hidden rounded-full bg-zinc-800">
                    {/* Ghost Bar: 上一次操作的能级 (背景条) */}
                    <div
                      className="absolute left-0 top-0 h-full rounded-full bg-zinc-700/50"
                      style={{ width: `${Math.max(2, Math.min(100, (row.prevScore / maxDeityScore) * 100))}%` }}
                    />
                    {/* Current Bar: 当前能级 (主条) */}
                    <div
                      className="absolute left-0 top-0 h-full rounded-full bg-[linear-gradient(90deg,rgba(34,211,238,0.7),rgba(103,232,249,1))]"
                      style={{ 
                        width: `${Math.max(4, Math.min(100, (row.score / maxDeityScore) * 100))}%`,
                        boxShadow: row.delta > 0 ? '0 0 8px rgba(16, 185, 129, 0.4)' : 'none',
                        transition: 'width 320ms ease, box-shadow 220ms ease'
                      }}
                    />
                  </div>

                  {/* 终端风格演化回溯 Tooltip */}
                  <div className="pointer-events-none absolute left-full top-0 z-[100] ml-2 hidden w-80 origin-left scale-95 rounded border border-cyan-500/30 bg-black/95 p-2 shadow-2xl backdrop-blur-md group-hover:block group-hover:scale-100 transition-all duration-150">
                    <p className="mb-2 border-b border-cyan-500/20 pb-1 text-[9px] font-bold uppercase tracking-widest text-cyan-400">
                      EVOLUTION_LEDGER: {row.name} (CAP=8)
                    </p>
                    <div className="space-y-1">
                      {row.history.filter((entry, idx) => idx === 0 || entry.visible_ratio_change !== false).map((entry, idx) => (
                        <div
                          key={idx}
                          className={`font-mono text-[9px] leading-tight px-1 py-0.5 rounded ${
                            entry.highlight_type === "cyan" || entry.step === "L1.5_FLOW_SETTLEMENT"
                              ? "bg-cyan-500/10 border-l border-cyan-500/50"
                              : ""
                          }`}
                        >
                          <span className={`${entry.step.startsWith('L1.5') ? 'text-cyan-400 font-bold' : 'text-zinc-500'}`}>[{entry.step}]</span>
                          <span className="mx-1 text-zinc-600">{"->"}</span>
                          {typeof entry.ratio_applied === "number" && Math.abs(entry.ratio_applied) >= 0.005 ? (
                            <span className={entry.ratio_applied > 0 ? "text-[#10B981]" : entry.ratio_applied < 0 ? "text-[#EF4444]" : "text-zinc-600"}>
                              {entry.ratio_applied > 0 ? "+" : ""}{(entry.ratio_applied * 100).toFixed(1)}%
                            </span>
                          ) : entry.delta != null && (
                            <span className={entry.delta > 0 ? "text-[#10B981]" : entry.delta < 0 ? "text-[#EF4444]" : "text-zinc-600"}>
                              {entry.delta > 0 ? "+" : ""}{entry.delta.toFixed(2)}
                            </span>
                          )}
                          <span className="mx-1 text-zinc-600">{"->"}</span>
                          <span className="text-cyan-300">{entry.val.toFixed(2)}</span>
                          <span className="mx-2 text-zinc-700">|</span>
                          <span className="text-zinc-400 italic">{entry.reason}</span>
                        </div>
                      ))}
                    </div>

                    {/* V17.34：电流拓扑图简版 */}
                    {physicsSnapshot?.payload?.flow_topology && (
                      <div className="mt-3 border-t border-cyan-500/20 pt-2">
                        <p className="mb-1 text-[8px] font-bold text-zinc-500 uppercase tracking-widest">Global Current Topology (KCL)</p>
                        <div className="grid grid-cols-1 gap-0.5 text-[8px] font-mono text-zinc-400">
                           {(physicsSnapshot.payload.flow_topology as Array<{rel: string, from_el: string, to_el: string, current: number, resistance?: number, stress?: number}>).filter(f => f.from_el === row.name || f.to_el === row.name).slice(0, 6).map((flow, fidx) => (
                             <div key={fidx} className="flex items-center gap-1">
                                <span className={flow.rel === "生" ? "text-emerald-500" : "text-amber-500"}>{flow.from_el}</span>
                                <span className="text-zinc-600">{"--("}{flow.rel}/I={flow.current.toFixed(1)}/R={(flow.resistance ?? 0).toFixed(2)}{")-->"}</span>
                                <span className={flow.rel === "生" ? "text-emerald-500" : "text-amber-500"}>{flow.to_el}</span>
                             </div>
                           ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[11px] text-zinc-500">暂无十神数值</p>
          )}
        </div>
      </div>

      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-cyan-300">因果锚点</p>
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] ${
              causalAligned ? "bg-emerald-950/80 text-emerald-200" : "bg-amber-950/80 text-amber-200"
            }`}
          >
            {causalAligned ? "已对齐" : "待核对"}
          </span>
        </div>
        <div className="space-y-1 text-[11px] text-zinc-200">
          <p>物理快照：{causalPhysicsAnchor}</p>
          <p className="font-mono text-[10px] text-cyan-200/90 break-all">fp={causalPhysicsFp}</p>
          <p>审计快照：{causalAuditAnchor}</p>
          <p className="font-mono text-[10px] text-cyan-200/90 break-all">fp={causalAuditFp}</p>
        </div>
      </div>

      <div className="mt-3 space-y-2 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3">
        <div className="flex items-center justify-between">
          <p className="text-[11px] text-cyan-300">仲裁分流</p>
          <span className="text-[10px] text-zinc-500">
            手动 {manualDecisions.length} / 系统 {autoResolutions.length} / LLM {llmArbitrationContext.length}
          </span>
        </div>
        <div className="space-y-2">
          <div className="rounded-lg border border-violet-500/15 bg-zinc-900/60 p-2">
            <p className="text-[10px] tracking-[0.2em] text-violet-200">MANUAL_DECISIONS</p>
            <div className="mt-2 space-y-1 text-[10px] text-zinc-300">
              {manualDecisions.length ? manualDecisions.slice(0, 8).map((row, idx) => (
                <div key={`manual_${idx}`} className="rounded border border-violet-500/10 bg-zinc-950/60 px-2 py-1">
                  <p className="text-violet-100">{String(row.label || row.title || "—")}</p>
                  <p className="mt-0.5 text-zinc-500">
                    {String(row.source || row.plugin_id || "unknown")} · {String(row.target_god || (row.physical_impact as Record<string, unknown> | undefined)?.target_god || "无目标神")}
                  </p>
                  <p className="mt-0.5 font-mono text-violet-200/80">{traceArbitrationChain(row, "手动")}</p>
                  {row.resolved_from_llm ? <p className="mt-0.5 text-cyan-200/80">来自 LLM 仲裁 · {String(row.llm_resolution_state || "promoted_to_manual")}</p> : null}
                  <p className="mt-0.5 text-zinc-400">{traceImpactText(row)}</p>
                </div>
              )) : <p className="text-zinc-500">暂无手动裁决项</p>}
            </div>
          </div>

          <div className="rounded-lg border border-amber-500/15 bg-zinc-900/60 p-2">
            <p className="text-[10px] tracking-[0.2em] text-amber-200">AUTO_RESOLUTIONS</p>
            <div className="mt-2 space-y-1 text-[10px] text-zinc-300">
              {autoResolutions.length ? autoResolutions.slice(0, 8).map((row, idx) => (
                <div key={`auto_${idx}`} className="rounded border border-amber-500/10 bg-zinc-950/60 px-2 py-1">
                  <p className="text-amber-100">{String(row.label || row.title || "—")}</p>
                  <p className="mt-0.5 text-zinc-500">{String(row.source || row.plugin_id || "unknown")}</p>
                  <p className="mt-0.5 font-mono text-amber-200/80">{traceArbitrationChain(row, "自动")}</p>
                  {row.resolved_from_llm ? <p className="mt-0.5 text-cyan-200/80">来自 LLM 仲裁 · {String(row.llm_resolution_state || "collapsed_to_system")}</p> : null}
                  <p className="mt-0.5 text-zinc-400">{tracePromptPreview(row)}</p>
                </div>
              )) : <p className="text-zinc-500">暂无系统自动裁决项</p>}
            </div>
          </div>

          <div className="rounded-lg border border-cyan-500/15 bg-zinc-900/60 p-2">
            <p className="text-[10px] tracking-[0.2em] text-cyan-200">LLM_ARBITRATION_CONTEXT</p>
            <div className="mt-2 space-y-1 text-[10px] text-zinc-300">
              {llmArbitrationContext.length ? llmArbitrationContext.slice(0, 8).map((row, idx) => (
                <div key={`llm_${idx}`} className="rounded border border-cyan-500/10 bg-zinc-950/60 px-2 py-1">
                  <p className="text-cyan-100">{String(row.label || row.title || "—")}</p>
                  <p className="mt-0.5 text-zinc-500">{String(row.source || row.plugin_id || "unknown")}</p>
                  <p className="mt-0.5 font-mono text-cyan-200/80">{traceArbitrationChain(row, "LLM")}</p>
                  <p className="mt-0.5 text-zinc-400">
                    {String(row.llm_resolution_policy || "context_only")} · {String(row.llm_resolution_state || "pending_context")} · {String(row.llm_resolution_result || "consume_context")}
                  </p>
                  <p className="mt-0.5 text-zinc-400">{tracePromptPreview(row)}</p>
                </div>
              )) : <p className="text-zinc-500">暂无 LLM 仲裁上下文</p>}
            </div>
          </div>
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

      <details className="mt-3 rounded-xl border border-cyan-500/20 bg-zinc-950/70 p-3" open>
        <summary className="cursor-pointer text-[11px] text-cyan-300">插件 / Fact 分组</summary>
        <div className="mt-3">
        <p className="text-[11px] text-cyan-300">命中插件</p>
        <p className="mt-1 text-[11px] text-zinc-200">
          {traceHits.length ? (traceHits as string[]).join(" / ") : "暂无命中"}
        </p>
        </div>
        <div className="mt-3">
        <p className="text-[11px] text-cyan-300">织造 Fact</p>
        <div className="mt-1 space-y-1">
          {traceFacts.length ? (
            (traceFacts as string[]).map((x, idx) => (
              <p key={`${idx}_${x}`} className="text-[11px] text-zinc-200">
                {idx + 1}. {String(x)}
              </p>
            ))
          ) : (
            <p className="text-[11px] text-zinc-500">暂无 Fact</p>
          )}
        </div>
        </div>
        <div className="mt-3 space-y-2">
          <p className="text-[11px] text-cyan-300">插件分组</p>
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
            <p className="text-[11px] text-zinc-500">暂无插件分组</p>
          )}
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
    </aside>
  );
}
