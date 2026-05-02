# V20 Prestart V19 Deep Review

Date: 2026-05-01
Audience: Bazi analyst, system architect, V20 implementation owner
Status: final pre-V20 architecture review with analyst/architect feedback integrated

## Executive Decision

V19 has reached the point where it is more valuable as a reference system than as the next implementation base.

The V19 work successfully discovered the right product and reasoning shape:

```text
chart facts
-> deterministic core / rule graph
-> bazi feature spine
-> portrait projection / question routing / evidence pack
-> answer boundary
-> synthetic validation / silent evolution
```

But it also carries the full exploration history from P10 to P84. The code and documents now mix production runtime, historical compatibility, lab governance, synthetic evaluation, UI experiments, manifest contracts, and future algorithm slots in the same tree. V20 should keep V19 as the archive and knowledge/reference base, then rebuild a smaller system around the final architecture discovered in P84.

## V19 System Shape

### Runtime Chain

Current runtime entrypoints:

- `v19.server`
- `v19.agent.structure`
- `v19.core.system`
- `v19.rule_graph_runtime_context`
- `v19.rule_graph_orchestrator`
- `v19.bazi_features`
- `v19.bazi_guided_questions`
- `v19.guided_evidence_pack`
- `v19.llm`
- `v19.frontend`

Current runtime flow:

```text
birth input
-> chart / luck / flow structure
-> core feature / strength / structure / inference
-> knowledge context + Rule DB signals
-> Rule Graph runtime route pack
-> structure portrait
-> bazi_feature_layer
-> guided question context
-> guided answer evidence pack
-> deterministic answer sections / optional LLM prompt context
-> UI profile summary and answer surface
```

The best V19 architectural result is P84: `bazi_feature_layer` becomes the common language between knowledge, rules, portrait, recommendations, answer evidence, and feedback.

### Lab / Governance / Evolution Chain

Current lab and evolution entrypoints:

- `v19.lab_interfaces`
- `v19.bazi_rule_db`
- `v19.synthetic_validation.*`
- `docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json`

Current governance flow:

```text
knowledge draft / reviewed unit
-> rule proposal / question proposal
-> validation run
-> review packet
-> controlled approval
-> version record
-> Rule DB candidate
-> synthetic gate / active replay scoring / canary
-> runtime route-only or evidence-only use
```

Current self-evolution flow:

```text
synthetic cases
-> framework audit
-> dry-run active replay scoring
-> canary trial
-> scorecard
-> silent training ledger
-> silent eval queue
-> tuning proposal
-> smart approval gate
```

The important boundary is stable: learning can create reports, proposals, queues, eval rows, and calibration signals. It must not directly mutate core rule truth, chart facts, user-facing conclusions, or production rule activation.

## Module Review

### 1. Chart / Core

Key files:

- `v19/agent/structure.py`
- `v19/core/chart.py`
- `v19/core/features.py`
- `v19/core/strength.py`
- `v19/core/structure.py`
- `v19/core/inference.py`
- `v19/core/system.py`
- `v19/core/inference_schema.py`

Strengths:

- Clear deterministic boundary for chart facts, ten gods, elements, strength, structure, and core inference.
- Guardrails consistently say core outputs are structural signals, not domain conclusions.
- Existing schema validation gives V20 a good pattern for contract-first core outputs.

Problems:

- `agent.structure` still combines input parsing, lunar conversion, chart construction, flow year, luck cycles, relations, and fallback agent reply.
- Some core computation is newer and cleaner than surrounding runtime, but is not yet the actual center of all downstream modules.
- V17/V18 algorithm assets are referenced through comparison and migration notes, but not cleanly lifted into the V19 core.

V20 recommendation:

- Make `core/` the first-class root and keep it pure.
- Split calendar, chart, relations, ten gods, strength, and time context into small typed modules.
- Migrate only stable pure-function assets from legacy review first: stem/branch constants, hidden stems, ten-god mapping, branch relation geometry, three harmony/meeting geometry, vault existence facts.

### 2. Knowledge / Rule DB / Rule Graph

Key files:

- `v19/knowledge/*`
- `v19/knowledge_store.py`
- `v19/bazi_rule_db.py`
- `v19/rule_graph_orchestrator.py`
- `v19/rule_graph_runtime_context.py`

Strengths:

