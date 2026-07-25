# V50 Cognitive Authority Refoundation

## Implementation & Acceptance Report v1

Date: 2026-07-13  
Scope: cognitive authority, facts-first context, deterministic fact repair, product projection, validation baseline  
Status: **implementation slice accepted; professional Mingli quality pending expert review**

---

## 1. Executive conclusion

This slice has completed the intended authority correction:

```text
Deterministic World Facts
        ↓
Independent LLM First Look
        ↓
Experimental Tool Challenge Pack
        ↓
LLM Hypothesis Comparison and Whole-chart Cognition
        ↓
Locked-fact Repair and Epistemic Review
        ↓
Role-specific Product Projection
```

The system no longer treats Graph, Path, Role, Mechanism labels, or estimated sensitivity as the answer before the LLM has seen the chart. The LLM owns whole-chart interpretation and hypothesis selection. The system owns locked facts, context organization, tool provenance, evidence traceability, deterministic repair, role boundaries, and audit records.

This is not a claim that the 35 outputs are already professionally correct. It is a claim that the cognitive authority order, deterministic fact boundary, validation runner, and product projection boundary now behave as designed.

---

## 2. Acceptance status

| Area | Status | Evidence |
|---|---|---|
| Cognitive authority order | PASS | Independent Pattern context contains no experimental tool observation |
| LLM whole-chart authority | PASS | LLM selects and compares hypotheses; deterministic code does not choose useful god or final mechanism |
| Tool role | PASS | Graph / Path / Role / sensitivity appear only in Challenge Pack and remain explicitly experimental |
| Deterministic chart facts | PASS | Same-element hidden-stem roots fixed; final hard fact conflicts are zero |
| Locked-fact repair | PASS | System repairs only root/relation wording under deterministic authority and retains LLM hypothesis authority |
| Product role projection | PASS | Guest / Member / Practitioner / Research outputs are enforced server-side |
| Long live validation | PASS | 35/35 cases completed, 24 structure families, 0 generation failures |
| Regression suite | PASS | 181 tests passed |
| Professional Mingli correctness | PENDING | Requires blind expert review and V30/human comparison |
| Cognitive promotion | BLOCKED | No self-generated output may become gold data automatically |

---

## 3. Implemented changes

### 3.1 Authority and world-model contracts

The contracts now distinguish:

```text
deterministic_fact
neutral_relation
retrieved_knowledge
experimental_tool_observation
llm_hypothesis
human_feedback
```

Candidate work paths retain provenance and competing path references. Useful-god reasoning is represented as a conditional lens attached to a selected hypothesis and work path, not as a deterministic element label.

### 3.2 Facts-first two-pass cognition

The first Pattern pass receives:

```text
pillars
calendar facts
hidden stems
ten-god ledger
season and root facts
neutral branch relations
relevant knowledge
```

It does not receive Graph importance, candidate paths, role labels, or estimated ablation scores.

Only after an independent first look has been formed does the Challenge Pack expose experimental observations. The LLM must compare those observations with its own hypotheses instead of inheriting them as conclusions.

### 3.3 Tool downgrade

The following outputs are now explicitly experimental:

```text
Graph ranking
Path Explorer results
Role classifier output
estimated sensitivity / ablation
mechanism labels derived from these tools
```

They may suggest attention or counterexamples. They may not freeze Pattern, select a hypothesis, assign useful god, or override LLM cognition.

### 3.4 Root fact correction

The previous material engine considered a day stem rooted only when the exact same stem appeared in hidden stems. This was incorrect for same-element roots, for example:

```text
丙日主
午藏丁
```

The material engine now records same-element hidden-stem root sources. Root facts include the day element and concrete root-source branches.

### 3.5 Locked-fact repair

The system now separates two actions:

```text
Deterministic repair
    correct an objectively false root or branch-relation phrase

Mingli judgment
    decide Pattern, hypothesis, work path, useful god, or domain meaning
```

Examples of allowed repair:

```text
日主无根
→ 日主根气受损、支撑有限

巳火冲申金, when the ledger supports 巳申合
→ 巳火与申金相合

子水遥冲巳火, when no branch clash exists but water controls fire
→ 子水克制巳火
```

The repair does not change `selected_hypothesis_id`. Alternative hypotheses, success conditions, failure conditions, and counterfactual statements are not rewritten merely to make the primary hypothesis pass.

Every live repair is recorded in `locked_fact_repairs`, and the epistemic receipt keeps `repaired=true`.

### 3.6 Review semantics

The final review now distinguishes:

```text
hard_fact_conflict
world_model_coverage_gap
semantic_review_candidate
professional_expert_judgment
```

An unmodeled half-combination or punishment is not labeled as an engine failure. It is recorded as a world-model coverage gap. Semantic checks run over assertive claims rather than rejected alternatives, Probe questions, and hypothetical failure conditions.

The deterministic reviewer is a fact guard. The semantic reviewer remains a diagnostic peer-review aid and is not allowed to replace the LLM's hypothesis.

### 3.7 Product projection

Server-side role projection now protects the distinction between:

