import type { PhysicsLabConfig, PluginSwitches, PluginWeights } from "@/features/stream-board/models";
import type { Lang } from "@/types/bazi";

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
