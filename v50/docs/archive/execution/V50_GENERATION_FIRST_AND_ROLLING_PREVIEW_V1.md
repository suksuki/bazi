# V50 Generation-First and Rolling Preview v1

## Status

```yaml
status: frozen_for_current_product_iteration
generation_first: true
semantic_review_blocks_delivery: false
semantic_review_triggers_llm_retry: false
schema_retry_count: 0
review_data_retained_for_research: true
```

This policy is intentionally temporary. Prompt compilation, output normalization, and epistemic review will be redesigned later. Until then, weak review rules must not make users wait for a second model call or discard a useful reading.

## Runtime Rule

The cognitive chain calls the model once per authorized reasoning stage.

```text
LLM result
-> schema parse
-> minimal deterministic cleanup
-> deliver stage result
-> record review observations asynchronously in the result
```

It must not become:

```text
LLM result
-> semantic review
-> reject
-> ask LLM to rewrite
-> review again
-> reject the reading
```

Only these failures may stop a stage:

- transport failure or timeout;
- empty response;
- response that cannot be recovered as the required JSON object;
- a structurally impossible object that cannot be instantiated by the public contract.

The following may be recorded as observations but may not trigger regeneration, quarantine, or user-visible failure:

- vocabulary preference;
- prose length;
- assertion density;
- hypothesis ranking preference;
- generic-language warnings;
- evidence coverage warnings;
- optional field omissions;
- review confidence or completeness judgments.

## Minimal Cleanup Boundary

Allowed local cleanup:

- remove Markdown fences around JSON;
- extract the first recoverable JSON object;
- trim whitespace and repeated display lines;
- remove references to fact IDs that do not exist;
- apply a small explicit regex list for unsupported deterministic claims;
- normalize bookkeeping fields required by the output contract.

Forbidden local cleanup:

- invent a new Mingli conclusion;
- replace the model's whole reading with a generic safety template;
- promote a secondary hypothesis because a reviewer prefers it;
- ask the model to rewrite a semantically valid response;
- hide a stage merely because diagnostic review returned `passed: false`.

Review receipts remain available to administrators, practitioners, and future prompt-cleaning research. They do not own product delivery.

## Rolling Preview Contract

Every long LLM wait must expose useful work already completed.

```text
stage result arrives
-> add one concise result line to the preview queue
-> type the line into the current waiting surface
-> hold briefly
-> roll upward
-> type the next available result
-> continue rotating until the reading takes over
```

The preview is available in both places:

1. the initial whole-chart loading scene;
2. the progressive reading canvas while later stages are still running.

For a domain exploration, the loading surface rotates already known whole-chart findings until the new domain result arrives. It must not display invented progress text as if it were a new conclusion.

Stage preview sources:

| Stage | Preferred preview |
| --- | --- |
| chart | confirmed pillars |
| pattern preview | `preview_line` |
| pattern | `first_look` or `whole_chart_thesis` |
| work path | `work_path.path_statement` |
| Ziwei | `integrated_thesis` or `ziwei_first_look` |
| prior prediction | first `prior_predictions[].claim` |
| whole chart | `first_look` or `whole_chart_thesis` |
| domain wait | current whole-chart findings, then domain result |

Public copy must describe what Abu has seen. It must not mention verifier passes, schema repair, internal review gates, or engineering stages.

## Product Invariants

```yaml
llm_semantic_regeneration_count: 0
review_triggered_model_calls: 0
review_triggered_result_quarantine: 0
review_triggered_user_failure: 0
preview_uses_real_stage_results: true
preview_single_line: true
preview_continuously_rotates_while_waiting: true
```

This policy does not weaken the immutable chart fact engine. Four pillars, calendar facts, Ziwei facts, and authorization boundaries remain deterministic. It only removes the current semantic reviewer from the critical delivery path.