- V19 has a strong knowledge-to-rule governance shape.
- Rule Graph is the right runtime abstraction: chart graph + question intent + rule candidate retrieval + deterministic scoring + arbitration.
- `future_model_slots` already reserve GNN/RL in the correct place: rerank / path embedding / question policy only.

Problems:

- `bazi_rule_db.py` is too large and blends state storage, ingestion, smart gate, adapter facts, matching, scoring, and signal rendering.
- Rule Graph candidate scoring is deterministic but mostly hand-tuned; this is acceptable for V19, but V20 should expose weight config and evaluation deltas.
- The Rule Graph and Feature Spine are still adjacent systems, not one unified graph-feature pipeline.

V20 recommendation:

- Use a typed `RuleCandidate`, `RulePath`, `FeatureCandidate`, and `EvidenceRef`.
- Separate retrieval, scoring, arbitration, answer audit, and active iteration governance.
- Introduce a `ranking/` layer that can support deterministic weights now and learning-to-rank active replay mode later.

### 3. Feature Spine

Key files:

- `v19/bazi_features.py`
- `docs/v19/V19_P84_BAZI_FEATURE_SPINE.md`

Strengths:

- This is the best V19 abstraction.
- It unifies rules, knowledge, portrait projection, recommended questions, answer evidence, and feedback.
- It finally demotes portrait from a parallel driver to a feature projection and calibration surface.

Problems:

- Current `FEATURE_PROFILES` are still tightly derived from `structure_portrait` option ids.
- Feature generation is not yet a first-class compiler from chart facts + rule paths + knowledge units.
- The feature schema is a dict convention, not a typed model.

V20 recommendation:

- Make `BaziFeature` the central contract from day one.
- Build feature candidates from deterministic core, rule graph paths, knowledge units, and feedback as separate sources.
- Give each feature explicit fields: `id`, `domain`, `source_layers`, `evidence_refs`, `confidence`, `readiness`, `boundary`, `question_hooks`, `answer_hooks`, `calibration_state`.

### 4. Portrait / Calibration

Key files:

- `v19/structure_portrait.py`
- `v19/lab_interfaces.py`
- `docs/v19/V19_P81_*`
- `docs/v19/V19_P82_*`
- `docs/v19/V19_P83_*`

Strengths:

- Portrait became a useful UI and calibration object.
- V19 correctly removed `structure_portrait.question_bias` from the runtime main chain in P84.
- Calibration feedback is profile-scoped and does not mutate rules.

Problems:

- `structure_portrait.py` still contains old question bias compatibility, label ontology, option model, feedback application, Bayesian-style confidence, calibration plan, and prompt context in one module.
- Portrait was necessary for discovery, but V20 should not rebuild it as a separate reasoning layer.

V20 recommendation:

- Replace `structure_portrait` with `interaction/portrait_projection.py`.
- Portrait options should be generated from `BaziFeature` and write back only to `FeatureCalibrationSignal`.
- Do not keep portrait question bias at all.

### 5. Guided Questions / Answer / Evidence

Key files:

- `v19/bazi_guided_questions.py`
- `v19/guided_evidence_pack.py`
- `v19/agent/renderers.py`
- `v19/llm.py`

Strengths:

- Recommended questions are chart-specific and now feature-spine driven.
- Guided answers carry evidence packs and answer boundaries.
- Deterministic answer sections make safety testable.

Problems:

- `bazi_guided_questions.py` is a 4k-line mixed module: question registry, signal extraction, personalization, ranking, answer composition, multilingual labels, feature/portrait sections, rule matching, and helpers.
- Answer logic and question ranking are too entangled.
- LLM prompt context is safer than earlier versions, but still receives a large mixed payload.

V20 recommendation:

- Split into:
  - `interaction/question_catalog.py`
  - `interaction/question_ranker.py`
  - `answer/evidence_pack.py`
  - `answer/composer.py`
  - `answer/prompt_context.py`
- Make every answer consume `BaziFeature[] + EvidenceRef[] + BoundaryPolicy`.
- Keep deterministic answer composition as the default; let LLM rewrite only verified answer plans.

### 6. Frontend / Product Surface

Key files:

- `v19/frontend/oracle.html`
- `v19/frontend/assets/oracle.js`
- `v19/frontend/assets/styles.css`
- `v19/frontend/lab.html`
- `v19/frontend/assets/admin.js`

Strengths:

- V19 UI now surfaces feature chips, portrait projection, question recommendations, evidence summary, profile state, and lab/admin tools.
- It validates that feature spine can be made visible to users.

