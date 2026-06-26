# V30 Hidden Factors and Dialogue Discovery

Updated: 2026-06-13

## Runtime Rule

Hidden attributes and hidden amplification factors are not treated as directly computable conclusions.

They must be discovered through dialogue signals:

- boundary years
- special event years
- repeated user states
- strength changes under luck/flow context
- user-confirmed contradictions between chart expectation and lived experience

The runtime may create hypotheses and probes, but it must not finalize a hidden factor without user feedback.

## Current Mainline Slice

```text
hidden stem evidence
-> HiddenFactorProbe
-> q_v30_hidden_factor_boundary_discovery
-> recommendation score
-> HiddenFactorState
-> LatentBaziProfile
-> runtime trace/admin diagnostics
```

Current acceptance:

- The probe status is `needs_dialogue`.
- The boundary is `hypothesis_only_not_deterministic_chart_conclusion`.
- The runtime question asks for special-year/state feedback before treating hidden stems as amplifiers.
- The UI recommendation marks the topic as `hidden_factor` and the stage as `dialogue_discovery`.
- Synthetic smoke validates this as a required case.
- `HiddenFactorState` now persists dialogue-derived special years, repeated states, feedback IDs, and amplifier strength.
- The API exposes V30-only hidden-factor feedback/state endpoints under `/api/v30/readings/{reading_id}/hidden-factor/*`.
- Postgres stores hidden-factor state in `v30_hidden_factor_states`.
- Synthetic gradient validates that calibrated special-year + repeated-state feedback becomes `amplifier_candidate` without mutating chart facts.
- Persisted state now rehydrates runtime presentation and admin trace.
- Persisted `amplifier_candidate` state conditions question recommendation reasons, question graph policy notes, and answer context role contract.
- Event-year modeling is active: year-only and repeated-state-only feedback stay in `dialogue_in_progress`; year + state alignment is the positive amplifier-candidate path.
- Conflicting feedback has priority over positive merge and downgrades candidate strength.
- Synthetic validation covers year-only, state-only, year+state, multi-year+state, candidate-then-denial, and pure-denial cases.
- Training emits `v30.training_signal.hidden_factor_event_alignment` with state coverage, average strength, candidate/conflict/denial counts, event-year coverage, and repeated-state coverage.
- HF-R1.1 adds `v30.latent_bazi_profile.v1` as the chart-bound consumption layer over `HiddenFactorState`.
- `latent_bazi_profile` links each structured state to `reading_id`, `context_id`, day master, natal pillars, domains, ten-god families, dynamic paths, RBD claims, evidence ids, source feedback ids, and source question ids.
- Customer-facing language should say “校准线索/背景校准线索,” not the internal term “隐藏因子.”

## 2026-06-13 Review

Conclusion:

- The old flow was not completely isolated.
- It was still only half-integrated because it mainly influenced question strategy and diagnostics.
- It did not expose a stable, chart-bound attribute profile that RBD/M3/M5/M6 could consume.

Refactor decision:

- Keep `HiddenFactorState` as the persisted compatibility state.
- Add `LatentBaziProfile` as the runtime profile used by downstream modules.
- Continue to block chart-fact mutation.
- Next task is RBD consumption gate: RBD may use the profile to calibrate route/claim priority, but not to create deterministic facts.

Updated: 2026-05-21

## Purpose

Some Bazi-relevant attributes cannot be calculated from the chart alone.

V30 needs a design for hidden attributes and hidden amplification factors that can only be inferred through dialogue, boundary checks, special-year events, and current state feedback.

This layer must be separate from deterministic chart facts.

## Core Principle

Hidden factors are not chart facts.

They are dialogue-discovered hypotheses.

They may influence:

- Question recommendation.
- Mainline confidence.
- Portrait nuance.
- Answer boundaries.
- Follow-up strategy.
- Training signals.

They may not:

- Mutate `ChartContext`.
- Rewrite pillars, ten gods, or structure facts.
- Become a hard verdict without evidence.
- Override deterministic evidence.

## Why This Exists

Two people with similar charts can diverge because of hidden amplifiers:

- Environment.
- Family structure.
- Education path.
- Health baseline.
- Risk exposure.
- Major past events.
- Relationship status.
- Career industry.
- Financial leverage.
- Migration or location change.
- Psychological state.
- Support system.

These factors can amplify, suppress, delay, or redirect Bazi structures.

The chart can suggest where to ask. It cannot directly know the answer.

## Hidden Factor Model

### HiddenAttribute

Represents a user-specific state not directly computable from the chart.

Required fields:

```text
attribute_id
domain
label
status
evidence_sources
confidence
last_confirmed_at
boundary
```

Allowed `status`:

```text
unknown
hypothesized
user_confirmed
user_denied
conflicting
expired
```

### AmplificationFactor

Represents a factor that changes the strength, timing, or expression of a chart structure.

Required fields:

```text
factor_id
domain
target_structure_id
amplifies
suppresses
shifts_timing
confidence
source_attribute_ids
boundary
```

Examples:

- Career industry amplifies authority/wealth paths.
- Family pressure amplifies resource/authority pressure.
- Health baseline suppresses output/wealth activation.
- Migration amplifies flow-year branch interaction.
- Financial leverage amplifies wealth volatility.

## Dialogue Discovery Flow

```text
StructureState
-> MainlineState
-> HiddenFactorHypothesis[]
-> BoundaryQuestion[]
-> UserAnswer
-> HiddenFactorFeedback
-> HiddenFactorState
-> Mainline/Question/Answer adjustment
```

## Current HiddenFactorState Contract

