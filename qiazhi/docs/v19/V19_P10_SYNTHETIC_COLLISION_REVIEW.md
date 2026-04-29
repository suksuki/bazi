# V19 P10 Synthetic Collision Review

Date: 2026-04-29

## Goal

P10 Synthetic Collision Review verifies that V19 can evolve through controlled synthetic cases instead of noisy real birth charts.

The review checks:

- synthetic chart mapping
- wealth-oriented guided-question recommendation
- fact retrieval
- knowledge retrieval
- answer text
- internal/debug term cleanup
- baseline vs knowledge-augmented evidence delta
- failure attribution and draft proposal generation

## Matrix

The P10 matrix currently contains 12 explicit-pillar synthetic cases:

| Case | Structure label | Collision focus |
| --- | --- | --- |
| `syn.guided.month_command_boundary` | 机会型-月令边界 | month-command strength boundary |
| `syn.guided.ten_god_visible_hidden` | 机会型-十神透藏混合 | visible vs hidden Ten God evidence |
| `syn.guided.hidden_stem_complete_mapping` | 稳定型-藏干完整映射 | complete hidden-stem mapping |
| `syn.guided.branch_penalty_harm_break` | 波动型-刑害破边界 | penalty / harm / break boundary |
| `syn.guided.three_meeting_boundary` | 机会型-三会结构 | three-meeting boundary |
| `syn.guided.time_relation_context_only` | 波动型-时间层碰撞 | time-layer relation boundary |
| `syn.guided.vault_hidden_stem_boundary` | 稳定型-墓库承载 | vault and hidden-stem reading |
| `syn.guided.income_structure_no_internal_terms` | 稳定型-财富元素清晰 | income-structure user copy |
| `syn.guided.branch_clash_combination_collision` | 波动型-冲合并见 | clash + combination collision |
| `syn.guided.income_wealth_missing_unstable` | 波动型-财富元素缺失 | missing wealth element |
| `syn.guided.income_wealth_disrupted_volatility` | 波动型-财富可达被冲 | disrupted wealth accessibility |
| `syn.guided.income_three_harmony_binding` | 机会型-三合牵制 | three-harmony binding signal |

All cases are explicit synthetic pillars. They do not use real birth data.

## Required Chain

Each case runs:

```text
synthetic chart
-> recommended questions
-> fact retrieval
-> knowledge retrieval
-> answer composition
-> forbidden text checks
-> baseline vs kb_augmented comparison
-> evidence delta
-> failure attribution if needed
```

The default required wealth-oriented question is `q_income_stability`; every P10 synthetic case currently keeps it in the recommendation set.

## Baseline vs KB-Augmented

The collision runner executes each case twice:

- `baseline`: no knowledge augmentation
- `kb_augmented`: normal knowledge retrieval enabled

The expected behavior is:

- routing stays stable
- source signal category stays stable
- relation facts stay stable
- evidence increases when relevant knowledge is expected
- user text does not expose knowledge IDs or internal fields

Current result:

- routing mutation: 0
- source-signal mutation: 0
- internal/debug term leakage: 0
- expected P10 knowledge misses: 0

## Stable Structures

Stable in the current P10 run:

- 月令边界进入回答，且不单独推出身强/身弱/好坏
- 十神透出/藏干分层进入回答
- 藏干完整映射进入回答
- 刑、害、破按关系边界处理，没有扩写成灾祸
- 三会与三合不再被统一折叠成普通“合”
- 时间层关系保持为上下文，不改写本命结构
- 墓库回答能说明位置与藏干
- 收入结构回答不暴露内部字段
- 冲合并见能同时保留冲和合
- 财富缺失、财富可达被冲、三合牵制都能进入收入结构问题链路

## Misfires And Missing Structures

Current run:

- misfire structures: none
- missing structures: none
- failed synthetic cases: 0

The runner still emits `evolution_report` on failure. Each failed case must produce:

- audit record
- attribution layer
- draft suggestion
- analyst review requirement
- no runtime mutation

Draft suggestion targets include:

- `knowledge_seed_draft`
- `rule_db_structured_fact_draft`
- `guided_question_ranking_draft`
- `answer_expression_seed_draft`

## P11 Candidates

Recommended P11 directions:

- Expand branch collision matrix: clash + harm, combination + break, three harmony + three meeting in the same chart.
- Expand income structure matrix: wealth visible, wealth missing, wealth bound, wealth disrupted, wealth conflicted, structure binding.
- Add expected answer-shape checks for concise but complete answers.
- Add synthetic cases for rule proposal generation from failing knowledge/rule gaps.
- Add analyst review UI for synthetic failure audit records and draft suggestions.

## Verification

```bash
python3 -m pytest -q v19/tests/test_guided_synthetic_collision.py
python3 -m pytest -q v19/tests
```

Latest local result:

```text
P10 synthetic collision: 12 total, 12 passed, 0 failed
Full tests: 41 passed
```

## Guardrails

This review does not prove real-world accuracy.

It only proves controlled chain behavior for synthetic structural cases:

- no automatic learning
- no automatic rule promotion
- no automatic knowledge promotion
- no runtime mutation from test results
- analyst/admin review required for semantic promotion