Problems:

- UI has grown alongside backend experiments and mirrors too many internal concepts.
- Lab/admin/product surfaces are not cleanly separated.

V20 recommendation:

- Build three surfaces separately:
  - user oracle surface
  - analyst review surface
  - admin/evolution lab surface
- User surface should display features, evidence boundaries, and questions; not P-stage internals.

### 7. Synthetic Validation / Evolution

Key files:

- `v19/synthetic_validation/guided_cases.py`
- `v19/synthetic_validation/guided_runner.py`
- `v19/synthetic_validation/rule_conversion_validation.py`
- `v19/synthetic_validation/rule_db_readiness.py`
- `v19/synthetic_validation/silent_evolution.py`
- `v19/synthetic_validation/silent_training_ledger.py`
- `v19/synthetic_validation/silent_eval_queue.py`
- `v19/synthetic_validation/structure_portrait_matrix.py`
- `v19/synthetic_validation/mainline_completion_audit.py`

Strengths:

- This is one of V19's most valuable assets.
- Synthetic cases, active replay scoring, smart gate, canary, and silent eval queue form a real governed evolution workflow.
- The system consistently checks forbidden text, answer mutation, runtime mutation, rule activation, route coverage, and evidence binding.

Problems:

- The validation suite is spread across many P-stage modules.
- Synthetic cases are still partly hand-authored and partly contract fixtures, not a unified dataset format.
- The system has ledgers and queues, but no durable run registry or model/ranking artifact registry.

V20 recommendation:

- Promote synthetic validation into `v20/validation` as a first-class kernel.
- Define one case schema with labels for:
  - expected features
  - forbidden features
  - expected question intents
  - answer boundary requirements
  - evidence refs
  - mutation invariants
- Add regression deltas and artifact snapshots.
- Make every learning/ranking proposal prove itself against this kernel.

## Algorithm Review

### Active V19 Algorithms

1. Deterministic chart and relation extraction.
2. Core feature extraction and strength/structure scoring.
3. Rule Graph deterministic path selection.
4. Condition-model style synthetic evaluation.
5. Feature spine scoring and question bias.
6. Bayesian-style confidence formula in portrait compilation.
7. Contract-based active replay scoring.
8. Auto evaluator scorecard for silent evolution.
9. Smart gate risk routing.

### Reserved / Not Yet Real Algorithms

1. Bayesian scoring: mostly deterministic confidence formulas; not a statistical learner.
2. GNN: reserved for path embedding / rerank only; no model, labels, or training pipeline.
3. RL: reserved for question ordering and dialog policy only; no reward model.
4. Active learning: present in design language, not a runtime selector.
5. Embedding retrieval: not yet formalized in V19.
6. Learning-to-rank: not yet formalized; weights are hand-tuned.

### V20 Algorithm Policy

V20 should introduce advanced algorithms, but only as a governed assistive layer.

Allowed early:

- embedding retrieval for knowledge/rule/synthetic case recall
- deterministic graph algorithms for path coverage and conflict analysis
- Bayesian-style internal calibration for feature confidence
- bounded learning-to-rank in active replay mode for question and path rerank
- clustering/active learning for synthetic coverage gaps and proposal grouping

Delayed:

- GNN path embedding until labeled eval datasets and explanation tools exist
- RL dialog policy until stable reward definitions exist
- neural prediction models for Bazi conclusions

Forbidden in production core:

- black-box core inference
- user feedback directly updating rules
- neural model deciding useful-god, wealth, health, relationship, career, or fortune conclusions
- model-generated chart facts
- automatic production activation from synthetic pass alone

## Architecture Problems To Fix In V20

1. P-stage accumulation.
   V19 documents and code preserve too many historical phases. V20 should use stable domain names, not P-stage names, in runtime code.

2. Oversized modules.
   `bazi_guided_questions.py`, `lab_interfaces.py`, `server.py`, and `bazi_rule_db.py` are too broad.

3. Dict contracts everywhere.
   V19 is flexible but hard to reason about. V20 should use dataclasses or typed schemas at module boundaries.

4. Runtime and lab coupling.
   V19 server exposes runtime, admin, lab, proposal, validation, and evolution APIs in one file.

5. Feature spine is late.
   P84 is the right architecture but arrived after many compatibility layers. V20 should start from it.

6. Synthetic validation is powerful but scattered.
   V20 should make it a central service, not a collection of historical regression modules.

