# V19 Component Architecture v1

This document turns the V19 product experience, wireframe, visual system, and layout primitives into an implementation-ready component architecture.

It is not UI code.

It is not an API contract.

It defines the frontend component contract, TypeScript data shapes, and page state machine that future UI implementation must follow.

## 1. Purpose

V19 UI is a structured reasoning interface.

It must visualize this pipeline:

```text
System Contract -> Input -> Chart Structure -> Inference Signals -> Result -> Evidence -> Feedback -> Replay
```

The component architecture exists to prevent three failures:

```text
1. Result-first prediction UI
2. Chat-like narrative UI
3. Domain components that silently add reasoning
```

## 2. Non-negotiable Component Rules

```text
1. Components render state; they do not infer fate.
2. UI components never create domain conclusions.
3. UI components never calculate scores.
4. UI components never call LLMs.
5. UI components never bypass Core / Inference / Mapping / Contract.
6. Result components must cite evidence.
7. Replay components must show trust anchors.
8. Unsupported actions must be disabled by StateGate.
9. All user-facing labels must support zh / en / ko.
10. Mobile reading order must preserve the reasoning pipeline.
```

## 3. Shared TypeScript Primitives

These shapes are frontend-facing type contracts.

They may be implemented as TypeScript interfaces, Zod schemas, or generated types later.

### Locale

```ts
type UiLocale = "zh" | "en" | "ko";

type LocalizedLabel = {
  zh: string;
  en: string;
  ko: string;
};
```

### Cognitive Layer

```ts
type CognitiveLayer =
  | "system_contract"
  | "input"
  | "chart"
  | "inference"
  | "theme"
  | "result"
  | "evidence"
  | "feedback"
  | "replay"
  | "governance";
```

### UI Source Binding

```ts
type UiSourceBinding = {
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
```

Rules:

```text
sourceKey must be machine-readable.
sourceVersion is required for schema, mapping, contract, verifier, and rule-derived data.
Free-form source descriptions are not allowed.
```

## 4. Layout Primitive Contracts

### SectionContainer

```ts
type SectionContainerProps = {
  layer: CognitiveLayer;
  title: LocalizedLabel;
  subtitle?: LocalizedLabel;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  trustAnchor?: boolean;
  status?: "pending" | "ready" | "verified" | "blocked" | "warning";
  children: React.ReactNode;
};
```

Rules:

```text
System Contract cannot be collapsed on first visit.
Inference defaults to collapsed.
Evidence may collapse after 2 to 3 visible items.
Replay technical detail defaults to collapsed on mobile.
Blocked sections must explain why.
```

### LayerDivider

```ts
type LayerDividerProps = {
  layer: CognitiveLayer;
  label: LocalizedLabel;
  state?: "pending" | "ready" | "verified" | "blocked";
};
```

Rules:

```text
LayerDivider communicates reasoning position.
It is not a decorative border.
Every major section should have a visible layer label on mobile.
```

### TrustBar

```ts
type TrustBarProps = {
  verifierStatus: "passed" | "blocked" | "warning" | "unknown";
  confidence?: number;
  evidenceCount?: number;
  contractHash?: string;
  schemaVersion?: string;
  mappingVersion?: string;
  engineVersion?: string;
  verifierVersion?: string;
};
```

Rules:

```text
TrustBar shows system verification state only.
It must not imply good fate or bad fate.
Long hashes must wrap, truncate safely, or expand on tap.
```

### StateGate

```ts
type StateGateProps = {
  enabled: boolean;
  reason?: LocalizedLabel;
  requiredState?: OracleStateName;
  children: React.ReactNode;
};
```

Rules:

```text
Disabled actions must explain why.
Unsupported themes are disabled, not hidden.
StateGate is required for theme selection and prediction submission.
```

## 5. Signal Display Contracts

### SignalTag

```ts
type SignalTagCategory =
  | "day_master"
  | "ten_god"
  | "structure"
  | "flow"
  | "conflict"
  | "uncertainty"
  | "verification"
  | "risk";

type SignalTagProps = {
  label: LocalizedLabel;
  value: string;
  category: SignalTagCategory;
  source?: UiSourceBinding;
  confidence?: number;
};
```

Rules:

```text
SignalTag value must be bounded.
SignalTag must not contain a sentence.
SignalTag must not contain destiny narrative.
```

### ChartStructureSummary

```ts
type ChartStructureSummaryProps = {
  signals: SignalTagProps[];
  maxVisibleSignals?: 5;
};
```

Rules:

