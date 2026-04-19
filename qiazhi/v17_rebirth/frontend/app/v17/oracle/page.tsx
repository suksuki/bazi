"use client";

/**
 * V17.23 — OraclePage（精简版）
 *
 * 组件职责：纯 JSX 组合 + 路由入口。
 * 所有状态与业务逻辑已迁移至 hooks/useOracleSession.ts。
 * 调试面板已迁移至 components/V17_TracePanel.tsx。
 */

import { RotateCcw, Sparkles } from "lucide-react";

import { V17_DecisionInbox } from "@/components/V17_DecisionInbox";
import { V17_NatalInput } from "@/components/V17_NatalInput";
import { V17_PurpleVerdictCard } from "@/components/V17_PurpleVerdictCard";
import { V17_SixPillarsPanel } from "@/components/V17_SixPillarsPanel";
import { V17_TracePanel } from "@/components/V17_TracePanel";
import { useOracleSession } from "@/hooks/useOracleSession";
import { classicalPatternCatalog } from "@/types/classicalPatternCatalog";

function decisionPluginLabel(row: Record<string, unknown>): string {
  return String(
    row.source_label || row.display_name || row.definition_text || row.plugin_id || row.source || "",
  ).trim();
}

function normalizePluginKey(value: unknown): string {
  return String(value || "").trim().toLowerCase();
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

function patternConfidenceTone(score: number): string {
  if (score >= 0.82) return "border-emerald-500/25 bg-emerald-950/35 text-emerald-100";
  if (score >= 0.64) return "border-cyan-500/25 bg-cyan-950/35 text-cyan-100";
  if (score >= 0.48) return "border-amber-500/25 bg-amber-950/35 text-amber-100";
  return "border-zinc-500/20 bg-zinc-900/70 text-zinc-300";
}

function normalizePatternScope(scope: unknown): string {
  const key = String(scope || "").trim();
  if (key === "natal") return "原局";
  if (key === "luck_background") return "大运背景";
  if (key === "luck_only") return "大运触发";
  if (key === "flow_trigger") return "流年引动";
  if (key === "flow_only") return "流年主导";
  if (key === "runtime_pair") return "运流联动";
  if (key === "mixed") return "混合来源";
  return key || "来源待定";
}

function patternFamilyByName(name: string): string {
  return classicalPatternCatalog.find((item) => item.name === name)?.family || "格局候选";
}

type LivePatternCandidate = {
  key: string;
  name: string;
  family: string;
  confidence: number;
  scope: string;
  source: string;
  target: string;
  projectionText: string;
  profileText: string;
  manifestation: string;
  scopeWeights: Array<{ label: string; ratio: number }>;
  gate: string;
  gateReason: string;
  breakRisks: string[];
  statusLabel: string;
};

function normalizeManifestation(value: unknown): string {
  const key = String(value || "").trim();
  if (key === "manifested") return "成格";
  if (key === "supported") return "候选成立";
  if (key === "latent") return "潜势待成";
  if (key === "contested") return "受扰待核";
  return "观察中";
}

function patternStatusToneForRuntime(status: string): string {
  if (status === "成格") return "border-emerald-500/25 bg-emerald-950/35 text-emerald-100";
  if (status === "候选成立") return "border-cyan-500/25 bg-cyan-950/35 text-cyan-100";
  if (status === "受扰待核") return "border-rose-500/25 bg-rose-950/35 text-rose-100";
  if (status === "潜势待成") return "border-amber-500/25 bg-amber-950/35 text-amber-100";
  return "border-zinc-500/20 bg-zinc-900/70 text-zinc-300";
}

function normalizeScopeWeights(value: unknown): Array<{ label: string; ratio: number }> {
  if (!value || typeof value !== "object") return [];
  return Object.entries(value as Record<string, unknown>)
    .map(([key, raw]) => ({ label: normalizePatternScope(key), ratio: Number(raw || 0) }))
    .filter((item) => Number.isFinite(item.ratio) && item.ratio > 0)
    .sort((a, b) => b.ratio - a.ratio)
    .slice(0, 4);
}

function buildPatternJudgement(
  leader: LivePatternCandidate | undefined,
  runners: LivePatternCandidate[],
): string {
  if (!leader) return "当前盘面尚未形成稳定格局候选，系统仍在等待更多结构证据完成聚合。";
  const parts: string[] = [];
  const leadScope = leader.scope || "来源待定";
  const leadStatus = leader.statusLabel || "观察中";
  parts.push(`当前以「${leader.name}」为主格局，处于${leadStatus}态势`);
  parts.push(`主要证据来自${leadScope}`);
  if (leader.target && leader.target !== "未定目标") {
    parts.push(`主落点聚焦在${leader.target}`);
  }
  if (runners.length) {
    const topRunners = runners
      .slice(0, 2)
      .map((item) => `${item.name}${Math.round(item.confidence * 100)}%`)
      .join("、");
    if (topRunners) parts.push(`次格局候选包括${topRunners}`);
  }
  if (leader.breakRisks.length) {
    parts.push(`但当前受${leader.breakRisks.slice(0, 2).join("、")}牵制，仍需继续核验是否破格`);
  } else if (leader.gateReason) {
    parts.push(leader.gateReason);
  }
  return `${parts.join("，")}。`;
}

function deriveLivePatternCandidates(
  allRows: Array<Record<string, unknown>>,
  pluginClaims: Array<Record<string, unknown>>,
): LivePatternCandidate[] {
  const candidates = new Map<string, LivePatternCandidate>();
  let globalGate = "";
  let globalGateReason = "";
  let globalBreakRisks: string[] = [];
  const ingest = (row: Record<string, unknown>, source: string) => {
    const name = String(row.pattern_candidate || row.pattern_name || "").trim();
    if (!name) return;
    const confidenceRaw = row.pattern_confidence_percent ?? row.pattern_confidence ?? row.match_ratio ?? 0;
    let confidence = Number(confidenceRaw || 0);
    if (confidence > 1) confidence = confidence / 100;
    confidence = Number.isFinite(confidence) ? confidence : 0;
    const target = String(row.target_god || "").trim();
    const scope = String(row.pattern_scope_label || normalizePatternScope(row.pattern_scope)).trim();
    const projectionText = compactProjection(row.cluster_projection);
    const manifestation = normalizeManifestation(row.manifestation_state);
    const scopeWeights = normalizeScopeWeights(row.scope_weights);
    const profile = Array.isArray(row.pattern_profile) ? row.pattern_profile : [];
    const profileText = profile
      .slice(0, 3)
      .map((item) => {
        if (!item || typeof item !== "object") return "";
        const family = String((item as { family?: string }).family || "").trim();
        const percent = Number((item as { percent?: number }).percent || 0);
        if (!family) return "";
        return `${family}${percent > 0 ? ` ${Math.round(percent)}%` : ""}`;
      })
      .filter(Boolean)
      .join(" / ");
    const key = `${name}::${target || "na"}`;
    const current = candidates.get(key);
    const next: LivePatternCandidate = {
      key,
      name,
      family: patternFamilyByName(name),
      confidence,
      scope: scope || "来源待定",
      source,
      target: target || "未定目标",
      projectionText,
      profileText,
      manifestation,
      scopeWeights,
      gate: globalGate,
      gateReason: globalGateReason,
      breakRisks: globalBreakRisks,
      statusLabel: manifestation,
    };
    if (!current || next.confidence > current.confidence) {
      candidates.set(key, next);
      return;
    }
    if (current && !current.scopeWeights.length && scopeWeights.length) current.scopeWeights = scopeWeights;
    if (current && !current.profileText && profileText) current.profileText = profileText;
    if (current && !current.projectionText && projectionText) current.projectionText = projectionText;
    if (current && current.statusLabel === "观察中" && manifestation !== "观察中") current.statusLabel = manifestation;
  };

  for (const row of [...pluginClaims, ...allRows]) {
    const pluginId = String(row.plugin_id || row.source || "").trim();
    if (pluginId === "classical.pattern.formation_gate.v1") {
      globalGate = String(row.pattern_gate || "").trim();
      globalGateReason = String(row.pattern_gate_reason || "").trim();
    }
    if (pluginId === "classical.pattern.break_guard.v1") {
      globalBreakRisks = Array.isArray(row.pattern_break_risks)
        ? (row.pattern_break_risks as unknown[]).map((item) => String(item || "").trim()).filter(Boolean)
        : [];
    }
  }

  for (const row of pluginClaims) ingest(row, "claim");
  for (const row of allRows) ingest(row, "decision");

  return Array.from(candidates.values())
    .map((item) => {
      const statusLabel = item.breakRisks.length
        ? "受扰待核"
        : item.gate === "月令成格" || item.gate === "强轴成格" || item.gate === "双线成格"
          ? "成格"
          : item.manifestation;
      return { ...item, gate: globalGate, gateReason: globalGateReason, breakRisks: globalBreakRisks, statusLabel };
    })
    .sort((a, b) => b.confidence - a.confidence);
}

export default function OraclePage() {
  const s = useOracleSession();

  const payload = (s.physicsSnapshot?.payload || {}) as Record<string, unknown>;
  const fourPillars =
    payload.four_pillars && typeof payload.four_pillars === "object"
      ? (payload.four_pillars as { year?: string; month?: string; day?: string; hour?: string })
      : undefined;
  const luckPillarSnap = payload.luck_pillar;
  const flowPillarSnap = payload.flow_pillar;
  const manualRows = Array.isArray(payload.manual_inbox) ? payload.manual_inbox as Array<Record<string, unknown>> : [];
  const autoRows = Array.isArray(payload.auto_decisions) ? payload.auto_decisions as Array<Record<string, unknown>> : [];
  const allRows = Array.isArray(payload.all_decisions) ? payload.all_decisions as Array<Record<string, unknown>> : [];
  const meta = payload.meta && typeof payload.meta === "object" ? payload.meta as Record<string, unknown> : {};
  const pluginClaims = Array.isArray(meta.plugin_claims) ? meta.plugin_claims as Array<Record<string, unknown>> : [];
  const recomputeContributions = Array.isArray(meta.plugin_recompute_contributions)
    ? meta.plugin_recompute_contributions as Array<Record<string, unknown>>
    : [];
  const pluginLabelById = new Map<string, string>();
  for (const row of allRows) {
    const label = decisionPluginLabel(row);
    const key = normalizePluginKey(row.plugin_id || row.source);
    if (key && label && !pluginLabelById.has(key)) pluginLabelById.set(key, label);
  }
  const uniquePlugins = Array.from(
    new Set(
      allRows
        .map(decisionPluginLabel)
        .filter(Boolean),
    ),
  );
  const manualPlugins = Array.from(
    new Set(
      manualRows
        .map(decisionPluginLabel)
        .filter(Boolean),
    ),
  );
  const autoPlugins = Array.from(
    new Set(
      autoRows
        .map(decisionPluginLabel)
        .filter(Boolean),
      ),
  );
  const pluginMatchRows = Array.from(
    pluginClaims.reduce((acc, row) => {
      const key = normalizePluginKey(row.plugin_id);
      if (!key) return acc;
      const current = acc.get(key) || { count: 0, sum: 0, pluginId: String(row.plugin_id || ""), label: pluginLabelById.get(key) || String(row.plugin_id || "") };
      const ratio = Number(row.match_ratio || 0);
      if (Number.isFinite(ratio) && ratio > 0) {
        current.count += 1;
        current.sum += ratio;
      }
      acc.set(key, current);
      return acc;
    }, new Map<string, { count: number; sum: number; pluginId: string; label: string }>() ).values(),
  )
    .map((row) => ({ ...row, avg: row.count ? row.sum / row.count : 0 }))
    .filter((row) => row.count > 0)
    .sort((a, b) => b.avg - a.avg)
    .slice(0, 8);
  const pluginFocusRows = Array.from(
    pluginClaims.reduce((acc, row) => {
      const key = normalizePluginKey(row.plugin_id);
      if (!key) return acc;
      const projectionText = compactProjection(row.cluster_projection);
      const existing = acc.get(key);
      const ratio = Number(row.match_ratio || 0);
      const candidate = {
        pluginId: String(row.plugin_id || ""),
        label: pluginLabelById.get(key) || String(row.plugin_id || ""),
        target: String(row.target_god || "").trim(),
        ratio: Number.isFinite(ratio) ? ratio : 0,
        projectionText,
        share: Number(row.projection_share || 0),
      };
      if (!existing || candidate.ratio > existing.ratio) acc.set(key, candidate);
      return acc;
    }, new Map<string, { pluginId: string; label: string; target: string; ratio: number; projectionText: string; share: number }>() ).values(),
  )
    .sort((a, b) => b.ratio - a.ratio)
    .slice(0, 6);
  const livePatternCandidates = deriveLivePatternCandidates(allRows, pluginClaims);
  const patternLeader = livePatternCandidates[0];
  const patternRunners = livePatternCandidates.slice(1, 4);
  const activePatternScopes = Array.from(new Set(livePatternCandidates.map((item) => item.scope).filter(Boolean))).slice(0, 5);
  const leaderBreakRisks = patternLeader?.breakRisks || [];
  const patternJudgement = buildPatternJudgement(patternLeader, patternRunners);

  return (
    <main className="min-h-screen bg-zinc-950 p-6 text-zinc-100">
      <section className="mx-auto flex w-full max-w-4xl flex-col gap-4">

        {/* ── 顶栏 ── */}
        <header className="flex items-center justify-between gap-2 text-violet-300">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            <h1 className="text-lg font-semibold tracking-wide">V17 Oracle Temple</h1>
          </div>
          {s.running ? (
            <button
              type="button"
              onClick={s.resetRun}
              className="inline-flex items-center gap-1 rounded-md border border-violet-300/40 bg-violet-900/20 px-2 py-1 text-xs text-violet-100 hover:bg-violet-800/30"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              重测
            </button>
          ) : null}
        </header>

        {/* ── 排盘输入 ── */}
        <div className="relative">
          {s.running ? (
            <div className="absolute inset-0 z-20 animate-[fadeOut_280ms_ease-out_forwards] rounded-2xl bg-black/50 backdrop-blur-[1px]" />
          ) : null}
          {!s.running ? <V17_NatalInput onStart={s.startRun} /> : null}
        </div>

        {/* ── 运行态主体 ── */}
        {s.running ? (
          <div
            className={`grid min-h-[60vh] gap-3 ${
              s.traceOpen ? "md:grid-cols-[1fr_320px]" : "md:grid-cols-[1fr_64px]"
            }`}
          >

            {/* ── 左列：命盘 + 判词 + 决策收件箱 ── */}
            <div className="w-full space-y-3">
              <V17_SixPillarsPanel
                fourPillars={fourPillars}
                luckPillarFromServer={typeof luckPillarSnap === "string" ? luckPillarSnap : undefined}
                flowPillarFromServer={typeof flowPillarSnap === "string" ? flowPillarSnap : undefined}
                birthTimeISO={s.birthTimeISO}
                gender={s.natalGender}
                calendarType={s.natalCalendar}
                selectedYear={s.selectedLuckYear}
                onYearChange={s.setSelectedLuckYear}
              />
              <V17_PurpleVerdictCard
                frames={s.frames}
                onToggleTrace={() => s.setTraceOpen((v) => !v)}
                connectTickMs={s.connectTickMs}
                running={s.running}
                llmStatusText={s.llmStatusText}
                llmStatusDetail={s.llmStatusDetail}
                llmLifecyclePhase={s.llmLifecyclePhase}
              />
              <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-2.5">
                <p className="text-xs text-zinc-400">
                  待处理决策 {s.pendingDecisionWorkCount} 条
                  {s.canAutoGenerateVerdict ? " · 已满足自动生成断言条件" : " · 处理完成后将自动生成新断言"}
                </p>
                <button
                  type="button"
                  onClick={() => s.triggerVerdict("请基于当前已通过的决策，生成新的八字断言。")}
                  className="inline-flex items-center gap-1 rounded-md border border-cyan-500/30 bg-cyan-950/25 px-2 py-1 text-xs text-cyan-100 hover:bg-cyan-900/35"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  显示八字断言
                </button>
              </div>
              {uniquePlugins.length ? (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-zinc-300">
                    <span>命中插件 {uniquePlugins.length}</span>
                    <span>手动来源 {manualPlugins.length}</span>
                    <span>自动/上下文 {autoPlugins.length}</span>
                  </div>
                  <div className="mt-2 grid gap-2 md:grid-cols-2">
                    <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-2">
                      <div className="text-[10px] uppercase tracking-wide text-amber-300">Manual Sources</div>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {manualPlugins.length ? manualPlugins.map((name) => (
                          <span key={`manual_${name}`} className="rounded-full border border-amber-900/50 bg-amber-950/30 px-2 py-0.5 text-[10px] text-amber-100">
                            {name}
                          </span>
                        )) : <span className="text-[10px] text-zinc-500">当前没有手动来源插件。</span>}
                      </div>
                    </div>
                    <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-2">
                      <div className="text-[10px] uppercase tracking-wide text-sky-300">Auto / Context Sources</div>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {autoPlugins.length ? autoPlugins.map((name) => (
                          <span key={`auto_${name}`} className="rounded-full border border-sky-900/50 bg-sky-950/30 px-2 py-0.5 text-[10px] text-sky-100">
                            {name}
                          </span>
                        )) : <span className="text-[10px] text-zinc-500">当前没有自动或上下文来源插件。</span>}
                      </div>
                    </div>
                  </div>
                  {pluginMatchRows.length ? (
                    <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-950/60 p-2">
                      <div className="text-[10px] uppercase tracking-wide text-emerald-300">Plugin Match Ratio</div>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {pluginMatchRows.map((row) => (
                          <span key={`match_${row.pluginId}`} className="rounded-full border border-emerald-900/50 bg-emerald-950/30 px-2 py-0.5 text-[10px] text-emerald-100">
                            {row.label} {Math.round(row.avg * 100)}%
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {pluginFocusRows.length ? (
                    <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-950/60 p-2">
                      <div className="text-[10px] uppercase tracking-wide text-fuchsia-300">Plugin Focus Map</div>
                      <div className="mt-2 grid gap-1.5">
                        {pluginFocusRows.map((row) => (
                          <div key={`focus_${row.pluginId}`} className="rounded border border-zinc-800 bg-zinc-900/50 px-2 py-1 text-[10px] text-zinc-300">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <span className="text-fuchsia-100">{row.label}</span>
                              <span className="text-fuchsia-300">{Math.round(row.ratio * 100)}%</span>
                            </div>
                            <div className="mt-0.5 text-zinc-400">
                              主落点 {row.target || "未定"}{row.share > 0 ? ` · 占比 ${Math.round(row.share * 100)}%` : ""}
                            </div>
                            {row.projectionText ? <div className="mt-0.5 text-zinc-500">{row.projectionText}</div> : null}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {recomputeContributions.length ? (
                    <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-950/60 p-2">
                      <div className="text-[10px] uppercase tracking-wide text-sky-300">Base Recompute Contributions</div>
                      <div className="mt-2 grid gap-1">
                        {recomputeContributions.slice(0, 8).map((row, idx) => (
                          <div key={`recompute_${idx}`} className="flex flex-wrap items-center justify-between gap-2 text-[10px] text-zinc-300">
                            <span>{String(row.target_god || "—")}</span>
                            <span className="text-zinc-500">
                              {Number(row.before || 0).toFixed(2)} → {Number(row.after || 0).toFixed(2)}
                            </span>
                            <span className="text-sky-300">delta {Number(row.delta_abs || 0).toFixed(2)}</span>
                            <span className="text-zinc-500">ratio {Number(row.ratio_total || 0).toFixed(3)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
              <div className="rounded-xl border border-cyan-500/20 bg-[linear-gradient(180deg,rgba(12,74,110,0.32),rgba(9,9,11,0.76))] p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.22em] text-cyan-300">Pattern Overview</p>
                    <p className="mt-1 text-sm text-cyan-50">当前盘面的主格局、次格局、动态来源、置信度与系统判读</p>
                  </div>
                  <div className="flex flex-wrap gap-1.5 text-[10px]">
                    <span className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-2 py-1 text-cyan-100">
                      候选 {livePatternCandidates.length}
                    </span>
                    {activePatternScopes.map((scope) => (
                      <span key={`pattern_scope_${scope}`} className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-2 py-1 text-cyan-100">
                        {scope}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="mt-3 rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3">
                  <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">System Reading</p>
                  <p className="mt-2 text-[12px] leading-6 text-cyan-50">{patternJudgement}</p>
                </div>

                {patternLeader ? (
                  <div className="mt-3 grid gap-3 xl:grid-cols-[1.05fr_0.95fr]">
                    <div className="rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">Primary Pattern</p>
                          <p className="mt-1 text-lg text-cyan-50">{patternLeader.name}</p>
                          <p className="mt-1 text-[11px] text-zinc-400">{patternLeader.family}</p>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          <span className={`rounded-full border px-2 py-1 text-[10px] ${patternStatusToneForRuntime(patternLeader.statusLabel)}`}>
                            {patternLeader.statusLabel}
                          </span>
                          <span className={`rounded-full border px-2 py-1 text-[10px] ${patternConfidenceTone(patternLeader.confidence)}`}>
                            置信 {Math.round(patternLeader.confidence * 100)}%
                          </span>
                        </div>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-1.5 text-[10px]">
                        <span className="rounded-full border border-cyan-500/20 bg-cyan-950/30 px-2 py-1 text-cyan-100">{patternLeader.scope}</span>
                        <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-200">主落点 {patternLeader.target}</span>
                        <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-300">{patternLeader.source === "claim" ? "来自 Claim 层" : "来自 Decision 层"}</span>
                      </div>
                      {(patternLeader.gate || patternLeader.gateReason) ? (
                        <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-900/45 p-2">
                          <p className="text-[10px] uppercase tracking-[0.16em] text-emerald-300">Formation Gate</p>
                          <p className="mt-1 text-[11px] text-emerald-100">{patternLeader.gate || "候选审计"}</p>
                          {patternLeader.gateReason ? <p className="mt-1 text-[10px] leading-relaxed text-zinc-400">{patternLeader.gateReason}</p> : null}
                        </div>
                      ) : null}
                      {patternLeader.scopeWeights.length ? (
                        <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-900/45 p-2">
                          <p className="text-[10px] uppercase tracking-[0.16em] text-cyan-300">Scope Evidence</p>
                          <div className="mt-2 grid gap-1.5">
                            {patternLeader.scopeWeights.map((item) => (
                              <div key={`${patternLeader.key}_${item.label}`} className="grid gap-1">
                                <div className="flex items-center justify-between text-[10px]">
                                  <span className="text-zinc-300">{item.label}</span>
                                  <span className="text-cyan-200">{Math.round(item.ratio * 100)}%</span>
                                </div>
                                <div className="h-1.5 overflow-hidden rounded-full bg-zinc-800">
                                  <div className="h-full rounded-full bg-[linear-gradient(90deg,rgba(34,211,238,0.95),rgba(45,212,191,0.95))]" style={{ width: `${Math.max(6, Math.round(item.ratio * 100))}%` }} />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : null}
                      {patternLeader.profileText ? (
                        <p className="mt-3 text-[11px] leading-relaxed text-zinc-300">
                          家族混合：<span className="text-cyan-100">{patternLeader.profileText}</span>
                        </p>
                      ) : null}
                      {patternLeader.projectionText ? (
                        <p className="mt-2 text-[11px] leading-relaxed text-zinc-400">
                          投影焦点：{patternLeader.projectionText}
                        </p>
                      ) : null}
                      {leaderBreakRisks.length ? (
                        <div className="mt-3 rounded-lg border border-rose-500/20 bg-rose-950/20 p-2">
                          <p className="text-[10px] uppercase tracking-[0.16em] text-rose-300">Break Risks</p>
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {leaderBreakRisks.map((risk) => (
                              <span key={`${patternLeader.key}_${risk}`} className="rounded-full border border-rose-500/20 bg-zinc-950/50 px-2 py-1 text-[10px] text-rose-100">
                                {risk}
                              </span>
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </div>

                    <div className="rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3">
                      <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">Secondary Patterns</p>
                      <div className="mt-2 grid gap-2">
                        {patternRunners.length ? (
                          patternRunners.map((item) => (
                            <div key={item.key} className="rounded-lg border border-zinc-800 bg-zinc-900/55 p-2">
                              <div className="flex items-start justify-between gap-2">
                                <div>
                                  <p className="text-[11px] text-cyan-50">{item.name}</p>
                                  <p className="text-[9px] text-zinc-500">{item.family} · {item.scope}</p>
                                </div>
                                <div className="flex flex-wrap gap-1">
                                  <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${patternStatusToneForRuntime(item.statusLabel)}`}>
                                    {item.statusLabel}
                                  </span>
                                  <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${patternConfidenceTone(item.confidence)}`}>
                                    {Math.round(item.confidence * 100)}%
                                  </span>
                                </div>
                              </div>
                              <p className="mt-1 text-[10px] text-zinc-300">
                                主落点 {item.target}{item.profileText ? ` · ${item.profileText}` : ""}
                              </p>
                              {item.scopeWeights.length ? (
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {item.scopeWeights.map((scope) => (
                                    <span key={`${item.key}_${scope.label}`} className="rounded-full border border-zinc-700 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                                      {scope.label} {Math.round(scope.ratio * 100)}%
                                    </span>
                                  ))}
                                </div>
                              ) : null}
                              {item.projectionText ? <p className="mt-1 text-[9px] text-zinc-500">{item.projectionText}</p> : null}
                            </div>
                          ))
                        ) : (
                          <div className="rounded-lg border border-zinc-800 bg-zinc-900/55 p-2 text-[10px] text-zinc-500">
                            当前尚未形成明确的次格局分层，系统只识别到一个主候选。
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="mt-3 rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3 text-[11px] text-zinc-400">
                    当前盘面还没有显式格局候选，系统会随着插件命中和 Claim 聚合继续补全。
                  </div>
                )}
              </div>
              <V17_DecisionInbox
                frames={s.frames}
                adoptedIds={s.adoptedDecisions.map((x) => x.id).filter((id): id is string => !!id)}
                locked={s.decisionInboxLocked}
                lockMessage={s.decisionInboxLockMessage}
                onAdopted={s.handleAdopted}
                onAdoptedBatch={s.handleAdoptedBatch}
                onPlanAction={s.handlePlanAction}
              />
              {!s.hasNarrative ? (
                <p className="mt-3 text-xs text-violet-200/80">V17 织造启动中，正在同步快照与叙事流...</p>
              ) : null}
            </div>
            {/* ── 因果链路调试边栏（可收缩）── */}
            <V17_TracePanel
              collapsed={!s.traceOpen}
              onToggle={() => s.setTraceOpen((v) => !v)}
              llmMeta={s.llmMeta}
              llmLifecyclePhase={s.llmLifecyclePhase}
              llmStatusText={s.llmStatusText}
              llmStatusDetail={s.llmStatusDetail}
              modelLabel={s.modelLabel}
              connectTickMs={s.connectTickMs}
              lastHeartbeatStep={s.lastHeartbeatStep}
              heartbeatHistory={s.heartbeatHistory}
              streamClosed={s.streamClosed}
              fullTrace={s.fullTrace}
              llmAuditSnapshot={s.llmAuditSnapshot}
              latestNarrator={s.latestNarrator as { payload?: Record<string, unknown> } | undefined}
              traceHits={s.traceHits}
              traceFacts={s.traceFacts}
              birthTimeISO={s.birthTimeISO}
              natalGender={s.natalGender}
              natalCalendar={s.natalCalendar}
              selectedLuckYear={s.selectedLuckYear}
              streamEndpoint={s.streamEndpoint}
              streamBody={s.streamBody}
              streamQuery={s.streamQuery}
              physicsSnapshot={s.physicsSnapshot as { payload?: Record<string, unknown> } | undefined}
            />

          </div>
        ) : null}
      </section>
    </main>
  );
}