7. Advanced algorithms are only placeholders.
   V20 should implement the first governed algorithm layer, but keep it away from core truth.

## V20 Proposed Architecture

```text
v20/
  core/
    calendar.py
    chart.py
    constants.py
    ten_gods.py
    relations.py
    strength.py
    time_context.py
  features/
    schema.py
    compiler.py
    confidence.py
    boundaries.py
  knowledge/
    schema.py
    loader.py
    retrieval.py
  graph/
    chart_graph.py
    rule_graph.py
    scoring.py
    arbitration.py
  ranking/
    deterministic.py
    active_ltr.py
    calibration.py
  interaction/
    questions.py
    portrait_projection.py
    feedback.py
  answer/
    evidence.py
    plan.py
    composer.py
    prompt_context.py
  llm/
    contracts.py
    prompts.py
    structured_outputs.py
    validators.py
    tasks.py
  validation/
    synthetic_schema.py
    cases.py
    evaluator.py
    active_replay_delta.py
    golden.py
  corpus/
    enumerator.py
    canonical_case.py
    precompute_runner.py
    partition.py
    storage.py
    diff.py
  learning/
    ledger.py
    proposal.py
    active_learning.py
    activation_policy.py
    artifact_registry.py
  api/
    runtime.py
    analyst.py
    lab.py
    admin.py
  frontend/
    oracle/
    analyst/
    admin/
    shared/
```

Boundary refinements from architecture review:

- `core/` only emits `ChartFacts`, `TimeContext`, and `CoreInference`; it must not depend on knowledge, portrait, LLM, ledger, or learning.
- `features/` is the center; `BaziFeature` must be compiled from core signals, rule paths, knowledge refs, and calibration signals, not from portrait options.
- `knowledge/` may use embedding retrieval, but only for recall from reviewed knowledge or sandbox draft pools; embedding cannot bypass evidence-pack gates.
- `answer/` must use `EvidencePack -> AnswerPlan -> deterministic composer -> optional LLM rewrite`.
- `llm/` should become a bounded intelligence layer with typed tasks and validators, not a free-form answer authority.
- `validation/` is a first-class kernel, not a lab appendage.
- `learning/` owns ledger, proposal, artifact registry, and active iteration policy; it may produce candidates, not production truth.
- `api/` must split runtime, analyst, admin, and lab routers from day one.

## Product Continuity Requirements

V20 should be a clean rewrite, not a product reset. These V19 capabilities must be preserved as first-class V20 requirements:

### Multi-User

V20 must retain user/profile separation:

- multiple users
- multiple profiles per user
- profile-scoped birth input and calibration history
- session continuity
- feedback scoped to user/profile/case hash

Runtime inference must not leak one user's profile, feedback, calibration state, or answer history into another user's context.

### Multi-Role

V20 should keep explicit role boundaries:

- guest / anonymous preview
- registered user
- practitioner / analyst
- admin
- system / evaluator

Role boundaries should affect API permissions and UI surfaces:

- users can view their own chart, features, questions, answers, and calibration options
- practitioners can review evidence, annotate features, and confirm/deny projections
- analysts can label synthetic/golden cases and review proposals
- admins can manage knowledge releases, artifact registries, model/ranking configs, and active iteration policys

No role should bypass evidence-pack and answer-boundary requirements.

### Multilingual

V20 must retain multilingual answer and UI capacity:

- Chinese remains the primary authoring and validation language.
- English and Korean surfaces should remain supported as product surfaces.
- Internal ids, rule ids, and debug labels must never leak into any language.
- Multilingual output should be generated from `AnswerPlan` and localized labels, not from free-form LLM inference.

Validation must include forbidden text and internal-term leakage checks per locale.

### Multi-Terminal / Responsive Surfaces

V20 UI must support adaptive use across:

- desktop browser
- mobile browser
- tablet-width layouts
- analyst/admin workbench screens

The UI should not expose V19/P-stage internals to normal users. It should expose:

- feature chips
- evidence boundaries
- recommended questions
- answer plan sections
- portrait projection/calibration options
- confidence wording that is safe for users

Analyst/admin surfaces can expose:

- feature ids
- evidence refs
- synthetic case labels
- corpus coverage reports
- artifact registry and active iteration policy status

### UI Alignment For V20

V20 UI should be redesigned around the new architecture:

