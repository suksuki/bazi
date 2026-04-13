"use client";

import { AnimatePresence, LayoutGroup, motion } from "framer-motion";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { BlindLogicMirror } from "@/components/BlindLogicMirror";
import { ComparisonBridgeModal } from "@/components/ComparisonBridgeModal";
import { StrategicCoreHUD } from "@/components/StrategicCoreHUD";
import { TopologyMapV1 } from "@/components/TopologyMapV1";
import { elementColorClass } from "@/constants/termMap";
import { DecisionItem } from "@/features/decision-engine/components/DecisionItem";
import { DecisionInboxCard, VerdictChangeLog } from "@/features/decision-inbox/types";
import type {
  DecisionSignalToNoiseMeta,
  DeityEnergyAxis,
  LogicDiff,
  UserIntentionId,
} from "@/features/stream-board/models";
import type { Lang } from "@/types/bazi";
import {
  getCardElement,
  getCardLabel,
  getEvidenceTone,
  isAuditorProposal,
  pruneSelectedIds,
  sgjgEnergeticLabelForCard,
} from "@/features/decision-inbox/utils";
import { LiveVerdictDisplay } from "@/features/stream-board/components/LiveVerdictDisplay";
import { PatternWaterlinePanel } from "@/features/stream-board/components/PatternWaterlinePanel";
import { WillIntentionSelector } from "@/features/stream-board/components/WillIntentionSelector";
import type { PatternThresholdRow } from "@/features/stream-board/models";
import { LogicEvolutionAxis } from "@/features/stream-board/components/LogicEvolutionAxis";
import type { DecisionJournalEntry } from "@/features/stream-board/decisionJournal";

type Props = {
  cards: DecisionInboxCard[];
  resultLogs: string[];
  verdictBody?: string;
  /** 物理预判 Markdown 骨架（Orchestrator / 无 LLM）；优先于终判正文展示占位 */
  verdictSkeleton?: string | null;
  /** 影子预览：悬停卡发现的 VF 行（淡紫斜体 + PREVIEW） */
  previewVfSkeleton?: string | null;
  /** 结构预览：格局预警（PREVIEW） */
  previewPatternAlert?: string | null;
  /** 中枢 physics_update：格局引力水位（稳态） */
  patternThresholds?: PatternThresholdRow[];
  /** V6.9：与 `pattern_thresholds_status` 对齐（EMPTY_NO_DATA 等） */
  patternThresholdsStatus?: string | null;
  /** V9.1：与顶栏 `patternCodexHeadline` 同源，法典水位区命中名展示 */
  codexHitSummary?: string;
  /** 影子预览：悬停时的格局水位 */
  previewPatternThresholds?: PatternThresholdRow[] | null;
  /** 影子预览激活（用于水位线「意志步进」脉动） */
  patternPreviewShadowActive?: boolean;
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
  /** 非中文界面：判词整行走翻译；十神可点击拆句仅在中文下保留 */
  lang?: Lang;
  /** 从 Inbox L1 卡片跳转到 Debug「插件碰撞」并滚动到对应 plugin_outputs 行 */
  onOpenPluginAudit?: (pluginId: string) => void;
  /** 悬停卡片：影子预览（能量补丁 + 结构类白名单） */
  onDecisionCardPreviewEnter?: (patchId: string) => void;
  onDecisionCardPreviewLeave?: () => void;
  /** 结构预览链已建立：当前 Hover 卡片外沿极弱紫晕 */
  previewGlowCardId?: string | null;
  /** 中枢 SSE audit_pulse：因果路由备忘流，展示于逻辑演化轴顶栏 */
  orchestratorCausalAuditPulse?: string | null;
  /** 全量测算结束递增，驱动主断言区骨架首秒高亮 */
  calculationNonce?: number;
  /** 终判流式/合并完成后递增，驱动 LiveVerdictDisplay 强制刷新 */
  verdictBodyRenderNonce?: number;
  streamingText?: string;
  skeletonContentKey?: string;
  traceChipLogs?: string[];
  traceConflictLabels?: string[];
  preInjectionDeityDisplay?: {
    deity_scores?: Record<string, number>;
    deity_energy_axes?: Record<string, DeityEnergyAxis>;
  } | null;
  showPreInjectionAbsSnapshot?: boolean;
  onShowPreInjectionAbsSnapshotChange?: (next: boolean) => void;
  /** 当前十神分（与注塑前快照对比，用于意志 Toast） */
  deityScores?: Record<string, number>;
  /** 追加型决策日志，供逻辑演化轴展示 */
  decisionJournal?: DecisionJournalEntry[];
  /** 物理审计 LLM diagnosis（含从 logic_proposal 提拔），裁决舱「审计备忘」即时展示 */
  physicsAuditDiagnosis?: string | null;
  /** V6.1：卡片 id → 已填充的 AI 推荐理由（前缀另加 t("ai.recommend.reason")） */
  aiRecommendationHints?: Record<string, string>;
  /** V6.3：全知推荐请求进行中（展示细进度流光） */
  aiRecommendationsBusy?: boolean;
  /** V10：意志锚点（WILL_PROXY） */
  userIntention?: UserIntentionId | "" | undefined;
  onUserIntentionChange?: (next: UserIntentionId) => void;
  userIntentionDisabled?: boolean;
  /** V11：meta.intention_context.topology_node_will_inverse_factor，拓扑虚线与节点报告 */
  topologyWillInverseFactor?: number;
};

