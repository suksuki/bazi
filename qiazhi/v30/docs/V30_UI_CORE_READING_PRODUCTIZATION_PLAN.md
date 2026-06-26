# V30 UI-R1 Core Bazi Reading Productization Plan

Updated: 2026-06-13

## Why This Becomes Mainline

UI-R1 is not a visual polish task. It is a core Bazi measurement usability task.

Current review found that V30 can calculate chart facts and module outputs, but the customer-facing product surface does not yet turn them into usable multi-role Bazi reading text.

Observed sample:

```text
BirthInput: 1990-02-04 23:30, Beijing, female
Four pillars: 庚午 / 戊寅 / 庚子 / 戊子
Current luck: 甲戌, 2020-2029
Flow year 2026: 丙午
Day master: 庚金
```

The system can produce:

- deterministic pillars, luck cycle, flow year, ten-gods, five-element distribution, and branch clashes.
- M5 ranked decisions: slightly weak, ordinary structure review, resource/self-support useful-god direction.
- M3/RBD paths, claims, portraits, features, and dynamic structure rows.
- IQ question candidates and answer panel.

But the product output still says things like:

```text
事业可以进入具体问题，但仍按候选路径表达，不做确定断语。
财务可以进入具体问题，但仍按候选路径表达，不做确定断语。
```

This is not acceptable as Bazi reading output. The system is exposing module posture instead of producing a reading.

## Current Failure Findings

### F1 Domain Cards Are Template-Like

`reading_surface.domain_cards[]` carries `summary`, `customer_takeaway`, `diagnosis_summary`, `diagnosis_claims`, `diagnosis_paths`, and `portrait_dimensions`, but the UI and projection still privilege generic summaries.

Required correction:

- Customer card must show a concrete Bazi assertion first.
- The assertion must cite chart facts or RBD evidence in customer-safe wording.
- Generic phrases like "可以进入具体问题" must fail acceptance unless used as secondary helper text.

### F2 Basic Assertions Are Not Productized

The UI shows pillars and ten-gods, but does not produce a concise reading from:

- day-master state.
- five-element distribution.
- visible/hidden ten-gods.
- root/vault facts.
- branch relations.
- strength / structure / useful-god ranked decisions.
- current luck and flow year.

Required correction:

- Add a `basic_assertions` product layer.
- It must include `day_master_assertion`, `structure_assertion`, `useful_god_direction`, `current_luck_flow_assertion`, and `risk_boundary`.
- It must remain bounded: no fake final destiny verdict, no event-year invention, no chart-fact mutation.

### F3 Bazi Paths Are Too Abstract

Structure paths currently surface as generic chains such as:

```text
官杀 -> 印星，回到日主。
财星 -> 官杀 -> 印星，回到日主。
```

Required correction:

- Convert paths into practical Bazi reading rows:
  - path name.
  - why this path is active in this chart.
  - which domain it affects.
  - what it suggests for career, wealth, relationship, health, or timing.
  - what question should be asked next if evidence is insufficient.

### F4 Portraits And Features Are Underused

M3/RBD has features and portrait dimensions, but customer and practitioner surfaces do not clearly expose:

- Bazi feature list.
- portrait dimensions.
- hidden-factor clues.
- feature-to-claim links.
- portrait-to-domain links.

Required correction:

- Add `bazi_features` and `bazi_portraits` to the customer-safe projection.
- Customer view: 3-5 concise traits with plain language.
- Practitioner view: evidence-linked feature/portrait rows.
- Admin view: full IDs, source modules, rule/claim/path links.

### F5 Intelligent Q&A Answers The Wrong Domain

Observed failure:

- Question: `财运更适合主动争取还是保守积累？`
- Answer text drifted into career/post responsibility.

Required correction:

- Answer composer must bind to `selected_question.topic`.
- Domain mismatch must fail validation.
- If question domain is wealth, answer must include wealth-specific claims, paths, and practical reading rows.
- If evidence is weak, answer should still answer the question first, then state what remains uncertain.

### F6 Q&A Chain Is Too Verbose

The user-facing question page shows too much process:

- repeated summary.
- answer panel.
- quick choices.
- question card.
- local question turns.
- hidden-factor form.
- queued questions.

Required correction:

- Customer view should show:
  - current answer.
  - Bazi basis.
  - one next question.
  - optional "补充年份/状态" collapsed or secondary.
- Question-chain details move to practitioner/admin.

### F7 LLM Is Underpowered

Current LLM behavior is mostly expression rewrite. It receives too much general context and not enough task-specific Bazi reading intent.

Required correction:

- LLM remains forbidden from generating chart facts.
- LLM must be upgraded as a Bazi expression and synthesis layer:
  - use task-specific context packs.
  - receive selected domain and question.
  - receive curated facts, claims, paths, portraits, features, and role contract.
  - return structured JSON matching the task.
