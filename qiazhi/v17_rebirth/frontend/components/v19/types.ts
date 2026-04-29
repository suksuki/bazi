export type UiLocale = "zh" | "en" | "ko";

export type LocalizedLabel = {
  zh: string;
  en: string;
  ko: string;
};

export type CognitiveLayer =
  | "system_contract"
  | "input"
  | "chart"
  | "time"
  | "inference"
  | "theme"
  | "result"
  | "evidence"
  | "feedback"
  | "replay"
  | "governance";

export type UiSourceBinding = {
  sourceType:
    | "core_feature"
    | "strength"
    | "structure"
    | "inference"
    | "mapping"
    | "contract"
    | "verifier"
    | "ledger"
    | "synthetic_validation";
  sourceKey: string;
  sourceVersion?: string;
};

export type TrustBarProps = {
  verifierStatus: "passed" | "blocked" | "warning" | "unknown";
  confidence?: number;
  evidenceCount?: number;
  contractHash?: string;
  schemaVersion?: string;
  mappingVersion?: string;
  engineVersion?: string;
  verifierVersion?: string;
};

export type SignalTagCategory =
  | "day_master"
  | "ten_god"
  | "structure"
  | "flow"
  | "conflict"
  | "uncertainty"
  | "verification"
  | "risk";

export type SignalTagProps = {
  label: LocalizedLabel;
  value: string;
  category: SignalTagCategory;
  source?: UiSourceBinding;
  confidence?: number;
};

export type ChartStructureSummaryProps = {
  signals: SignalTagProps[];
  maxVisibleSignals?: 5;
};

export type TimeStructureSummaryProps = {
  flowYear: import("@/lib/v19/timeStructureTypes").FlowYear;
};

export type InferenceSignalValue =
  | "none"
  | "low"
  | "medium"
  | "high"
  | "weak"
  | "strong"
  | "balanced"
  | "leaning_weak"
  | "leaning_strong"
  | "stable"
  | "unstable"
  | "conflicted"
  | "blocked"
  | "active";

export type InferenceSignalItem = {
  signalKey: string;
  label: LocalizedLabel;
  value: InferenceSignalValue | string;
  category: SignalTagCategory;
  shortReason?: LocalizedLabel;
  sources: UiSourceBinding[];
  confidence?: number;
  expandable?: boolean;
};

export type InferenceSignalListProps = {
  signals: InferenceSignalItem[];
  defaultCollapsed: true;
};

export type SupportedThemeId =
  | "wealth_structure"
  | "income_stability"
  | "risk_opportunity";

export type DisabledThemeId =
  | "career"
  | "relationship"
  | "health"
  | "full_chart_general_reading";

export type ThemeId = SupportedThemeId | DisabledThemeId;

export type ThemeOption = {
  themeId: ThemeId;
  label: LocalizedLabel;
  enabled: boolean;
  disabledReason?: LocalizedLabel;
  requiredSignals?: string[];
};

export type ResultSummaryItem = {
  key: string;
  label: LocalizedLabel;
  value: string;
  sources: UiSourceBinding[];
};

export type ResultSummaryProps = {
  items: ResultSummaryItem[];
  maxLines: 2;
};

export type EvidenceCard = {
  evidenceId: string;
  label: LocalizedLabel;
  signalKey: string;
  detail: LocalizedLabel;
  strength?: "low" | "medium" | "high";
  sources: UiSourceBinding[];
  verifierStatus?: "passed" | "warning" | "blocked" | "unknown";
};

export type EvidenceCardListProps = {
  evidence: EvidenceCard[];
  visibleCount?: 2 | 3;
  expandable: boolean;
};

export type ResultAction =
  | { type: "feedback"; enabled: boolean; reason?: LocalizedLabel }
  | { type: "replay"; enabled: boolean; reason?: LocalizedLabel }
  | { type: "ask_followup"; enabled: boolean; reason?: LocalizedLabel };

export type ResultCardProps = {
  trust: TrustBarProps;
  summary: ResultSummaryProps;
  risk?: SignalTagProps[];
  uncertainty?: SignalTagProps[];
  actions: ResultAction[];
};

export type FeedbackValue =
  | "accurate"
  | "partly_accurate"
  | "unclear"
  | "wrong"
  | "unsafe_or_unsupported";

export type FeedbackPanelProps = {
  predictionId: string;
  allowedValues: FeedbackValue[];
  submitted?: boolean;
};

export type ReplayAnchor = {
  label: LocalizedLabel;
  value: string;
  source: UiSourceBinding;
};

export type ReplayCardProps = {
  predictionId: string;
  contractHash: string;
  verifierStatus: TrustBarProps["verifierStatus"];
  anchors: ReplayAnchor[];
  publicSafe: boolean;
};

export type BirthInputState = {
  date?: string;
  time?: string;
  place?: string;
  timezone?: string;
  calendarType?: "solar" | "lunar";
  completeness: "empty" | "partial" | "complete";
};

export type OracleStateName =
  | "first_screen"
  | "birth_input"
  | "chart_pending"
  | "chart_ready"
  | "inference_ready"
  | "theme_selectable"
  | "theme_selected"
  | "prediction_pending"
  | "result_ready"
  | "feedback_ready"
  | "feedback_submitted"
  | "replay_ready"
  | "blocked"
  | "error";

export type OracleUiState = {
  state: OracleStateName;
  locale: UiLocale;
  birthInput?: BirthInputState;
  chart?: ChartStructureSummaryProps;
  inference?: InferenceSignalListProps;
  themes?: ThemeOption[];
  selectedThemeId?: SupportedThemeId;
  result?: ResultCardProps;
  evidence?: EvidenceCardListProps;
  feedback?: FeedbackPanelProps;
  replay?: ReplayCardProps;
  blockedReason?: LocalizedLabel;
  errorCode?: string;
};

export function labelText(label: LocalizedLabel, locale: UiLocale): string {
  return label[locale] || label.en || label.zh || label.ko;
}
