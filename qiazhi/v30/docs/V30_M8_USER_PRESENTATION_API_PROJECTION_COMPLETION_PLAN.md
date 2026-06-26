# V30 M8 User Presentation / API Projection Completion Plan

Updated: 2026-05-24

## Purpose

M8 is the customer presentation and API projection layer for the eight core Bazi modules. Its job is to keep the UI/API simple while preserving the strength of M1-M7 behind the surface.

M8 must:

- show the core Bazi calculation result before questions.
- preserve additive API fields such as `reading_surface`, `questions`, `answer_panel`, `diagnostics`, and next-question ids.
- hide diagnostics, policy payloads, training internals, hidden-factor state, raw scores, and internal strategy traces from guest/user projections.
- keep practitioner/admin/lab diagnostics role-gated.
- never rewrite chart facts or ranked decisions through projection.

## Current Baseline

| Module | Current | Target | Current judgment |
|---|---:|---:|---|
| M8 User Presentation / API Projection | 90% | 90% | Phase sealed: `v30.api_projection_contract.v1` is active, guest/user leak scan passes, core calculation appears before question flow, additive API fields are preserved, diagnostics remain role-gated, and synthetic/518K gates are stable. |

## Completion Scope

- Added top-level `projection_contract` to `ClientPresentationModel`.
- Added `v30.api_projection_contract.v1`.
- Added `v30.projection_leak_scan.v1`.
- Sanitized `reading_surface.next_question` so customer projections do not leak internal policy trace fields.
- Added `m8_api_projection_contract` synthetic tier over the 30-case canonical real-case pack.
- Added `v30.training_signal.api_projection_contract` for visibility-policy coverage.

## Validation 2026-05-24 Final Seal

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract
v30.synthetic.m8_api_projection_contract: passed (30/30)
pytest -q tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py::test_synthetic_m8_api_projection_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
8 passed
pytest -q tests/test_v30_scaffold.py
8 passed
python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (95/95)
python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260524044648490844: eligible, cases=8, json_fallback
```

## Remaining Gap

M8 is phase sealed for current API/UI projection. Future work should focus on product polish and durable session/auth boundaries, not reopening core calculation modules unless a real validation failure appears.

## Next Task

```text
Eight core Bazi modules are phase sealed. Next mainline: post-seal release hardening and targeted defect cleanup only.
```
