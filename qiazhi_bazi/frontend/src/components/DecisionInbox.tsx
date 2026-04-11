"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { BlindLogicMirror } from "@/components/BlindLogicMirror";
import { ComparisonBridgeModal } from "@/components/ComparisonBridgeModal";
import { StrategicCoreHUD } from "@/components/StrategicCoreHUD";
import { TopologyMapV1 } from "@/components/TopologyMapV1";
import { elementColorClass } from "@/constants/termMap";
import { DecisionItem } from "@/features/decision-engine/components/DecisionItem";
import { DecisionInboxCard, VerdictChangeLog } from "@/features/decision-inbox/types";
import type { DecisionSignalToNoiseMeta, LogicDiff } from "@/features/stream-board/models";
import {
  getCardElement,
  getCardLabel,
  getEvidenceTone,
  isAuditorProposal,
  isVerdictDeity,
  pruneSelectedIds,
  sgjgEnergeticLabelForCard,
  splitVerdictLine,
} from "@/features/decision-inbox/utils";
import { SkillLinkedAssertionLine } from "@/features/stream-board/components/ResultInterpretation";

type Props = {
  cards: DecisionInboxCard[];
  resultLogs: string[];
  verdictBody?: string;
  verdictChangeLog?: VerdictChangeLog;
  logicalEvidence?: string[];
  workVector?: Record<string, unknown>;
  topologyGraph?: Record<string, unknown>;
  structureCandidates?: Record<string, unknown>;
  structureFinalDecision?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  stressTestResult?: Record<string, unknown>;
  genderComparisonResult?: Record<string, unknown>;
  highlightVerdict?: boolean;
  onSelectionChange?: (selected: DecisionInboxCard[]) => void;
  onVerdictDeityClick?: (deity: string) => void;
  onStrategicDeityHover?: (deity?: string) => void;
  onEvidenceClick?: (evidence: string) => void;
  onShowVersionHistory?: () => void;
  onStressTest?: (scenario: string) => Promise<void>;
  onGenderCompare?: () => Promise<void>;
  pluginWeights?: { blindSchool: number; wangshuai: number };
  onPluginWeightsChange?: (next: { blindSchool: number; wangshuai: number }) => void;
  onApplyPluginWeights?: () => Promise<void>;
  hasVerdictHistory?: boolean;
  selectionResetToken?: number;
  summaryVersionLabel?: string;
  summaryChanged?: boolean;
  l1Certified?: boolean;
  /** L1 全局熵，驱动 HUD 脉冲与故障艺术联动 */
  globalEntropy?: number | null;
  /** 指令舱降噪：隐藏核心看板（HUD + 盲派镜像） */
  hideStrategicPanel?: boolean;
  logicDiff?: LogicDiff;
  actionMode?: "FULL" | "SEMANTIC" | "SYNCING" | "PARAMETER_DIRTY";
  autoSyncIdle?: boolean;
  t?: (s: string) => string;
  inboxResetNonce?: number;
  /** 终审已签发：冻结勾选与语义权重滑杆 */
  interactionLocked?: boolean;
  /** physics_tensor.meta.l1_junction_flags：伤官见官能级等 */
  l1JunctionFlags?: Record<string, unknown>;
  /** physics_tensor.meta.decision_signal_to_noise：信噪比门控（阈值等） */
  decisionSignalToNoise?: DecisionSignalToNoiseMeta | null;
};

