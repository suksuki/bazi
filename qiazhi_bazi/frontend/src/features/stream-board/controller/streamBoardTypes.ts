import type {
  DeityComponent,
  DeityEnergyAxis,
  PhysicsLabConfig,
  PluginSwitches,
  PluginWeights,
} from "@/features/stream-board/models";
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
};

export type NavigationInfo = {
  navType: "reload" | "navigate" | "back_forward" | "unknown";
  hasValidSnapshot: boolean;
  intent: "FRESH_START" | "RESTORE_AUDIT";
};

/** 静默 analyze-seed 成功后写入 physics/tensor 相关 state */
export type SilentRecalcPhysicsSetters = {
  setMetadata: (v: BaziMetadata | null) => void;
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
};

/** 静默重算成功后交给 persistSnapshot 的固定字段子集 */
export type SilentRecalcPersistSnapshotPayload = {
  physics_tensor: Record<string, unknown>;
  metadata: Record<string, unknown>;
  timeline: Record<string, unknown> | null;
  llm_prompt: string;
  audit_summary: unknown;
  consultationIdOverride: number | null;
  healthOverride: { dbOk: boolean; llmOk: boolean };
  seedSignatureOverride: string | null;
};
