# V30 Post-Seal Release Hardening Plan

Updated: 2026-06-05

## Purpose

The eight core Bazi modules are phase sealed. Post-seal work should not reopen core modules unless a real validation failure appears.

This phase hardens release gates, API contracts, and validation cadence so future changes cannot accidentally ship:

- missing core Bazi reading output.
- missing M5 ranked decisions.
- missing M6 practical domain contracts.
- guest/user internal projection leaks.
- hidden diagnostics or policy payload leaks.
- release gates that report `eligible` while carrying failures.

## Completed 2026-05-24

- Added release-gate check `post_seal_contracts`.
- `post_seal_contracts` validates:
  - customer `core_bazi_reading` exists.
  - strength, structure, and useful-god ranked decisions are projected.
  - practical domains are projected.
  - `v30.api_projection_contract.v1` is active.
  - customer surface order starts with `core_bazi_reading` and `domain_cards`.
  - guest/user leak scan passes.
  - user diagnostics remain hidden.
  - admin diagnostics remain visible.
- Hardened `synthetic_all` release check:
  - API projection contract coverage is counted.
  - user leak-pass coverage is counted.
  - M6 practical domain contract coverage is counted.
  - any appended release-check failure now correctly makes the check fail.
- Added explicit `phase_seal_coverage` summary for M1-M8.
- Added `phase_seal_passed_count = 8` to `post_seal_contracts`.
- Added R2 release-gate check `production_api_smoke` for health, reading creation, user/admin view projection, answer refresh, interaction state, and read-history projection.
- Added live-port smoke script `scripts/run_production_api_smoke.py`.
- Updated release-gate tests and script expectation through R2 from 3 quick checks to 5 quick checks.
- Added R3 read-history owner/visibility checks to `production_api_smoke`.
- Added `v30.reading_history_ownership.v1`, sanitized guest/user history projection, and diagnostic-role read-history diagnostics.
- Added R4 release-gate check `llm_live_smoke`.
- Added `v30.llm_live_smoke.v1` artifacts and `v30.llm_no_mutation_proof.v1` for chart facts, ranked decisions, model signal, and interaction state.

## Validation 2026-05-24

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_release_gate.py
3 passed
python3 scripts/run_release_gate.py --sample-limit 2
v30.release_gate.quick.20260524052314: eligible mode=quick checks=4
- runtime_smoke: passed
- post_seal_contracts: passed
- synthetic_all: passed
- 518k_sample: passed
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260524114624: eligible, checks=4, phase_seal_passed_count=8
synthetic_all: passed (95/95)
518k_sample: eligible, cases=2, json_fallback, v30.518k.sample.20260524114640640275

pytest -q tests/unit/test_release_gate.py
3 passed
pytest -q tests/test_v30_scaffold.py tests/unit/test_presentation_projection.py
14 passed
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260604011732: eligible, checks=5, production_api_smoke=passed
python3 scripts/run_production_api_smoke.py --base-url http://127.0.0.1:9030 --reading-id r2-live-api-smoke-202606040120 --json
v30.production_api_smoke.v1: passed

python3 -m compileall -q v30 scripts/run_production_api_smoke.py
passed
pytest -q tests/unit/test_runtime_repository.py tests/test_v30_scaffold.py
17 passed
pytest -q tests/unit/test_release_gate.py
3 passed
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260605051922: eligible, checks=5, production_api_smoke.history_owner_scope=actor_and_session
python3 scripts/run_production_api_smoke.py --base-url http://127.0.0.1:9030 --reading-id r3-live-history-smoke-202606050520 --json
v30.production_api_smoke.v1: passed

pytest -q tests/unit/test_llm_context.py tests/unit/test_expression_framework.py
12 passed
pytest -q tests/unit/test_release_gate.py
3 passed
python3 scripts/run_llm_live_smoke.py --reading-id r4-llm-live-smoke-20260605 --json
v30.llm_live_smoke.20260605062559199852: passed, smoke_status=unconfigured
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260605062559: eligible, checks=6, llm_live_smoke=passed
```

## Gate Cadence

- Small targeted fixes: run affected unit tests and affected synthetic tier only.
- Core contract or projection changes: run `tests/unit/test_release_gate.py`, affected projection tests, and affected synthetic tier.
- Release/pointer boundary: run `scripts/run_release_gate.py --mode standard` with sample and selected shard.
- Full pytest and full 518K remain explicit, not default.

## Next Task

```text
R13 External Release Dry Run And Full Pytest Decision.
```