- LLM must not receive the entire runtime payload.
- LLM output must be checked for:
  - domain alignment.
  - evidence usage.
  - forbidden final-event claims.
  - role density.
  - no internal ID leakage.

## Mainline Task Breakdown

### UI-R1.1 Product Reading Acceptance Audit

Goal:

- Freeze the current failure as an explicit acceptance artifact.
- Add a targeted validation that catches:
  - generic domain cards.
  - no basic assertions.
  - no feature/portrait rows.
  - answer/question domain mismatch.
  - role output not differentiated.

Default validation:

```text
python3 scripts/run_ui_core_reading_product_acceptance.py
pytest -q tests/unit/test_ui_core_reading_product_acceptance.py
```

Status: Complete 2026-06-13

Implemented:

- Added `v30.ui_core_reading_product_acceptance.v1`.
- Added `scripts/run_ui_core_reading_product_acceptance.py`.
- Added `tests/unit/test_ui_core_reading_product_acceptance.py`.
- The audit uses a deterministic BirthInput sample, not a smoke-only chart:
  - `1990-02-04 23:30`, Beijing, female.
  - `庚午 / 戊寅 / 庚子 / 戊子`.
  - current luck `甲戌`.
  - flow year `丙午`.
- The audit exits successfully when the audit itself runs, even if product readiness is blocked.

Validation:

```text
pytest -q tests/unit/test_ui_core_reading_product_acceptance.py
2 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=4/9
failed=basic_assertions_present, bazi_features_and_portraits_projected, bazi_paths_projected_as_reading, role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.2 Basic Assertion Projection
```

Current interpretation:

- Core chart calculation is ready for this sample.
- Domain cards and selected wealth answer are no longer the immediate blocker in this sample.
- Product readiness is blocked by missing productized assertions, feature/portrait projection, path reading rows, role-specific answer text, and LLM product context-pack visibility.

### UI-R1.2 Basic Assertion Projection

Goal:

- Add a customer-safe `basic_assertions` block to `reading_surface`.
- Build assertions from deterministic facts, M5 ranked decisions, and time context.

Required output:

```text
reading_surface.basic_assertions
core_bazi_reading.basic_assertions
```

Fields:

- `day_master_assertion`
- `strength_assertion`
- `structure_assertion`
- `useful_god_direction`
- `current_luck_flow_assertion`
- `risk_boundary`
- `evidence_labels`

Status: Complete 2026-06-13

Implemented:

- Added `reading_surface.basic_assertions`.
- Added matching `core_bazi_reading.basic_assertions`.
- Each row includes `assertion`, `evidence`, `evidence_labels`, `source_modules`, and a boundary.
- The projection covers:
  - `day_master_assertion`
  - `strength_assertion`
  - `structure_assertion`
  - `useful_god_direction`
  - `current_luck_flow_assertion`
  - `risk_boundary`
- Assertions are generated from deterministic chart facts, M3 structure paths, M4 model signal consumption through M5, M5 ranked decisions, and time context.
- No chart fact mutation, no fixed useful-god verdict, no fixed event prediction.

Validation:

```text
python3 -m compileall -q v30/presentation/client_model.py v30/validation/ui_core_reading_product_acceptance.py scripts/run_ui_core_reading_product_acceptance.py
passed

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=5/9
failed=bazi_features_and_portraits_projected, bazi_paths_projected_as_reading, role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.3 Bazi Feature And Portrait Projection
```

### UI-R1.3 Bazi Feature And Portrait Projection

Goal:

- Review and surface M3/RBD Bazi features and portraits.
- Customer view gets concise traits.
- Practitioner view gets evidence-linked traits.
- Admin keeps full diagnostics.

Required output:

```text
reading_surface.bazi_features
reading_surface.bazi_portraits
diagnostics.real_bazi_diagnosis.features
diagnostics.real_bazi_diagnosis.portraits
```

Acceptance:

- At least 5 features are available for ready charts.
- At least 5 portrait rows are available for ready charts.
- Customer rows must be readable and not expose raw IDs by default.
- Practitioner rows must retain evidence labels.

Status: Complete 2026-06-13

Implemented:

- Added `reading_surface.bazi_features`.
- Added `reading_surface.bazi_portraits`.
- Customer roles receive concise rows without raw `feature_id` / `portrait_id`.
- Practitioner/admin roles receive evidence-linked rows with ids, evidence ids, path ids, and counter notes.
- Product statement cleanup removes raw source notation such as `season=`, `strongest=`, and `v30.krp.` from customer rows.
- Projection prefers structure, useful-god, career, wealth, relationship, health, timing, and hidden-factor rows over backend governance-only rows.

