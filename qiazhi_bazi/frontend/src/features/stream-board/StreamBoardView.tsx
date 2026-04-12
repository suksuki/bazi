"use client";

import React, { useCallback, useEffect, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArbiterLogicDrawer } from "@/components/ArbiterLogicDrawer";
import { AuditSidebar } from "@/components/AuditSidebar";
import { BaziCard } from "@/components/BaziCard";
import { BlindLogicMirror } from "@/components/BlindLogicMirror";
import { LogicGlitchOverlay } from "@/components/LogicGlitchOverlay";
import { ReferenceYearSelect } from "@/components/ReferenceYearSelect";
import { SeedInput } from "@/components/SeedInput";
import { StrategicCoreHUD } from "@/components/StrategicCoreHUD";
import { TopologyMapV1 } from "@/components/TopologyMapV1";
import { LabViewModeFab } from "@/components/layout/LabViewModeFab";
import { SnapshotBanner } from "@/features/stream-board/components/SnapshotBanner";
import { VerdictCertificate } from "@/features/stream-board/components/VerdictCertificate";
import { BlindSkillHighlightProvider } from "@/features/stream-board/context/BlindSkillHighlightContext";
import { FINAL_VERDICT_ABS_DELTA_THRESHOLD, I18N } from "./constants";
import {
  type DecisionSignalToNoiseMeta,
  StreamBoardViewModel,
  InboxCard,
  type SeedPayload,
  type SeedSubmitResult,
} from "./models";
import { buildCausalSovereigntySlice } from "./utils/causalSovereigntyFromSnapshot";
import { buildFullRecalcInputBundle, physicsTensorFingerprint } from "./utils/physicsTensorFingerprint";
import { buildStreamBoardViewDerivedState } from "./viewModel";
import { decisionIdsSignature, normalizeDecisionIds } from "./controller/streamBoardPure";
import { useActiveView } from "@/components/layout/ActiveViewContext";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import { usePulseReplay } from "@/features/stream-board/stores/pulseReplayContext";
import { BoardVisionPanel } from "./components/BoardVisionPanel";
import { BoardCommandPanel } from "./components/BoardCommandPanel";
import { PatternStatus, type PatternProfileSlice } from "./components/PatternStatus";



