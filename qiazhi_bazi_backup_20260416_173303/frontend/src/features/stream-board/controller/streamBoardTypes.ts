import type { Dispatch, SetStateAction } from "react";
import type {
  DeityComponent,
  DeityEnergyAxis,
  PatternThresholdRow,
  PhysicsLabConfig,
  PluginSwitches,
  PluginWeights,
} from "@/features/stream-board/models";
import type { LabLlmRoundSnapshot } from "@/features/stream-board/stores/LabSessionContext";
import type { BaziMetadata, Lang, TimelineSnapshot } from "@/types/bazi";

/** 与 SessionConsensus / 终判 payload 对齐的轻量结构 */
export type ConsensusItem = { decision_key: string; confirmed_value?: number; reasoning?: string };

export type ConfirmedDecisionItem = { id: string; label: string; is_confirmed: boolean; confirmed_at?: string };

export type MetricSnapshot = { absLossTotal: number | null; entropy: number | null };

/** 静默 analyze-seed 重算时从 ref 读取的上下文 */
export type SilentBoardCtx = {
  consultationId: number | null;
  labConfig: PhysicsLabConfig;
  pluginSwitches: PluginSwitches;
  pluginWeights: PluginWeights;
  lang: Lang;
  baselineMetrics: MetricSnapshot | null;
  confirmedDecisionIds: string[];
  /** 与 seed-preview / 排盘大运流年一致，静默 analyze-seed 写入 external_overrides */
  temporalGanzhiOverride: { liunian: string; dayun: string } | null;
  /** URL ``?pure_physics_audit=1``：纯物理审计，不请求格局插件 */
  purePhysicsAudit?: boolean;
};

export type NavigationInfo = {
  navType: "reload" | "navigate" | "back_forward" | "unknown";
  hasValidSnapshot: boolean;
  intent: "FRESH_START" | "RESTORE_AUDIT";
};

/** 静默 analyze-seed 成功后写入 physics/tensor 相关 state */
export type SilentRecalcPhysicsSetters = {
  setMetadata: Dispatch<SetStateAction<BaziMetadata | null>>;
  setTimeline: (v: TimelineSnapshot | null) => void;
  setDeityScores: (v: Record<string, number>) => void;
  setDeityEnergyAxes: (v: Record<string, DeityEnergyAxis>) => void;
  setDeityComponents: (v: Record<string, DeityComponent>) => void;
  setDeityTraceDetails: (v: Record<string, Record<string, unknown>>) => void;
  setPhysicsAudit: (v: Record<string, unknown> | null) => void;
  setPhysicsConfidence: (v: number | null) => void;
  setPhysicsEvidence: (v: string[]) => void;
  setPhysicsParams: (v: Record<string, number>) => void;
  setGlobalEntropy: (v: number | null) => void;
  setPatternThresholds: Dispatch<SetStateAction<PatternThresholdRow[]>>;
  setPatternThresholdsStatus: Dispatch<SetStateAction<string | null>>;
};

/** 静默重算成功后交给 persistSnapshot 的固定字段子集 */
export type SilentRecalcPersistSnapshotPayload = {
  physics_tensor: Record<string, unknown>;
  metadata: Record<string, unknown>;
  timeline: Record<string, unknown> | null;
  llm_prompt: string;
  first_observation_llm?: LabLlmRoundSnapshot;
  physics_auditor_llm?: LabLlmRoundSnapshot;
  audit_summary: unknown;
  consultationIdOverride: number | null;
  healthOverride: { dbOk: boolean; llmOk: boolean };
  seedSignatureOverride: string | null;
};
