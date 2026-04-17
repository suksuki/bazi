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

export default function OraclePage() {
  const s = useOracleSession();

  const fourPillars = s.physicsSnapshot?.payload?.four_pillars;
  const luckPillarSnap = s.physicsSnapshot?.payload?.luck_pillar;
  const flowPillarSnap = s.physicsSnapshot?.payload?.flow_pillar;

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
              />
              <V17_DecisionInbox
                frames={s.frames}
                adoptedIds={s.adoptedDecisions.map((x) => x.id)}
                sessionId={s.sessionId}
                locked={s.decisionInboxLocked}
                lockMessage={s.decisionInboxLockMessage}
                onAdopted={s.handleAdopted}
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
              connectPhase={s.connectPhase}
              collapsePhase={s.collapsePhase}
              modelLabel={s.modelLabel}
              connectTickMs={s.connectTickMs}
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