```text
Feature Spine
-> Question Suggestions
-> Evidence Pack
-> Answer Plan
-> Calibration / Feedback
```

The first screen should feel like a usable Bazi analysis workspace, not a lab dashboard. Lab/evolution/corpus tooling should be separated into analyst/admin surfaces.

V20 frontend should have shared design primitives for:

- feature chip rows
- evidence source rows
- answer boundary notices
- question cards
- calibration option controls
- role-aware navigation
- locale switching
- responsive panels

The product continuity rule is: V20 may simplify implementation, but it should not regress user/profile/role/language/device support that V19 already proved valuable.

## LLM Role In V20

V19 integrated an OpenAI-compatible / Ollama LLM client and prompt context, but the LLM mostly remained optional:

- connection probe / model list / chat test
- fallback free-form agent reply
- guided-answer rewrite after deterministic answer composition
- draft guided-question proposal helper

This was safe, but underused. V20 should strengthen the LLM role while preserving the V19 charter boundary:

```text
LLM can audit, summarize, plan, explain, localize, draft, and critique.
LLM cannot create chart facts, change core confidence, activate rules, write truth ledgers, or bypass evidence gates.
```

### Runtime LLM Roles

Allowed runtime roles:

- intent clarification: map user language to known question intents, with fallback to deterministic question catalog
- answer-plan explanation: explain a verified `AnswerPlan` in natural language
- evidence summarization: turn evidence refs into user-readable explanation without adding facts
- follow-up handling: identify whether the user asks for clarification, deeper evidence, language change, or a new question
- multilingual localization: rewrite verified answer plans into Chinese, English, or Korean using locale labels and forbidden-text checks
- tone adaptation: make the answer concise, professional, beginner-friendly, or practitioner-facing
- safe uncertainty expression: explain evidence thresholds and unknowns without turning them into probability fortune claims

Runtime LLM output must be contract-checked:

```text
AnswerPlan
-> LLM rewrite candidate
-> forbidden-text scan
-> internal-id leakage scan
-> evidence coverage scan
-> claim support scan
-> fallback to deterministic answer if rejected
```

### Analyst / Lab LLM Roles

Allowed analyst and lab roles:

- failure attribution draft from synthetic/eval failures
- knowledge unit draft extraction from reviewed sources
- rule proposal draft summarization
- synthetic case suggestion for uncovered feature combinations
- corpus cluster explanation and anomaly summary
- evidence packet critique
- answer boundary critique
- translation QA across locales
- analyst review packet summarization

All outputs remain proposals or drafts. Analyst/admin approval is still required for knowledge, rule, feature, ranking, and artifact activation.

### LLM Structured Contracts

V20 should not call the LLM with one large mixed payload. Each LLM task should have:

- task name
- allowed input fields
- required output schema
- forbidden output fields
- evidence refs that can be cited
- locale
- risk level
- validator
- fallback behavior

Initial LLM task contracts:

```text
intent_classification
answer_plan_rewrite
evidence_summary
clarifying_question_generation
knowledge_draft_extraction
synthetic_case_proposal
eval_failure_attribution
corpus_cluster_summary
multilingual_localization
```

### LLM Guardrails

V20 LLM guardrails:

- no chart fact creation
- no hidden-stem, ten-god, relation, or calendar calculation by LLM
- no rule activation
- no feature confidence mutation
- no corpus label mutation
- no direct user-feedback-to-rule update
- no unsupported conclusion
- no fortune, health, relationship, wealth, career event prediction
- no internal ids in user-facing answer
- no source-free knowledge claim

### LLM Evaluation

LLM behavior must enter the same validation kernel:

- answer rewrite pass/fail
- locale leakage checks
- hallucinated claim checks
- evidence coverage checks
- forbidden text checks
- deterministic fallback rate
- latency and timeout metrics
- rejection reason distribution

LLM artifacts should be versioned:

```text
prompt_contract_version
model_id
provider
temperature
input_schema_version
validator_version
eval_report_id
decision_record
```

### V20 LLM Policy

V20 should make LLM more useful, not more authoritative.

The LLM's strongest V20 role is as a bounded co-analyst:

```text
structured system generates facts, features, evidence, and boundaries
LLM explains, localizes, critiques, and proposes
validators decide whether the LLM output is usable
ledger records every accepted or rejected LLM artifact
```

## Deep Learning And Full-Corpus Strategy

The user proposed an important V20 direction: if the relevant Bazi structure space is around 518K cases, V20 could precompute and profile every case, then use that corpus as a learning and self-evolution substrate.

