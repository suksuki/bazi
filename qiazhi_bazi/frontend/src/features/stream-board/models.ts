import type { BaziMetadata, FourPillars, Lang, TimelineSnapshot } from "@/types/bazi";
import type { Dispatch, SetStateAction } from "react";
import type { DecisionJournalEntry } from "@/features/stream-board/decisionJournal";

export type SeedPayload = {
  date: string;
  time: string;
  calendar: "solar" | "lunar";
  gender: "male" | "female";
};

/**
 * analyze-seed 结束态：成功含 tensor 供指纹对比；失败带可读错误（主栏/入口须展示，避免静默失败）。
 */
export type SeedSubmitResult =
  | { ok: true; physics_tensor: Record<string, unknown> | null }
  | { ok: false; error: string };

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
  cardType?: "conflict" | "auditor-proposal" | "proposal" | "L1_STRUCTURE";
  proposal?: LogicProposal;
  /** 与盲派 skill_manifest 对齐，可由 UI 推断或上游写入 */
  skillId?: string;
  /** 跳转 Debug「插件碰撞」时滚动定位的 plugin_outputs 键（物理引擎为 sys.core.physics） */
  pluginAuditAnchorId?: string;
  /** 格局主权与 L1 冲突时：Decision Inbox 角标与路由语义 */
  sovereigntyMark?: "PATTERN_SOVEREIGNTY";
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
  /** L1 base_physics 原子算子 η，与后端 PhysicsConfig / DEFAULT_PHYSICS_SETTINGS 对齐 */
  L1_OP_PROD_ETA?: number;
  L1_OP_DEST_ETA?: number;
  L1_OP_CONN_ETA?: number;
  /** 跨柱干支传导灵敏度（0..2），与 interaction_params / physics_settings 对齐 */
  INTERDIMENSIONAL_CONDUCTIVITY?: number;
  INTERDIMENSIONAL_BARRIER_STRENGTH?: number;
  CONDUCTIVITY_DECAY_RATE?: number;
  GHOST_ENERGY_DAMPING?: number;
  MANGPAI_ETA_DIMENSIONAL_CRUSH?: number;
  MANGPAI_ROOT_RESONANCE?: number;
  /** 1=启用，0=关闭（与后端 physics_config 浮点开关一致） */
  INTERDIMENSIONAL_SHIELD_ENABLE?: number;
  STEM_BRANCH_ROOT_RESONANCE_ENABLE?: number;
  STEM_BRANCH_VERTICAL_CRUSH_ENABLE?: number;
  /** L1 核心冲突算子簇总开关与分项 η（与 DEFAULT_PHYSICS_SETTINGS / skill_manifest 对齐） */
  L1_CORE_CONFLICT_OPS_ENABLE?: number;
  L1_OWL_FOOD_DAMPING?: number;
  L1_WEALTH_SEAL_COLLAPSE?: number;
  L1_BLADE_CLASH_INSTABILITY?: number;
  L1_ROBBER_WEALTH_ALLOC_LOSS?: number;
  L1_GOV_KILL_EFFICIENCY_LOSS?: number;
  /** Junction 伤官见官坐标畸变衰减（与 SGJG_* 协议对齐） */
  SGJG_COORDINATE_DISTORTION_DECAY?: number;
  /** 墓库冲开倍率（op_grave / skill l1_grave_vault_01） */
  GRAVE_BURST_MULTIPLIER?: number;
  /** 三合 φ 门控强度（op_phi_clamp） */
  L1_SANHE_PHI_CLAMP?: number;
  /** 十二长生状态缩放峰值乘子（op_status） */
  STATUS_BOOST_MULTIPLIER?: number;
  /** 用户环境方位：东/南/西/北/中；触发后端 L1_OP_GEOGRAPHY 场强演示 */
  user_target_direction?: string;
  /** 深度地支 / 天干五合：与 DEFAULT_PHYSICS_SETTINGS 对齐，供 Admin 实验滑块写入 analyze-seed */
  L1_SUB_BRANCH_OP_ENABLE?: number;
  SUB_BRANCH_BANHE_PHI?: number;
  SUB_BRANCH_BANHE_ABS_BOOST?: number;
  SUB_BRANCH_BANHE_VECTOR_BOOST?: number;
  SUB_BRANCH_SANHE_ABS_BOOST?: number;
  SUB_BRANCH_SANHE_REQ_WANG_ZHI?: number;
  SANHE_ALPHA_LEAKAGE?: number;
  SUB_BRANCH_LIUHE_ABS_BOOST?: number;
  SUB_BRANCH_SANXING_ABS_DAMP?: number;
  SUB_BRANCH_LIUCHONG_ABS_DAMP?: number;
  SUB_BRANCH_LIUHAI_ABS_DAMP?: number;
  SUB_BRANCH_LIUPO_ABS_DAMP?: number;
  SUB_BRANCH_LIUHAI_ENABLE?: number;
  SUB_BRANCH_LIUPO_ENABLE?: number;
  L1_STEM_FUSION_ENABLE?: number;
  STEM_FUSION_VECTOR_LEAK_RATIO?: number;
  STEM_FUSION_BRANCH_SUPPORT_RATIO?: number;
  /** L0 原子层：与后端 DEFAULT_PHYSICS_SETTINGS / l0_* 表对齐 */
  L0_HIDDEN_ENERGY_SCALE?: number;
  L0_ROOT_BOOST_FACTOR?: number;
  L0_YM_DH_WEIGHT_RATIO?: number;
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

