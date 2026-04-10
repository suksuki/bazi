import type { BaziMetadata, Lang, TimelineSnapshot } from "@/types/bazi";
import type { Dispatch, SetStateAction } from "react";

export type SeedPayload = {
  date: string;
  time: string;
  calendar: "solar" | "lunar";
  gender: "male" | "female";
};

export type LogicProposal = {
  title?: string;
  param_key?: string;
  suggested_value?: number;
  reason?: string;
  expected_impact?: string;
  sql_patch?: string;
  source_role?: string;
};

export type InboxCard = {
  id: string;
  title: string;
  markdown: string;
  conflictDetail?: string;
  displayText?: string;
  cardType?: "conflict" | "auditor-proposal" | "proposal";
  proposal?: LogicProposal;
  /** 与盲派 skill_manifest 对齐，可由 UI 推断或上游写入 */
  skillId?: string;
};

export type DeityEnergyAxis = {
  absolute_energy?: number;
  relative_percentage?: number;
};

export type DeityComponent = {
  total_score?: number;
  stem_score?: number;
  root_score?: number;
  root_sources?: string[];
  stem_sources?: string[];
  is_floating?: boolean;
};

export type LlmDiagnosticData = {
  diagnosis?: string;
  alignment_score?: number;
  top_anomaly?: string;
  causal_reasoning?: string;
  tuning_suggestions?: string[];
  sql_patch?: string;
  refresh_hint?: string;
  structured_hit?: boolean;
  repair_mode?: string;
  logic_proposal?: LogicProposal;
};

export type PhysicsLabConfig = {
  WEIGHT_LUCK: number;
  WEIGHT_YEAR: number;
  BASE_BACKFIRE_RISK: number;
  HIGH_IMBALANCE_RISK: number;
  TOMB_LOCK_RATE: number;
  CLIMATE_INTENSITY: number;
  STEM_RESONANCE_BOOST: number;
  TRANSFER_DISTANCE_DECAY: number;
  WORK_MIN_THRESHOLD: number;
  SHOW_WEAK_WORK_PATHS: number;
};

export type PluginSwitches = {
  blindSchool: boolean;
  wangshuai: boolean;
  wealthRisk: boolean;
  /** 盲派子开关：穿破六害扫描 */
  blindSchoolPierceHarm: boolean;
  /** 盲派子开关：墓库闭库断言 */
  blindSchoolTombVault: boolean;
  /** 盲派子开关：宾主财官红利 */
  blindSchoolHostGuest: boolean;
};

export type PluginWeights = {
  blindSchool: number;
  wangshuai: number;
};

export type StreamThemeChroma = {
  bgColor: string;
  blindRatio: number;
  wangshuaiRatio: number;
  isConflictOverload: boolean;
  hasPolarityReversal: boolean;
};

export type FinalVerdictChangeLog = {
  physics_diff?: string[];
  consensus_diff?: string[];
  text_diff_hint?: string;
};

export type FinalVerdictResult = {
  body: string;
  changeLog: FinalVerdictChangeLog;
  logicalEvidence: string[];
  versionId: string;
  workVector?: Record<string, unknown>;
  topologyGraphV1?: Record<string, unknown>;
  structureCandidatesV0?: Record<string, unknown>;
  structureFinalDecisionV0?: Record<string, unknown>;
  auditLog?: Record<string, unknown>;
  confirmedDecisions?: Array<{ id: string; label: string; is_confirmed: boolean; confirmed_at?: string }>;
};

export type FinalVerdictHistoryItem = {
  versionId: string;
  body: string;
  changeLog: FinalVerdictChangeLog;
  logicalEvidence: string[];
  createdAt: string;
};

export type StressTestResult = {
  rollback_triggered?: boolean;
  hit_triggers?: string[];
  delta_abs?: number;
  structure_stability_shift?: { from?: string; to?: string };
};

export type GenderComparisonResult = {
  male_dayun?: string;
  female_dayun?: string;
  male_peak_abs?: number;
  female_peak_abs?: number;
  male_work_net?: number;
  female_work_net?: number;
  male_path_break_score?: number;
  female_path_break_score?: number;
  summary?: string;
};

export type LogicDiff = {
  baseline_abs_loss_total: number | null;
  current_abs_loss_total: number | null;
  abs_delta: number | null;
  baseline_entropy: number | null;
  current_entropy: number | null;
  entropy_delta: number | null;
};