This is valuable and should be designed into V20. The correct framing is:

```text
full-corpus structural precompute
-> feature snapshot corpus
-> coverage map / diff map
-> representation learning / embedding
-> active rerank / calibration / proposal generation
-> validation and active iteration policy
```

It is not:

```text
full-corpus destiny truth table
-> black-box fortune model
-> automatic conclusion engine
```

### Corpus Scale Note

The exact count needs definition:

- Pure four-pillar ganzhi combinations are `60^4 = 12,960,000`.
- A 120-year real-time hour-slot corpus is roughly `120 * 365 * 12 = 525,600`, close to the user's 518K estimate.
- These are different corpora. V20 should support both concepts:
  - `structural_combination_space`
  - `calendar_hour_slot_space`

The first covers symbolic combinations. The second covers a practical date/time range and calendar assumptions.

### What The Corpus Should Store

Each precomputed case may store:

```text
case_id
canonical chart facts
core inference signals
chart graph snapshot
rule path candidates
bazi features
evidence refs
question candidates
answer plan coverage
boundary flags
embeddings / graph features / learned artifact refs
```

Each layer must carry versions and hashes:

```text
input_hash
calendar_version
core_version
rule_graph_version
knowledge_release_id
feature_compiler_version
precompute_run_id
artifact_hash
```

This makes full-corpus diff possible when a rule, feature compiler, calendar assumption, or knowledge release changes.

### What The Corpus Must Not Store As Truth

- hard fortune conclusions
- wealth event outcomes
- health or relationship outcomes
- fixed useful-god / unfavorable-god verdicts
- model-generated chart facts
- unreviewed answer text as labels
- user feedback as rule truth

The corpus is a structural map. It can show how the system currently interprets structure; it cannot prove real-world destiny accuracy.

### Learning Uses

Allowed learning uses:

- embedding retrieval for similar charts, knowledge units, rules, and synthetic cases
- self-supervised representation learning from chart facts and feature co-occurrence
- graph embedding or GNN for path similarity, coverage gaps, and rerank candidates
- learning-to-rank active replay reports for questions and rule paths
- Bayesian-style calibration of feature confidence and uncertainty
- clustering for failure attribution and proposal grouping
- active learning to propose missing synthetic/golden cases

Forbidden learning uses:

- black-box core inference
- model-generated Bazi facts
- neural model deciding useful god, pattern success/failure, wealth, health, relationship, career, or fortune conclusions
- automatic production rule activation
- user feedback directly updating rule truth

### Dataset And Artifact Registry

V20 should create registries before any learned artifact can affect runtime:

```text
DatasetRegistry
- corpus_full_calendar_hour_slots
- corpus_structural_combination_space
- corpus_stratified_sample
- synthetic_golden
- synthetic_mechanism_matrix
- practitioner_benchmark
- user_feedback_active_replay
- negative_boundary_cases

ArtifactRegistry
- precompute_snapshot
- embedding_index
- graph_embedding_model
- ltr_weight_config
- bayesian_calibration_table
- clustering_report
- eval_report
- activation_candidate

RunRegistry
- run_id
- input dataset version
- code version
- config version
- output artifact ids
- metrics
- failures
- blocked actions

DecisionRegistry
- artifact_id
- review status
- approved scope
- production eligibility
- rollback pointer
```

No artifact may enter runtime ranking, retrieval, or calibration without:

```text
dataset_version
code_version
eval_report
decision_record
rollback_policy
```

## V20 Phase Plan

### Phase 0: Blueprint And Contracts

- Write V20 system charter.
- Define `ChartFacts`, `BaziFeature`, `EvidencePack`, `QuestionCandidate`, `AnswerPlan`, `SyntheticCase`.
- Import no V19 runtime code except stable constants and simple pure functions after review.

### Phase 1: Thin Deterministic Mainline

```text
birth input
-> chart facts
-> feature compiler
-> question candidates
-> answer plan
-> evidence pack
-> deterministic answer
```

Goal: small, typed, testable, no lab complexity.

Analyst minimum coverage for Phase 1:

