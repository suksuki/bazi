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

function decisionPluginLabel(row: Record<string, unknown>): string {
  return String(
    row.source_label || row.display_name || row.definition_text || row.plugin_id || row.source || "",
  ).trim();
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
                </div>
              ) : null}
              <V17_DecisionInbox
                frames={s.frames}
                adoptedIds={s.adoptedDecisions.map((x) => x.id).filter((id): id is string => !!id)}
                sessionId={s.sessionId}
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
