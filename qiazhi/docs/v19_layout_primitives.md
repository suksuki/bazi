# V19 Layout Primitives and Component Architecture Seed

V19 UI is a reasoning system visualization pipeline.

It must not be organized as a generic page layout.

It must be organized by cognition layer and reasoning order.

## 1. Non-negotiable Cognitive Layers

Every V19 product surface must respect this data and cognition order:

```text
Layer 0: System Contract
Layer 1: Input
Layer 2: Chart Structure
Layer 3: Inference Signals
Layer 4: Result
Layer 5: Evidence
Layer 6: Feedback
Layer 7: Replay
```

This is not visual decoration.

It is the UI expression of the reasoning pipeline.

No result component may appear before chart structure and inference context exist.

No evidence component may be detached from the result it supports.

No replay component may omit trust anchors.

## 2. Layout Primitives

Layout primitives are non-business components.

They enforce structure before any domain-specific UI appears.

## SectionContainer

Purpose:

```text
force visible reasoning-layer separation
```

Type shape:

```ts
type SectionContainerProps = {
  layer:
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
  title: LocalizedLabel;
  subtitle?: LocalizedLabel;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  trustAnchor?: boolean;
  children: React.ReactNode;
};
```

Rules:

```text
Inference section defaults to collapsed.
Evidence can collapse after 2 to 3 visible items.
Replay technical details default to collapsed on mobile.
System Contract cannot be collapsed on first visit.
```

## TrustBar

Purpose:

```text
make trust state visible without turning the page into a technical dashboard
```

Type shape:

```ts
type TrustBarProps = {
  verifierStatus: "passed" | "blocked" | "warning" | "unknown";
  confidence?: number;
  evidenceCount?: number;
  contractHash?: string;
  schemaVersion?: string;
  mappingVersion?: string;
};
```

Visual placement:

```text
Result Card top
Replay Card top
Desktop right trust column when useful
```

Rules:

```text
TrustBar must not imply fate quality.
TrustBar only shows system verification state.
Long hashes must wrap or truncate with expand.
```

## LayerDivider

Purpose:

```text
show where the user is in the reasoning pipeline
```

Type shape:

```ts
type LayerDividerProps = {
  layer: SectionContainerProps["layer"];
  label: LocalizedLabel;
  state?: "pending" | "ready" | "verified" | "blocked";
};
```

Visual shape:

```text
label + subtle line
```

Examples:

```text
Chart Structure ─────────
Inference Signals ───────
Evidence ────────────────
```

Rules:

```text
LayerDivider is not a generic border.
It communicates reasoning position.
```

## StateGate

Purpose:

```text
enforce capability boundary through UI state
```

Type shape:

```ts
type StateGateProps = {
  enabled: boolean;
  reason?: LocalizedLabel;
  children: React.ReactNode;
};
```

Use for:

```text
theme selection
question actions
prediction generation
feedback submission
rule activation actions
```

Rules:

```text
Disabled actions must explain why.
Unsupported themes are disabled, not merely discouraged by copy.
StateGate is a trust component, not a convenience component.
```

## 3. Shared Types

Localized labels:

```ts
type LocalizedLabel = {
  zh: string;
  en: string;
  ko: string;
};
```

Signal tag:

```ts
type SignalTagProps = {
  label: LocalizedLabel;
  value: string;
  category: "day_master" | "ten_god" | "structure" | "flow" | "conflict" | "uncertainty";
  source?: string;
};
```

## 4. `/oracle` Component Tree

First implementation target:

```text
OraclePage
 ├─ SystemContractHeader
 ├─ BirthInputPanel
 ├─ SectionContainer (chart)
 │    └─ ChartStructureSummary
 ├─ SectionContainer (inference, collapsed=true)
 │    └─ InferenceSignalList
 ├─ SectionContainer (theme)
 │    └─ ThemeSelector
 │         └─ StateGate for each theme
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

The tree must preserve this order on mobile.

Desktop may use columns, but reading order must remain the same.

## 5. `/oracle` First Screen Structure

The first screen must contain:

```text
SystemContractHeader
CurrentScopePanel
PrimaryActionPanel
```

SystemContractHeader:

```text
title: this is a verifiable Bazi prediction system
content: system first understands chart structure, then provides verifiable predictions
```

CurrentScopePanel:

```text
enabled:
- wealth structure
- income stability
- risk and opportunity

