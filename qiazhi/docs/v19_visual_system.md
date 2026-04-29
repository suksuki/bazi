# V19 Visual System Direction v1

V19 visual design is about trust in a reasoning system.

It is not mystical decoration.

It is not a chat interface.

It is not a data dashboard for experts only.

The visual system must help users understand:

```text
chart structure -> inference signals -> verified result
```

## 1. Design Principles

### Calm

The interface should feel steady, precise, and readable.

Avoid emotional overclaiming.

Avoid sensational fortune-telling aesthetics.

### Structured

The page should visibly separate:

```text
input
chart structure
inference signals
result
evidence
feedback
replay
```

Users should always know what layer they are looking at.

### Trust-first

Trust cues should be visible before decorative cues.

Important trust anchors:

```text
verifier status
confidence
evidence count
contract hash
schema version
mapping version
replay availability
```

### Non-mystical

Do not use:

```text
fortune-telling booth visuals
tarot aesthetics
neon occult symbols
purple mysticism defaults
overly smoky backgrounds
```

V19 may feel culturally aware, but it must not feel superstitious or theatrical.

### Non-chat-like

V19 is a structured reasoning interface, not a chatbot.

Do not make the main result look like:

```text
assistant bubble
user bubble
infinite chat stream
raw conversational answer
```

Questions may be entered conversationally, but results must be structured.

## 2. Cognitive Load Rules

### Oracle first screen

The first screen must communicate:

```text
what this system is
what can be asked now
what to do next
```

Visual order:

```text
System identity
Supported scope
Primary CTA
```

### Chart before inference

After birth input:

```text
show simplified Chart Structure Summary immediately
keep Inference Summary collapsed by default
```

Reason:

```text
users should first see the chart
then inspect reasoning
```

### Theme selection constraint

Theme selection must be constrained by UI state, not just copy.

Current selectable themes:

```text
wealth structure
income stability
risk and opportunity
```

Disabled themes:

```text
career
relationship
health
full chart general reading
```

Disabled themes must show a short reason:

```text
not yet supported by reviewed rules
```

## 3. Color System

V19 should use a restrained, high-legibility palette.

The recommended visual direction:

```text
warm paper / ink / mineral blue / soft amber / verified green
```

Avoid dark purple default.

Avoid pure black-on-neon sci-fi.

### Tokens

```text
background.base        warm off-white or deep ink
background.surface     calm card surface
background.subtle      section background
text.primary           high-contrast ink
text.secondary         muted slate
text.meta              low-emphasis gray
border.default         soft neutral
border.strong          structured divider
```

### Primary: trust

Use for:

```text
primary CTA
verified anchors
selected state
important navigation
```

Suggested direction:

```text
mineral blue
```

### Secondary: structure

Use for:

```text
chart structure
inference signal tags
layer labels
section dividers
```

Suggested direction:

```text
graphite / slate / muted teal
```

### Warning: uncertainty

Use for:

```text
uncertainty
unsupported scope
requires review
drift warning
```

Suggested direction:

```text
soft amber
```

### Success: verification

Use for:

```text
verifier passed
contract checked
replay available
feedback recorded
```

Suggested direction:

```text
verified green
```

### Risk

Use sparingly for:

```text
high risk
rule drift
verifier failure
invalid state
```

Suggested direction:

```text
muted red
```

## 4. Typography

Typography should clarify hierarchy, not add personality noise.

### Hierarchy

```text
Display title
Page title
Section title
Signal label
Evidence text
Meta text
Technical id
```

### Display title

Use for:

```text
home hero
major page identity
```

Tone:

```text
clear
restrained
not mystical
```

### Section title

Use for:

```text
Chart Structure
Inference Signals
Result
Evidence
Replay
```

Section titles should be short.

### Signal label

Use for bounded values:

```text
day_master_state
structural_stability
peer_vs_wealth
weak_signal
```

Signal labels should be compact and scannable.

### Evidence text

Evidence text should support 2 to 3 line previews.

Long evidence should be expandable.

### Meta text

Use for:

```text
contract hash
schema version
mapping version
created_at
review status
```

Meta text must wrap safely.

### Multilingual compatibility

Must support:

```text
zh
en
ko
```

Rules:

```text
never rely on fixed-width labels
allow button text to wrap or grow
avoid ultra-condensed layouts
test Korean line length
test English phrase wrapping
```

## 5. Component Visual Rules

## Result Card

Purpose:

```text
show the verified result without becoming narrative-heavy
```

Required parts:

```text
result summary
confidence badge
verifier badge
risk / uncertainty mini row
primary action: feedback
secondary action: replay
```

Mobile:

```text
single card
summary first
badges below summary
actions full-width or two-column
```

Desktop:

```text
result card can sit beside evidence panel
```

## Evidence Card

Purpose:

```text
explain why a result exists
```

Required parts:

```text
evidence label
source layer
confidence or relevance when available
short reason
expand details
```

Mobile:

```text
show 2 evidence cards by default
collapse the rest
no dense tables
```

## Replay Card

Purpose:

```text
make verification portable
```

Required parts:

```text
prediction_id
contract hash
verifier status
engine version
inference schema version
mapping registry version
redaction notice
```

Technical ids must wrap.

## Chip

Use for:

```text
recommended questions
theme selection
supported scopes
filter controls
```

Rules:

```text
large enough for touch
horizontal scroll allowed only for chip rows
selected state must be obvious
disabled state must explain why
```

## Signal Tag

Use for:

```text
day_master_state
structural_stability
internal_conflict
uncertainty_source
```

Rules:

```text
bounded value only
no prose
source available on expand
color indicates category, not fortune quality
```

## Badge

Use for:

```text
verifier passed
confidence
reviewed
draft
deprecated
drift warning
```

Rules:

```text
badges must not look like final fate judgments
badges indicate system state
```

## Boundary Card

Use for unsupported questions.

Required parts:

```text
unsupported reason
supported alternatives
one-click rewrite action
```

Mobile:

```text
short copy
alternative chips
primary rewrite button
```

## 6. Mobile-first Spacing

### Layout

```text
page padding: 16px minimum
card padding: 16px to 20px
section gap: 20px to 28px
card gap: 12px to 16px
```

### Touch area

```text
minimum tap height: 44px
preferred primary button height: 48px
chip height: 36px minimum
icon-only buttons must include accessible label
```

### Vertical rhythm

Mobile pages should use:

```text
short section
short action
short feedback loop
```

Avoid:

```text
long unbroken paragraphs
stacked technical panels before user sees result
wide grids
tables
```

## 7. Page-specific Visual Direction

### `/`

Visual mood:

```text
clear introduction
trust architecture
professional but approachable
```

Avoid:

```text
landing page hype
mystical visual overload
wealth demo framing
```

### `/oracle`

Visual mood:

```text
guided structured workspace
```

Critical visual order:

```text
first screen contract
birth input
chart structure summary
collapsed inference summary
theme selection
result
evidence
feedback
replay
```

### `/replay`

Visual mood:

```text
verification document
```

Critical visual anchors:

```text
redaction state
verifier status
contract hash
engine/schema/mapping versions
evidence summary
```

### `/practitioner`

Visual mood:

```text
review workspace
```

Use denser information than user pages, but still avoid raw table overload.

### `/admin`

Visual mood:

```text
governance console
```

Admin actions must look deliberate, not casual.

Activation controls need strong risk framing.

## 8. Prohibited Visual Patterns

Do not use:

```text
mystical purple-on-black default
tarot / crystal / occult motifs
chat bubble result stream
raw LLM answer block as primary output
dense technical table on mobile
unbounded text cards
horizontal page scroll
tiny chip buttons
score-first result display
fortune-good / fortune-bad color semantics
```

## 9. Implementation Boundary

This document defines visual direction only.

It does not implement components.

It does not connect APIs.

It does not modify V18 UI.

It does not modify V19 Core, Inference, Mapping Registry, or Synthetic Validation.

Next step:

```text
V19 component architecture
```

Then:

```text
V19 UI implementation prototype
```
