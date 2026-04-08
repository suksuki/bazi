import type { BaziMetadata, DecisionStep, Lang, TimelineSnapshot } from "@/types/bazi";
import type { Dispatch, SetStateAction } from "react";

export type SeedPayload = {
  date: string;
  time: string;
  calendar: "solar" | "lunar";
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
  auditLog?: Record<string, unknown>;
};

export type FinalVerdictHistoryItem = {
  versionId: string;
  body: string;
  changeLog: FinalVerdictChangeLog;
  logicalEvidence: string[];
  createdAt: string;
};

export type StreamBoardViewModel = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  busy: boolean;
  drawerOpen: boolean;
  setDrawerOpen: Dispatch<SetStateAction<boolean>>;
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
  auditorProposalCards: InboxCard[];
  autoConvertedParamKey: string | null;
  consensusHistory: Array<{ decision_key: string; confirmed_value?: number; reasoning?: string }>;
  cards: InboxCard[];
  resultLogs: string[];
  finalVerdictBody: string;
  finalVerdictChangeLog: FinalVerdictChangeLog;
  finalLogicalEvidence: string[];
  finalWorkVector: Record<string, unknown> | null;
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
  mergedSteps: DecisionStep[];
  logicDrawerOpen: boolean;
  logicDrawerTitle: string;
  logicDrawerFocus: string;
  logicDrawerDetails: string[];
  logicDrawerTrace: Record<string, unknown> | null;
  setLogicDrawerOpen: Dispatch<SetStateAction<boolean>>;
  onSeedSubmit: (payload: SeedPayload) => Promise<void>;
  addAuditorProposalToInbox: (proposal: LogicProposal) => void;
  onExecuteDecision: (selected: InboxCard[]) => Promise<void>;
  openLogicDrawer: (payload: { title: string; focus: string; details: string[]; deityTrace?: Record<string, unknown> }) => void;
  openLogicDrawerByDeity: (deity: string) => void;
  onEvidenceItemClick: (evidence: string) => void;
  showVerdictHistory: () => void;
  onRollback: (id: string) => Promise<void>;
  applyCurrentSqlPatch: () => Promise<void>;
  applyLabConfigAndRecalculate: () => Promise<void>;
  t: (text: string) => string;
};