export function DecisionInbox({
  cards,
  resultLogs,
  verdictBody = "",
  verdictChangeLog = {},
  logicalEvidence = [],
  workVector = {},
  topologyGraph = {},
  structureCandidates = {},
  structureFinalDecision = {},
  metadata = {},
  stressTestResult = {},
  genderComparisonResult = {},
  highlightVerdict = false,
  onSelectionChange,
  onVerdictDeityClick,
  onStrategicDeityHover,
  onEvidenceClick,
  onShowVersionHistory,
  onStressTest,
  onGenderCompare,
  pluginWeights = { blindSchool: 0.8, wangshuai: 0.6 },
  onPluginWeightsChange,
  onApplyPluginWeights,
  hasVerdictHistory = false,
  selectionResetToken = 0,
  summaryVersionLabel,
  summaryChanged = false,
  l1Certified = false,
  globalEntropy = null,
  hideStrategicPanel = false,
  logicDiff,
  actionMode = "SEMANTIC",
  autoSyncIdle = true,
  t = (s) => s,
  inboxResetNonce = 0,
  interactionLocked = false,
  l1JunctionFlags,
  decisionSignalToNoise,
}: Props) {
  const [selectedIds, setSelectedIds] = useState<Record<string, boolean>>({});
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [stressInput, setStressInput] = useState("壬辰");
  const [sectionOpen, setSectionOpen] = useState({
    strategic: true,
    summary: true,
  });
  const [summaryOpen, setSummaryOpen] = useState({
    diff: true,
    evidence: false,
    work: true,
    topology: false,
    structure: true,
  });
  const [comparisonOpen, setComparisonOpen] = useState(false);
  const [weighting, setWeighting] = useState(pluginWeights);
  const [inboxResetWaveKey, setInboxResetWaveKey] = useState(0);
  const inboxNoncePrevRef = useRef<number | null>(null);
  const normalizeDeityList = (value: unknown): string[] => {
    if (Array.isArray(value)) return value.map((item) => String(item || "").trim()).filter(Boolean);
    if (typeof value === "string") {
      return value
        .split(/[、,/\s]+/)
        .map((item) => item.trim())
        .filter(Boolean);
    }
    return [];
  };
  const useful = normalizeDeityList(
    (structureFinalDecision as {
      utility_god?: unknown;
      strategic_advice?: { core_useful_gods?: unknown };
    }).utility_god
      || (structureFinalDecision as { strategic_advice?: { core_useful_gods?: unknown } }).strategic_advice?.core_useful_gods,
  );
  const obstacle = normalizeDeityList(
    (structureFinalDecision as {
      obstacle_god?: unknown;
      strategic_advice?: { core_obstacle_gods?: unknown };
    }).obstacle_god
      || (structureFinalDecision as { strategic_advice?: { core_obstacle_gods?: unknown } }).strategic_advice?.core_obstacle_gods,
  );
  const climateSummary = String(
    ((structureFinalDecision as { climate_adjustment?: { summary?: string } }).climate_adjustment?.summary) || "--",
  );
  const extremeAbsLoss = Number(logicDiff?.abs_delta || 0) > 100;
  const baseRecommendation = String(
    ((structureFinalDecision as { strategic_advice?: { recommendation?: string } }).strategic_advice?.recommendation) || "",
  ).trim();
  const energyRiskHint = "风险提示：当前物理能耗过高（abs_delta > 100），应优先执行降耗与稳态校准。";
  const strategicRecommendation = baseRecommendation
    ? (extremeAbsLoss && !baseRecommendation.includes("物理能耗过高")
      ? `${baseRecommendation} ${energyRiskHint}`
      : baseRecommendation)
    : (extremeAbsLoss ? energyRiskHint : "");

  const selectedCards = cards.filter((c) => selectedIds[c.id]);
  function applySelection(next: Record<string, boolean>) {
    if (interactionLocked) return;
    setSelectedIds(next);
    const nextSelected = cards.filter((card) => Boolean(next[card.id]));
    onSelectionChange?.(nextSelected);
  }
  const hasReboundRisk = (((workVector as { work_vectors?: Array<Record<string, unknown>> }).work_vectors) || [])
    .some((item) => {
      const gain = Number(item.unlock_gain ?? 0);
      const risk = Number(item.backfire_risk ?? 0);
      return String(item.momentum_direction || "") === "REBOUND" || risk >= gain;
    });
  const energyPeakAbs = Math.max(
    Number((structureCandidates as { self_abs?: number }).self_abs || 0),
    Number((workVector as { host_abs?: number }).host_abs || 0),
    Number((workVector as { guest_abs?: number }).guest_abs || 0),
  );
  const workExpectation = Number((workVector as { work_expectation?: number }).work_expectation || 0);
  const weakPathEnabled = Number((((workVector as { runtime_physics_config?: Record<string, unknown> }).runtime_physics_config || {}).SHOW_WEAK_WORK_PATHS) || 0) > 0.5;
  const diagnosticHint = (energyPeakAbs > 10 && Math.abs(workExpectation) < 0.1)
    ? `检测到能量高度淤积（Abs: ${energyPeakAbs.toFixed(2)}），做功路径已被岁运阻断。${weakPathEnabled ? "当前已开启逻辑透深。" : "建议开启“逻辑透深”检查被隐藏的内耗路径。"}`
    : "";

  useEffect(() => {
    // 卡片内容可能因翻译或流式更新变化；仅移除不存在的 id，避免勾选被瞬间清空。
    setSelectedIds((prev) => pruneSelectedIds(prev, cards.map((card) => card.id)));
  }, [cards]);

  useEffect(() => {
    setSelectedIds({});
  }, [selectionResetToken]);
  useEffect(() => {
    const prev = inboxNoncePrevRef.current;
    if (prev === null) {
      inboxNoncePrevRef.current = inboxResetNonce;
      return;
    }
    if (inboxResetNonce > prev) {
      setInboxResetWaveKey((k) => k + 1);
    }
    inboxNoncePrevRef.current = inboxResetNonce;
  }, [inboxResetNonce]);
  useEffect(() => {
    setWeighting(pluginWeights);
  }, [pluginWeights.blindSchool, pluginWeights.wangshuai]);
  async function runStress() {
    await onStressTest?.(stressInput);
  }

  const feedbackSessionHint = String(
    (metadata as { consultation_id?: unknown; session_id?: unknown }).consultation_id ??
      (metadata as { session_id?: unknown }).session_id ??
      "",
  );

  function renderVerdictLine(line: string, idx: number) {
    const parts = splitVerdictLine(line);
    const isFallbackLine = line.includes("[SYSTEM_FALLBACK]");
    const lineClass = `whitespace-pre-wrap leading-relaxed ${
      summaryChanged
        ? "rounded-md bg-gradient-to-r from-amber-500/10 via-emerald-500/5 to-transparent px-2 py-1 text-emerald-200"
        : "text-emerald-300"
    } ${
      highlightVerdict ? "text-[1.2rem] font-semibold" : "text-sm"
    } ${
      isFallbackLine ? "animate-pulse rounded border border-rose-500/35 bg-rose-500/10 px-2 py-1 text-rose-300" : ""
    }`;
    return (
      <SkillLinkedAssertionLine
        key={`${idx}-${line.slice(0, 12)}`}
        line={line}
        className={lineClass}
        assertionIndex={idx}
        sessionHint={feedbackSessionHint}
        interactionLocked={interactionLocked}
      >
        {parts.map((part, i) => (
          isVerdictDeity(part) ? (
            <button
              key={`${idx}-${i}-${part}`}
              type="button"
              onClick={() => onVerdictDeityClick?.(part)}
              className="mx-[1px] rounded border border-sky-500/30 bg-sky-500/10 px-1 text-sky-200 hover:bg-sky-500/20"
              title={`查看 ${part} 的演算路径`}
            >
              {part}
            </button>
          ) : (
            <span key={`${idx}-${i}`}>{part}</span>
          )
        ))}
      </SkillLinkedAssertionLine>
    );
  }

  function toggleSection(key: keyof typeof sectionOpen) {
    setSectionOpen((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function toggleSummary(key: keyof typeof summaryOpen) {
    setSummaryOpen((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/60">
      <AnimatePresence>
        {inboxResetWaveKey > 0 ? (
          <motion.div
            key={inboxResetWaveKey}
            className="pointer-events-none absolute inset-0 z-[1] rounded-2xl"
            initial={{ opacity: 0.48, scale: 0.9 }}
            animate={{ opacity: 0, scale: 1.42 }}
            transition={{ duration: 0.88, ease: [0.22, 1, 0.36, 1] }}
            style={{
              background: "radial-gradient(circle at 50% 32%, rgba(168, 85, 247, 0.42), transparent 72%)",
              boxShadow: "inset 0 0 88px rgba(168, 85, 247, 0.28)",
            }}
          />
        ) : null}
      </AnimatePresence>
    <section className="relative z-10 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium">{t("Decision Inbox")}</h3>
        <span className="text-xs text-zinc-500">{t("流式对话与决策卡片")}</span>
      </div>
      {!hideStrategicPanel ? (
        <div className="mb-3 rounded-xl border border-zinc-800 bg-zinc-950 p-2">
        <button
          type="button"
          onClick={() => toggleSection("strategic")}
          className="flex w-full items-center justify-between rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-left text-xs text-zinc-200 hover:bg-zinc-800"
        >
          <span>核心看板（Strategic HUD + 盲派镜像）</span>
          <span>{sectionOpen.strategic ? "收起" : "展开"}</span>
        </button>
        {sectionOpen.strategic ? (
          <div className="mt-2">
            <StrategicCoreHUD
              structureFinalDecision={structureFinalDecision}
              pluginWeights={pluginWeights}
              hasReboundRisk={hasReboundRisk}
              energyPeak={energyPeakAbs}
              globalEntropy={globalEntropy}
              genderLabel={String((metadata as { gender?: string }).gender || "")}
              diagnosticHint={diagnosticHint}
              onPickDeity={(deity) => {
                onVerdictDeityClick?.(deity);
                onStrategicDeityHover?.(deity);
              }}
            />
            <div className="mb-2 rounded border border-zinc-700 bg-zinc-900 p-2 text-[11px] text-zinc-300">
              <p className="mb-1">语义权重滑杆（Plugin Weights）</p>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                <label>
                  盲派 {weighting.blindSchool.toFixed(2)}
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={weighting.blindSchool}
                    disabled={interactionLocked}
                    onChange={(e) => setWeighting((prev) => ({ ...prev, blindSchool: Number(e.target.value) }))}
                    onMouseUp={async () => {
                      if (interactionLocked) return;
                      onPluginWeightsChange?.(weighting);
                      await onApplyPluginWeights?.();
                    }}
                    className="w-full disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </label>
                <label>
                  旺衰 {weighting.wangshuai.toFixed(2)}
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={weighting.wangshuai}
                    disabled={interactionLocked}
                    onChange={(e) => setWeighting((prev) => ({ ...prev, wangshuai: Number(e.target.value) }))}
                    onMouseUp={async () => {
                      if (interactionLocked) return;
                      onPluginWeightsChange?.(weighting);
                      await onApplyPluginWeights?.();
                    }}
                    className="w-full disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </label>
                <button
                  type="button"
                  disabled={interactionLocked}
                  onClick={async () => {
                    if (interactionLocked) return;
                    onPluginWeightsChange?.(weighting);
                    await onApplyPluginWeights?.();
                  }}
                  className="rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-zinc-200 hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  应用权重并重算
                </button>
              </div>
            </div>
            <BlindLogicMirror
              workVector={workVector}
            />
          </div>
        ) : null}
        </div>
      ) : null}

      <div className="space-y-3 pb-20">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-3">
          <h4 className="text-sm font-medium text-zinc-100">Decision Items</h4>
          <p className="mt-1 text-xs text-zinc-400">{t("勾选决策项后可在统一动作条触发语义裁决。")}</p>
          {decisionSignalToNoise?.inbox_conflict_cards_eligible === false && metadata && Object.keys(metadata).length > 0 ? (
            <p className="mt-2 font-mono text-[10px] leading-relaxed text-zinc-600">
              [SIGNAL_GATE_ACTIVE]: 微弱因果噪声已物理屏蔽，阈值:{" "}
              {typeof decisionSignalToNoise.threshold === "number"
                ? decisionSignalToNoise.threshold.toFixed(1)
                : "5.0"}{" "}
              Abs
            </p>
          ) : null}
          <div className="mt-3 space-y-2">
            {cards.length === 0 ? <p className="text-xs text-zinc-500">{t("暂无可执行决策项。")}</p> : null}
            <AnimatePresence initial={false}>
              {cards.map((card) => (
                (() => {
                  const labelText = getCardLabel(card);
                  const element = getCardElement(card);
                  const isProposal = isAuditorProposal(card.cardType);
                  const showDeltaBadge = actionMode === "PARAMETER_DIRTY" && autoSyncIdle;
                  return (
                    <motion.label
                      key={card.id}
                      initial={{ opacity: 0, x: 18 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -100 }}
                      transition={{ duration: 0.22 }}
                      className={`block ${interactionLocked ? "opacity-60" : ""}`}
                    >
                      <DecisionItem
                        label={labelText}
                        selected={Boolean(selectedIds[card.id])}
                        isProposal={isProposal}
                        dotClassName={elementColorClass(element)}
                        deltaAbs={logicDiff?.abs_delta}
                        showDeltaBadge={showDeltaBadge}
                        skillId={card.skillId}
                        energeticLevelLabel={sgjgEnergeticLabelForCard(card, l1JunctionFlags)}
                        toggleDisabled={interactionLocked}
                        onToggle={() =>
                          applySelection({
                            ...selectedIds,
                            [card.id]: !selectedIds[card.id],
                          })
                        }
                      />
                    </motion.label>
                  );
                })()
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <section className="mt-4 rounded-xl border border-zinc-800 bg-zinc-950 p-2">
        <button
          type="button"
          onClick={() => toggleSection("summary")}
          className="flex w-full items-center justify-between rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-left text-xs text-zinc-200 hover:bg-zinc-800"
        >
          <span>结果总览（Result Summary）</span>
          <span>{sectionOpen.summary ? "收起" : "展开"}</span>
        </button>
        {sectionOpen.summary ? (
      <div
        className={`mt-2 rounded-xl bg-zinc-950 p-3 ${
          highlightVerdict ? "border-2 border-amber-400/70 shadow-[0_0_18px_rgba(251,191,36,0.25)]" : "border border-zinc-800"
        }`}
      >
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-zinc-200">{t("Result Summary")}</h4>
          <div className="flex items-center gap-2">
            {hasVerdictHistory ? (
              <button
                type="button"
                onClick={() => onShowVersionHistory?.()}
                className="rounded-md border border-zinc-700 bg-zinc-900 px-2 py-0.5 text-[10px] text-zinc-300 hover:bg-zinc-800"
              >
                查看历史版本
              </button>
            ) : null}
            {summaryVersionLabel ? (
              <span className="rounded-md border border-zinc-700 bg-zinc-900 px-2 py-0.5 text-[10px] text-zinc-400">
                {summaryVersionLabel}
              </span>
            ) : null}
          </div>
        </div>
        <div className="mt-2 space-y-1">
          <div className="mb-2 grid grid-cols-1 gap-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 md:grid-cols-3">
            <div className="rounded border border-emerald-600/40 bg-emerald-500/10 px-2 py-1">
              <p className="text-[10px] text-emerald-300/90">用神</p>
              <p className="text-xs font-medium text-emerald-100">{useful.length ? useful.join(" / ") : "--"}</p>
            </div>
            <div className="rounded border border-rose-600/40 bg-rose-500/10 px-2 py-1">
              <p className="text-[10px] text-rose-300/90">忌神</p>
              <p className="text-xs font-medium text-rose-100">{obstacle.length ? obstacle.join(" / ") : "--"}</p>
            </div>
            <div className="rounded border border-sky-600/40 bg-sky-500/10 px-2 py-1">
              <p className="text-[10px] text-sky-300/90">调候</p>
              <p className="text-xs font-medium text-sky-100">{climateSummary}</p>
            </div>
          </div>
          {l1Certified ? (
            <div className="mb-2 inline-flex items-center rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-300">
              L1 Certified
            </div>
          ) : null}
          {!verdictBody && resultLogs.length === 0 ? <p className="text-xs text-zinc-500">{t("等待确认后生成阶段结论…")}</p> : null}
          {verdictBody
            ? verdictBody.split("\n").map((x, i) => renderVerdictLine(x, i))
            : resultLogs.map((x, i) => renderVerdictLine(x, i))}
          {(verdictChangeLog.physics_diff?.length || verdictChangeLog.consensus_diff?.length || verdictChangeLog.text_diff_hint) ? (
            <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
              <button
                type="button"
                onClick={() => toggleSummary("diff")}
                className="mb-2 flex w-full items-center justify-between rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-zinc-300 hover:bg-zinc-800"
              >
                <span>变更差分（Physics / Consensus / Text）</span>
                <span>{summaryOpen.diff ? "收起" : "展开"}</span>
              </button>
              {summaryOpen.diff ? (
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                <div className="rounded border border-zinc-700 bg-zinc-950 p-2">
                  <p className="mb-1 text-zinc-300">物理场变动</p>
                  {(verdictChangeLog.physics_diff || []).length === 0 ? <p className="text-zinc-500">- 无</p> : null}
                  {(verdictChangeLog.physics_diff || []).map((x, i) => <p key={`pd-${i}`} className="text-zinc-400">- {x}</p>)}
                </div>
                <div className="rounded border border-zinc-700 bg-zinc-950 p-2">
                  <p className="mb-1 text-zinc-300">共识固化</p>
                  {(verdictChangeLog.consensus_diff || []).length === 0 ? <p className="text-zinc-500">- 无</p> : null}
                  {(verdictChangeLog.consensus_diff || []).map((x, i) => <p key={`cd-${i}`} className="text-zinc-400">- {x}</p>)}
                </div>
                <div className="rounded border border-zinc-700 bg-zinc-950 p-2">
                  <p className="mb-1 text-zinc-300">判词修正</p>
                  <p className="text-zinc-400">{verdictChangeLog.text_diff_hint || "无"}</p>
                </div>
              </div>
              ) : null}
            </div>
          ) : null}
          {logicalEvidence.length > 0 ? (
            <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
              <button
                type="button"
                onClick={() => {
                  setEvidenceOpen((v) => !v);
                  if (!summaryOpen.evidence) toggleSummary("evidence");
                }}
                className="rounded border border-zinc-700 bg-zinc-950 px-2 py-0.5 text-zinc-300 hover:bg-zinc-800"
              >
                {evidenceOpen ? "收起证据快照" : "展开证据快照"}
              </button>
              <button
                type="button"
                onClick={() => toggleSummary("evidence")}
                className="ml-2 rounded border border-zinc-700 bg-zinc-950 px-2 py-0.5 text-zinc-300 hover:bg-zinc-800"
              >
                {summaryOpen.evidence ? "隐藏模块" : "显示模块"}
              </button>
              {evidenceOpen && summaryOpen.evidence ? (
                <div className="mt-2 max-h-40 space-y-1 overflow-auto">
                  {logicalEvidence.map((x, i) => (
                    <button
                      key={`ev-${i}`}
                      type="button"
                      onClick={() => onEvidenceClick?.(x)}
                      className={`block w-full rounded border px-2 py-1 text-left hover:border-sky-500/40 hover:text-sky-200 ${getEvidenceTone(x)}`}
                      title="点击下钻证据"
                    >
                      {x}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
          {Array.isArray((workVector as { work_vectors?: unknown[] })?.work_vectors)
            && ((workVector as { work_vectors?: unknown[] })?.work_vectors || []).length > 0 ? (
              <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
                <button
                  type="button"
                  onClick={() => toggleSummary("work")}
                  className="mb-2 flex w-full items-center justify-between rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-left text-zinc-300 hover:bg-zinc-800"
                >
                  <span>盲派做功链路图（L2）</span>
                  <span>{summaryOpen.work ? "收起" : "展开"}</span>
                </button>
                {summaryOpen.work ? <div className="space-y-1">
                  {((workVector as { work_vectors?: Array<Record<string, unknown>> }).work_vectors || []).slice(0, 3).map((item, idx) => {
                    const net = Number(item.expected_work ?? 0);
                    const tone = net > 0 ? "text-cyan-300" : (net < 0 ? "text-orange-300" : "text-zinc-300");
                    const trigger = String(item.detail || item.type || "冲");
                    const unlockFailed = Boolean(item.unlock_failed);
                    return (
                      <p key={`wv-${idx}`} className={`${tone} ${unlockFailed ? "line-through decoration-dashed" : ""}`}>
                        触发: {trigger}
                        {" -> "}
                        释放: {Number(item.released_energy ?? 0).toFixed(2)}
                        {" -> "}
                        损耗: -{Number(item.backfire_risk ?? 0).toFixed(2)}
                        {" -> "}
                        净值: {net >= 0 ? "+" : ""}{net.toFixed(2)}
                        {unlockFailed ? " [解锁失败/链路断裂]" : ""}
                      </p>
                    );
                  })}
                </div> : null}
              </div>
            ) : null}
          <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
            <button
              type="button"
              onClick={() => toggleSummary("topology")}
              className="mb-2 flex w-full items-center justify-between rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-left text-zinc-300 hover:bg-zinc-800"
            >
              <span>拓扑图（Topology）</span>
              <span>{summaryOpen.topology ? "收起" : "展开"}</span>
            </button>
            {summaryOpen.topology ? <TopologyMapV1 graph={topologyGraph} /> : null}
          </div>
          {typeof (structureCandidates as { hud?: unknown }).hud === "object" ? (
            <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
              <p className="mb-1 text-zinc-300">格局态射仪表盘（V0）</p>
              <div className="grid grid-cols-1 gap-1 text-zinc-400 md:grid-cols-3">
                <p>正格倾向: {Number(((structureCandidates as { hud?: Record<string, unknown> }).hud || {}).stable_pct || 0).toFixed(2)}%</p>
                <p>从格倾向: {Number(((structureCandidates as { hud?: Record<string, unknown> }).hud || {}).follower_pct || 0).toFixed(2)}%</p>
                <p>跃迁倾向: {Number(((structureCandidates as { hud?: Record<string, unknown> }).hud || {}).leap_pct || 0).toFixed(2)}%</p>
              </div>
            </div>
          ) : null}
          {typeof (structureFinalDecision as { primary_structure?: unknown }).primary_structure === "string" ? (
            <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
              <button
                type="button"
                onClick={() => toggleSummary("structure")}
                className="mb-2 flex w-full items-center justify-between rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-left text-zinc-300 hover:bg-zinc-800"
              >
                <span>L2 格局终审结果（V0）</span>
                <span>{summaryOpen.structure ? "收起" : "展开"}</span>
              </button>
              {summaryOpen.structure ? <>
              <p className={`text-sm font-semibold ${Boolean((stressTestResult as { rollback_triggered?: boolean }).rollback_triggered) ? "animate-pulse rounded bg-rose-500/20 px-2 py-0.5 text-rose-300" : "text-zinc-200"}`}>
                {String((structureFinalDecision as { primary_structure_humanized?: string; primary_structure?: string }).primary_structure_humanized || (structureFinalDecision as { primary_structure?: string }).primary_structure || "--")}
              </p>
              {Number((structureCandidates as { self_abs?: number }).self_abs || 0) > 5 ? (
                <p className="mt-1 rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-200">
                  当前日主能量过剩（{Number((structureCandidates as { self_abs?: number }).self_abs || 0).toFixed(2)}），急需通过做功泄耗，否则易固执与内耗。
                </p>
              ) : null}
              <p className="mt-1 text-zinc-400">
                置信度: {Math.round(Number((structureFinalDecision as { decision_confidence?: number }).decision_confidence || 0) * 100)}%
              </p>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded bg-zinc-800">
                <div
                  className="h-full bg-emerald-500/80"
                  style={{ width: `${Math.max(0, Math.min(100, Number((structureFinalDecision as { decision_confidence?: number }).decision_confidence || 0) * 100))}%` }}
                />
              </div>
              <p className="mt-2 text-zinc-400">理由链</p>
              <div className="space-y-1">
                {((structureFinalDecision as { logical_reasoning_chain?: string[] }).logical_reasoning_chain || []).map((line, idx) => (
                  <p key={`reason-${idx}`} className="text-zinc-500">{line}</p>
                ))}
              </div>
              <p className="mt-2 text-zinc-400">回滚触发器</p>
              <div className="space-y-1">
                {((structureFinalDecision as { rollback_triggers?: string[] }).rollback_triggers || []).map((line, idx) => (
                  <p key={`rollback-${idx}`} className="text-amber-300">⚠ {line}</p>
                ))}
              </div>
              {strategicRecommendation ? (
                <div
                  className={`mt-2 rounded border p-2 ${
                    extremeAbsLoss
                      ? "border-rose-500/40 bg-rose-500/10 text-rose-200"
                      : "border-cyan-500/30 bg-cyan-500/10 text-cyan-200"
                  }`}
                >
                  {strategicRecommendation}
                </div>
              ) : null}
              <div className="mt-2 rounded border border-zinc-700 bg-zinc-950 p-2">
                <p className="text-zinc-300">压力测试模拟器（预埋）</p>
                <div className="mt-1 flex items-center gap-2">
                  <input
                    value={stressInput}
                    onChange={(e) => setStressInput(e.target.value)}
                    className="w-28 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-200"
                    placeholder="壬辰"
                  />
                  <button
                    type="button"
                    onClick={() => void runStress()}
                    className="rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-300 hover:bg-zinc-800"
                    title="执行岁运压力测试"
                  >
                    模拟大运：{stressInput || "壬辰"}
                  </button>
                  <button
                    type="button"
                    onClick={async () => {
                      await onGenderCompare?.();
                      setComparisonOpen(true);
                    }}
                    className="rounded border border-fuchsia-700/40 bg-fuchsia-500/10 px-2 py-1 text-fuchsia-200 hover:bg-fuchsia-500/20"
                    title="对比同盘男女路径差异"
                  >
                    对比镜像性别结果
                  </button>
                </div>
                {Boolean((stressTestResult as { rollback_triggered?: boolean }).rollback_triggered) ? (
                  <div className="mt-2 rounded border border-rose-500/40 bg-rose-500/10 p-2 text-rose-300">
                    [RED_COLLAPSE] {((stressTestResult as { hit_triggers?: string[] }).hit_triggers || []).join(" | ") || "触发回滚"}
                  </div>
                ) : null}
                {typeof (genderComparisonResult as { summary?: string }).summary === "string" && (genderComparisonResult as { summary?: string }).summary ? (
                  <div className="mt-2 rounded border border-fuchsia-500/40 bg-fuchsia-500/10 p-2 text-fuchsia-200">
                    {(genderComparisonResult as { summary?: string }).summary}
                    <p className="mt-1 text-[11px] text-fuchsia-300">
                      男：{String((genderComparisonResult as { male_dayun?: string }).male_dayun || "--")} / 峰值Abs {Number((genderComparisonResult as { male_peak_abs?: number }).male_peak_abs || 0).toFixed(2)}
                      {" | "}
                      女：{String((genderComparisonResult as { female_dayun?: string }).female_dayun || "--")} / 峰值Abs {Number((genderComparisonResult as { female_peak_abs?: number }).female_peak_abs || 0).toFixed(2)}
                    </p>
                  </div>
                ) : null}
              </div>
              </> : null}
            </div>
          ) : null}
        </div>
      </div>
        ) : null}
      </section>
      <ComparisonBridgeModal
        open={comparisonOpen}
        onClose={() => setComparisonOpen(false)}
        result={genderComparisonResult}
        currentGender={String((metadata as { gender?: string }).gender || "")}
      />
    </section>
    </div>
  );
}