Validation:

```text
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=6/9
failed=bazi_paths_projected_as_reading, role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.4 Bazi Path Reading Projection
```

### UI-R1.4 Bazi Path Reading Projection

Goal:

- Convert path chains into real reading output.

Required output:

```text
reading_surface.bazi_paths
domain_cards[].path_summary
domain_cards[].path_assertions
```

Each path row must include:

- path label.
- practical meaning.
- domain impact.
- active evidence.
- uncertainty boundary.

Status: Complete 2026-06-13

Implemented:

- Added `reading_surface.bazi_paths`.
- Added `domain_cards[].path_summary`.
- Added `domain_cards[].path_assertions`.
- Product path rows now include:
  - `path_label`
  - `path_chain`
  - `why_active`
  - `meaning`
  - `domain_impact`
  - `active_evidence`
  - `uncertainty_boundary`
  - `confidence_band`
- Customer rows hide diagnostic score/counter-evidence internals.
- Practitioner/admin rows retain score, counter evidence, and blocked overclaim fields.

Example product rows:

```text
官印相生：压力、规则或职责需要转成资质、凭证、学习能力或平台承接。
财官印制化：财星不是单独看收入，而是先牵动责任与压力，再看资源、资质或平台如何承接。
食伤生财：财富更依赖输出、技术、表达、方案或流量能否稳定转化。
```

Validation:

```text
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=7/9
failed=role_outputs_are_differentiated, llm_context_pack_has_product_layers
next=UI-R1.8 Multi-Role Reading Surfaces
```

### UI-R1.5 Domain Cards Consume Claims, Paths, Features, Portraits

Goal:

- Replace generic `summary/customer_takeaway` priority with product reading synthesis.

Required card order:

1. concrete assertion.
2. Bazi basis.
3. path/feature/portrait support.
4. practical suggestion.
5. optional follow-up.

Forbidden as primary text:

- `可以进入具体问题`
- `仍按候选路径表达`
- `不做确定断语`
- `系统会结合`
- `请补充更多信息` before giving an answer

Status update 2026-06-13:

- RBD-backed domain readings now carry `v30.core_bazi_claim_quality.v1`.
- `summary`, `customer_takeaway`, and `diagnosis_summary` use the RBD public diagnosis summary when available.
- Customer projection exposes `domain_cards[].core_claim_quality` as safe quality flags and counts.
- UI acceptance checks that career, wealth, relationship, health, and timing cards are traceable, Bazi-specific, and free of generic fallback language.
- Structure dynamic `top_paths[]` now include customer-visible `diagnosis_statement` text, not just internal path metadata.

Validation:

```text
pytest -q tests/unit/test_real_bazi_product_reading_acceptance.py tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_ui_core_reading_product_acceptance.py tests/unit/test_synthetic_archetype_rule_claim_calibration.py
11 passed

python3 scripts/run_real_bazi_product_reading_acceptance.py
v30.real_bazi_product_reading_acceptance.v1: passed (6/6) rbd_s110_product_reading_accepted
```

### UI-R1.6 Domain-Bound Answer Composer

Goal:

- Make answer generation answer the selected question.

Rules:

- Question topic controls answer domain.
- Answer text must include domain-specific evidence.
- Answer must not drift into another domain unless explicitly explaining cross-domain interaction.
- If user selects `wealth:risk`, answer must answer wealth risk before asking anything else.

### UI-R1.7 LLM Context And Prompt Upgrade

Goal:

- Make LLM useful as a Bazi reading synthesis layer.

LLM task types:

| Task | Use |
|---|---|
| `customer_initial_reading` | Synthesize first customer reading from assertions/cards/features/paths. |
| `domain_followup_answer` | Answer one user question in the selected domain. |
| `practitioner_review` | Produce denser evidence-chain wording for practitioners. |
| `portrait_feature_explanation` | Explain traits and hidden-factor clues. |

Context pack must include only:

- `selected_question`
- `role_contract`
- `basic_assertions`
- `domain_card` for selected domain
- `bazi_features`
- `bazi_portraits`
- `bazi_paths`
- `time_context`
- `allowed_boundaries`

Context pack must exclude:

- raw runtime payload.
- policy weights.
- training candidates.
- pointer data.
- internal trace unless admin.

Prompt output schema:

```json
{
  "answer_text": "string",
  "bazi_basis": ["string"],
  "used_paths": ["string"],
  "used_features": ["string"],
  "uncertainty_boundary": "string",
  "next_question_hint": "string"
}
```

Acceptance:

- Live provider remains explicit-only.
- Fake/deterministic provider must still validate prompt construction.
- If LLM is unavailable, rule-bound answer must still be concrete and domain-aligned.

Status: Complete 2026-06-13

