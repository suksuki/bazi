# V40 Phase 67: Hidden Factor Probe Engine

## Goal

Phase 67 turns hidden-factor probing into a V40 runtime capability instead of a loose UI question.

The engine does three things:

1. Reads `DecisionVerdict`, `BranchCandidate`, and runtime signals.
2. Computes whether a hidden-factor question has enough value of information.
3. Emits one focused `ProbeCandidate` that can later become user dialogue, practitioner calibration, `HiddenAttributeUpdate`, `TrainingLabelEvent`, and `RuntimeSignal`.

It does not replace the report, does not auto-start dialogue, does not mutate chart facts, and does not give LLM or the central brain verdict authority.

## Runtime Shape

```text
RuntimeSignal / BranchCandidate / DecisionVerdict
  -> Hidden Factor Probe Engine
  -> ProbeCandidate(topic=hidden_attribute)
  -> ProbeAnswerResult
  -> reality_probe RuntimeSignal
  -> future DecisionEngine / conversation / training replay
```

## Why This Matters

Some bazi conclusions cannot be resolved by chart facts alone. A user may have repeated career blocks, relationship patterns, money distribution conflicts, or health rhythm feedback that changes which branch should be weighted.

V40 keeps this uncertainty explicit:

- ordinary users see a simple question only when it is useful;
- practitioners can use the probe as a calibration lens;
- the answer becomes trainable evidence;
- chart facts remain immutable.

## Engine Rules

`build_hidden_factor_probe_candidates` ranks focus topics by:

- low verdict confidence;
- `mixed` or `weak_candidate` assertion level;
- branch probability gaps that are too close;
- branch or verdict counter evidence;
- hidden-attribute or mixed runtime signals.

The engine emits at most one probe by default. The probe:

- uses `Topic.HIDDEN_ATTRIBUTE`;
- binds back to concrete verdicts and branches;
- stores `target_hidden_attribute_ids`;
- has simple option choices;
- exposes `expected_information_gain` and `user_cost`;
- sets `ask_now` only when information gain clearly exceeds user cost.

## Answer Binding

`build_hidden_factor_answer_runtime_signal` converts a `ProbeAnswerResult` into a `RuntimeSignal` with:

- `source = reality_probe`;
- `source_ref = hidden_factor_probe_answer`;
- trainable targets for `probe_voi`, hidden-factor attribute weight, and reality-probe signal weight;
- no decision authority;
- no chart fact mutation.

This lets future runtime passes and conversation turns consume the answer as evidence without pretending the answer changed the natal chart.

## UI Boundary

The user report, probe, and conversation remain separate surfaces.

The hidden-factor probe may become a conversation seed after the report is accepted. It should not interrupt the report rendering, should not appear as a self-answering block, and should not be shown as engineering language.

## Training Boundary

Hidden-factor feedback is trainable, but only through allowed policy units:

```text
probe_voi.*
hidden_factor.*
signal_weight.reality_probe.hidden_attribute
```

Training after validation may become active immediately, with replay and rollback as the repair path.

## Files

```text
v40/probes/hidden_factor.py
v40/decision/engine.py
v40/conversation/seeds.py
tests/test_v40_phase67_hidden_factor_probe_engine.py
```
