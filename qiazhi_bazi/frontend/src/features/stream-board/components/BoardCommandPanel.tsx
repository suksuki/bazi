import React from "react";
import { motion } from "framer-motion";
import { DecisionInbox } from "@/components/DecisionInbox";
import { ReferenceYearSelect } from "@/components/ReferenceYearSelect";
import { UnifiedActionBar } from "@/components/UnifiedActionBar";
import { BlindSkillBadgeRow } from "./BlindSkillBadgeRow";
import { EnergyFlowChainStrip } from "./EnergyFlowChainStrip";
import { TemporalYearSlider } from "./TemporalYearSlider";
import { WillReplayPanel } from "./WillReplayPanel";
import { useActiveView } from "@/components/layout/ActiveViewContext";
import type { DecisionSignalToNoiseMeta, StreamBoardViewModel, InboxCard } from "../models";

// Recreate these constants to avoid dependencies if needed, or import from somewhere.
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

export interface BoardCommandPanelProps {
  viewModel: StreamBoardViewModel;
  draftSeed: any;
  simpleBoard: any;
  isPreviewBoard: boolean;
  seedPreviewBusy: boolean;
  seedPreviewError: string | null;
  lastSubmittedDecisionIds: string[];
  blindSkillBadges: any[];
  setCurrentDecisions: (decisions: InboxCard[]) => void;
  setDecisionIds: (ids: string[]) => void;
  handleMainBarRun: () => void;
  handleRevokeDecision: (id: string) => void;
  revertEntropyDelta: number | null;
  actionMode: "FULL" | "SEMANTIC" | "SYNCING" | "PARAMETER_DIRTY";
  isDecisionDirty: boolean;
  actionSyncing: boolean;
  primaryLabelOverride?: string;
  canIssueFinal: boolean;
  checklistResetToken: number;
  workExpectation: number;
  backfireRiskVal: number;
  releasedEnergyVal: number;
  hasVerdictHistory: boolean;
  summaryVersionLabel: string;
  l1JunctionFlags: Record<string, unknown> | undefined;
  decisionSignalToNoise?: DecisionSignalToNoiseMeta | null;
  /** 返回仅生辰入口（清空命盘与流水线） */
  onBackToSeedEntry?: () => void;
}

