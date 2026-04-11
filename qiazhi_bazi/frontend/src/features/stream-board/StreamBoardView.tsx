"use client";

import React, { useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArbiterLogicDrawer } from "@/components/ArbiterLogicDrawer";
import { AuditSidebar } from "@/components/AuditSidebar";
import { BaziCard } from "@/components/BaziCard";
import { BlindLogicMirror } from "@/components/BlindLogicMirror";
import { DecisionInbox } from "@/components/DecisionInbox";
import { LogicGlitchOverlay } from "@/components/LogicGlitchOverlay";
import { ReferenceYearSelect } from "@/components/ReferenceYearSelect";
import { SeedInput } from "@/components/SeedInput";
import { StrategicCoreHUD } from "@/components/StrategicCoreHUD";
import { TenGodNumericList } from "@/components/TenGodNumericList";
import { TopologyMapV1 } from "@/components/TopologyMapV1";
import { UnifiedActionBar } from "@/components/UnifiedActionBar";
import { LabViewModeFab } from "@/components/layout/LabViewModeFab";
import { BlindSkillBadgeRow } from "@/features/stream-board/components/BlindSkillBadgeRow";
import { SnapshotBanner } from "@/features/stream-board/components/SnapshotBanner";
import { VerdictCertificate } from "@/features/stream-board/components/VerdictCertificate";
import { WillReplayPanel } from "@/features/stream-board/components/WillReplayPanel";
import { BlindSkillHighlightProvider } from "@/features/stream-board/context/BlindSkillHighlightContext";
import { FINAL_VERDICT_ABS_DELTA_THRESHOLD, I18N } from "./constants";
import { StreamBoardViewModel, InboxCard } from "./models";
import { buildStreamBoardViewDerivedState } from "./viewModel";
import { computeBlindSkillBadges } from "@/features/stream-board/utils/blindSkillRuntime";
import { decisionIdsSignature, normalizeDecisionIds } from "./controller/streamBoardPure";
import { useActiveView } from "@/components/layout/ActiveViewContext";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import { BoardVisionPanel } from "./components/BoardVisionPanel";
import { BoardCommandPanel } from "./components/BoardCommandPanel";



