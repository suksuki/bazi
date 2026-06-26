# V30 Latent Bazi Profile Refactor Plan

Updated: 2026-06-13

## Review Conclusion

Hidden-factor interaction was not fully isolated, but it was only half-integrated.

Existing links before HF-R1:

- Structured answer constraints could validate years, repeated states, recurrence, intensity, and confidence.
- Unified interaction brain could convert valid structured turns into hidden-factor feedback.
- API storage could persist `HiddenFactorState` by `reading_id` and `context_id`.
- Runtime rehydration could condition question recommendation, question graph, central brain focus, admin diagnostics, and training signals.

Missing core link:

- The saved state was still mostly a dialogue/session state.
- It did not become a chart-bound, multi-dimensional Bazi attribute profile.
- It did not explicitly link each user-confirmed state to day master, natal pillars, ten-god families, dynamic paths, RBD claims, or evidence ids.
- RBD/M3/M5/M6 could see a broad status, but not a structured latent profile they could safely consume.
- User-facing surfaces still leaked the engineering term “hidden factor.”

Therefore the right refactor is not another UI patch. The system needs an internal `latent_bazi_profile` layer.

## Core Principle

The user should never need to understand “hidden factor.”

The product experience should be:

- The system asks short, constrained follow-up questions.
- The user selects years, repeated states, or domain context.
- The backend updates a chart-bound latent profile.
- That profile helps future question strategy, rule/path calibration, diagnosis routing, training, and later calculation experiments.

The profile must never mutate deterministic chart facts:

- no pillar rewrite
- no luck-cycle rewrite
- no flow-year/month rewrite
- no fixed event prediction
- no direct promotion to final verdict

## Contract

Active runtime layer:

```text
v30.latent_bazi_profile.v1
```

Required binding:

- `reading_id`
- `context_id`
- day master and day-master element
- natal pillars
- active time-layer summary
- source hidden-factor state id
- source feedback ids
- source question ids
- linked evidence ids
- linked dynamic path ids
- linked RBD claim ids

Dimension model:

```text
state_tag
status
linked_domains
linked_ten_god_families
linked_dynamic_path_ids
linked_claim_ids
linked_evidence_ids
years
recurrence
intensity
confidence
signal_strength
```

Current state tags:

- `career_pressure`
- `role_change`
- `wealth_fluctuation`
- `partnership_distribution`
- `relationship_repetition`
- `family_pressure`
- `health_rhythm`
- `credential_pressure`
- `relocation_change`

## HF-R1 Mainline Tasks

### HF-R1.1 Runtime Profile Contract

Status: completed.

Implemented:

- Added `v30/hidden_factor/latent_profile.py`.
- Added `LatentBaziProfile` and `LatentBaziProfileDimension`.
- Added `build_latent_bazi_profile(...)`.
- Added `summarize_latent_bazi_profile(...)`.
- `attach_hidden_factor_state()` now builds and stores:
  - `policy_effect.latent_bazi_profile`
  - `policy_effect.latent_bazi_profile_summary`
- Admin diagnostics expose both profile and summary.
- Customer-facing wording now uses “校准线索/背景校准线索” instead of “隐藏因子.”
- Added `tests/unit/test_latent_bazi_profile.py`.

Verification:

```text
pytest -q tests/unit/test_latent_bazi_profile.py tests/unit/test_hidden_factor_state.py tests/unit/test_interaction_constraints.py
python3 -m compileall -q v30/hidden_factor v30/runtime.py v30/presentation/client_model.py
```

Result:

```text
17 passed
```

### HF-R1.2 RBD Consumption Gate

Next.

Goal:

- Let RBD route decisions consume `latent_bazi_profile` as calibration context.
- Do not let it create chart facts.
- Add rule/path scoring hooks that can prefer relevant domains and claims when a latent dimension is chart-linked.
- Add tests that verify a career-pressure profile raises career/useful-god calibration priority without changing pillars or timing facts.

Acceptance:

- `real_bazi_diagnosis` receives a profile summary in its route context.
- Domain route summaries include latent-profile calibration notes for admin.
- Customer answer may use the meaning of the calibration only after RBD selects traceable claims.
- Tests prove no chart-fact mutation.

### HF-R1.3 Training Signal Alignment

Goal:

- Emit a dedicated training signal:

```text
v30.training_signal.latent_bazi_profile_alignment
```

- Inputs:
  - profile dimensions
  - linked evidence/path/claim coverage
  - structured-answer validity
  - state conflicts/denials/expired status
- Outputs:
  - question strategy calibration
  - RBD route calibration
  - claim specificity calibration

Not allowed:

- pointer promotion
- chart fact mutation
- live policy auto-apply

### HF-R1.4 UI And Product Language

Goal:

- Hide the internal “hidden factor” concept from customer and practitioner screens.
- Present it as concise calibration questions and background clues.
- Keep admin diagnostics precise with internal keys.

Acceptance:

- Customer UI shows no “隐藏因子” wording.
- Structured choices stay short.
- Invalid answers ask user to reselect instead of accepting polluted free text.
- Answer history records the original question and the calibration effect.

## Mainline Priority

After HF-R1.1, the concept was refined into HF-R2: latent personal Bazi attributes.

`latent_bazi_profile` remains the evidence-binding layer. The calculation-ready layer is now:

```text
v30.latent_bazi_attributes.v1
```

Reference:

```text
docs/V30_LATENT_BAZI_ATTRIBUTES_SYSTEM_PLAN.md
```

The next priority is HF-R2.2: consume `latent_bazi_attributes.calculation_modifiers` in a diagnostic-only individualized calculation projection.