export function BoardCommandPanel({
  viewModel,
  draftSeed,
  simpleBoard,
  isPreviewBoard,
  seedPreviewBusy,
  seedPreviewError,
  lastSubmittedDecisionIds,
  blindSkillBadges,
  setCurrentDecisions,
  setDecisionIds,
  handleMainBarRun,
  handleRevokeDecision,
  revertEntropyDelta,
  actionMode,
  isDecisionDirty,
  actionSyncing,
  primaryLabelOverride,
  canIssueFinal,
  checklistResetToken,
  workExpectation,
  backfireRiskVal,
  releasedEnergyVal,
  hasVerdictHistory,
  summaryVersionLabel,
  l1JunctionFlags,
  decisionSignalToNoise,
  onBackToSeedEntry,
}: BoardCommandPanelProps) {
  const { setActiveView } = useActiveView();
  const {
    t,
    lang,
    busy,
    referenceYear,
    setReferenceYear,
    metadata,
    globalEntropy,
    setAsBaseline,
    isFinalized,
    sigShiftFlashKey,
    cards,
    resultLogs,
    finalVerdictBody,
    finalVerdictChangeLog,
    finalLogicalEvidence,
    finalWorkVector,
    finalTopologyGraphV1,
    finalStructureCandidatesV0,
    finalStructureFinalDecisionV0,
    stressTestResult,
    genderComparisonResult,
    openLogicDrawerByDeity,
    setHoveredDeity,
    onEvidenceItemClick,
    showVerdictHistory,
    selectionResetToken,
    summaryChanged,
    l1Certified,
    runStressTest,
    runGenderComparison,
    pluginWeights,
    setPluginWeights,
    labConfig,
    setLabConfig,
    energyFlowAudit,
    timeline,
    rerunFinalVerdictWithWeights,
    logicDiff,
    inboxResetNonce,
    confirmedDecisions,
    physicsAudit,
    physicsConfidence,
    physicsEvidence,
  } = viewModel;

  return (
    <motion.div
      key="command"
      initial={{ opacity: 0, x: 16 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -16 }}
      transition={{ duration: 0.22 }}
      className="space-y-3"
    >
      <div className="rounded-2xl border border-amber-500/30 bg-zinc-900/80 shadow-[0_0_0_1px_rgba(251,191,36,0.08)]">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 px-3 py-2.5">
          <span className="text-xs font-medium text-amber-100/95">{t("命盘 · 六柱与流年")}</span>
          {onBackToSeedEntry ? (
            <button
              type="button"
              onClick={onBackToSeedEntry}
              disabled={Boolean(busy || isFinalized)}
              className="shrink-0 rounded-lg border border-zinc-600 bg-zinc-800/90 px-2.5 py-1 text-[10px] font-medium text-zinc-200 hover:border-amber-500/40 hover:text-amber-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("返回重新测算")}
            </button>
          ) : null}
        </div>
        <div className="px-2 pb-2 pt-2">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <label className="flex flex-col gap-0.5 text-[10px] text-zinc-400 sm:flex-row sm:items-center sm:gap-1.5">
              <span>{t("流年（参考年）")}</span>
              <ReferenceYearSelect
                value={referenceYear}
                onChange={setReferenceYear}
                className="w-[4.75rem] rounded border border-zinc-600 bg-zinc-900 px-1.5 py-0.5 font-mono text-[11px] text-zinc-100"
              />
            </label>
            <label className="flex flex-col gap-0.5 text-[10px] text-zinc-400 sm:flex-row sm:items-center sm:gap-1.5">
              <span title={t("地理场演示：南强化火、北强化水（需重新测算）")}>{t("环境方位")}</span>
              <select
                value={labConfig.user_target_direction ?? ""}
                onChange={(e) => {
                  const v = e.target.value.trim();
                  setLabConfig((prev) => ({ ...prev, user_target_direction: v || undefined }));
                }}
                className="max-w-[5.5rem] rounded border border-zinc-600 bg-zinc-900 px-1 py-0.5 font-mono text-[11px] text-zinc-100"
              >
                <option value="">—</option>
                <option value="东">{t("东")}</option>
                <option value="南">{t("南")}</option>
                <option value="西">{t("西")}</option>
                <option value="北">{t("北")}</option>
                <option value="中">{t("中")}</option>
              </select>
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
            <TemporalYearSlider
              referenceYear={referenceYear}
              onYearChange={setReferenceYear}
              timeline={timeline}
              disabled={Boolean(busy || isFinalized)}
              className="mb-2"
              t={t}
            />
          ) : null}
          <EnergyFlowChainStrip
            audit={energyFlowAudit}
            motionKey={referenceYear}
            className="mb-2 transition-opacity duration-500 ease-out"
            t={t}
          />
          {simpleBoard ? (
            <div className="grid grid-cols-3 gap-1.5 sm:grid-cols-6 md:grid-cols-9">
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
          ) : (
            <p className="text-sm text-zinc-500">{t("掐指一算后在此显示：四柱 / 大运 / 流年")}</p>
          )}
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
        t={t}
      />
      <div className="rounded-md border border-zinc-800 bg-zinc-950/60 px-2 py-1 text-[10px] text-zinc-400">
        {t("提交 IDs：")}{" "}
        {lastSubmittedDecisionIds.length ? lastSubmittedDecisionIds.join(", ") : "[]"}
      </div>
      <BlindSkillBadgeRow badges={blindSkillBadges} t={t} />
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
        decisionSignalToNoise={decisionSignalToNoise}
        lang={lang}
      />
      <WillReplayPanel
        items={confirmedDecisions || []}
        onRevoke={handleRevokeDecision}
        revertEntropyDelta={revertEntropyDelta}
        t={t}
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
  );
}
