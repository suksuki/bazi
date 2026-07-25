# VNext Phase 0 P0-G1.6 Evidence Gate Closure Long Task v1

Status: `executed; analyst decisions and external freezes pending`

## Purpose

P0-G1.6 does not test whether VNext is professionally better. It closes the evidence and isolation questions raised after P0-G1.5, then stops before the sealed 180-output run.

```text
P0-G1.5 machine preparation
-> retained conflict classification
-> effective Lane / input isolation audit
-> repair authority audit
-> critical pairwise schedule
-> human and Frontier freeze packets
-> P0-G2 remains blocked
```

## Product Constitution bridge

The new product design is merged as a downstream acceptance bridge, not as benchmark context.

```text
accepted P0 whole-chart cognition
-> FormalInsight
-> LifeCase.BaselineInsight
-> on-demand domain cognition
-> role projection
-> Abu explanation and action
```

Phase 0 career and wealth fields remain diagnostic tests of domain reasoning. They do not authorize production to precompute all domains during first run. Abu dialogue, Life Case history, Reality Evidence, UI state and narrative style are forbidden model inputs in Round 1 and are not scored as professional cognition.

## Lanes

### Lane A - Fact conflict classification

Audit the retained Holistic conflict against the exact natal facts, original output, detector input and parser result. Classify it as model cognition, context, parser or epistemic disagreement. Do not rerun the model to make the metric green.

### Lane B - Non-sealed input isolation

Development and model-policy selection use self-contained fixture packs. Non-sealed Preflight must not load the full taxonomy, formal manifest, Expert Reference or Reality Evidence.

### Lane C - Effective Lane isolation

Compare declared Lane policy with the actual prompt and context. A policy claim such as `plain professional request` is not accepted when the effective prompt contains a hidden synthesis protocol.

### Lane D - Repair authority

Separate mechanical JSON/schema recovery from deterministic fact rewriting and professional cognition. Any repair touching hypotheses, work paths, useful-god reasoning, portraits or domains requires an explicit policy decision.

### Lane E - Pairwise review

Every formal chart must include the six critical anonymous comparisons:

```text
VNext vs Current V50
VNext vs Direct Frontier
VNext vs Holistic
VNext vs Fact-only
Holistic vs Fact-only
Direct Same Model vs Fact-only
```

### Lane F - Human / Frontier / snapshot gates

Prepare the human-authored Expert Reference worksheet and complete Frontier policy contract. Do not fabricate either. A final FormalRunLock requires a clean committed source and execution environment.

## Findings

1. The retained `子午冲 / 午辰冲` flags were parser-scope failures: the model used 午 in future, counterfactual and question clauses, not as a natal branch.
2. Non-sealed Preflight previously loaded the full taxonomy and Expert Reference metadata. The runner now uses an isolated Development fixture pack and does not open Expert Reference in dry mode.
3. The shared Direct prompt includes a seven-step synthesis protocol despite the policy saying `plain professional request`; analyst decision is required.
4. Current deterministic fact repair can rewrite hypothesis, work-path, useful-god, portrait and domain text; analyst decision is required.
5. The six required anonymous pairwise comparisons are now explicit in the review contract.

## Reproduce

```bash
cd /Users/liujin/DEV/AIProjects/bazi/qiazhi/v50
PYTHONPATH=.:packages:apps ../.venv/bin/python \
  scripts/v50_prepare_vnext_phase0_g1_6.py \
  --run-id phase0-g1-6-20260715-v1 \
  --output-dir reports/vnext-phase0-g1/phase0-g1-6-20260715-v1

PYTHONPATH=.:packages:apps ../.venv/bin/pytest -q \
  tests/test_v50_vnext_phase0_benchmark.py \
  tests/test_v50_vnext_phase0_g1_6.py
```

## Stop rule

Do not run P0-G2 until:

```text
human Expert Reference frozen
true Frontier policy frozen
clean reproducible snapshot frozen
Direct prompt boundary approved
repair authority approved
new full non-sealed live Preflight passed
```

No professional winner may be declared in P0-G1.6.