disabled:
- career
- relationship
- health
- full chart general reading
```

PrimaryActionPanel:

```text
enter birth information
use sample chart
```

## 6. Chart Structure Summary Rules

Chart Summary is the product's first concrete artifact.

It must be scannable.

Rules:

```text
maximum 5 signals
each signal label should be 12 Chinese characters or fewer when possible
must use SignalTag
must not use sentences
must not include prediction conclusion
```

Example:

```text
Day Master: weak
Structure: unstable
Conflict: internal
Flow: blocked
Evidence: available
```

## 7. Inference Signal Expansion Rules

Inference Summary defaults to collapsed.

Expanded signal shape:

```text
Signal
short reason, one line
source
expand -> details
```

Allowed:

```text
bounded signal value
source binding
confidence
short reason
```

Forbidden:

```text
long narrative
domain conclusion
free-form fate explanation
LLM-style paragraph
```

## 8. Result Summary Rules

Result is not narrative.

Result Summary must be compact.

Rules:

```text
maximum 2 lines
no causal paragraph
no long explanation
no unsupported theme expansion
no raw LLM text
```

Preferred result format:

```text
Income stability: low
Volatility: high
```

Forbidden:

```text
Because the wealth star is combined, your income will...
```

The causal material belongs in Evidence, not Result Summary.

## 9. ThemeSelector Rules

ThemeSelector must constrain choices.

Current selectable options:

```text
wealth_structure
income_stability
risk_opportunity
```

Disabled options:

```text
career
relationship
health
full_chart_general_reading
```

Disabled reason:

```text
not yet supported by reviewed rules
```

ThemeSelector must use StateGate.

## 10. EvidenceCardList Rules

Evidence cards explain why the result exists.

Mobile:

```text
show 2 cards by default
expand for more
no dense tables
```

Each evidence card:

```text
label
source layer
short reason
confidence or relevance if available
expand details
```

## 11. ReplayCard Rules

Replay is a verification document entry point.

ReplayCard must include:

```text
prediction_id
contract hash
verifier status
Core Bazi Engine version
Inference Schema version
Mapping Registry version
redaction state
```

Technical IDs must wrap safely.

## 12. Visual Generation Prompt

Use this prompt for visual exploration only.

It is not an implementation spec.

```text
Design a mobile-first and desktop web UI for a structured reasoning system, not a chatbot.

Core concept:
chart structure -> inference signals -> verified result -> evidence -> replay

Style:
calm, structured, trust-first, non-mystical, professional

DO NOT include:
chat bubbles
assistant-style conversation
mystical purple/black theme
tarot or fortune visuals

Layout:
clear section separation using labeled dividers

Sections:
1. System contract header (what it is / what you can ask / next step)
2. Birth input panel
3. Chart Structure Summary (compact signal tags)
4. Inference Signals (collapsed by default)
5. Theme selection (with disabled states and reasons)
6. Result Card (with trust bar: verifier, confidence, hash)
7. Evidence cards (2 visible, expandable)
8. Replay card (technical verification info)

Color system:
warm paper background OR deep ink
mineral blue (primary)
slate / graphite (structure)
soft amber (uncertainty)
verified green (trust)
muted red (risk)

Typography:
clear hierarchy
short labels
no long paragraphs

Important:
Make the UI feel like a reasoning instrument, not a prediction app.
```

## 13. Boundary

This document defines UI structure primitives only.

It does not implement components.

It does not connect APIs.

It does not modify V18 UI.

It does not change V19 Core, Inference, Mapping Registry, Synthetic Validation, or backend services.

Next step:

```text
V19 Component Architecture -> TypeScript schema + state model
```