export type LlmChatMessage = { role: string; content: string };

export type VerdictNarrativeChunk = {
  chunk_id: string;
  text: string;
  branch_chars?: string[];
  pillar_keys?: string[];
  conflict_point_ids?: string[];
};

export type FinalVerdictResult = {
  body: string;
  changeLog: FinalVerdictChangeLog;
  logicalEvidence: string[];
  versionId: string;
  /** 终判段落与地支 / conflict_point 的弱锚点（后端启发式） */
  narrativeChunks?: VerdictNarrativeChunk[];
  workVector?: Record<string, unknown>;
  topologyGraphV1?: Record<string, unknown>;
  structureCandidatesV0?: Record<string, unknown>;
  structureFinalDecisionV0?: Record<string, unknown>;
  auditLog?: Record<string, unknown>;
  confirmedDecisions?: Array<{ id: string; label: string; is_confirmed: boolean; confirmed_at?: string }>;
  /** 终判单次请求的 messages（与 /v1/final-verdict 对齐） */
  llmRequestMessages?: LlmChatMessage[];
  /** 模型原始返回（多为 JSON 包裹的 Markdown） */
  llmRawResponse?: string;
  llmMeta?: Record<string, unknown>;
  /** 终判回写：断言锚点层等，供 merge 进 snapshot.metadata */
  metadataMemoryPatch?: Record<string, unknown>;
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

/** physics_tensor.meta.decision_signal_to_noise：Inbox 判词观察项门控 */
export type DecisionSignalToNoiseMeta = {
  inbox_conflict_cards_eligible?: boolean;
  threshold?: number;
  abs_estimate?: number | null;
  has_critical_marker?: boolean;
  /** 三合聚能已登记时后端强制放行判词观察项 */
  sanhe_inbox_bypass?: boolean;
};

export type StreamBoardViewModel = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  busy: boolean;
  consultationId: number | null;
  metadata: BaziMetadata | null;
  timeline: TimelineSnapshot | null;
  /** 公历参考年：驱动大运/流年展示；与后端 get_timeline_snapshot(reference_year) 一致 */
  referenceYear: number;
  setReferenceYear: Dispatch<SetStateAction<number>>;
  /** 正式排盘前的轻量四柱+大运流年（/v1/seed-preview） */
  seedPreviewPillars: FourPillars | null;
  seedPreviewTimeline: TimelineSnapshot | null;
  seedPreviewBusy: boolean;
  seedPreviewError: string | null;
  /** 草稿生辰变化时防抖请求预览；传 null 清空预览态 */
  scheduleSeedDraftPreview: (payload: SeedPayload | null) => void;
  /** 立即请求 /v1/seed-preview（「选择出生日期」按钮，不经防抖） */
  refreshSeedPreview: (payload: SeedPayload) => Promise<void>;
  /** 已有正式结果时用户改草稿：清空排盘/终判等，直至再次测算 */
  clearLabPipelineForSeedDraft: () => void;
  /** 当前实验室记录的上次已提交生辰（与 metadata 对齐）；用于判断是否草稿偏离 */
  lastCommittedSeedSignature: string | null;
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
  /** 多插件因果路由包，来自 physics_tensor.meta.causal_routing */
  causalRouting: Record<string, unknown> | null;
  /** physics_tensor.meta.pattern_profile：从格/化格候选等 */
  patternProfile: Record<string, unknown> | null;
  /** physics_tensor.meta.energy_flow_audit：五行相生流通审计 */
  energyFlowAudit: Record<string, unknown> | null;
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
  /** 实验室快照中的追加型决策日志（语义抑制） */
  decisionJournal?: DecisionJournalEntry[];
  /** 写入实验室快照（含 decision_journal） */
  mergeLabSnapshot?: (diff: Record<string, unknown>) => void;
  setConfirmedDecisionIds?: Dispatch<SetStateAction<string[]>>;
  urlDecisionHydrated?: boolean;
  /** 来自 URL ?tag=，供 SnapshotBanner 展示，避免子组件使用 useSearchParams 触发 Suspense */
  snapshotUrlTag?: string;
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
  onSeedSubmit: (payload: SeedPayload) => Promise<SeedSubmitResult>;
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