export function StreamBoardView(viewModel: StreamBoardViewModel) {
  const { setActiveView } = useActiveView();
  const handleOpenPluginAudit = useCallback(
    (pluginId: string) => {
      try {
        sessionStorage.setItem("qiazhi_debug_plugin_focus", pluginId);
      } catch {
        /* ignore quota / private mode */
      }
      setActiveView("debug");
    },
    [setActiveView],
  );
  const {
    lang,
    setLang,
    busy,
    narrativeReshapeActive,
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
    patternProfile,
    consensusHistory,
    cards,
    resultLogs,
    confirmedDecisionIds,
    setConfirmedDecisionIds,
    urlDecisionHydrated,
    snapshotUrlTag,
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
    runFinalVerdictSynthesis,
    appendSystemAuditLog,
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
    verdictSkeletonContentKey,
  } = viewModel;
  const decisionIds = React.useMemo(() => confirmedDecisionIds || [], [confirmedDecisionIds]);
  const setDecisionIds = React.useMemo(
    () => setConfirmedDecisionIds ?? (() => undefined),
    [setConfirmedDecisionIds],
  );
  const decisionHydrated = Boolean(urlDecisionHydrated);
  const { state: labUiState } = useLabStore();
  const labSnapshotRef = React.useRef(labUiState.snapshot);
  labSnapshotRef.current = labUiState.snapshot;
  const sovereigntyDominant = Boolean(labUiState.snapshot?.interaction_hub?.sovereignty_dominant);
  const l1JunctionFlags = (labUiState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined)
    ?.l1_junction_flags as Record<string, unknown> | undefined;
  const decisionSignalToNoise = (labUiState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined)
    ?.decision_signal_to_noise as DecisionSignalToNoiseMeta | undefined;

  const causalSovereigntyForCert = useMemo(
    () => buildCausalSovereigntySlice(labUiState.snapshot as Record<string, unknown> | null | undefined),
    [labUiState.snapshot],
  );

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
  const [seedFlowPhase, setSeedFlowPhase] = React.useState<"entry" | "main">("entry");
  const [seedEntryMountKey, setSeedEntryMountKey] = React.useState(0);
  const [actionSyncing, setActionSyncing] = React.useState(false);
  /** 掐指一算（全量 analyze-seed）专用 Loading，与语义重算 actionSyncing 分离 */
  const [isCalculating, setIsCalculating] = React.useState(false);
  /** 全量掐指（analyze-seed）成功次数：0 尚未成功；≥1 可持续「掐指再算」，无轮次上限（仅签发后锁定） */
  const [calculationCount, setCalculationCount] = React.useState(0);
  const [lastSuccessfulInputBundle, setLastSuccessfulInputBundle] = React.useState<string | null>(null);
  /** 供 analyze-seed 异步结束后读取「上一拍」成功 bundle，避免闭包陈旧；也用于同参复核时的物理收敛判定 */
  const lastSuccessfulInputBundleRef = React.useRef<string | null>(null);
  const calculationCountRef = React.useRef(0);
  const [calculationNonce, setCalculationNonce] = React.useState(0);
  const pulseReplay = usePulseReplay();
  useEffect(() => {
    if (!pulseReplay?.recordLabPulseSnapshot) return;
    if (!metadata?.pillars) return;
    const sk = String(verdictSkeletonContentKey || "").trim() || null;
    pulseReplay.recordLabPulseSnapshot({
      ts: Date.now(),
      deityScores: { ...deityScores },
      skeleton: sk,
    });
  }, [pulseReplay, calculationNonce, verdictSkeletonContentKey, metadata?.pillars, deityScores]);
  const [inboxScanActive, setInboxScanActive] = React.useState(false);
  const [runSuccessFootnote, setRunSuccessFootnote] = React.useState("");
  const [fullRunErrorFootnote, setFullRunErrorFootnote] = React.useState("");
  const inboxPulseTimerRef = React.useRef<number | null>(null);
  const runSuccessClearRef = React.useRef<number | null>(null);
  const fullRunErrorClearRef = React.useRef<number | null>(null);
  /** 物理收敛并触发终审整合后的短窗：忽略 bundle 字符串瞬时失配导致的成功次数复位 */
  const bundleTier2ResetSuppressedUntilRef = React.useRef(0);

  React.useEffect(
    () => () => {
      if (inboxPulseTimerRef.current) window.clearTimeout(inboxPulseTimerRef.current);
      if (runSuccessClearRef.current) window.clearTimeout(runSuccessClearRef.current);
      if (fullRunErrorClearRef.current) window.clearTimeout(fullRunErrorClearRef.current);
    },
    [],
  );
  const [currentDecisions, setCurrentDecisions] = React.useState<InboxCard[]>([]);
  const [checklistResetToken, setChecklistResetToken] = React.useState(0);
  const [draftSeed, setDraftSeed] = React.useState<{ date: string; time: string; calendar: "solar" | "lunar"; gender: "male" | "female" } | null>(null);
  const [lastAppliedSeedSignature, setLastAppliedSeedSignature] = React.useState("");
  const [lastAppliedParamSignature, setLastAppliedParamSignature] = React.useState("");
  const [lastAppliedDecisionsSignature, setLastAppliedDecisionsSignature] = React.useState("[]");
  const touchStartX = React.useRef<number | null>(null);

  const goToSeedInput = React.useCallback(() => {
    setViewMode("COMMAND");
    setSeedFlowPhase("main");
  }, []);
  const hasBoard = Boolean(metadata?.pillars);

  React.useEffect(() => {
    if (metadata?.pillars) setSeedFlowPhase("main");
  }, [metadata?.pillars]);

  React.useEffect(() => {
    if (seedFlowPhase === "entry") setViewMode("COMMAND");
  }, [seedFlowPhase]);

  const handleSeedFormSubmitForEntry = React.useCallback(
    async (p: SeedPayload): Promise<void> => {
      await onSeedSubmit(p);
    },
    [onSeedSubmit],
  );

  const handleBackToSeedEntry = React.useCallback(() => {
    if (isFinalized) return;
    clearLabPipelineForSeedDraft();
    setDraftSeed(null);
    setSeedFlowPhase("entry");
    setSeedEntryMountKey((k) => k + 1);
    setLastAppliedSeedSignature("");
    setCalculationCount(0);
    calculationCountRef.current = 0;
    setLastSuccessfulInputBundle(null);
    setRunSuccessFootnote("");
    bundleTier2ResetSuppressedUntilRef.current = 0;
  }, [isFinalized, clearLabPipelineForSeedDraft]);
  const currentSeedSignature = draftSeed ? JSON.stringify(draftSeed) : "";
  const currentParamSignature = JSON.stringify(pluginWeights || {});
  const seedDirty = Boolean(currentSeedSignature && currentSeedSignature !== lastAppliedSeedSignature);
  const paramDirty = currentParamSignature !== lastAppliedParamSignature;
  const currentDecisionsSignature = decisionIdsSignature(decisionIds);
  const isDecisionDirty = currentDecisionsSignature !== lastAppliedDecisionsSignature;

  const fullRecalcInputBundle = React.useMemo(
    () =>
      buildFullRecalcInputBundle({
        seedSignature: currentSeedSignature,
        paramSignature: currentParamSignature,
        referenceYear,
        labConfig,
      }),
    [currentSeedSignature, currentParamSignature, referenceYear, labConfig],
  );

  React.useEffect(() => {
    if (isFinalized) return;
    if (lastSuccessfulInputBundle === null) return;
    if (fullRecalcInputBundle === lastSuccessfulInputBundle) return;
    if (Date.now() < bundleTier2ResetSuppressedUntilRef.current) {
      return;
    }
    setCalculationCount(0);
    calculationCountRef.current = 0;
    bundleTier2ResetSuppressedUntilRef.current = 0;
    setRunSuccessFootnote("");
    if (runSuccessClearRef.current) {
      window.clearTimeout(runSuccessClearRef.current);
      runSuccessClearRef.current = null;
    }
  }, [fullRecalcInputBundle, lastSuccessfulInputBundle, isFinalized]);

  lastSuccessfulInputBundleRef.current = lastSuccessfulInputBundle;
  calculationCountRef.current = calculationCount;

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
      setCalculationCount(0);
      calculationCountRef.current = 0;
      setLastSuccessfulInputBundle(null);
      bundleTier2ResetSuppressedUntilRef.current = 0;
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
      ? `${t("检测到能量高度淤积（Abs: {abs}），做功路径受阻。").replace("{abs}", energyPeakAbs.toFixed(2))}${
          weakPathEnabled ? t("已开启逻辑透深。") : ""
        }`
      : "";
  const hasReboundRisk = backfireRiskVal > 0.35;
  const actionMode: "FULL" | "SEMANTIC" | "SYNCING" | "PARAMETER_DIRTY" = actionSyncing || busy || isCalculating
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
    ? t("已签发 (Issued)")
    : actionSyncing || busy || isCalculating
      ? undefined
      : calculationCount >= 1
        ? t("掐指再算")
        : t("掐指一算");

  const handleFullCalculate = React.useCallback(async () => {
    if (!draftSeed) return;
    const t0 = Date.now();
    setIsCalculating(true);
    setInboxScanActive(true);
    if (inboxPulseTimerRef.current) window.clearTimeout(inboxPulseTimerRef.current);
    inboxPulseTimerRef.current = window.setTimeout(() => {
      setInboxScanActive(false);
      inboxPulseTimerRef.current = null;
    }, 950);

    if (runSuccessClearRef.current) {
      window.clearTimeout(runSuccessClearRef.current);
      runSuccessClearRef.current = null;
    }
    setRunSuccessFootnote("");
    setFullRunErrorFootnote("");
    if (fullRunErrorClearRef.current) {
      window.clearTimeout(fullRunErrorClearRef.current);
      fullRunErrorClearRef.current = null;
    }

    const prevTensor = labSnapshotRef.current?.physics_tensor;
    const prevHash = physicsTensorFingerprint(prevTensor);

    try {
      const timeoutMs = 120_000;
      const result: SeedSubmitResult = await Promise.race([
        onSeedSubmit(draftSeed),
        new Promise<SeedSubmitResult>((resolve) => {
          window.setTimeout(
            () => resolve({ ok: false, error: t("计算超时（120s），请检查网络或后端。") }),
            timeoutMs,
          );
        }),
      ]).catch((e: unknown) => ({
        ok: false as const,
        error: e instanceof Error ? e.message : t("排盘过程异常中断。"),
      }));

      if (!result.ok) {
        const elapsedErr = Date.now() - t0;
        await new Promise((resolve) => setTimeout(resolve, Math.max(0, 800 - elapsedErr)));
        setFullRunErrorFootnote(result.error);
        fullRunErrorClearRef.current = window.setTimeout(() => {
          setFullRunErrorFootnote("");
          fullRunErrorClearRef.current = null;
        }, 10_000);
        return;
      }

      // 1) 先判定物理收敛（与 LLM 叙事解耦），立即提交档位与成功 bundle，再进入最短 UI 节拍
      const nextHash = physicsTensorFingerprint(result.physics_tensor);
      /** 物理收敛核指纹一致（双端非空），与 LLM 叙事解耦 */
      const physicsFingerprintMatch = prevHash !== "" && nextHash !== "" && prevHash === nextHash;

      const seedSig = JSON.stringify(draftSeed);
      const paramSig = JSON.stringify(pluginWeights || {});
      const bundleAfterSuccess = buildFullRecalcInputBundle({
        seedSignature: seedSig,
        paramSignature: paramSig,
        referenceYear,
        labConfig,
      });
      const prevCount = calculationCountRef.current;
      /** 同参再次全量：bundle 与上次成功一致时的收敛兜底（tensor 指纹噪声下仍视为稳态） */
      const samePhysicsBundleSecondTap =
        prevCount >= 1 &&
        lastSuccessfulInputBundleRef.current !== null &&
        bundleAfterSuccess === lastSuccessfulInputBundleRef.current;
      const tierConverged = physicsFingerprintMatch || samePhysicsBundleSecondTap;
      const nextCount = prevCount + 1;
      /** 与旧「第二轮收敛」一致：至少完成过一次全量后的收敛才触发终审整合，首轮指纹一致只提示稳态 */
      const shouldRunFinalVerdictSynthesis = tierConverged && prevCount >= 1;

      setCalculationCount(nextCount);
      calculationCountRef.current = nextCount;
      if (shouldRunFinalVerdictSynthesis) {
        bundleTier2ResetSuppressedUntilRef.current = Date.now() + 2800;
      }

      setLastAppliedSeedSignature(seedSig);
      setLastAppliedParamSignature(paramSig);
      setLastSuccessfulInputBundle(bundleAfterSuccess);
      lastSuccessfulInputBundleRef.current = bundleAfterSuccess;

      const elapsedAfterFetch = Date.now() - t0;
      await new Promise((resolve) => setTimeout(resolve, Math.max(0, 800 - elapsedAfterFetch)));

      if (shouldRunFinalVerdictSynthesis) {
        if (runSuccessClearRef.current) {
          window.clearTimeout(runSuccessClearRef.current);
          runSuccessClearRef.current = null;
        }
        setRunSuccessFootnote(
          t("✨ 物理已收敛：终审整合已执行。你可无限次「掐指再算」；改参或改运后将重新进入初算节拍。"),
        );
        window.setTimeout(() => {
          void runFinalVerdictSynthesis({ delayMs: 1000, trigger: "physics_converged" });
        }, 160);
      } else {
        setRunSuccessFootnote(
          tierConverged && !samePhysicsBundleSecondTap
            ? t("✨ 物理逻辑已达收敛稳态，当前参数配置已为最优解。")
            : t("计算完成，已更新逻辑视图"),
        );
        runSuccessClearRef.current = window.setTimeout(() => {
          setRunSuccessFootnote("");
          runSuccessClearRef.current = null;
        }, 10_000);
      }
    } finally {
      setIsCalculating(false);
      setCalculationNonce((prev) => prev + 1);
    }
  }, [draftSeed, onSeedSubmit, pluginWeights, referenceYear, labConfig, t, runFinalVerdictSynthesis]);

  const runSemanticRecompute = React.useCallback(async (decisions: InboxCard[]) => {
    setActionSyncing(true);
    try {
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

  /**
   * 主栏点击分流（严格优先级，勿随意调换）：
   * 1 生辰脏全量 → 2 未决冲突语义/裁决管线 → 3 可签发则签发 → 4 默认再次全量掐指（无限轮）
   */
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
    await handleFullCalculate();
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
        active={Boolean(streamThemeChroma.isConflictOverload && streamThemeChroma.hasPolarityReversal)}
        entropy={globalEntropy}
      />
      {seedFlowPhase === "main" ? (
        <LabViewModeFab viewMode={viewMode} onToggle={() => setViewMode((m) => (m === "VISION" ? "COMMAND" : "VISION"))} />
      ) : null}
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">{t(I18N[lang].title)}</h1>
          <p className="mt-1 font-mono text-[11px] text-amber-200/90">
            {t("未决冲突：")}
            {unresolvedConflictCount}
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
        </div>
      </header>

      {narrativeReshapeActive ? (
        <div
          className="mb-3 overflow-hidden rounded-lg border border-fuchsia-500/45 bg-gradient-to-r from-fuchsia-950/55 via-violet-950/45 to-cyan-950/35 px-3 py-2 shadow-[inset_0_0_28px_rgba(217,70,239,0.12)]"
          data-testid="narrative-reshape-banner"
        >
          <div className="flex flex-col gap-0.5 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-[11px] font-semibold tracking-wide text-fuchsia-50/95">{t("意志正在重塑现实…")}</p>
            <p className="text-[10px] text-fuchsia-200/75">{t("意志注塑中…")}</p>
          </div>
          <div className="relative mt-2 h-1 overflow-hidden rounded-full bg-zinc-900/90">
            <motion.div
              className="absolute left-0 top-0 h-full w-2/5 rounded-full bg-gradient-to-r from-transparent via-fuchsia-400/85 to-cyan-300/70"
              initial={{ x: "-40%" }}
              animate={{ x: ["-40%", "120%", "-40%"] }}
              transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
            />
          </div>
        </div>
      ) : null}

      {hasBoard ? <PatternStatus profile={patternProfile as PatternProfileSlice | null} className="mb-3" t={t} /> : null}

      {sovereigntyDominant ? (
        <div
          className="mb-2 rounded-lg border border-amber-400/55 bg-gradient-to-r from-amber-500/20 via-amber-400/15 to-amber-600/10 px-3 py-2 text-center text-[11px] font-semibold tracking-[0.2em] text-amber-100 shadow-[0_0_24px_rgba(251,191,36,0.18)]"
          data-testid="sovereignty-dominant-banner"
        >
          {t("主权占优")}
        </div>
      ) : null}

      {seedFlowPhase === "entry" ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mx-auto w-full max-w-xl space-y-3"
        >
          <div className="rounded-2xl border border-amber-500/30 bg-zinc-900/80 shadow-[0_0_0_1px_rgba(251,191,36,0.08)]">
            <div className="border-b border-zinc-800 px-3 py-2.5 text-xs font-medium text-amber-100/95">
              {t("生辰八字 · 地法（The Seed）")}
            </div>
            <div className="p-3">
              <SeedInput
                key={seedEntryMountKey}
                hydrateFrom={draftSeed}
                onSubmit={handleSeedFormSubmitForEntry}
                busy={busy}
                t={t}
                hideSubmitButton
                entryCommitAction={{
                  label: t("选定开始测算"),
                  busy: seedPreviewBusy,
                  onClick: async (p) => {
                    handleSeedPayloadChange(p);
                    await refreshSeedPreview(p);
                    setSeedFlowPhase("main");
                    setViewMode("COMMAND");
                  },
                }}
                onPayloadChange={handleSeedPayloadChange}
              />
            </div>
          </div>
        </motion.div>
      ) : (
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
                  setCurrentDecisions={setCurrentDecisions}
                  setDecisionIds={setDecisionIds}
                  handleMainBarRun={handleMainBarRun}
                  actionMode={actionMode}
                  isDecisionDirty={isDecisionDirty}
                  actionSyncing={actionSyncing || isCalculating}
                  primaryLabelOverride={primaryLabelOverride}
                  canIssueFinal={canIssueFinal}
                  checklistResetToken={checklistResetToken}
                  calculationNonce={calculationNonce}
                  inboxScanActive={inboxScanActive}
                  runSuccessFootnote={runSuccessFootnote}
                  fullRunErrorFootnote={fullRunErrorFootnote}
                  calculationCount={calculationCount}
                  hasVerdictHistory={hasVerdictHistory}
                  summaryVersionLabel={summaryVersionLabel}
                  l1JunctionFlags={l1JunctionFlags}
                  decisionSignalToNoise={decisionSignalToNoise}
                  onBackToSeedEntry={handleBackToSeedEntry}
                  onOpenPluginAudit={handleOpenPluginAudit}
                />
              )}
            </AnimatePresence>
          </div>
        </div>
      )}

      {labUiState.isFinalized && labUiState.finalizationReport?.hash ? (
        <motion.div
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="relative z-0 mt-8 border-t border-zinc-800/90 pt-6 shadow-[0_-12px_40px_rgba(0,0,0,0.35)]"
        >
          <p className="mb-2 text-center text-[10px] font-medium uppercase tracking-[0.25em] text-zinc-500">
            {t("终审已签发 · 公文压底")}
          </p>
          <VerdictCertificate
            hash={labUiState.finalizationReport.hash}
            committedAt={labUiState.finalizationReport.committedAt}
            logicDiff={logicDiff}
            effectiveSkillIds={
              labUiState.finalizationReport.effectiveSkillIds ??
              (labUiState.snapshot?.metadata?.verdict_effective_skill_ids as string[] | undefined)
            }
            solidGhostRatio={
              (() => {
                const m = labUiState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined;
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
            t={t}
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
