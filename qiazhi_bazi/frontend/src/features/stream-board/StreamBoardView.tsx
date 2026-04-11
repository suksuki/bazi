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
import type { InboxCard, StreamBoardViewModel } from "./models";
import { buildStreamBoardViewDerivedState } from "./viewModel";
import { computeBlindSkillBadges } from "@/features/stream-board/utils/blindSkillRuntime";
import { decisionIdsSignature, normalizeDecisionIds } from "./controller/streamBoardPure";
import { useActiveView } from "@/components/layout/ActiveViewContext";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";

const STEM_META: Record<string, { element: "wood" | "fire" | "earth" | "metal" | "water"; yinYang: "yang" | "yin" }> = {
  甲: { element: "wood", yinYang: "yang" },
  乙: { element: "wood", yinYang: "yin" },
  丙: { element: "fire", yinYang: "yang" },
  丁: { element: "fire", yinYang: "yin" },
  戊: { element: "earth", yinYang: "yang" },
  己: { element: "earth", yinYang: "yin" },
  庚: { element: "metal", yinYang: "yang" },
  辛: { element: "metal", yinYang: "yin" },
  壬: { element: "water", yinYang: "yang" },
  癸: { element: "water", yinYang: "yin" },
};

const BRANCH_META: Record<string, { element: "wood" | "fire" | "earth" | "metal" | "water"; yinYang: "yang" | "yin" }> = {
  子: { element: "water", yinYang: "yang" },
  丑: { element: "earth", yinYang: "yin" },
  寅: { element: "wood", yinYang: "yang" },
  卯: { element: "wood", yinYang: "yin" },
  辰: { element: "earth", yinYang: "yang" },
  巳: { element: "fire", yinYang: "yin" },
  午: { element: "fire", yinYang: "yang" },
  未: { element: "earth", yinYang: "yin" },
  申: { element: "metal", yinYang: "yang" },
  酉: { element: "metal", yinYang: "yin" },
  戌: { element: "earth", yinYang: "yang" },
  亥: { element: "water", yinYang: "yin" },
};