```text
Default maximum is 5 visible signals.
Each visible signal should be short enough to scan on mobile.
No free-form paragraph is allowed.
```

Example:

```text
Day Master: weak
Structure: unstable
Conflict: internal
Flow: blocked
Uncertainty: weak_signal
```

### InferenceSignal

```ts
type InferenceSignalValue =
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

type InferenceSignalItem = {
  signalKey: string;
  label: LocalizedLabel;
  value: InferenceSignalValue | string;
  category: SignalTagCategory;
  shortReason?: LocalizedLabel;
  sources: UiSourceBinding[];
  confidence?: number;
  expandable?: boolean;
};

type InferenceSignalListProps = {
  signals: InferenceSignalItem[];
  defaultCollapsed: true;
};
```

Rules:

```text
Each inference signal must have at least one source.
shortReason is one line only.
Expanded content may show technical detail but must not become narrative fortune telling.
```

## 6. Theme Selection Contract

### ThemeOption

```ts
type SupportedThemeId =
  | "wealth_structure"
  | "income_stability"
  | "risk_opportunity";

type DisabledThemeId =
  | "career"
  | "relationship"
  | "health"
  | "full_chart_general_reading";

type ThemeId = SupportedThemeId | DisabledThemeId;

type ThemeOption = {
  themeId: ThemeId;
  label: LocalizedLabel;
  enabled: boolean;
  disabledReason?: LocalizedLabel;
  requiredSignals?: string[];
};

type ThemeSelectorProps = {
  options: ThemeOption[];
  selectedThemeId?: SupportedThemeId;
  onSelect: (themeId: SupportedThemeId) => void;
};
```

Rules:

```text
Only enabled supported themes may be selected.
Disabled themes must remain visible with a reason.
ThemeSelector does not infer whether a theme is possible.
It only renders capability state provided by system state.
```

## 7. Result Display Contract

### ResultSummary

```ts
type ResultSummaryItem = {
  key: string;
  label: LocalizedLabel;
  value: string;
  sources: UiSourceBinding[];
};

type ResultSummaryProps = {
  items: ResultSummaryItem[];
  maxLines: 2;
};
```

Rules:

```text
ResultSummary is not a paragraph.
Maximum visible summary is 2 lines.
No causal chain paragraph is allowed.
No unsupported domain conclusion is allowed.
```

Allowed shape:

```text
Income stability: low
Volatility: high
```

Forbidden shape:

```text
Because wealth is combined and the day master is weak, your income will...
```

### EvidenceCard

```ts
type EvidenceCard = {
  evidenceId: string;
  label: LocalizedLabel;
  signalKey: string;
  strength?: "low" | "medium" | "high";
  sources: UiSourceBinding[];
  verifierStatus?: "passed" | "warning" | "blocked" | "unknown";
};

type EvidenceCardListProps = {
  evidence: EvidenceCard[];
  visibleCount?: 2 | 3;
  expandable: boolean;
};
```

Rules:

```text
Evidence cards must be attached to a result.
Evidence is shown before long explanation.
Mobile default is 2 visible evidence cards.
```

### ResultCard

```ts
type ResultCardProps = {
  trust: TrustBarProps;
  summary: ResultSummaryProps;
  risk?: SignalTagProps[];
  uncertainty?: SignalTagProps[];
  actions: ResultAction[];
};

type ResultAction =
  | { type: "feedback"; enabled: boolean; reason?: LocalizedLabel }
  | { type: "replay"; enabled: boolean; reason?: LocalizedLabel }
  | { type: "ask_followup"; enabled: boolean; reason?: LocalizedLabel };
```

Rules:

```text
ResultCard must include TrustBar.
ResultCard must not render raw LLM output.
ResultCard must not display score unless the Contract explicitly provides a bounded display value.
```

## 8. Feedback and Replay Contracts

### FeedbackPanel

```ts
type FeedbackValue =
  | "accurate"
  | "partly_accurate"
  | "unclear"
  | "wrong"
  | "unsafe_or_unsupported";

type FeedbackPanelProps = {
  predictionId: string;
  allowedValues: FeedbackValue[];
  submitted?: boolean;
};
```

Rules:

```text
Feedback creates learning signal only.
Feedback must not directly modify active rules.
```

### ReplayCard

```ts
type ReplayCardProps = {
  predictionId: string;
  contractHash: string;
  verifierStatus: TrustBarProps["verifierStatus"];
  anchors: ReplayAnchor[];
  publicSafe: boolean;
};

type ReplayAnchor = {
  label: LocalizedLabel;
  value: string;
  source: UiSourceBinding;
};
```