export type StreamBoardViewModel = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  busy: boolean;
  consultationId: number | null;
  metadata: BaziMetadata | null;
  timeline: TimelineSnapshot | null;
  selectedBranch?: string;
  setSelectedBranch: Dispatch<SetStateAction<string | undefined>>;
  auditItems: import("@/components/AuditSidebar").AuditItem[];
  health: { dbOk: boolean; llmOk: boolean };
  llmModelName: string;
  i18nCalls: number;
  deityScores: Record<string, number>;
  deityEnergyAxes: Record<string, DeityEnergyAxis>;
  deityComponents: Record<string, DeityComponent>;
  deityTraceDetails: Record<string, Record<string, unknown>>;
  hoveredDeity?: string;
  setHoveredDeity: Dispatch<SetStateAction<string | undefined>>;
  confirmedConflicts: string[];
  llmDiagnosticData: LlmDiagnosticData | null;
  physicsParams: Record<string, number>;
  /** L1 合成全局熵 0..1，来自 physics_tensor.meta.global_entropy */
  globalEntropy: number | null;
  auditorProposalCards: InboxCard[];
  autoConvertedParamKey: string | null;
  consensusHistory: Array<{ decision_key: string; confirmed_value?: number; reasoning?: string }>;
  cards: InboxCard[];
  resultLogs: string[];
  finalVerdictBody: string;
  finalVerdictChangeLog: FinalVerdictChangeLog;
  finalLogicalEvidence: string[];
  finalWorkVector: Record<string, unknown> | null;
  finalTopologyGraphV1: Record<string, unknown> | null;
  finalStructureCandidatesV0: Record<string, unknown> | null;
  finalStructureFinalDecisionV0: Record<string, unknown> | null;
  confirmedDecisions?: Array<{ id: string; label: string; is_confirmed: boolean; confirmed_at?: string }>;
  confirmedDecisionIds?: string[];
  setConfirmedDecisionIds?: Dispatch<SetStateAction<string[]>>;
  urlDecisionHydrated?: boolean;
  /** 来自 URL ?tag=，供 SnapshotBanner 展示，避免子组件使用 useSearchParams 触发 Suspense */
  snapshotUrlTag?: string;
  snapshotAvailable?: boolean;
  setAsBaseline?: () => void;
  logicDiff?: LogicDiff;
  stressTestResult: StressTestResult | null;
  genderComparisonResult: GenderComparisonResult | null;
  finalVerdictHistory: FinalVerdictHistoryItem[];
  selectionResetToken: number;
  finalVerdictVersionId: string;
  conclusionVersion: number;
  summaryChanged: boolean;
  l1Certified: boolean;
  physicsAudit: Record<string, unknown> | null;
  physicsConfidence: number | null;
  physicsEvidence: string[];
  labConfig: PhysicsLabConfig;
  setLabConfig: Dispatch<SetStateAction<PhysicsLabConfig>>;
  showPhysicsAudit: boolean;
  setShowPhysicsAudit: Dispatch<SetStateAction<boolean>>;
  pluginSwitches: PluginSwitches;
  setPluginSwitches: Dispatch<SetStateAction<PluginSwitches>>;
  pluginWeights: PluginWeights;
  setPluginWeights: Dispatch<SetStateAction<PluginWeights>>;
  streamThemeChroma: StreamThemeChroma;
  rerunFinalVerdictWithWeights: (selectedCards?: InboxCard[]) => Promise<void>;
  logicDrawerOpen: boolean;
  logicDrawerTitle: string;
  logicDrawerFocus: string;
  logicDrawerDetails: string[];
  logicDrawerTrace: Record<string, unknown> | null;
  setLogicDrawerOpen: Dispatch<SetStateAction<boolean>>;
  onSeedSubmit: (payload: SeedPayload) => Promise<void>;
  addAuditorProposalToInbox: (proposal: LogicProposal) => void;
  onExecuteDecision: (selected: InboxCard[]) => Promise<void>;
  refreshVerdict: (selected: InboxCard[]) => Promise<void>;
  executeDecisionAndRefresh: (selected: InboxCard[]) => Promise<void>;
  appendSystemAuditLog: (line: string) => void;
  revokeConfirmedDecision?: (id: string) => Promise<void>;
  openLogicDrawer: (payload: { title: string; focus: string; details: string[]; deityTrace?: Record<string, unknown> }) => void;
  openLogicDrawerByDeity: (deity: string) => void;
  onEvidenceItemClick: (evidence: string) => void;
  showVerdictHistory: () => void;
  applyCurrentSqlPatch: () => Promise<void>;
  applyLabConfigAndRecalculate: () => Promise<void>;
  /** 静默重算 Abs：按当前 runtimeConfig 重拉 analyze-seed，不进入流式叙事 */
  reCalculateAbs: () => Promise<void>;
  runStressTest: (scenario: string) => Promise<void>;
  runGenderComparison: () => Promise<void>;
  t: (text: string) => string;
  inboxResetNonce: number;
  sigShiftFlashKey: number;
  isFinalized: boolean;
  finalizeVerdict: () => Promise<void>;
  syncBarrierSeq: number;
};