- four-pillar facts: stems, branches, day master, elements, hidden stems, ten-god mapping
- month command / season evidence as strength evidence, not a standalone verdict
- day-master capacity evidence bundle, not a hard strong/weak verdict
- visible and hidden ten-god source layers
- branch relations: harmony, clash, punishment, harm, break, three harmony, three meeting, vault existence
- time layer as trigger/background only, never rewriting natal structure
- useful-god boundary as candidate paths and evidence threshold, not fixed favorable/unfavorable verdict
- pattern as review index only, not success/failure verdict
- wealth as material/path/vault/constrained/volatility features only, not event prediction

### Phase 2: Product Shell And UI Alignment

- Build runtime API with user/profile/session boundaries.
- Add role-aware API router separation for runtime, analyst, admin, and lab.
- Build the V20 user oracle surface around feature spine, questions, evidence, answer plan, and calibration.
- Preserve Chinese, English, and Korean output surfaces through localized labels and answer plans.
- Add responsive desktop/mobile/tablet layouts.
- Add LLM status, fallback state, and answer rewrite provenance to the UI without exposing internal prompts.

### Phase 3: Validation Kernel

- Port P10/P11/P48/P50/P52/P84 invariants into one synthetic schema.
- Add golden case snapshots.
- Add forbidden text and mutation gates.
- Add 24-32 hand-fixed golden cases across calendar boundaries, strength boundaries, ten-god visibility, branch relations, time layer, useful-god boundary, wealth structure, and high-risk domain safety.
- Require each mechanism feature to have positive, negative, time-interference, and hidden/source-layer-interference synthetic cases.
- Add LLM contract validation cases: hallucination, internal-id leakage, unsupported conclusion, locale drift, and fallback behavior.

### Phase 4: Corpus Schema And Stratified Precompute

- Define corpus case schema, snapshot schema, partition strategy, and hash/version policy.
- Start with stratified corpus before full corpus.
- Generate coverage map and diff report, not learned runtime behavior.

### Phase 5: Learning And Calibration

- Add feedback ledger.
- Add feature calibration signals.
- Add Bayesian-style confidence calibration.
- Add active-learning proposals for missing synthetic cases.
- Add LLM-assisted proposal drafting for missing cases and failure attribution, still proposal-only.

### Phase 6: Full-Corpus Dry Run

- Run full calendar-hour-slot corpus or full structural-combination corpus as a dry-run artifact.
- Produce coverage map, feature frequency map, rule-path density, conflict hotspots, and boundary-risk queues.
- Do not promote any learned result automatically.

### Phase 7: Governed Advanced Algorithms

- Add embedding retrieval for knowledge/rule recall.
- Add bounded learning-to-rank active replay mode.
- Add evaluation deltas before any ranking change.
- Add LLM-assisted rerank explanations and reviewer summaries, not LLM-driven ranking decisions.

### Phase 8: GNN / Graph Embedding Research Track

- Only after labeled eval dataset exists.
- Use for path rerank and similarity clustering.
- Never for core fact or conclusion generation.

### Phase 9: Active iteration Gate For Learned Artifacts

- Learned artifacts can enter runtime only through explicit approval, scoped activation, regression pass, and rollback manifest.
- The first acceptable learning artifact should be a transparent `ltr_weight_config` or `bayesian_calibration_table`, not a neural conclusion model.

## Questions For Analyst

1. Which V19 domains must V20 Phase 1 cover: strength, useful-god boundary, wealth, branch relations, time context, pattern, career, relationship, health?
2. Which legacy algorithm assets from `legacy_algorithm_review.md` are domain-safe enough for first migration?
3. Which answer boundaries are non-negotiable for user-facing V20?
4. Which synthetic cases are the minimum golden set before V20 replaces V19 in runtime?
5. What should count as acceptable "confidence" language, and what must stay internal only?

## Questions For Architect

1. Should V20 use dataclasses, Pydantic models, or plain typed dicts at module boundaries?
2. Should API be split into runtime/lab/admin routers from day one?
3. What is the minimal durable ledger needed before learning/ranking experiments?
4. How should embedding retrieval be sandboxed so it cannot bypass reviewed knowledge and evidence pack gates?
5. What is the first acceptable learning artifact: weight config, calibration table, rerank report, or model artifact registry?

## Preliminary Recommendation

Start V20. Do not continue adding layers to V19.

V19 should remain:

- reference implementation
- knowledge and document archive
- regression source
- synthetic case source
- governance pattern source

V20 should be:

- smaller
- typed
- feature-spine-first
- validation-first
- learning-ready
- advanced-algorithm-capable but governance-bounded

## Analyst And Architect Feedback Summary

