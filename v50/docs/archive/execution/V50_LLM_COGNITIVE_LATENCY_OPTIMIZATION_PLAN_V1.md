# V50 LLM Cognitive Latency Optimization Plan v1

Status: active

## Principle

Latency may be reduced by removing repeated work, repairing only invalid fields, caching identical cognition, improving model serving, and delivering validated stages progressively.

Latency may not be reduced by replacing the cognitive model with an unqualified model, removing competing hypotheses, weakening factual review, shortening the reading into templates, or converting uncertainty into unsupported certainty.

## Observed Baseline

Reference chart: solar 1990-01-01 12:00, Seoul, male.

Baseline completed run:

```text
chart facts                         0.1s
pattern                            24.5s
work path                          22.4s
ziwei generation + full repair     81.8s
prior predictions                  16.3s
career + wealth + both repairs    108.3s
total                             253.5s
```

The slowest sections were not the main Pattern and work-path reasoning. They were broad regeneration after narrow validation failures.

An additional same-chart run showed a separate serving failure: the first `qwen3.5:35b` Pattern request received no response before the transport timeout. This is model-serving tail latency, not a DeepBazi reasoning-stage dependency.

## Optimization Layers

### L0. No-Waste Repair

- repair only the invalid cross-lens Probe when the Ziwei cognition itself is valid;
- repair only the domain that failed domain review;
- normalize structurally valid four-step causal text before asking the model to rewrite it;
- never rerun a valid Pattern, work path or domain because another independent field failed.

### L1. Progressive Cognitive Delivery

- show the accepted Pattern as soon as Pattern review passes;
- show the accepted work path while Ziwei is still running;
- show the whole-chart brief and first Probe before optional domain generation completes;
- label every partial artifact as provisional or accepted;
- a later failure must not erase an earlier accepted artifact.

### L2. Validated Cognition Cache

Cache key must include:

```text
normalized chart facts
analysis year and timing scope
fact-engine versions
knowledge snapshot version
context-compiler version
prompt/protocol version
model identity and inference policy
requested cognitive stage
```

Only artifacts with a passed stage review may enter the cache. Probe answers, user notes and case-local beliefs are never shared through the chart cognition cache.

### L3. On-Demand Domain Cognition

- whole-chart cognition remains the first public result;
- the selected life domain runs next;
- other domains remain available but are generated when opened;
- existing passed domains are reused;
- background prefetch is allowed only when it does not delay the user's selected task.

This changes delivery order, not reasoning depth.

### L4. Model Serving Audit

Record for every Ollama call:

```text
request queued duration
model load duration
prompt token count and prompt-eval duration
generated token count and generation duration
total duration
timeout or transport failure
model residency state
context length
```

Do not increase `OLLAMA_NUM_PARALLEL` before measuring available VRAM. Ollama memory use scales with parallel requests and context allocation. Do not lower context length until prompt-token measurements prove the smaller allocation is sufficient for every protected stage.

### L5. Bounded Transport Recovery

- distinguish queue timeout, connection failure, schema failure and epistemic failure;
- retry transient transport failures with the same qualified model and unchanged context;
- use a bounded total latency budget rather than one unbounded request;
- do not route an epistemic failure to a weaker model as fallback;
- open a circuit after repeated server stalls and expose a recoverable product state.

## Metrics

```text
time_to_chart_ready
time_to_pattern
time_to_whole_chart_brief
time_to_selected_domain
time_to_complete_reading
p50 / p95 / p99 by stage and model
full_regeneration_avoided_count
cache_hit_rate by stage
transport_timeout_rate
schema_failure_rate
epistemic_failure_rate
accepted_artifact_retention_rate
```

Quality metrics must be reported beside latency:

```text
fact conflict rate
critical Pattern omission rate
alternative-hypothesis coverage
causal-chain completeness
counter-evidence coverage
expert blind preference
```

## Promotion Gates

An optimization may be promoted only when:

- protected factual tests remain fully passing;
- blind cognitive quality does not regress;
- no new template fallback is introduced;
- p95 stage latency improves or accepted results reach users earlier;
- failure and cache behavior remain auditable;
- model identity and inference settings are recorded.

## Current Changes

- interrupted jobs now terminate visibly instead of polling forever;
- failed cognition shows a retry surface instead of an infinite loading canvas;
- invalid Ziwei integration cannot block a valid Bazi reading;
- Probe-only Ziwei failures use a focused Probe repair;
- only the failed domain is regenerated;
- a four-line causal chain returned in one array item is normalized without changing its content.
- Ollama load, prompt-eval, generation, token-count and total-duration metrics are now attached to cognitive stage receipts;
- all cognitive stages default to the qualified `qwen3.5:35b` authority, while Gemma remains an expression/Abu wording candidate and Qwen 8B remains intake-only;
- Pattern context now uses an auditable Attention Receipt and averages about 17 KB / 39 selected facts across the 75-case fixture matrix.

No model was downgraded. No Mingli fact rule or epistemic threshold was weakened.