```text
state_id
reading_id
context_id
status
amplifier_strength
amplifier_candidate
special_event_years
repeated_states
event_year_signal
repeated_state_signal
alignment_score
time_layer_alignment_score
feedback_ids
denied_feedback_ids
conflict_feedback_ids
evidence_ids
next_feedback_needed
boundary
stale_after_days
expires_at
updated_at
```

`event_year_signal`:

```text
years
year_count
is_multi_year
bound_to_time_context
context_bindings
```

`repeated_state_signal`:

```text
states
state_count
domains
is_narrow_domain_repeat
```

State statuses:

```text
not_applicable
needs_dialogue
dialogue_in_progress
feedback_calibrated
amplifier_candidate
user_denied
conflicting
expired
```

Feedback statuses:

```text
affirmed
denied
conflicting
expired
```

Current behavior:

- Special year + repeated state -> `amplifier_candidate`.
- Special year only -> `dialogue_in_progress`.
- Repeated state only -> `dialogue_in_progress`.
- User denial without positive evidence -> `user_denied`.
- User denial after a candidate state -> `conflicting`.
- Multi-year + narrow repeated state raises alignment and strength, capped as a feedback-conditioned hypothesis.
- Expired positive state -> `expired`, `amplifier_candidate=false`, reduced strength, and `refresh_hidden_factor_feedback` in `next_feedback_needed`.
- Hidden factors remain `hidden_factor_state_feedback_hypothesis_not_chart_fact`; they never mutate chart facts.

Storage:

```text
local_json -> .runtime/hidden_factor_states/
postgres -> v30_hidden_factor_states
```

## Question Types

Hidden factor discovery should use question types, not templates.

### Boundary Question

Purpose: distinguish whether a structure is active, blocked, or redirected.

Example intent:

```text
assess_resource_support_real_world
```

### Special-Year Question

Purpose: test whether time-layer activation corresponds to lived events.

Example intent:

```text
check_flow_year_activation_around_specific_year
```

### State Question

Purpose: understand current condition or pressure.

Example intent:

```text
check_current_career_pressure_state
```

### Domain Confirmation Question

Purpose: confirm which life domain is carrying the structure.

Example intent:

```text
confirm_wealth_channel_domain
```

## Special-Year Discovery

V30 can identify years worth asking about from:

- Luck cycle transition.
- Annual branch clash/combine.
- Hidden stem activation.
- Structure path volatility.
- Mainline timing sensitivity.

But V30 must phrase them as confirmation questions, not claims.

Correct stance:

```text
This year is structurally worth checking. Did something around career/relationship/family/health shift then?
```

Incorrect stance:

```text
That year definitely caused a specific event.
```

## Runtime Placement

Hidden factors belong after deterministic reasoning and before final answer/presentation:

```text
ChartContext
-> FeatureEvidence
-> StructureState
-> MainlineState
-> HiddenFactorHypothesis
-> QuestionRecommendation
-> UserAnswer
-> HiddenFactorState
-> AnswerContext
```

## Interaction With Question Intelligence

Question recommendation should use hidden factors in two ways:

1. Discover unknown amplifiers.
2. Use confirmed amplifiers to choose better next questions.

Guest/user views still require bound anchors.

Hidden factor questions must bind to:

- Current chart context.
- Structure or mainline.
- Specific missing requirement.
- Specific expected information gain.

## Interaction With LLM

LLM may:

- Render boundary questions naturally.
- Explain why a confirmation question matters.
- Use confirmed hidden factors in answer tone and emphasis.
- Summarize user-confirmed state.

LLM may not:

- Treat hypothesized hidden factors as confirmed.
- Invent hidden factors from chart alone.
- Convert a special-year question into a definite prediction.

## Validation

Synthetic validation should include hidden factor cases:

### Positive Confirmation

User confirms a factor; answer and next question adapt.

### Denial

User denies a factor; recommendation must downrank that hypothesis.

### Conflict

User gives conflicting answers; system must mark factor as conflicting.

### Expiration

Old state becomes stale; system must ask again or reduce confidence.

### Special-Year Boundary

System asks about a structurally relevant year without making a deterministic event claim.

Current synthetic cases:

- `hidden_factor_event_year_state_001`: year + state -> `amplifier_candidate`.
- `hidden_factor_multi_year_state_001`: multi-year + state -> stronger `amplifier_candidate`.
- `hidden_factor_year_only_state_001`: year only -> `dialogue_in_progress`.
- `hidden_factor_repeated_state_only_001`: state only -> `dialogue_in_progress`.
- `hidden_factor_denied_001`: denial without positive evidence -> `user_denied`.
- `hidden_factor_conflict_after_candidate_001`: denial after candidate -> `conflicting`.

## Training

Hidden factor training should tune:

- Which boundary question to ask.
- Which year to ask about.
- How much confirmed factors influence ranking.
- When stale factors expire.
- How to handle denial/conflict.
- How much event-year/repeated-state alignment should affect amplifier confidence.

Policy family:

```text
hidden_factor_policy
```

Auto-apply requires:

- Synthetic dialogue validation.
- Role visibility validation.
- Answer drift validation.
- Optional 518K sample distribution check for question frequency.

## Storage

Hidden factors are user/session state, not chart facts.

Suggested storage:

```text
v30_feedback_events
v30_runtime_traces
v30_readings
```

Potential future table:

```text
v30_hidden_factor_states
```

Redis key:

```text
v30:{env}:hidden_factor:{reading_id}
```

## Acceptance

- Hidden factors are modeled separately from chart facts.
- User confirmation can update hidden factor state.
- Denial/conflict can reduce or block hypotheses.
- Special-year questions are framed as confirmation, not prediction.
- LLM never treats unconfirmed factors as facts.
- Question intelligence can use hidden factors without losing anchor binding.