```text
Guest
Member
Practitioner
Research Master
```

The modes still project one cognition result; they do not create separate Mingli engines. Professional hypotheses, tool provenance, counter-evidence, and research details are not leaked into public modes.

---

## 4. Validation design

### 4.1 Baseline composition

```yaml
case_count: 35
structure_family_count: 24
development: 5
acceptance: 24
blind: 6
```

The suite includes ordinary structures, mixed structures, controlled combinations, timing sufficiency/insufficiency, and unsupported-domain boundaries. Expected contracts were not shown to the model.

### 4.2 Live model

```yaml
model: qwen3.5:35b
endpoint: local Ollama-compatible service
live_cases_completed: 35
generation_failures: 0
```

### 4.3 Final observed metrics

```yaml
independent_pattern_tool_leak_count: 0
challenge_pack_missing_count: 0
hard_fact_conflict_case_count: 0
world_model_coverage_gap_case_count: 4
strict_semantic_review_failure_case_count: 20

avg_structural_specificity: 0.8686
avg_falsifiability: 0.8581
avg_causal_completeness: 1.0
avg_fact_traceability: 1.0
avg_deterministic_fact_consistency: 1.0
avg_generic_language_risk: 0.0850

avg_contrastive_distinction: 0.7758
avg_portable_template_risk: 0.2242
```

These are diagnostic signals. They do not prove that the selected Pattern, work path, useful god, or life-domain conclusions are professionally correct.

### 4.4 Remaining world-model coverage gaps

Four cases contain relation claims that the current deterministic ledger does not yet have authority to judge:

```text
c2.converter_dominant.01
c2.mixed_no_obvious_main_path.01
c2.clash_breaks_main_path.02
c2.climate_regulation_dominant.02
```

The gaps concern half-combination and punishment coverage. They remain research items and were not converted into hard failures or silently promoted into deterministic rules.

### 4.5 Remaining semantic-review candidates

Twenty cases still contain at least one semantic-review candidate. The recurring categories are:

```text
element / ten-god role wording
five-element causal wording
overconfident wording
alternative hypothesis comparison completeness
unmodeled branch-relation knowledge
```

Some are genuine LLM errors; some are limitations of lexical review, such as reading `湿土晦火生金` as if it asserted `火生金`. Therefore this count is a queue for syntax-aware review and human audit, not a professional failure rate.

---

## 5. Test results

```text
Targeted cognition / fact / runner tests:
45 passed

Full V50 regression:
181 passed in 9.77s
```

No UI, theory, model weights, or production deployment were changed in this slice.

---

## 6. Reproduction

Run the full regression:

```bash
cd /Users/liujin/DEV/AIProjects/bazi/qiazhi/v50
PYTHONPATH=packages:apps ../.venv312/bin/pytest -q
```

Recompute the final diagnostics without another LLM call:

```bash
cd /Users/liujin/DEV/AIProjects/bazi/qiazhi/v50
PYTHONPATH=packages:apps ../.venv312/bin/python \
  scripts/v50_run_cognitive_authority_baseline.py \
  --run-id local-recompute \
  --reuse-live reports/cognitive-authority-baseline/20260713-cognitive-authority-final-live-v1/cognitive_authority_baseline_v1.json \
  --output-dir /tmp/v50-cognitive-authority-recompute
```

Canonical final artifacts:

```text
reports/cognitive-authority-baseline/20260713-cognitive-authority-final-acceptance-v2/
  cognitive_authority_baseline_v1.json
  cognitive_authority_baseline_v1.md
  cognitive_authority_expert_review_packet_v1.md
```

---

## 7. Boundary declaration

```yaml
training_performed: false
weights_modified: false
theory_modified: false
ui_modified: false
production_deployed: false
self_generated_output_promoted_to_gold: false
automated_quality_used_as_professional_judge: false
llm_cognitive_authority_enabled: true
deterministic_fact_repair_enabled: true
experimental_tools_allowed_to_judge: false
```

---

## 8. Next gate

The next authorized gate is not more architecture and not automatic training.

It is:

```text
6 blind cases
        ↓
expert Mingli review
        ↓
same-chart V30 / human comparison
        ↓
classify true LLM errors vs reviewer false positives vs world-model gaps
        ↓
only then decide the next knowledge, context, tool, or model-policy slice
```

The blind review must score:

```text
盘面重心是否抓对
主假设是否优于竞争假设
主做功因果是否闭合
用神是否条件化而非固定标签
是否产生这张盘专属的可验证断言
是否遗漏关键反证
是否仍有跨盘模板语言
确定性命盘事实是否可靠
```

No case from this run may be used as gold training data before that review.

---

## 9. Final decision

This implementation slice is accepted because the architecture now gives each actor the correct authority:

```text
LLM understands and compares.
The world model supplies facts and knowledge.
Tools challenge attention.
The system repairs locked facts and records provenance.
Experts judge professional Mingli quality.
Users provide case evidence, not global truth.
```

Professional quality remains deliberately unaccepted until blind review. That is not an unfinished engineering task; it is the correct next epistemic gate.
