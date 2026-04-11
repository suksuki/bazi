import React from "react";
import { motion } from "framer-motion";
import { BaziCard } from "@/components/BaziCard";
import { BlindLogicMirror } from "@/components/BlindLogicMirror";
import { StrategicCoreHUD } from "@/components/StrategicCoreHUD";
import { TenGodNumericList } from "@/components/TenGodNumericList";
import { TopologyMapV1 } from "@/components/TopologyMapV1";
import { ReferenceYearSelect } from "@/components/ReferenceYearSelect";
import { BlindSkillBadgeRow } from "./BlindSkillBadgeRow";
import { TemporalYearSlider } from "./TemporalYearSlider";
import { LogicSummary } from "./LogicSummary";
import type { StreamBoardViewModel } from "../models";
import { useLabStore } from "../stores/useLabStore";

export interface BoardVisionPanelProps {
  viewModel: StreamBoardViewModel;
  hasBoard: boolean;
  isPreviewBoard: boolean;
  globalEntropy: number | null;
  visionDiagnosticHint: string;
  hasReboundRisk: boolean;
  energyPeakAbs: number;
  blindSkillBadges: any[];
  goToSeedInput: () => void;
  hardRouteLogs: string[];
  climateSeason: string;
  releasedEnergyVal: number;
}

export function BoardVisionPanel({
  viewModel,
  hasBoard,
  isPreviewBoard,
  globalEntropy,
  visionDiagnosticHint,
  hasReboundRisk,
  energyPeakAbs,
  blindSkillBadges,
  goToSeedInput,
  hardRouteLogs,
  climateSeason,
  releasedEnergyVal,
}: BoardVisionPanelProps) {
  const {
    t,
    lang,
    metadata,
    timeline,
    referenceYear,
    setReferenceYear,
    finalStructureFinalDecisionV0,
    pluginWeights,
    openLogicDrawerByDeity,
    deityScores,
    deityEnergyAxes,
    deityComponents,
    hoveredDeity,
    selectedBranch,
    confirmedConflicts,
    setSelectedBranch,
    deityTraceDetails,
    llmDiagnosticData,
    consensusHistory,
    labConfig,
    openLogicDrawer,
    setHoveredDeity,
    busy,
    isFinalized,
    finalWorkVector,
    finalTopologyGraphV1,
    physicsAudit,
    causalRouting,
  } = viewModel;

  const { state: labState } = useLabStore();
  const snapMeta = React.useMemo(() => {
    const m = labState.snapshot?.physics_tensor?.meta;
    return m && typeof m === "object" ? (m as Record<string, unknown>) : {};
  }, [labState.snapshot?.physics_tensor?.meta]);
  const stemFusionMeta = (snapMeta.stem_fusion_v1 || null) as Record<string, unknown> | null;
  const l1StatusBlock = snapMeta.l1_status_v1 as { per_deity?: Record<string, { work_efficiency?: number }> } | undefined;
  const l1StatusPerDeity = l1StatusBlock?.per_deity ?? null;
  const pivotBlock = snapMeta.pivot_defense_v1 as
    | { target_pivot?: string; defense_semantic?: string }
    | undefined;
  const pivotDeity = (pivotBlock?.target_pivot && String(pivotBlock.target_pivot)) || null;
  const pivotDefenseSemantic = (pivotBlock?.defense_semantic && String(pivotBlock.defense_semantic)) || null;

  return (
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
      <LogicSummary physicsAudit={physicsAudit} t={t} />
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
          t={t}
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
            {metadata?.pillars ? (
              <TemporalYearSlider
                referenceYear={referenceYear}
                onYearChange={setReferenceYear}
                timeline={timeline}
                disabled={Boolean(busy || isFinalized)}
                className="w-full min-w-[200px] max-w-md"
                t={t}
              />
            ) : null}
            {isPreviewBoard ? (
              <span className="rounded border border-amber-500/45 bg-amber-500/12 px-1 py-0.5 text-[9px] text-amber-200">{t("预览")}</span>
            ) : null}
          </div>
        </div>
        {/* md+ 与指令舱顶栏徽章去重：桌面端仅在 Command 模式展示 BlindSkillBadgeRow */}
        <div className="md:hidden">
          <BlindSkillBadgeRow badges={blindSkillBadges} t={t} />
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
              causalRouting={causalRouting}
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
              stemFusionMeta={stemFusionMeta}
              l1StatusPerDeity={l1StatusPerDeity}
              pivotDeity={pivotDeity}
              pivotDefenseSemantic={pivotDefenseSemantic}
              fluxKey={referenceYear}
              t={t}
            />
          </div>
        </div>
      </section>
      <div className="min-h-[min(52dvh,420px)] flex-1 rounded-2xl border border-zinc-800 bg-zinc-950/60 p-2">
        <BlindLogicMirror workVector={finalWorkVector || {}} t={t} />
      </div>
      <div className="flex min-h-[min(42dvh,360px)] flex-1 flex-col rounded-2xl border border-zinc-800 bg-zinc-950/50 p-2">
        <TopologyMapV1 graph={finalTopologyGraphV1 || {}} />
      </div>
    </motion.div>
  );
}