Required replay anchors:

```text
Core Bazi Engine version
Inference Schema version
Mapping Registry version
Contract version
Verifier version
prediction_id
contract hash
verifier status
```

Rules:

```text
Replay must be readable on mobile.
Replay must not leak private birth data in public-safe mode.
Long IDs and hashes must not break layout.
```

## 9. Oracle Page Component Tree

Mobile reading order is mandatory:

```text
OraclePage
 ├─ SystemContractHeader
 ├─ CurrentScopePanel
 ├─ PrimaryActionPanel
 ├─ BirthInputPanel
 ├─ SectionContainer (chart)
 │    └─ ChartStructureSummary
 ├─ SectionContainer (inference, collapsed=true)
 │    └─ InferenceSignalList
 ├─ SectionContainer (theme)
 │    └─ ThemeSelector
 │         └─ StateGate for each option
 ├─ SectionContainer (result)
 │    └─ ResultCard
 │         ├─ TrustBar
 │         ├─ ResultSummary
 │         ├─ RiskRow
 │         └─ ActionRow
 ├─ SectionContainer (evidence)
 │    └─ EvidenceCardList
 ├─ SectionContainer (feedback)
 │    └─ FeedbackPanel
 └─ SectionContainer (replay)
      └─ ReplayCard
```

Desktop may place sections in columns, but the logical order must remain:

```text
contract -> input -> chart -> inference -> theme -> result -> evidence -> feedback -> replay
```

## 10. Oracle State Model

The Oracle UI must be driven by a finite state machine.

The UI must not infer missing states from partial data.

### State Names

```ts
type OracleStateName =
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
```

### State Shape

```ts
type OracleUiState = {
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

type BirthInputState = {
  date?: string;
  time?: string;
  place?: string;
  timezone?: string;
  calendarType?: "solar" | "lunar";
  completeness: "empty" | "partial" | "complete";
};
```

### Events

```ts
type OracleEvent =
  | { type: "START_INPUT" }
  | { type: "USE_SAMPLE_CHART" }
  | { type: "UPDATE_BIRTH_INPUT"; payload: BirthInputState }
  | { type: "SUBMIT_BIRTH_INPUT" }
  | { type: "CORE_READY"; chart: ChartStructureSummaryProps }
  | { type: "INFERENCE_READY"; inference: InferenceSignalListProps }
  | { type: "THEMES_READY"; themes: ThemeOption[] }
  | { type: "SELECT_THEME"; themeId: SupportedThemeId }
  | { type: "SUBMIT_PREDICTION" }
  | { type: "RESULT_READY"; result: ResultCardProps; evidence: EvidenceCardListProps }
  | { type: "FEEDBACK_READY"; feedback: FeedbackPanelProps }
  | { type: "SUBMIT_FEEDBACK"; value: FeedbackValue }
  | { type: "REPLAY_READY"; replay: ReplayCardProps }
  | { type: "BLOCK"; reason: LocalizedLabel }
  | { type: "FAIL"; errorCode: string };
```

### Transition Table

```text
first_screen -> START_INPUT -> birth_input
first_screen -> USE_SAMPLE_CHART -> chart_pending
birth_input -> UPDATE_BIRTH_INPUT -> birth_input
birth_input -> SUBMIT_BIRTH_INPUT -> chart_pending
chart_pending -> CORE_READY -> chart_ready
chart_ready -> INFERENCE_READY -> inference_ready
inference_ready -> THEMES_READY -> theme_selectable
theme_selectable -> SELECT_THEME -> theme_selected
theme_selected -> SUBMIT_PREDICTION -> prediction_pending
prediction_pending -> RESULT_READY -> result_ready
result_ready -> FEEDBACK_READY -> feedback_ready
feedback_ready -> SUBMIT_FEEDBACK -> feedback_submitted
result_ready -> REPLAY_READY -> replay_ready
feedback_submitted -> REPLAY_READY -> replay_ready
any -> BLOCK -> blocked
any -> FAIL -> error
```

### Guards

```text
SUBMIT_BIRTH_INPUT requires birthInput.completeness = complete.
INFERENCE_READY requires chart_ready.
THEMES_READY requires inference_ready.
SELECT_THEME requires theme.enabled = true.
SUBMIT_PREDICTION requires selectedThemeId.
RESULT_READY requires TrustBar and evidence.
REPLAY_READY requires predictionId, contractHash, and verifierStatus.
```

### StateGate Mapping