Implemented:

- LLM answer metadata now exposes `context_pack_summary`.
- `context_pack_summary.layers` includes:
  - `basic_assertions`
  - `domain_card`
  - `bazi_features`
  - `bazi_portraits`
  - `bazi_paths`
  - `time_context`
  - `role_contract`
- LLM prompt compact surface now includes product reading layers, not only summary/next question.
- Customer answer projection keeps only safe metadata and still exposes the context layer summary.
- Provider execution and live smoke remain explicit-only.

Validation:

```text
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_reading_accepted
product_ready=True audit_ready=True
passed=9/9
next=UI-R1.10 Product-Level Synthetic Validation
```

### UI-R1.8 Multi-Role Reading Surfaces

Goal:

- Make the same chart render differently by role.

Role output:

| Role | Output |
|---|---|
| guest | concise reading preview, no diagnostics. |
| user | practical answer, plain Bazi terms, one follow-up. |
| practitioner | evidence chain, features, portraits, paths, uncertainty. |
| admin | full diagnostics, IDs, source modules, LLM status. |

Acceptance:

- User and practitioner text must not be identical.
- Admin must retain diagnostics.
- Guest/user must not leak internal IDs or policies.

Status: Complete 2026-06-13

Implemented:

- Added diagnostic role answer projection for practitioner/admin/analyst/lab.
- User answer remains concise and practical.
- Practitioner answer now includes:
  - original answer.
  - basic judgment summary.
  - path review.
  - feature/portrait review.
  - uncertainty boundary and evidence count.
- Added `reading_surface.role_contract` with role density, diagnostic visibility, and answer style.
- Role adaptation is projection-only and does not mutate answer facts, chart facts, luck, or flow.

Validation:

```text
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py
8 passed

python3 scripts/run_ui_core_reading_product_acceptance.py
v30.ui_core_reading_product_acceptance.v1: ui_r1_product_acceptance_baseline_recorded
product_ready=False audit_ready=True
passed=8/9
failed=llm_context_pack_has_product_layers
next=UI-R1.7 LLM Context And Prompt Upgrade
```

### UI-R1.9 Question UI Simplification

Goal:

- Replace verbose question chain with one high-quality interaction unit.

Customer view:

- current answer.
- Bazi basis.
- one next question.
- optional collapsed clue form.

Practitioner/admin view:

- question chain.
- interaction state.
- hidden-factor state.
- internal next question.

### UI-R1.10 Product-Level Synthetic Validation

Status: complete.

Goal:

- Add synthetic typical Bazi cases that validate product reading text, not just module presence.

Cases:

- metal/resource pressure.
- wood/output conflict.
- fire/output wealth.
- hidden-factor boundary.

Checks:

- basic assertions present.
- paths present.
- features/portraits present.
- domain answers align with selected topic.
- LLM context pack includes required fields.
- role outputs differ.
- generic text rate below threshold.

Default validation:

```text
python3 scripts/run_synthetic_validation.py --tier ui_core_reading_product
v30.synthetic.ui_core_reading_product: passed (4/4)

pytest -q tests/unit/test_presentation_projection.py tests/unit/test_ui_core_reading_product_acceptance.py tests/unit/test_ui_core_reading_product_synthetic.py
9 passed
```

Implemented artifacts:

- `SYNTHETIC_UI_CORE_READING_PRODUCT_CASES`.
- `ui_core_reading_product` synthetic tier.
- `v30.ui_core_reading_product.synthetic_quality.v1`.
- `tests/unit/test_ui_core_reading_product_synthetic.py`.

Next:

```text
SYN-CAL4 Synthetic Archetype Calibration Closeout
```

## Data And Storage

This task does not mutate chart facts.

It may store product reading snapshots for review:

```text
v30_product_reading_snapshots
v30_product_answer_acceptance
v30_llm_context_pack_audit
```

If Postgres is unavailable, use existing JSON fallback.

## Non-Goals

- No chart fact mutation.
- No final destiny verdict.
- No invented event year.
- No policy pointer promotion.
- No full pytest after each subtask.
- No full 518K by default.
- No live LLM by default.

## Mainline Position

UI-R1 supersedes SYN-CAL4 as the next active task because it is a user-facing core measurement failure.

SYN-CAL4 remains valid but deferred:

```text
SYN-CAL4 Synthetic Archetype Calibration Closeout
status=deferred_until_UI_R1_acceptance_baseline
```

## Immediate Next Task

```text
UI-R1.10 Product-Level Synthetic Validation
```

Implement next:

- Add product-level synthetic cases for typical Bazi reading output.
- Validate assertions, features, portraits, paths, role differentiation, and LLM context layers together.
- Keep full pytest, synthetic all, 518K full, and live LLM explicit-only.