export function StreamBoardView(viewModel: StreamBoardViewModel) {
  const { setActiveView } = useActiveView();
  const {
    lang,
    setLang,
    busy,
    consultationId,
    metadata,
    timeline,
    referenceYear,
    setReferenceYear,
    seedPreviewPillars,
    seedPreviewTimeline,
    seedPreviewBusy,
    seedPreviewError,
    scheduleSeedDraftPreview,
    refreshSeedPreview,
    clearLabPipelineForSeedDraft,
    lastCommittedSeedSignature,
    selectedBranch,
    setSelectedBranch,
    auditItems,
    health,
    llmModelName,
    i18nCalls,
    deityScores,
    deityEnergyAxes,
    deityComponents,
    deityTraceDetails,
    hoveredDeity,
    setHoveredDeity,
    confirmedConflicts,
    llmDiagnosticData,
    globalEntropy,
    consensusHistory,
    cards,
    resultLogs,
    finalVerdictBody,
    finalVerdictChangeLog,
    finalLogicalEvidence,
    finalWorkVector,
    finalTopologyGraphV1,
    finalStructureCandidatesV0,
    finalStructureFinalDecisionV0,
    confirmedDecisions,
    confirmedDecisionIds,
    setConfirmedDecisionIds,
    urlDecisionHydrated,
    snapshotUrlTag,
    snapshotAvailable,
    setAsBaseline,
    logicDiff,
    stressTestResult,
    genderComparisonResult,
    finalVerdictHistory,
    selectionResetToken,
    finalVerdictVersionId,
    conclusionVersion,
    summaryChanged,
    l1Certified,
    physicsAudit,
    physicsConfidence,
    physicsEvidence,
    labConfig,
    pluginWeights,
    setPluginWeights,
    streamThemeChroma,
    rerunFinalVerdictWithWeights,
    logicDrawerOpen,
    logicDrawerTitle,
    logicDrawerFocus,
    logicDrawerDetails,
    logicDrawerTrace,
    setLogicDrawerOpen,
    onSeedSubmit,
    executeDecisionAndRefresh,
    appendSystemAuditLog,
    revokeConfirmedDecision,
    openLogicDrawer,
    openLogicDrawerByDeity,
    onEvidenceItemClick,
    showVerdictHistory,
    applyCurrentSqlPatch,
    runStressTest,
    runGenderComparison,
    t,
    inboxResetNonce,
    sigShiftFlashKey,
    isFinalized,
    finalizeVerdict,
  } = viewModel;
  const decisionIds = confirmedDecisionIds || [];
  const setDecisionIds = setConfirmedDecisionIds || (() => undefined);
  const decisionHydrated = Boolean(urlDecisionHydrated);
  const { state: labUiState } = useLabStore();
  const sovereigntyDominant = Boolean(labUiState.snapshot?.interaction_hub?.sovereignty_dominant);
  const blindSkillBadges = useMemo(
    () =>
      computeBlindSkillBadges(
        labUiState.snapshot?.physics_tensor as Record<string, unknown> | undefined,
        finalWorkVector,
      ),
    [labUiState.snapshot?.physics_tensor, finalWorkVector],
  );
  const l1JunctionFlags = (labUiState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined)
    ?.l1_junction_flags as Record<string, unknown> | undefined;

  const {
    hardRouteLogs,
    climateSeason,
    energyPeakAbs,
    workExpectation,
    backfireRiskVal,
    releasedEnergyVal,
    streamThemeStyle,
    summaryVersionLabel,
    hasVerdictHistory,
  } = buildStreamBoardViewDerivedState(viewModel);
  const [viewMode, setViewMode] = React.useState<"VISION" | "COMMAND">("COMMAND");
  const [actionSyncing, setActionSyncing] = React.useState(false);
  const [revokeGlitch, setRevokeGlitch] = React.useState(false);
  const [currentDecisions, setCurrentDecisions] = React.useState<InboxCard[]>([]);
  const [checklistResetToken, setChecklistResetToken] = React.useState(0);
  const [lastSubmittedDecisionIds, setLastSubmittedDecisionIds] = React.useState<string[]>([]);
  const [draftSeed, setDraftSeed] = React.useState<{ date: string; time: string; calendar: "solar" | "lunar"; gender: "male" | "female" } | null>(null);
  const [lastAppliedSeedSignature, setLastAppliedSeedSignature] = React.useState("");
  const [lastAppliedParamSignature, setLastAppliedParamSignature] = React.useState("");
  const [lastAppliedDecisionsSignature, setLastAppliedDecisionsSignature] = React.useState("[]");
  const [revertEntropyDelta, setRevertEntropyDelta] = React.useState<number | null>(null);
  const [pendingRevertEntropyCapture, setPendingRevertEntropyCapture] = React.useState(false);
  const touchStartX = React.useRef<number | null>(null);

  const goToSeedInput = React.useCallback(() => {
    setViewMode("COMMAND");
  }, []);
  const hasBoard = Boolean(metadata?.pillars);
  const currentSeedSignature = draftSeed ? JSON.stringify(draftSeed) : "";
  const currentParamSignature = JSON.stringify(pluginWeights || {});
  const seedDirty = Boolean(currentSeedSignature && currentSeedSignature !== lastAppliedSeedSignature);
  const paramDirty = currentParamSignature !== lastAppliedParamSignature;
  const currentDecisionsSignature = decisionIdsSignature(decisionIds);
  const isDecisionDirty = currentDecisionsSignature !== lastAppliedDecisionsSignature;
  const handleSeedPayloadChange = React.useCallback(
    (payload: { date: string; time: string; calendar: "solar" | "lunar"; gender: "male" | "female" }) => {
      const sig = JSON.stringify({
        date: payload.date,
        time: payload.time,
        calendar: payload.calendar,
        gender: payload.gender,
      });
      if (metadata && lastCommittedSeedSignature && sig !== lastCommittedSeedSignature && !isFinalized) {
        clearLabPipelineForSeedDraft();
      }
      setDraftSeed((prev) => {
        if (
          prev
          && prev.date === payload.date
          && prev.time === payload.time
          && prev.calendar === payload.calendar
          && prev.gender === payload.gender
        ) {
          return prev;
        }
        return payload;
      });
    },
    [metadata, lastCommittedSeedSignature, clearLabPipelineForSeedDraft, isFinalized],
  );

  React.useEffect(() => {
    if (!metadata) {
      setLastAppliedSeedSignature("");
    }
  }, [metadata]);

  React.useEffect(() => {
    if (metadata && lastCommittedSeedSignature) {
      setLastAppliedSeedSignature(lastCommittedSeedSignature);
    }
  }, [metadata, lastCommittedSeedSignature]);

  React.useEffect(() => {
    if (metadata) {
      scheduleSeedDraftPreview(null);
      return;
    }
    if (draftSeed) {
      scheduleSeedDraftPreview(draftSeed);
    } else {
      scheduleSeedDraftPreview(null);
    }
  }, [metadata, draftSeed, referenceYear, scheduleSeedDraftPreview]);

  const isPreviewBoard = Boolean(!metadata?.pillars && seedPreviewPillars);

  const simpleBoard = React.useMemo(() => {
    const pillars = metadata?.pillars ?? seedPreviewPillars;
    if (!pillars) return null;
    const tl = metadata?.pillars ? timeline : seedPreviewTimeline;
    const parseGanZhi = (text: string) => {
      const chars = Array.from(String(text || "").trim());
      return { stem: chars[0] || "-", branch: chars[1] || "-" };
    };
    return {
      year: { stem: pillars.year?.stem || "-", branch: pillars.year?.branch || "-" },
      month: { stem: pillars.month?.stem || "-", branch: pillars.month?.branch || "-" },
      day: { stem: pillars.day?.stem || "-", branch: pillars.day?.branch || "-" },
      hour: { stem: pillars.hour?.stem || "-", branch: pillars.hour?.branch || "-" },
      dayun: parseGanZhi(String(tl?.dayun || "--")),
      liunian: parseGanZhi(String(tl?.liunian || "--")),
    };
  }, [metadata?.pillars, timeline, seedPreviewPillars, seedPreviewTimeline]);


  const weakPathEnabled = Number(labConfig.SHOW_WEAK_WORK_PATHS || 0) > 0.5;
  const visionDiagnosticHint =
    energyPeakAbs > 10 && Math.abs(workExpectation) < 0.1
      ? `检测到能量高度淤积（Abs: ${energyPeakAbs.toFixed(2)}），做功路径受阻。${weakPathEnabled ? "已开启逻辑透深。" : ""}`
      : "";
  const hasReboundRisk = backfireRiskVal > 0.35;
  const actionMode: "FULL" | "SEMANTIC" | "SYNCING" | "PARAMETER_DIRTY" = actionSyncing || busy
    ? "SYNCING"
    : seedDirty
      ? "FULL"
      : (paramDirty || isDecisionDirty)
        ? "PARAMETER_DIRTY"
        : "SEMANTIC";

  const unresolvedConflictCount = cards.length;
  const absDeltaRaw = logicDiff?.abs_delta;
  const absDeltaLow =
    typeof absDeltaRaw === "number" &&
    Number.isFinite(absDeltaRaw) &&
    Math.abs(absDeltaRaw) < FINAL_VERDICT_ABS_DELTA_THRESHOLD;
  const canIssueFinal =
    Boolean(hasBoard) &&
    !isFinalized &&
    !seedDirty &&
    unresolvedConflictCount === 0 &&
    absDeltaLow;

  const primaryLabelOverride = isFinalized
    ? "已签发 (Issued)"
    : actionSyncing || busy
      ? undefined
      : seedDirty
        ? t("测算八字")
        : unresolvedConflictCount > 0
          ? "同步因果"
          : canIssueFinal
            ? "签发终审"
            : undefined;

  const handleFullCalculate = React.useCallback(async () => {
    if (!draftSeed) return;
    setActionSyncing(true);
    try {
      await onSeedSubmit(draftSeed);
      const seedSig = JSON.stringify(draftSeed);
      setLastAppliedSeedSignature(seedSig);
      setLastAppliedParamSignature(JSON.stringify(pluginWeights || {}));
    } finally {
      setActionSyncing(false);
    }
  }, [draftSeed, onSeedSubmit, pluginWeights]);

  const runSemanticRecompute = React.useCallback(async (decisions: InboxCard[]) => {
    setActionSyncing(true);
    try {
      setLastSubmittedDecisionIds(decisions.map((item) => item.id));
      await rerunFinalVerdictWithWeights(decisions);
      setLastAppliedParamSignature(JSON.stringify(pluginWeights || {}));
      setLastAppliedDecisionsSignature(decisionIdsSignature(decisions.map((item) => item.id)));
    } finally {
      setActionSyncing(false);
    }
  }, [rerunFinalVerdictWithWeights, pluginWeights]);

  const runDecisionExecution = React.useCallback(async (decisions: InboxCard[]) => {
    if (decisions.length === 0) return;
    setActionSyncing(true);
    try {
      setLastSubmittedDecisionIds(decisions.map((item) => item.id));
      await executeDecisionAndRefresh(decisions);
      setLastAppliedParamSignature(JSON.stringify(pluginWeights || {}));
      setLastAppliedDecisionsSignature(decisionIdsSignature(decisionIds));
    } finally {
      setActionSyncing(false);
    }
  }, [executeDecisionAndRefresh, pluginWeights, decisionIds]);

  const handleSemanticRecompute = React.useCallback(async () => {
    const selectedByIds = decisionIds
      .map((id) => cards.find((card) => card.id === id))
      .filter((item): item is InboxCard => Boolean(item));
    const selected = selectedByIds.length > 0 ? selectedByIds : currentDecisions;
    await runDecisionExecution(selected);
  }, [runDecisionExecution, decisionIds, cards, currentDecisions]);

  const handleMainBarRun = React.useCallback(async () => {
    if (isFinalized) return;
    if (seedDirty) {
      await handleFullCalculate();
      return;
    }
    if (unresolvedConflictCount > 0) {
      await handleSemanticRecompute();
      return;
    }
    if (canIssueFinal) {
      await finalizeVerdict();
      return;
    }
    await handleSemanticRecompute();
  }, [
    isFinalized,
    seedDirty,
    unresolvedConflictCount,
    canIssueFinal,
    finalizeVerdict,
    handleFullCalculate,
    handleSemanticRecompute,
  ]);

  React.useEffect(() => {
    setCurrentDecisions([]);
  }, [selectionResetToken]);

  const handleRevokeDecision = React.useCallback(async (id: string) => {
    setRevokeGlitch(true);
    setPendingRevertEntropyCapture(true);
    const next = currentDecisions.filter((item) => item.id !== id);
    setCurrentDecisions(next);
    setDecisionIds(next.map((item) => item.id));
    if (revokeConfirmedDecision) {
      await revokeConfirmedDecision(id);
    }
    await runSemanticRecompute(next);
    window.setTimeout(() => setRevokeGlitch(false), 180);
  }, [currentDecisions, setDecisionIds, revokeConfirmedDecision, runSemanticRecompute]);

  React.useEffect(() => {
    if (!pendingRevertEntropyCapture || actionSyncing) return;
    const delta = Number(logicDiff?.entropy_delta || 0);
    setRevertEntropyDelta(delta);
    appendSystemAuditLog(`[REVERSION_IMPACT] entropy_rebound: ${delta >= 0 ? "+" : ""}${delta.toFixed(2)}`);
    setPendingRevertEntropyCapture(false);
    window.setTimeout(() => setRevertEntropyDelta(null), 1800);
  }, [pendingRevertEntropyCapture, actionSyncing, logicDiff?.entropy_delta, appendSystemAuditLog]);

  React.useEffect(() => {
    if (!lastAppliedParamSignature) {
      setLastAppliedParamSignature(JSON.stringify(pluginWeights || {}));
    }
  }, [lastAppliedParamSignature, pluginWeights]);
  React.useEffect(() => {
    if (!lastAppliedDecisionsSignature) {
      setLastAppliedDecisionsSignature(decisionIdsSignature(decisionIds));
    }
  }, [lastAppliedDecisionsSignature, decisionIds]);

  React.useEffect(() => {
    if (!decisionHydrated) return;
    if (cards.length > 0) {
      const recovered = decisionIds
        .map((id) => cards.find((card) => card.id === id))
        .filter((item): item is InboxCard => Boolean(item));
      setCurrentDecisions((prev) => {
        const prevSig = JSON.stringify([...new Set(prev.map((item) => item.id))].sort());
        const nextSig = JSON.stringify([...new Set(recovered.map((item) => item.id))].sort());
        return prevSig === nextSig ? prev : recovered;
      });
    }
  }, [decisionHydrated, cards, decisionIds]);

  return (
    <main
      data-testid="stream-board-root"
      style={streamThemeStyle}
      className="mx-auto min-h-dvh w-full max-w-[1400px] px-3 py-4 transition-colors duration-500"
    >
      <div
        className="fixed inset-0 -z-10 transition-all duration-500"
        style={{
          background:
            "radial-gradient(120% 90% at 80% 10%, rgba(255,215,120,0.06), transparent 52%), linear-gradient(135deg, var(--stream-bg-color), #0f0f12 65%)",
          boxShadow: `inset 0 0 80px var(--stream-overload-color)`,
        }}
      />
      <BlindSkillHighlightProvider>
      <LogicGlitchOverlay
        active={(streamThemeChroma.isConflictOverload && streamThemeChroma.hasPolarityReversal) || revokeGlitch}
        entropy={revokeGlitch ? 0.9 : globalEntropy}
      />
      <LabViewModeFab viewMode={viewMode} onToggle={() => setViewMode((m) => (m === "VISION" ? "COMMAND" : "VISION"))} />
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">{t(I18N[lang].title)}</h1>
          <p className="mt-1 font-mono text-[11px] text-amber-200/90">
            Unresolved Conflicts: {unresolvedConflictCount}
          </p>
          <SnapshotBanner tag={snapshotUrlTag ?? ""} />
          <p className="text-xs text-zinc-500">{t(I18N[lang].subtitle)}</p>
          <span className="mt-1 inline-flex rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-300">
            {t("第一层完全对齐")}
          </span>
        </div>
        <div className="flex items-center gap-1">
          {(["ZH", "EN", "KO"] as const).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setLang(item)}
              className={`rounded-md px-2 py-1 text-xs ${lang === item ? "bg-amber-500 text-zinc-950" : "bg-zinc-800 text-zinc-300"}`}
            >
              {item}
            </button>
          ))}
          {snapshotAvailable ? (
            <span className="ml-1 rounded-md border border-cyan-500/35 bg-cyan-500/10 px-2 py-1 text-xs text-cyan-200">{t("会话已驻留")}</span>
          ) : null}
        </div>
      </header>

      {sovereigntyDominant ? (
        <div
          className="mb-2 rounded-lg border border-amber-400/55 bg-gradient-to-r from-amber-500/20 via-amber-400/15 to-amber-600/10 px-3 py-2 text-center text-[11px] font-semibold tracking-[0.2em] text-amber-100 shadow-[0_0_24px_rgba(251,191,36,0.18)]"
          data-testid="sovereignty-dominant-banner"
        >
          主权占优
        </div>
      ) : null}

      <div className="flex flex-col gap-3 md:flex-row">
        <div
          className="flex-1 space-y-3"
          onTouchStart={(e) => {
            touchStartX.current = e.changedTouches[0].clientX;
          }}
          onTouchEnd={(e) => {
            const x0 = touchStartX.current;
            touchStartX.current = null;
            if (x0 == null) return;
            const dx = e.changedTouches[0].clientX - x0;
            if (dx > 56) setViewMode("VISION");
            if (dx < -56) setViewMode("COMMAND");
          }}
        >
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="hidden rounded-lg border border-zinc-700 bg-zinc-900 p-0.5 md:flex">
              <button
                type="button"
                className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium ${
                  viewMode === "VISION" ? "bg-amber-500/25 text-amber-200" : "text-zinc-500"
                }`}
                onClick={() => setViewMode("VISION")}
              >
                {t("视觉仪表盘")}
              </button>
              <button
                type="button"
                className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium ${
                  viewMode === "COMMAND" ? "bg-cyan-500/20 text-cyan-200" : "text-zinc-500"
                }`}
                onClick={() => setViewMode("COMMAND")}
              >
                {t("指令舱")}
              </button>
            </div>
            <p className="text-[10px] text-zinc-500 md:hidden">{t("滑动主区域切换视图，或点右下角浮动按钮")}</p>
            <button
              type="button"
              onClick={() => setActiveView("debug")}
              className="text-left text-[10px] text-zinc-500 underline-offset-2 hover:text-amber-300/90 hover:underline"
            >
              {t("黑匣子（L1 审计）→")}
            </button>
          </div>

          <AnimatePresence mode="wait">
            {viewMode === "VISION" ? (
              <BoardVisionPanel
                viewModel={viewModel}
                hasBoard={hasBoard}
                isPreviewBoard={isPreviewBoard}
                globalEntropy={globalEntropy}
                visionDiagnosticHint={visionDiagnosticHint}
                hasReboundRisk={hasReboundRisk}
                energyPeakAbs={energyPeakAbs}
                blindSkillBadges={blindSkillBadges}
                goToSeedInput={goToSeedInput}
                hardRouteLogs={hardRouteLogs}
                climateSeason={climateSeason}
                releasedEnergyVal={releasedEnergyVal}
              />
            ) : (
              <BoardCommandPanel
                viewModel={viewModel}
                draftSeed={draftSeed}
                simpleBoard={simpleBoard}
                isPreviewBoard={isPreviewBoard}
                seedPreviewBusy={seedPreviewBusy}
                seedPreviewError={seedPreviewError}
                handleSeedPayloadChange={handleSeedPayloadChange}
                lastSubmittedDecisionIds={lastSubmittedDecisionIds}
                blindSkillBadges={blindSkillBadges}
                setCurrentDecisions={setCurrentDecisions}
                setDecisionIds={setDecisionIds}
                handleMainBarRun={handleMainBarRun}
                handleRevokeDecision={handleRevokeDecision}
                revertEntropyDelta={revertEntropyDelta}
                actionMode={actionMode}
                isDecisionDirty={isDecisionDirty}
                actionSyncing={actionSyncing}
                primaryLabelOverride={primaryLabelOverride}
                canIssueFinal={canIssueFinal}
                checklistResetToken={checklistResetToken}
                workExpectation={workExpectation}
                backfireRiskVal={backfireRiskVal}
                releasedEnergyVal={releasedEnergyVal}
                hasVerdictHistory={hasVerdictHistory}
                summaryVersionLabel={summaryVersionLabel}
                l1JunctionFlags={l1JunctionFlags}
              />
            )}
          </AnimatePresence>
        </div>
      </div>

      {labUiState.isFinalized && labUiState.finalizationReport?.hash ? (
        <motion.div
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="relative z-0 mt-8 border-t border-zinc-800/90 pt-6 shadow-[0_-12px_40px_rgba(0,0,0,0.35)]"
        >
          <p className="mb-2 text-center text-[10px] font-medium uppercase tracking-[0.25em] text-zinc-500">
            终审已签发 · 公文压底
          </p>
          <VerdictCertificate
            hash={labUiState.finalizationReport.hash}
            committedAt={labUiState.finalizationReport.committedAt}
            logicDiff={logicDiff}
            effectiveSkillIds={
              labUiState.finalizationReport.effectiveSkillIds ??
              (labUiState.snapshot?.metadata?.verdict_effective_skill_ids as string[] | undefined)
            }
          />
        </motion.div>
      ) : null}

      </BlindSkillHighlightProvider>

      <ArbiterLogicDrawer
        open={logicDrawerOpen}
        title={logicDrawerTitle}
        focus={logicDrawerFocus}
        details={logicDrawerDetails.length ? logicDrawerDetails : [llmDiagnosticData?.causal_reasoning || t("暂无批注内容。")]}
        deityTrace={logicDrawerTrace}
        auditSource={physicsAudit}
        onClose={() => setLogicDrawerOpen(false)}
        onApplySql={applyCurrentSqlPatch}
      />
    </main>
  );
}