### Analyst Feedback

The analyst agrees with starting V20, but raises four corrections:

1. Phase 1 cannot be too thin. It must cover core Bazi boundaries: strength evidence, ten-god visibility, hidden stems, branch relations, time context, useful-god evidence gates, and wealth structure as features only.
2. Calendar and chart construction are P0 risk. V20 cannot carry forward approximate jie boundaries or vague luck-cycle assumptions without marking them as assumptions.
3. Wealth should not become the axis of V20. It may appear as feature evidence, but not as event prediction.
4. Full-corpus learning is valuable as structural coverage, not as truth learning.

Minimum golden recommendation:

- 24-32 fixed golden cases.
- Mechanism-level synthetic cases with positive, negative, time interference, and hidden/source-layer interference examples.
- Every answer kind must check forbidden text, internal id leakage, evidence binding, and mutation invariants.

Follow-up analyst feedback adds implementation watchpoints:

1. Core module independence must be enforced, not only documented. `core/` should have strict import boundaries and should not import API, knowledge, learning, UI, LLM, or registry modules.
2. Synthetic validation should become a unified service. Learning, ranking, embedding, calibration, rule changes, and answer changes should all submit proposals to the same validation kernel.
3. Frontend role separation is a product and safety requirement. User, practitioner, analyst, admin, and evaluator surfaces should expose different data and tools by design.
4. Multilingual support must include internal isolation checks. Chinese, English, and Korean outputs all need forbidden-text and internal-id leakage validation.
5. Dataset and artifact versioning are required before learning experiments can matter. `DatasetRegistry`, `ArtifactRegistry`, `RunRegistry`, and `DecisionRegistry` are not optional once V20 introduces corpus precompute, embedding, LTR, Bayesian calibration, or graph learning.
6. Transition safety needs baseline diffing. V20 should compare deterministic baseline outputs against golden cases and V19 reference outputs where useful, then record feature, question, evidence, and answer-plan deltas.
7. Synthetic diversity must be tracked as coverage, not assumed. The validation kernel should report relation coverage, source-layer coverage, time-interference coverage, domain-safety coverage, and forbidden-text coverage.

Terminology correction:

- V20 core should not be described as producing "destiny judgement" or "fortune judgement".
- The safe terms are `structural understanding`, `feature candidate`, `answer boundary`, `answer plan`, and `user-facing answer conclusion`.
- Learned systems may improve retrieval, ranking, calibration, and proposal generation; they must not generate or overwrite core Bazi truth.

### Architect Feedback

The architect agrees with the V19-to-V20 split and recommends tightening implementation policy:

1. Use Pydantic models at API/persistence boundaries and dataclasses for pure core internals.
2. Split runtime, analyst, admin, and lab API routers from day one.
3. Add durable registries for runs, datasets, artifacts, decisions, and rollback.
4. Embedding retrieval may come early, but must only recall reviewed/sandbox candidates and must pass evidence/boundary gates.
5. Introduce advanced algorithms in this order:
   - embedding retrieval
   - Bayesian-style calibration
   - LTR active replay mode
   - GNN / graph embedding research
   - RL dialog policy research

The architect's strongest warning: V20 can learn ranking, retrieval, calibration, and proposal generation; it must not learn or overwrite Bazi truth.

## Final V20 Start Recommendation

Proceed with V20 as a new directory and keep V19 untouched as an archive.

Start with:

```text
ChartFacts
-> CoreInference
-> RulePath candidates
-> BaziFeature[]
-> QuestionCandidate[]
-> EvidencePack
-> AnswerPlan
-> deterministic answer
```

Design in from day one:

- typed contracts
- strict core import boundaries
- bounded LLM task contracts
- LLM validation and deterministic fallback
- multi-user/profile isolation
- role-aware API and UI surfaces
- multilingual answer plans
- responsive multi-terminal UI
- synthetic/golden validation
- unified validation service for all learning and ranking proposals
- mutation and forbidden-text gates
- corpus snapshot schemas
- learning ledger
- artifact registry
- deterministic baseline diff reports
- active iteration policy

Defer:

- production GNN
- production RL
- neural conclusion models
- direct rule mutation from feedback
- full lab/admin UI parity with V19

V20's strength should be this balance:

```text
deterministic core stays sober
full corpus sees the whole structure space
learning system discovers blind spots and ranking improvements
validation decides what is safe
human/governed active iteration decides what can enter runtime
```
