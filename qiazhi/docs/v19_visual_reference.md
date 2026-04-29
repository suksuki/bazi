# V19 Visual Reference Review

This document converts the analyst visual sketch into implementation guidance.

It does not replace:

```text
docs/v19_product_experience.md
docs/v19_wireframe.md
docs/v19_visual_system.md
docs/v19_layout_primitives.md
docs/v19_component_architecture.md
```

It acts as the visual reference for the first V19 UI prototype.

Reference image:

```text
/Users/liujin/Downloads/f8e6fc18-7300-4cf4-a5e6-e5e424722967.png
```

## 1. Overall Assessment

The sketch is directionally correct.

It successfully expresses V19 as:

```text
structured reasoning system
not chatbot
not mystical UI
not wealth-only demo
```

The strongest parts are:

```text
1. Clear pipeline header: chart structure -> inference signals -> verified result -> evidence -> replay
2. Mobile and desktop share the same reasoning order
3. Chart Structure Summary appears before Result
4. Inference Signals are collapsed by default
5. Theme Selection has disabled unsupported states
6. Result Card includes TrustBar before result summary
7. Evidence is visible but bounded
8. Replay and Verification appear as trust anchors
```

This sketch can be used as the visual anchor for:

```text
V19 UI Prototype v1
```

## 2. What Must Be Preserved

### Reasoning Order

The sketch preserves the correct order:

```text
System Contract
Birth Input
Chart Structure
Inference Signals
Theme Selection
Result
Evidence
Replay
```

This order must remain unchanged on mobile and desktop.

Desktop may use columns, but reading order must not change.

### Non-chat Product Shape

The sketch avoids:

```text
chat bubbles
assistant avatar answering
infinite conversation stream
mystical black/purple fortune UI
tarot/crystal symbolism
```

This should remain a hard design rule.

### TrustBar Placement

TrustBar appears at the top of the Result section.

This is correct.

Trust information should be visible before the user reads the result.

### Compact Chart Signals

The Chart Structure Summary uses compact tags:

```text
Day Master
Structure
Peer vs Wealth
Flow
Season
```

This matches the V19 rule:

```text
chart summary = scannable signals, not explanation paragraphs
```

### Bounded Evidence

Evidence shows:

```text
2 visible cards
view all action
source
confidence
details disclosure
```

This is correct for mobile-first readability.

## 3. Required Corrections Before Implementation

### Correction 1: Avoid Unverified Blockchain Language

The sketch includes:

```text
verifiable on-chain
```

This must not be used unless V19 actually writes replay or audit proof to a blockchain.

Preferred copy:

```text
This result is replayable and verifiable. Redacted for privacy.
```

Allowed technical anchors:

```text
prediction_id
contract_hash
verifier_status
schema_version
mapping_version
engine_version
audit_event_id
```

Forbidden unless actually implemented:

```text
on-chain
blockchain verified
decentralized proof
```

### Correction 2: Result Summary Must Stay Non-narrative

The visual direction is good:

```text
Income Stability: LOW
Volatility: High
```

Implementation must keep this as bounded fields.

Do not allow:

```text
Because your chart has X, your future income will Y...
```

Result copy must remain:

```text
short
bounded
contract-backed
evidence-linked
```

### Correction 3: Evidence Text Needs Tight Limits

The sketch uses short evidence paragraphs.

Implementation should enforce:

```text
title: one line
source: one line
summary: max 2 lines on mobile
details: collapsed by default
```

This prevents Evidence cards from becoming hidden narrative containers.

### Correction 4: Theme Selection Must Not Recenter Wealth

The visible enabled themes are:

```text
Wealth Structure
Income Stability
Risk & Opportunity
```

This is acceptable for the first controlled prediction theme.

But copy and IA must still communicate:

```text
V19 is a Bazi reasoning system.
Current phase supports a controlled wealth-related theme.
```

Do not rename the product or page around wealth.

### Correction 5: Mobile Bottom Navigation Should Be Role-safe

The mobile sketch shows:

```text
Home
History
Replay
Profile
```

This is acceptable for user surface.

But practitioner/admin entries must not appear in normal user bottom nav.

Admin and practitioner surfaces should remain guarded routes.

## 4. Visual Direction to Adopt

### Layout

Use the sketch as the base layout pattern:

```text
mobile: single-column card stack
desktop: left workflow rail + right result workspace
```

Mobile:

```text
System Contract
Birth Input
Chart Structure
Inference collapsed
Theme Selection
Result
Evidence
Replay
Bottom Nav
```

Desktop:

```text
top navigation
system contract strip
left column: input / chart / inference / theme
right column: result / evidence / replay
```

### Color

Adopt:

```text
warm paper background
ink text
mineral blue primary
slate structure
soft amber uncertainty
verified green trust
muted red risk
```

Avoid:

```text
purple mysticism
dark occult background
neon gradient excess
generic SaaS gray-only dashboard
```

### Density

The sketch density is acceptable on desktop.

Mobile implementation should be slightly more breathable than the sketch:

```text
larger section spacing
larger tap targets
fewer visible details per card
more collapse controls
```

## 5. Component Mapping

The sketch maps cleanly to V19 components:

```text
Top header -> ProductHeader / SystemContractHeader
Intro strip -> CurrentScopePanel + PrimaryActionPanel
Birth input card -> BirthInputPanel
Chart tags -> ChartStructureSummary + SignalTag
Inference collapsed card -> InferenceSignalList
Theme cards -> ThemeSelector + StateGate
Result panel -> ResultCard
Trust row -> TrustBar
Evidence cards -> EvidenceCardList
Replay section -> ReplayCard
Bottom nav -> MobileUserNav
```

## 6. Prototype Acceptance Rules

The first V19 UI prototype based on this sketch is accepted when:

```text
1. It does not reuse V18 UI components.
2. It renders mocked V19 state machine data only.
3. It preserves chart -> inference -> result -> evidence -> replay order.
4. It shows TrustBar before result content.
5. It keeps Inference collapsed by default.
6. It shows disabled unsupported themes with reasons.
7. It shows 2 evidence cards by default.
8. It avoids chat bubbles and mystical visuals.
9. It does not mention on-chain verification unless implemented.
10. It is readable on mobile first.
```

## 7. Next Step

The correct next step is:

```text
V19 UI Prototype v1
```

Scope:

```text
static frontend prototype
mocked V19 Oracle state
mobile-first /oracle page
desktop layout following the sketch
no backend API
no V18 UI reuse
no production prediction
```