const PREVIEW_HOVER_DEBOUNCE_MS = 50;

/** 推荐理由中的百分比数字加粗（如 稳定性+12.3%、达成度+4.0%、约 72%） */
function boldNumericPercentsInText(text: string): ReactNode[] {
  const re = /(约\s*\d+(?:\.\d+)?[%％]|[+-]?\d+(?:\.\d+)?[%％])/g;
  const out: ReactNode[] = [];
  let last = 0;
  let m: RegExpExecArray | null;
  let k = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      out.push(text.slice(last, m.index));
    }
    out.push(
      <strong key={`ai-reason-num-${k++}`} className="font-semibold text-amber-200/95">
        {m[1]}
      </strong>,
    );
    last = re.lastIndex;
  }
  if (last < text.length) {
    out.push(text.slice(last));
  }
  return out.length ? out : [text];
}

export function DecisionInbox({
  cards,
  resultLogs,
  verdictBody = "",
  verdictSkeleton = null,
  previewVfSkeleton = null,
  previewPatternAlert = null,
  patternThresholds = [],
  patternThresholdsStatus = null,
  codexHitSummary = "",
  previewPatternThresholds = null,
  patternPreviewShadowActive = false,
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
  lang = "ZH",
  onOpenPluginAudit,
  onDecisionCardPreviewEnter,
  onDecisionCardPreviewLeave,
  previewGlowCardId = null,
  orchestratorCausalAuditPulse = null,
  calculationNonce = 0,
  verdictBodyRenderNonce = 0,
  streamingText = "",
  skeletonContentKey = "",
  traceChipLogs = [],
  traceConflictLabels = [],
  preInjectionDeityDisplay = null,
  showPreInjectionAbsSnapshot = false,
  onShowPreInjectionAbsSnapshotChange,
  deityScores = {},
  decisionJournal = [],
  physicsAuditDiagnosis = null,
  aiRecommendationHints = {},
  aiRecommendationsBusy = false,
  userIntention,
  onUserIntentionChange,
  userIntentionDisabled = false,
  topologyWillInverseFactor,
}: Props) {
  const [selectedIds, setSelectedIds] = useState<Record<string, boolean>>({});
  const [physResonanceTick, setPhysResonanceTick] = useState(0);
  const [willToast, setWillToast] = useState<string | null>(null);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [stressInput, setStressInput] = useState("壬辰");
  const [sectionOpen, setSectionOpen] = useState({
    strategic: false,
    summary: true,
  });
  const [summaryOpen, setSummaryOpen] = useState({
    diff: true,
    evidence: false,
    topology: false,
    structure: true,
    /** 格局引力水位线：多格局亲和排行（与 L2 终审主结论对照） */
    patternGravity: true,
  });
  const [comparisonOpen, setComparisonOpen] = useState(false);
  const [weighting, setWeighting] = useState(pluginWeights);
  const [inboxResetWaveKey, setInboxResetWaveKey] = useState(0);
  const inboxNoncePrevRef = useRef<number | null>(null);
  const previewEnterDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(
    () => () => {
      if (previewEnterDebounceRef.current) {
        clearTimeout(previewEnterDebounceRef.current);
        previewEnterDebounceRef.current = null;
      }
    },
    [],
  );

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
  const energyRiskHint = t("风险提示：当前物理能耗过高（abs_delta > 100），应优先执行降耗与稳态校准。");
  const strategicRecommendation = baseRecommendation
    ? (extremeAbsLoss && !baseRecommendation.includes("物理能耗过高")
      ? `${baseRecommendation} ${energyRiskHint}`
      : baseRecommendation)
    : (extremeAbsLoss ? energyRiskHint : "");

  const selectedCards = cards.filter((c) => selectedIds[c.id]);
  function applySelection(next: Record<string, boolean>) {
    if (interactionLocked) return;
    setSelectedIds(next);
    setPhysResonanceTick((v) => v + 1);
    const nextSelected = cards.filter((card) => Boolean(next[card.id]));
    onSelectionChange?.(nextSelected);
  }

  useEffect(() => {
    if (physResonanceTick === 0) return;
    const pre = preInjectionDeityDisplay?.deity_scores;
    if (!pre || !deityScores || Object.keys(deityScores).length === 0) return;
    let bestName = "";
    let bestPct = 0;
    for (const k of Object.keys(deityScores)) {
      const cur = Number(deityScores[k] ?? 0);
      const base = Number(pre[k] ?? 0);
      const denom = Math.max(1e-6, Math.abs(base));
      const pct = ((cur - base) / denom) * 100;
      if (Math.abs(pct) > Math.abs(bestPct)) {
        bestPct = pct;
        bestName = k;
      }
    }
    if (!bestName || Math.abs(bestPct) < 0.35) return;
    const sign = bestPct > 0 ? "+" : "";
    const rounded = Math.abs(bestPct) >= 10 ? bestPct.toFixed(0) : bestPct.toFixed(1);
    setWillToast(t("意志注塑成功：{deity} 能量 {sign}{pct}%").replace("{deity}", bestName).replace("{sign}", sign).replace("{pct}", rounded));
    const id = window.setTimeout(() => setWillToast(null), 2600);
    return () => window.clearTimeout(id);
  }, [physResonanceTick, deityScores, preInjectionDeityDisplay, t]);
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
  const diagnosticHint =
    energyPeakAbs > 10 && Math.abs(workExpectation) < 0.1
      ? `${t("检测到能量高度淤积（Abs: {abs}），做功路径已被岁运阻断。").replace("{abs}", energyPeakAbs.toFixed(2))}${
          weakPathEnabled ? t("当前已开启逻辑透深。") : t("建议开启“逻辑透深”检查被隐藏的内耗路径。")
        }`
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
  }, [pluginWeights]);
  async function runStress() {
    await onStressTest?.(stressInput);
  }

  function toggleSection(key: keyof typeof sectionOpen) {
    setSectionOpen((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function toggleSummary(key: keyof typeof summaryOpen) {
    setSummaryOpen((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  return (
    <div className="relative min-w-0 max-w-full overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/60">
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
      {onUserIntentionChange ? (
        <div className="mb-3">
          <WillIntentionSelector
            value={userIntention}
            onChange={onUserIntentionChange}
            disabled={userIntentionDisabled}
            t={t}
          />
        </div>
      ) : null}
      {willToast ? (
        <div className="pointer-events-none fixed left-1/2 top-14 z-[60] max-w-[min(92vw,22rem)] -translate-x-1/2 rounded-lg border border-fuchsia-500/50 bg-fuchsia-950/95 px-3 py-2 text-center text-[11px] font-medium text-fuchsia-50 shadow-xl">
          {willToast}
        </div>
      ) : null}
      <div className="mb-3">
        <LogicEvolutionAxis
          resultLogs={resultLogs}
          decisionJournal={decisionJournal}
          metadata={metadata}
          liveCausalPulse={orchestratorCausalAuditPulse}
          t={t}
        />
      </div>

      <div className="space-y-3 pb-20">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-3">
          <h4 className="text-sm font-medium text-zinc-100">Decision Items</h4>
          <p className="mt-1 text-xs text-zinc-400">{t("勾选决策项后可在统一动作条触发语义裁决。")}</p>
          {decisionSignalToNoise?.inbox_conflict_cards_eligible === false && metadata && Object.keys(metadata).length > 0 ? (
            <p className="mt-2 font-mono text-[10px] leading-relaxed text-zinc-600">
              {t("[SIGNAL_GATE_ACTIVE]: 微弱因果噪声已物理屏蔽，阈值:")}{" "}
              {typeof decisionSignalToNoise.threshold === "number"
                ? decisionSignalToNoise.threshold.toFixed(1)
                : "5.0"}{" "}
              Abs
            </p>
          ) : null}
          {aiRecommendationsBusy ? (
            <div className="mt-2 space-y-1" role="status" aria-live="polite">
              <p className="text-[10px] font-medium uppercase tracking-[0.22em] text-amber-500/85">{t("ai.recommend.loading")}</p>
              <div className="relative h-px w-full overflow-hidden rounded-full bg-zinc-800/95">
                <motion.div
                  className="absolute inset-y-0 left-0 w-[38%] rounded-full bg-gradient-to-r from-transparent via-amber-400/75 to-transparent"
                  animate={{ x: ["-40%", "220%"] }}
                  transition={{ duration: 2.1, repeat: Infinity, ease: "linear" }}
                />
              </div>
            </div>
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
                  const aiReco = aiRecommendationHints[card.id];
                  return (
                    <motion.div
                      key={card.id}
                      initial={{ opacity: 0, x: 18 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -100 }}
                      transition={{ duration: 0.22 }}
                      className={`relative space-y-1 overflow-hidden rounded-lg pr-9 ${interactionLocked ? "opacity-60" : ""} ${
                        previewGlowCardId && previewGlowCardId === card.id
                          ? "ring-1 ring-violet-500/20 shadow-[0_0_22px_rgba(139,92,246,0.14)]"
                          : ""
                      }${aiReco ? " ring-1 ring-amber-500/18 shadow-[0_0_20px_rgba(251,191,36,0.08)]" : ""}`}
                      onPointerEnter={() => {
                        if (interactionLocked || !onDecisionCardPreviewEnter) return;
                        if (previewEnterDebounceRef.current) clearTimeout(previewEnterDebounceRef.current);
                        previewEnterDebounceRef.current = setTimeout(() => {
                          previewEnterDebounceRef.current = null;
                          onDecisionCardPreviewEnter(card.id);
                        }, PREVIEW_HOVER_DEBOUNCE_MS);
                      }}
                      onPointerLeave={() => {
                        if (previewEnterDebounceRef.current) {
                          clearTimeout(previewEnterDebounceRef.current);
                          previewEnterDebounceRef.current = null;
                        }
                        if (!onDecisionCardPreviewLeave) return;
                        onDecisionCardPreviewLeave();
                      }}
                    >
                      {aiReco ? (
                        <motion.div
                          aria-hidden
                          className="pointer-events-none absolute inset-0 z-0 rounded-lg"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ duration: 1.2 }}
                        >
                          <motion.div
                            className="absolute -left-[18%] -top-[22%] h-[150%] w-[150%] blur-2xl"
                            style={{
                              background:
                                "radial-gradient(circle at 30% 32%, rgba(251,191,36,0.14), transparent 46%), radial-gradient(circle at 74% 70%, rgba(168,85,247,0.11), transparent 48%), radial-gradient(circle at 50% 50%, rgba(34,211,238,0.06), transparent 55%)",
                            }}
                            animate={{ x: ["-3%", "4%", "-3%"], y: ["-2%", "3%", "-2%"] }}
                            transition={{ duration: 56, repeat: Infinity, ease: "easeInOut" }}
                          />
                        </motion.div>
                      ) : null}
                      {aiReco ? (
                        <div className="pointer-events-auto absolute right-1 top-1 z-20">
                          <div className="group/aiSpark relative">
                            <motion.span
                              className="relative flex h-7 w-7 cursor-default items-center justify-center rounded-full border border-amber-400/45 bg-gradient-to-br from-amber-500/35 via-fuchsia-600/25 to-cyan-500/30 shadow-[0_0_14px_rgba(251,191,36,0.45)]"
                              aria-label={t("AI 星火勋章")}
                              animate={{
                                boxShadow: [
                                  "0 0 10px rgba(251,191,36,0.35)",
                                  "0 0 18px rgba(168,85,247,0.55)",
                                  "0 0 10px rgba(251,191,36,0.35)",
                                ],
                              }}
                              transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
                            >
                              <motion.span
                                className="pointer-events-none absolute inset-0 rounded-full bg-gradient-to-tr from-transparent via-white/35 to-transparent opacity-70"
                                animate={{ rotate: [0, 360] }}
                                transition={{ duration: 4.5, repeat: Infinity, ease: "linear" }}
                              />
                              <span className="relative z-[1] text-[11px] leading-none text-amber-100">✦</span>
                            </motion.span>
                            <div
                              className="pointer-events-none invisible absolute right-0 top-[calc(100%+6px)] z-[40] w-[min(20rem,78vw)] rounded-lg border border-amber-500/35 bg-zinc-950/98 px-2.5 py-2 text-left text-[10px] leading-snug text-zinc-100 shadow-xl backdrop-blur-sm group-hover/aiSpark:visible group-hover/aiSpark:pointer-events-auto"
                              role="tooltip"
                            >
                              <span className="font-medium text-amber-200/95">{t("ai.recommend.reason")}</span>
                              <span className="text-zinc-200">{boldNumericPercentsInText(aiReco)}</span>
                            </div>
                          </div>
                        </div>
                      ) : null}
                      <label className="relative z-10 block">
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
                      </label>
                      {card.pluginAuditAnchorId && onOpenPluginAudit ? (
                        <button
                          type="button"
                          onClick={() => onOpenPluginAudit(String(card.pluginAuditAnchorId))}
                          className="relative z-10 ml-1 text-left text-[10px] text-cyan-400/90 underline-offset-2 hover:text-cyan-200 hover:underline"
                        >
                          {t("跳转插件碰撞审计")}
                        </button>
                      ) : null}
                    </motion.div>
                  );
                })()
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {!hideStrategicPanel ? (
        <div className="mb-3 rounded-xl border border-zinc-800 bg-zinc-950 p-2">
          <button
            type="button"
            onClick={() => toggleSection("strategic")}
            className="flex w-full items-center justify-between rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-left text-xs text-zinc-200 hover:bg-zinc-800"
          >
            <span>{t("核心看板（Strategic HUD + 盲派镜像）")}</span>
            <span>{sectionOpen.strategic ? t("收起") : t("展开")}</span>
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
                t={t}
                onPickDeity={(deity) => {
                  onVerdictDeityClick?.(deity);
                  onStrategicDeityHover?.(deity);
                }}
              />
              <div className="mb-2 rounded border border-zinc-700 bg-zinc-900 p-2 text-[11px] text-zinc-300">
                <p className="mb-1">{t("语义权重滑杆（Plugin Weights）")}</p>
                <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                  <label>
                    {t("盲派 ")}
                    {weighting.blindSchool.toFixed(2)}
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
                    {t("旺衰 ")}
                    {weighting.wangshuai.toFixed(2)}
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
                    {t("应用权重并重算")}
                  </button>
                </div>
              </div>
              <BlindLogicMirror workVector={workVector} t={t} />
            </div>
          ) : null}
        </div>
      ) : null}

      <section className="mt-4 rounded-xl border border-zinc-800 bg-zinc-950 p-2">
        <button
          type="button"
          onClick={() => toggleSection("summary")}
          className="flex w-full items-center justify-between rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-left text-xs text-zinc-200 hover:bg-zinc-800"
        >
          <span>{t("结果总览（Result Summary）")}</span>
          <span>{sectionOpen.summary ? t("收起") : t("展开")}</span>
        </button>
        {sectionOpen.summary ? (
      <div
        className={`mt-2 min-w-0 max-w-full overflow-x-hidden rounded-xl bg-zinc-950 p-3 ${
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
                {t("查看历史版本")}
              </button>
            ) : null}
            {summaryVersionLabel ? (
              <span className="rounded-md border border-zinc-700 bg-zinc-900 px-2 py-0.5 text-[10px] text-zinc-400">
                {summaryVersionLabel}
              </span>
            ) : null}
          </div>
        </div>
        <div className="mt-2 min-w-0 max-w-full space-y-1">
          <div className="mb-2 grid grid-cols-1 gap-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 md:grid-cols-3">
            <div className="rounded border border-emerald-600/40 bg-emerald-500/10 px-2 py-1">
              <p className="text-[10px] text-emerald-300/90">{t("用神")}</p>
              <p className="text-xs font-medium text-emerald-100">{useful.length ? useful.join(" / ") : "--"}</p>
            </div>
            <div className="rounded border border-rose-600/40 bg-rose-500/10 px-2 py-1">
              <p className="text-[10px] text-rose-300/90">{t("忌神")}</p>
              <p className="text-xs font-medium text-rose-100">{obstacle.length ? obstacle.join(" / ") : "--"}</p>
            </div>
            <div className="rounded border border-sky-600/40 bg-sky-500/10 px-2 py-1">
              <p className="text-[10px] text-sky-300/90">{t("调候")}</p>
              <p className="text-xs font-medium text-sky-100">
                {climateSummary === "--" ? "--" : t(climateSummary)}
              </p>
            </div>
          </div>
          {l1Certified ? (
            <div className="mb-2 inline-flex items-center rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-300">
              L1 Certified
            </div>
          ) : null}
          <LiveVerdictDisplay
            verdictSkeleton={verdictSkeleton ?? null}
            previewVfSkeleton={previewVfSkeleton}
            previewPatternAlert={previewPatternAlert}
            previewPatternThresholds={previewPatternThresholds}
            verdictBody={verdictBody}
            physicsAuditDiagnosis={physicsAuditDiagnosis}
            metadata={metadata}
            streamingText={streamingText}
            calculationNonce={calculationNonce}
            verdictBodyRenderNonce={verdictBodyRenderNonce}
            skeletonContentKey={skeletonContentKey}
            physResonanceKey={physResonanceTick}
            highlightVerdict={highlightVerdict}
            summaryChanged={summaryChanged}
            lang={lang}
            t={t}
            onVerdictDeityClick={onVerdictDeityClick}
            traceResultLogs={resultLogs}
            traceChipLogs={traceChipLogs}
            traceConflictLabels={traceConflictLabels}
            preInjectionDeityDisplay={preInjectionDeityDisplay}
            showPreInjectionAbsSnapshot={showPreInjectionAbsSnapshot}
            onShowPreInjectionAbsSnapshotChange={onShowPreInjectionAbsSnapshotChange}
            userIntention={userIntention}
          />
          {(verdictChangeLog.physics_diff?.length || verdictChangeLog.consensus_diff?.length || verdictChangeLog.text_diff_hint) ? (
            <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
              <button
                type="button"
                onClick={() => toggleSummary("diff")}
                className="mb-2 flex w-full items-center justify-between rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-zinc-300 hover:bg-zinc-800"
              >
                <span>{t("变更差分（Physics / Consensus / Text）")}</span>
                <span>{summaryOpen.diff ? t("收起") : t("展开")}</span>
              </button>
              {summaryOpen.diff ? (
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                <div className="rounded border border-zinc-700 bg-zinc-950 p-2">
                  <p className="mb-1 text-zinc-300">{t("物理场变动")}</p>
                  {(verdictChangeLog.physics_diff || []).length === 0 ? <p className="text-zinc-500">{t("- 无")}</p> : null}
                  {(verdictChangeLog.physics_diff || []).map((x, i) => (
                    <p key={`pd-${i}`} className="text-zinc-400">
                      - {t(x)}
                    </p>
                  ))}
                </div>
                <div className="rounded border border-zinc-700 bg-zinc-950 p-2">
                  <p className="mb-1 text-zinc-300">{t("共识固化")}</p>
                  {(verdictChangeLog.consensus_diff || []).length === 0 ? <p className="text-zinc-500">{t("- 无")}</p> : null}
                  {(verdictChangeLog.consensus_diff || []).map((x, i) => (
                    <p key={`cd-${i}`} className="text-zinc-400">
                      - {t(x)}
                    </p>
                  ))}
                </div>
                <div className="rounded border border-zinc-700 bg-zinc-950 p-2">
                  <p className="mb-1 text-zinc-300">{t("判词修正")}</p>
                  <p className="text-zinc-400">
                    {verdictChangeLog.text_diff_hint ? t(verdictChangeLog.text_diff_hint) : t("无")}
                  </p>
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
                {evidenceOpen ? t("收起证据快照") : t("展开证据快照")}
              </button>
              <button
                type="button"
                onClick={() => toggleSummary("evidence")}
                className="ml-2 rounded border border-zinc-700 bg-zinc-950 px-2 py-0.5 text-zinc-300 hover:bg-zinc-800"
              >
                {summaryOpen.evidence ? t("隐藏模块") : t("显示模块")}
              </button>
              {evidenceOpen && summaryOpen.evidence ? (
                <div className="mt-2 max-h-40 space-y-1 overflow-auto">
                  {logicalEvidence.map((x, i) => (
                    <button
                      key={`ev-${i}`}
                      type="button"
                      onClick={() => onEvidenceClick?.(x)}
                      className={`block w-full rounded border px-2 py-1 text-left hover:border-sky-500/40 hover:text-sky-200 ${getEvidenceTone(x)}`}
                      title={t("点击下钻证据")}
                    >
                      {t(x)}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
          <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
            <button
              type="button"
              onClick={() => toggleSummary("topology")}
              className="mb-2 flex w-full items-center justify-between rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-left text-zinc-300 hover:bg-zinc-800"
            >
              <span>{t("拓扑图（Topology）")}</span>
              <span>{summaryOpen.topology ? t("收起") : t("展开")}</span>
            </button>
            {summaryOpen.topology ? (
              <TopologyMapV1 graph={topologyGraph} willInverseFactor={topologyWillInverseFactor} t={t} />
            ) : null}
          </div>
          <LayoutGroup id="pattern-gravity-suite">
            <div className="mt-2 rounded-md border border-violet-900/40 bg-zinc-900/95 p-2 text-[11px] shadow-md shadow-violet-950/20">
              <button
                type="button"
                onClick={() => toggleSummary("patternGravity")}
                className="mb-2 flex w-full items-center justify-between gap-2 rounded border border-violet-800/40 bg-zinc-950/90 px-2 py-1 text-left text-zinc-300 hover:bg-violet-950/35"
              >
                <span className="min-w-0 flex-1">
                  <span className="block text-[10px] font-medium uppercase tracking-wider text-violet-300/90">
                    {t("拓扑 · 格局引力")}
                  </span>
                  {!summaryOpen.patternGravity && codexHitSummary.trim() ? (
                    <span className="mt-0.5 block truncate text-[10px] text-zinc-500" title={codexHitSummary.trim()}>
                      {codexHitSummary.trim()}
                    </span>
                  ) : null}
                </span>
                <span className="shrink-0 text-zinc-400">{summaryOpen.patternGravity ? t("收起") : t("展开")}</span>
              </button>
              {summaryOpen.patternGravity ? (
                <motion.div layout layoutId="pattern-waterline-orbit">
                  <PatternWaterlinePanel
                    key={lang}
                    committed={patternThresholds}
                    preview={previewPatternThresholds}
                    shadowActive={patternPreviewShadowActive}
                    patternThresholdsStatus={patternThresholdsStatus}
                    codexHitSummary={codexHitSummary}
                    t={t}
                    className="mt-0 border-0 bg-transparent p-0 shadow-none ring-0"
                  />
                </motion.div>
              ) : null}
            </div>
          </LayoutGroup>
          {typeof (structureFinalDecision as { primary_structure?: unknown }).primary_structure === "string" ? (
            <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
              <button
                type="button"
                onClick={() => toggleSummary("structure")}
                className="mb-2 flex w-full items-center justify-between rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-left text-zinc-300 hover:bg-zinc-800"
              >
                <span>{t("L2 格局终审结果")}</span>
                <span>{summaryOpen.structure ? t("收起") : t("展开")}</span>
              </button>
              {summaryOpen.structure ? <>
              <p className={`text-sm font-semibold ${Boolean((stressTestResult as { rollback_triggered?: boolean }).rollback_triggered) ? "animate-pulse rounded bg-rose-500/20 px-2 py-0.5 text-rose-300" : "text-zinc-200"}`}>
                {String((structureFinalDecision as { primary_structure_humanized?: string; primary_structure?: string }).primary_structure_humanized || (structureFinalDecision as { primary_structure?: string }).primary_structure || "--")}
              </p>
              {Number((structureCandidates as { self_abs?: number }).self_abs || 0) > 5 ? (
                <p className="mt-1 rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[11px] text-amber-200">
                  {t("当前日主能量过剩（")}
                  {Number((structureCandidates as { self_abs?: number }).self_abs || 0).toFixed(2)}
                  {t("），急需通过做功泄耗，否则易固执与内耗。")}
                </p>
              ) : null}
              <p className="mt-1 text-zinc-400">
                {t("置信度:")} {Math.round(Number((structureFinalDecision as { decision_confidence?: number }).decision_confidence || 0) * 100)}%
              </p>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded bg-zinc-800">
                <div
                  className="h-full bg-emerald-500/80"
                  style={{ width: `${Math.max(0, Math.min(100, Number((structureFinalDecision as { decision_confidence?: number }).decision_confidence || 0) * 100))}%` }}
                />
              </div>
              <p className="mt-2 text-zinc-400">{t("理由链")}</p>
              <div className="space-y-1">
                {((structureFinalDecision as { logical_reasoning_chain?: string[] }).logical_reasoning_chain || []).map((line, idx) => (
                  <p key={`reason-${idx}`} className="text-zinc-500">
                    {t(line)}
                  </p>
                ))}
              </div>
              <p className="mt-2 text-zinc-400">{t("回滚触发器")}</p>
              <div className="space-y-1">
                {((structureFinalDecision as { rollback_triggers?: string[] }).rollback_triggers || []).map((line, idx) => (
                  <p key={`rollback-${idx}`} className="text-amber-300">
                    ⚠ {t(line)}
                  </p>
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
                  {t(strategicRecommendation)}
                </div>
              ) : null}
              <div className="mt-2 rounded border border-zinc-700 bg-zinc-950 p-2">
                <p className="text-zinc-300">{t("压力测试模拟器（预埋）")}</p>
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
                    title={t("执行岁运压力测试")}
                  >
                    {t("模拟大运：")}
                    {stressInput || "壬辰"}
                  </button>
                  <button
                    type="button"
                    onClick={async () => {
                      await onGenderCompare?.();
                      setComparisonOpen(true);
                    }}
                    className="rounded border border-fuchsia-700/40 bg-fuchsia-500/10 px-2 py-1 text-fuchsia-200 hover:bg-fuchsia-500/20"
                    title={t("对比同盘男女路径差异")}
                  >
                    {t("对比镜像性别结果")}
                  </button>
                </div>
                {Boolean((stressTestResult as { rollback_triggered?: boolean }).rollback_triggered) ? (
                  <div className="mt-2 rounded border border-rose-500/40 bg-rose-500/10 p-2 text-rose-300">
                    [RED_COLLAPSE] {((stressTestResult as { hit_triggers?: string[] }).hit_triggers || []).join(" | ") || t("触发回滚")}
                  </div>
                ) : null}
                {typeof (genderComparisonResult as { summary?: string }).summary === "string" && (genderComparisonResult as { summary?: string }).summary ? (
                  <div className="mt-2 rounded border border-fuchsia-500/40 bg-fuchsia-500/10 p-2 text-fuchsia-200">
                    {t(String((genderComparisonResult as { summary?: string }).summary || ""))}
                    <p className="mt-1 text-[11px] text-fuchsia-300">
                      {t("男：")}
                      {String((genderComparisonResult as { male_dayun?: string }).male_dayun || "--")} / {t("峰值Abs")}{" "}
                      {Number((genderComparisonResult as { male_peak_abs?: number }).male_peak_abs || 0).toFixed(2)}
                      {" | "}
                      {t("女：")}
                      {String((genderComparisonResult as { female_dayun?: string }).female_dayun || "--")} / {t("峰值Abs")}{" "}
                      {Number((genderComparisonResult as { female_peak_abs?: number }).female_peak_abs || 0).toFixed(2)}
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
