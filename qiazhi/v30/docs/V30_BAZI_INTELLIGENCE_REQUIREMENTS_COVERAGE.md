# V30 Bazi Intelligence Requirements Coverage

Updated: 2026-06-10

## Purpose

`IR1` is the integrated backend requirements gate after the core module, productization, brain/training/synthetic, business acceptance, and Bazi LLM tracks have entered steady state.

It verifies that the current backend covers the original product requirements as one Bazi calculation system:

- Complete Bazi calculation support through M1-M8.
- Knowledge/rule/portrait/path/feature evidence supporting structure, model signal, ranked decisions, and practical reading.
- Multi-role and multi-locale projections for guest, user, practitioner, and admin.
- Continuous question answering with visible/internal next-question separation.
- Hidden-factor feedback as dialogue/calibration evidence, not chart facts.
- Bazi LLM answer expression through task/role context and output acceptance.
- Training and synthetic coverage for interaction and LLM behavior without chart-fact tuning.

## IR1 Completed

Implemented:

- `v30.bazi_intelligence_requirements_coverage.v1`
- `scripts/run_bazi_intelligence_requirements_coverage.py`
- `GET /api/v30/admin/mainline/bazi-intelligence-requirements-coverage`
- Unit coverage for ready path, blocked M3 path, and admin read-only endpoint.

Current validation:

```text
python3 scripts/run_bazi_intelligence_requirements_coverage.py
v30.bazi_intelligence_requirements_coverage.v1: passed (6/6) ir1_bazi_intelligence_requirements_covered

pytest -q tests/unit/test_bazi_intelligence_requirements_coverage.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
4 passed
```

IR1 intentionally does not run full pytest, synthetic all, 518K, live provider smoke, policy pointer promotion, or release gates.

## Accepted Coverage

| Area | Status | Evidence |
|---|---:|---|
| Core Bazi module chain | Passed | M1/M2 core reading, M3 support, M4 model signal, M5 ranked decisions, M6 practical domains, central brain metadata. |
| Multi-user / multi-locale projection | Passed | guest/user/practitioner/admin x zh/en/ko; customer diagnostics hidden; diagnostic roles visible. |
| Continuous Q&A / hidden factor | Passed | answered question outcome, interaction state, internal next question, hidden-factor amplifier candidate. |
| Bazi LLM expression | Passed | BL8 closeout accepted; runtime answer metadata uses Bazi LLM draft call; live provider is not required. |
| Training / synthetic | Passed | `interaction_loop` 5/5 and `bazi_llm_acceptance` 5/5; required training signals present. |
| Read-only boundaries | Passed | chart fact fingerprint preserved; hidden factor, training, and LLM cannot mutate chart facts. |

## Steady State

IR1 enters:

```text
IR-S1 Integrated Bazi Intelligence Steady State
```

## IR2 Backend API Journey Acceptance

IR2 proves the integrated requirements coverage through the actual `/api/v30` backend route handlers, not only through in-memory runtime builders.

Implemented:

- `v30.bazi_backend_api_journey_acceptance.v1`
- `scripts/run_bazi_backend_api_journey_acceptance.py`
- `GET /api/v30/admin/mainline/bazi-backend-api-journey-acceptance`
- Unit coverage for ready path, blocked hidden-factor rehydration, and admin read-only endpoint.

Current validation:

```text
python3 scripts/run_bazi_backend_api_journey_acceptance.py
v30.bazi_backend_api_journey_acceptance.v1: passed (6/6) ir2_bazi_backend_api_journey_accepted

pytest -q tests/unit/test_bazi_backend_api_journey_acceptance.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
4 passed
```

IR2 covers:

- `POST /api/v30/readings` with BirthInput and actor/session context.
- `GET /api/v30/readings/{reading_id}/view` for user, practitioner, and admin projections.
- `POST /api/v30/readings/{reading_id}/questions/{question_id}/answer` with answer refresh and interaction state.
- `POST /api/v30/readings/{reading_id}/hidden-factor/feedback` and `GET /state`.
- `GET /api/v30/readings/history` for customer-sanitized and admin-diagnostic views.
- `GET /api/v30/admin/mainline/bazi-intelligence-requirements-coverage`.

IR2 intentionally does not run full pytest, synthetic all, 518K, live provider smoke, policy pointer promotion, or release gates.

Default next step:

```text
wait_for_new_business_or_calibration_evidence
```

Reopen only on:

- New business requirement that existing projections or question flow cannot cover.
- New real-case calibration evidence that targets a specific module.
- Observed production drift in interaction, hidden-factor state, LLM output acceptance, or role visibility.
- Explicit release-boundary request.

Major gates remain explicit:

- `pytest -q`
- `python3 scripts/run_synthetic_validation.py --tier all`
- `python3 scripts/run_518k_validation.py --mode sample --limit 8`
- live provider smoke
- pointer promotion