const ELEMENT_STYLE = {
  wood: { yang: { color: "#b7f7a8", bg: "rgba(22,101,52,0.36)", border: "rgba(74,222,128,0.5)" }, yin: { color: "#7ae0a2", bg: "rgba(15,83,44,0.32)", border: "rgba(52,211,153,0.45)" } },
  fire: { yang: { color: "#ffb38a", bg: "rgba(124,45,18,0.36)", border: "rgba(251,146,60,0.5)" }, yin: { color: "#ff8ea1", bg: "rgba(136,19,55,0.32)", border: "rgba(244,114,182,0.45)" } },
  earth: { yang: { color: "#ffe08a", bg: "rgba(120,53,15,0.35)", border: "rgba(251,191,36,0.5)" }, yin: { color: "#ffd2a8", bg: "rgba(113,63,18,0.32)", border: "rgba(245,158,11,0.45)" } },
  metal: { yang: { color: "#d6e4ff", bg: "rgba(30,58,138,0.34)", border: "rgba(96,165,250,0.5)" }, yin: { color: "#f1d4ff", bg: "rgba(88,28,135,0.32)", border: "rgba(192,132,252,0.45)" } },
  water: { yang: { color: "#96d5ff", bg: "rgba(12,74,110,0.36)", border: "rgba(56,189,248,0.5)" }, yin: { color: "#9ed8ff", bg: "rgba(8,47,73,0.34)", border: "rgba(14,165,233,0.45)" } },
};

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
              <motion.div
                key="vision"
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 16 }}
                transition={{ duration: 0.22 }}
                className="flex min-h-[calc(100dvh-11rem)] flex-col gap-2"
              >
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-[11px] text-amber-100/90">
                  {t("视觉场 · 全局熵")} {globalEntropy != null ? globalEntropy.toFixed(3) : "—"}
                  {t("（沉浸式看盘）")}
                </div>
                <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-cyan-500/25 bg-cyan-950/40 px-3 py-2 text-[11px] text-cyan-100/95">
                  <span className="text-zinc-400">
                    {hasBoard ? t("当前已有排盘结果，可随时修改生辰重算。") : t("尚未排盘：请先录入生辰八字。")}
                  </span>
                  <button
                    type="button"
                    onClick={goToSeedInput}
                    className="shrink-0 rounded-lg border border-cyan-400/40 bg-cyan-500/15 px-3 py-1.5 text-xs font-medium text-cyan-100 hover:bg-cyan-500/25"
                  >
                    {hasBoard ? t("修改生辰") : t("录入生辰（地法）")}
                  </button>
                </div>
                <div className="sticky top-0 z-20 -mx-1 rounded-xl border border-zinc-800/80 bg-zinc-950/85 px-1 py-1 shadow-lg shadow-black/30 backdrop-blur-md">
                  <StrategicCoreHUD
                    structureFinalDecision={finalStructureFinalDecisionV0 || {}}
                    pluginWeights={pluginWeights}
                    onPickDeity={(deity) => openLogicDrawerByDeity(deity)}
                    hasReboundRisk={hasReboundRisk}
                    energyPeak={energyPeakAbs}
                    globalEntropy={globalEntropy}
                    diagnosticHint={visionDiagnosticHint}
                    genderLabel={String((metadata as { gender?: string } | null)?.gender || "")}
                  />
                </div>
                <section className="rounded-2xl border border-cyan-500/25 bg-zinc-950/70 p-2">
                  <div className="mb-2 flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/70 px-2 py-1.5">
                    <p className="text-xs font-medium text-cyan-200">{t("命盘仪表盘")}</p>
                    <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-400">
                      <span>
                        {t("大运")} {String((timeline as { dayun?: string } | null)?.dayun || "--")} · {t("流年")}{" "}
                        {String((timeline as { liunian?: string } | null)?.liunian || "--")}
                      </span>
                      <label className="flex flex-wrap items-center gap-1 text-[10px] text-zinc-500">
                        <span>{t("流年（参考年）")}</span>
                        <ReferenceYearSelect
                          value={referenceYear}
                          onChange={setReferenceYear}
                          className="w-[4.25rem] rounded border border-zinc-600 bg-zinc-900 px-1 py-0.5 font-mono text-[10px] text-zinc-100"
                        />
                      </label>
                      {isPreviewBoard ? (
                        <span className="rounded border border-amber-500/45 bg-amber-500/12 px-1 py-0.5 text-[9px] text-amber-200">{t("预览")}</span>
                      ) : null}
                    </div>
                  </div>
                  {/* md+ 与指令舱顶栏徽章去重：桌面端仅在 Command 模式展示 BlindSkillBadgeRow */}
                  <div className="md:hidden">
                    <BlindSkillBadgeRow badges={blindSkillBadges} />
                  </div>
                  <div className="grid gap-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-2">
                      <BaziCard
                        metadata={metadata}
                        timeline={timeline}
                        deityScores={deityScores}
                        deityEnergyAxes={deityEnergyAxes}
                        rootDetailsByDeity={deityComponents}
                        hoveredDeity={hoveredDeity}
                        selected={selectedBranch}
                        confirmedConflictDetails={confirmedConflicts}
                        onPickBranch={setSelectedBranch}
                        t={t}
                        lang={lang}
                      />
                    </div>
                    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-2">
                      <TenGodNumericList
                        deityScores={deityScores}
                        deityEnergyAxes={deityEnergyAxes}
                        deityComponents={deityComponents}
                        deityTraceDetails={deityTraceDetails}
                        topAnomaly={llmDiagnosticData?.top_anomaly}
                        consensusHistory={consensusHistory}
                        hardRouteLogs={hardRouteLogs}
                        tombLockRate={labConfig.TOMB_LOCK_RATE}
                        tombReleased={releasedEnergyVal > 0}
                        climateIntensity={labConfig.CLIMATE_INTENSITY}
                        climateSeason={climateSeason}
                        onOpenLogic={openLogicDrawer}
                        onHoverDeity={setHoveredDeity}
                      />
                    </div>
                  </div>
                </section>
                <div className="min-h-[min(52dvh,420px)] flex-1 rounded-2xl border border-zinc-800 bg-zinc-950/60 p-2">
                  <BlindLogicMirror workVector={finalWorkVector || {}} />
                </div>
                <div className="flex min-h-[min(42dvh,360px)] flex-1 flex-col rounded-2xl border border-zinc-800 bg-zinc-950/50 p-2">
                  <TopologyMapV1 graph={finalTopologyGraphV1 || {}} />
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="command"
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -16 }}
                transition={{ duration: 0.22 }}
                className="space-y-3"
              >
                <div className="rounded-2xl border border-amber-500/30 bg-zinc-900/80 shadow-[0_0_0_1px_rgba(251,191,36,0.08)]">
                  <div className="border-b border-zinc-800 px-3 py-2.5 text-xs font-medium text-amber-100/95">
                    {t("生辰八字 · 地法（The Seed）")}
                  </div>
                  <div className="px-1 pb-2 pt-1">
                    <SeedInput
                      onSubmit={onSeedSubmit}
                      busy={busy}
                      t={t}
                      hideSubmitButton
                      splitActions={{
                        onPreview: (p) => void refreshSeedPreview(p),
                        previewBusy: seedPreviewBusy,
                      }}
                      onPayloadChange={handleSeedPayloadChange}
                      rightSummarySlot={(
                        <div className="h-full bg-transparent px-1 py-1">
                          <div className="mb-2 flex flex-wrap items-center gap-2">
                            <label className="flex flex-col gap-0.5 text-[10px] text-zinc-400 sm:flex-row sm:items-center sm:gap-1.5">
                              <span>{t("流年（参考年）")}</span>
                              <ReferenceYearSelect
                                value={referenceYear}
                                onChange={setReferenceYear}
                                className="w-[4.75rem] rounded border border-zinc-600 bg-zinc-900 px-1.5 py-0.5 font-mono text-[11px] text-zinc-100"
                              />
                            </label>
                            <span className="w-full text-[9px] leading-snug text-zinc-600 sm:w-auto" title={t("流年参考年说明")}>
                              {t("流年参考年说明")}
                            </span>
                            {isPreviewBoard ? (
                              <span className="rounded border border-amber-500/50 bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-medium text-amber-200">
                                {t("预览")}
                              </span>
                            ) : null}
                            {seedPreviewBusy ? (
                              <span className="text-[10px] text-zinc-500">{t("推演中…")}</span>
                            ) : null}
                            {seedPreviewError && !metadata ? (
                              <span className="text-[10px] text-red-400/90" title={seedPreviewError}>
                                {t("预览加载失败")}
                              </span>
                            ) : null}
                          </div>
                          {simpleBoard ? (
                            <div className="h-full">
                              <div className="grid h-full grid-cols-9 gap-1.5">
                                {[
                                  { key: "年", value: simpleBoard.year },
                                  { key: "月", value: simpleBoard.month },
                                  { key: "日", value: simpleBoard.day },
                                  { key: "时", value: simpleBoard.hour },
                                  { key: "大运", value: simpleBoard.dayun },
                                  { key: "流年", value: simpleBoard.liunian },
                                ].map((item) => {
                                  const stemMeta = STEM_META[item.value.stem];
                                  const branchMeta = BRANCH_META[item.value.branch];
                                  const stemStyle = stemMeta ? ELEMENT_STYLE[stemMeta.element][stemMeta.yinYang] : null;
                                  const branchStyle = branchMeta ? ELEMENT_STYLE[branchMeta.element][branchMeta.yinYang] : null;
                                  return (
                                    <div key={item.key} className="min-w-0 rounded-md border border-zinc-700 bg-zinc-900/70 px-1 py-1 text-center">
                                      <p className="mb-1 text-[10px] text-zinc-500">{t(item.key)}</p>
                                      <p
                                        className="rounded px-1 py-0.5 text-[2.1rem] font-semibold leading-none"
                                        style={stemStyle ? { color: stemStyle.color, backgroundColor: stemStyle.bg, border: `1px solid ${stemStyle.border}` } : undefined}
                                      >
                                        {item.value.stem}
                                      </p>
                                      <p
                                        className="mt-1 rounded px-1 py-0.5 text-[2.1rem] font-semibold leading-none"
                                        style={branchStyle ? { color: branchStyle.color, backgroundColor: branchStyle.bg, border: `1px solid ${branchStyle.border}` } : undefined}
                                      >
                                        {item.value.branch}
                                      </p>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          ) : (
                            <p className="text-sm text-zinc-500">{t("掐指一算后在此显示：四柱 / 大运 / 流年")}</p>
                          )}
                        </div>
                      )}
                    />
                  </div>
                </div>
                <UnifiedActionBar
                  mode={actionMode}
                  globalEntropy={globalEntropy}
                  decisionDirty={isDecisionDirty}
                  onRun={handleMainBarRun}
                  onSetBaseline={setAsBaseline}
                  disabled={(actionMode === "FULL" && !draftSeed) || isFinalized}
                  sigShiftFlashKey={sigShiftFlashKey}
                  labelOverride={primaryLabelOverride}
                  issued={isFinalized}
                  issueFinalPurplePulse={canIssueFinal && !actionSyncing && !busy}
                />
                <div className="rounded-md border border-zinc-800 bg-zinc-950/60 px-2 py-1 text-[10px] text-zinc-400">
                  {t("提交 IDs：")}{" "}
                  {lastSubmittedDecisionIds.length ? lastSubmittedDecisionIds.join(", ") : "[]"}
                </div>
                <BlindSkillBadgeRow badges={blindSkillBadges} />
                <DecisionInbox
                  key={`decision-inbox-${checklistResetToken}`}
                  cards={cards}
                  resultLogs={resultLogs}
                  verdictBody={finalVerdictBody}
                  verdictChangeLog={finalVerdictChangeLog}
                  logicalEvidence={finalLogicalEvidence}
                  workVector={finalWorkVector || {}}
                  topologyGraph={finalTopologyGraphV1 || {}}
                  structureCandidates={finalStructureCandidatesV0 || {}}
                  structureFinalDecision={finalStructureFinalDecisionV0 || {}}
                  metadata={metadata || {}}
                  stressTestResult={stressTestResult || {}}
                  genderComparisonResult={genderComparisonResult || {}}
                  highlightVerdict={false}
                  onSelectionChange={(selected) => {
                    const picked = selected as InboxCard[];
                    setCurrentDecisions(picked);
                    setDecisionIds(picked.map((item) => item.id));
                  }}
                  onVerdictDeityClick={openLogicDrawerByDeity}
                  onStrategicDeityHover={setHoveredDeity}
                  onEvidenceClick={onEvidenceItemClick}
                  onShowVersionHistory={showVerdictHistory}
                  hasVerdictHistory={hasVerdictHistory}
                  selectionResetToken={selectionResetToken}
                  summaryVersionLabel={summaryVersionLabel}
                  summaryChanged={summaryChanged}
                  l1Certified={l1Certified}
                  t={t}
                  onStressTest={runStressTest}
                  onGenderCompare={runGenderComparison}
                  pluginWeights={pluginWeights}
                  onPluginWeightsChange={setPluginWeights}
                  onApplyPluginWeights={rerunFinalVerdictWithWeights}
                  globalEntropy={globalEntropy}
                  logicDiff={logicDiff}
                  actionMode={actionMode}
                  autoSyncIdle={!actionSyncing}
                  hideStrategicPanel
                  inboxResetNonce={inboxResetNonce}
                  interactionLocked={isFinalized}
                  l1JunctionFlags={l1JunctionFlags}
                />
                <WillReplayPanel
                  items={confirmedDecisions || []}
                  onRevoke={handleRevokeDecision}
                  revertEntropyDelta={revertEntropyDelta}
                />

                {finalWorkVector && Object.keys(finalWorkVector).length > 0 ? (
                  <div className="rounded-xl border border-fuchsia-500/35 bg-fuchsia-950/30 p-3 text-[11px] text-zinc-300">
                    <p className="mb-2 font-medium text-fuchsia-200/95">{t("做功路径摘要")}</p>
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                      <div>
                        <span className="text-zinc-500">{t("期望")}</span>{" "}
                        <span className="text-zinc-100">{workExpectation.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">{t("反噬风险")}</span>{" "}
                        <span className="text-zinc-100">{backfireRiskVal.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">{t("释放能")}</span>{" "}
                        <span className="text-zinc-100">{releasedEnergyVal.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                ) : null}

                {physicsAudit ? (
                  <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-3 text-xs text-zinc-400">
                    <p className="mb-2">
                      Physics Confidence:{" "}
                      <span className="text-emerald-300">
                        {physicsConfidence !== null ? `${Math.round(physicsConfidence * 100)}%` : "--"}
                      </span>
                      {physicsEvidence.length > 0 ? (
                        <span className="ml-2 text-[11px] text-zinc-500">Evidence: {physicsEvidence.slice(0, 2).join(" | ")}</span>
                      ) : null}
                    </p>
                    <button
                      type="button"
                      onClick={() => setActiveView("debug")}
                      className="text-left text-amber-400/90 underline-offset-2 hover:underline"
                    >
                      {t("在「黑匣子」查看完整 L1 流水线与物理张量 JSON →")}
                    </button>
                  </div>
                ) : null}
              </motion.div>
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