```text
Birth submit disabled until birth input is complete.
Theme selection disabled until inference_ready.
Unsupported themes remain disabled even after inference_ready.
Prediction submit disabled until theme_selected.
Feedback disabled until result_ready.
Replay disabled until contract hash and verifier status exist.
```

## 11. Route-level Component Architecture

### `/`

Purpose:

```text
explain system identity and lead into Oracle
```

Component tree:

```text
HomePage
 ├─ ProductHeader
 ├─ SystemIdentityHero
 ├─ CapabilityBoundaryCards
 ├─ ReasoningPipelinePreview
 ├─ TrustModelPanel
 ├─ RoleEntryCards
 └─ FooterMeta
```

Rules:

```text
HomePage may explain the system.
HomePage must not simulate a prediction.
HomePage must not center wealth.
```

### `/oracle`

Purpose:

```text
main user reasoning flow
```

Rules:

```text
OraclePage uses the Oracle state machine.
OraclePage must show chart before result.
OraclePage must keep inference structural.
```

### `/replay`

Purpose:

```text
verification document
```

Component tree:

```text
ReplayPage
 ├─ ReplayHeader
 ├─ TrustBar
 ├─ PublicSafeNotice
 ├─ ResultSummary
 ├─ EvidenceCardList
 ├─ ReplayAnchorList
 └─ VerificationTimeline
```

Rules:

```text
Replay is not a marketing page.
Replay must prove what was produced and how it was verified.
Public replay must redact private input.
```

### `/practitioner`

Purpose:

```text
professional review and correction
```

Component tree:

```text
PractitionerPage
 ├─ PractitionerHeader
 ├─ ReviewQueue
 ├─ InferenceSignalReviewPanel
 ├─ MappingReviewPanel
 ├─ SyntheticValidationPanel
 └─ CommentAndCorrectionPanel
```

Rules:

```text
Practitioner can review and propose.
Practitioner cannot activate production rules.
All actions require audit trail.
```

### `/admin`

Purpose:

```text
governance and production control
```

Component tree:

```text
AdminPage
 ├─ AdminHeader
 ├─ SystemHealthPanel
 ├─ KnowledgeGovernancePanel
 ├─ MappingGovernancePanel
 ├─ RuleActivationPanel
 ├─ AuditTrailPanel
 └─ RuntimeVisibilityPanel
```

Rules:

```text
Admin actions require explicit review state.
Activation must show synthetic validation state.
Redis must never appear as source of truth.
PostgreSQL is the persistent fact source.
```

## 12. Forbidden UI Outputs

No V19 UI component may render these unless they are explicitly supplied by a verified Contract-backed result:

```text
fortune quality judgment
overall life destiny judgment
relationship prediction
health prediction
career prediction
useful-god final judgment
free-form LLM answer
unverified score
raw active rule internals for users
```

The following keys are forbidden in component-local state:

```text
wealth_type
career_type
relationship_type
health_type
destiny_score
fortune_score
llm_answer
free_text_prediction
```

## 13. Implementation Readiness Checklist

Before UI code starts:

```text
1. SectionContainer, LayerDivider, TrustBar, and StateGate must be implemented first.
2. Oracle state machine must be implemented before ResultCard.
3. SignalTag must be implemented before ChartStructureSummary.
4. InferenceSignalList must accept only structured signals.
5. ThemeSelector must render disabled unsupported themes with reasons.
6. ResultCard must require TrustBar.
7. EvidenceCardList must require source bindings.
8. ReplayCard must require trust anchors.
9. All labels must use LocalizedLabel.
10. Mobile layout must preserve pipeline order.
```

## 14. Acceptance Criteria

V19 Component Architecture v1 is accepted when:

```text
1. `/oracle` can be implemented without inventing new component concepts.
2. No component needs to perform Bazi reasoning.
3. No component needs to call LLM.
4. Unsupported themes are representable as disabled states.
5. Replay can show verification anchors without layout hacks.
6. Result can be displayed without narrative paragraphs.
7. Evidence can be displayed before explanation.
8. Mobile and desktop share the same logical reading order.
9. zh / en / ko labels are first-class from the type layer.
10. The UI can fail closed when required state is missing.
```

## 15. Next Step

After this document is accepted, the correct next implementation step is:

```text
V19 UI Prototype v1
```

Scope:

```text
static frontend prototype
no backend API
no production prediction
mocked V19 state machine data
mobile-first `/oracle`
```

Do not implement:

```text
Domain Contract
LLM narrative
production integration
V18 UI compatibility
```
