# V30 Multi User / Terminal / Locale Productization Mainline

Updated: 2026-06-10

## Purpose

This is the controlling mainline for turning the existing role, session, client, and locale projection support into a usable product layer.

The core Bazi calculation modules M1-M8 remain sealed for the current scope. This mainline projects the existing runtime to different users, terminals, and languages; it must not recalculate, overwrite, or mutate chart facts.

## Scope

This mainline owns:

1. Multi-user projection: guest, user, practitioner, analyst, admin, lab.
2. Multi-terminal projection: web, mobile, admin, lab.
3. Multi-language projection: zh, en, ko.
4. Session and owner boundary hardening around the existing `actor_id/session_id` hooks.
5. Productized projection contracts for customer, practitioner, admin, and lab surfaces.
6. Locale terminology and fallback coverage.

This mainline does not own:

- Full login, payment, membership, or organization management.
- New Bazi calculation logic.
- LLM-generated chart facts.
- Full UI redesign.
- Full pytest, synthetic all, or full 518K on every subtask.

## Current Completion Snapshot

| Area | Current completion | Target | Current judgment |
|---|---:|---:|---|
| Multi-user projection | 100% | 100% | U5 complete: U1-U4 evidence is accepted and the current-scope multi-user projection is in U-S1 steady state. |
| Multi-terminal projection | 100% | 100% | U5 complete: web/mobile/admin/lab terminal projection contracts are frozen for current scope. |
| Multi-language projection | 100% | 100% | U5 complete: zh/en/ko Bazi terminology and fallback contracts are accepted for current scope. |
| Durable auth/session productization | 80% | 80% | U5 complete: strict actor/session owner projection is accepted; full login remains an explicit non-goal. |
| Productized terminal UI | 80% | 80% | U5 complete: API/projection terminal contracts are accepted; complete UI redesign remains an explicit non-goal. |
| Deep locale content | 85% | 85% | U5 complete: Bazi terminology depth and fallback coverage are accepted for current scope. |

## Execution Order

### U1 Multi User / Terminal / Locale Projection Readiness

Status: completed 2026-06-10.

Target:

- Multi-user projection 70% -> 80%.
- Multi-terminal projection 70% -> 78%.
- Multi-language projection 70% -> 76%.

Completed:

- Added `v30.multi_user_terminal_locale_readiness.v1`.
- Added `scripts/run_multi_user_terminal_locale_readiness.py`.
- Added `GET /api/v30/admin/productization/multi-user-terminal-locale-readiness`.
- Validated the full 6 role x 3 locale x 4 client matrix, 72 combinations total.
- Fixed role-first projection boundary: `guest/user` remain sanitized even on `admin/lab` clients.
- Filtered customer role actions to `submit_answer`; `run_training/open_trace` remain diagnostic-role only.

Validation:

```text
python3 scripts/run_multi_user_terminal_locale_readiness.py
v30.multi_user_terminal_locale_readiness.v1: passed (7/7) u1_projection_readiness_ready

pytest -q tests/unit/test_multi_user_terminal_locale_readiness.py tests/unit/test_presentation_projection.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_multi_user_terminal_locale_readiness_endpoint_is_read_only
10 passed in 4.34s
```

Full pytest / synthetic all / full 518K: not run for U1; reserved for major gates.

### U2 Session Ownership And Role Boundary Hardening

Status: completed 2026-06-10.

Target:

- Durable auth/session productization 40% -> 60%.
- Multi-user projection 80% -> 88%.

Scope:

- Harden `actor_id/session_id` owner projection.
- Verify guest, user, practitioner, analyst, admin, and lab history boundaries.
- Ensure customer roles never see another owner scope or diagnostic traces.
- Keep this as a minimal session/read-history foundation, not a full login system.

Completed:

- Added `v30.session_owner_boundary_readiness.v1`.
- Added `scripts/run_session_owner_boundary_readiness.py`.
- Added `GET /api/v30/admin/productization/session-owner-boundary-readiness`.
- Hardened `/api/v30/readings/history`: customer roles require both `actor_id` and `session_id`.
- Customer history no longer returns top-level `actor_id/session_id`; it exposes only presence flags and sanitized owner-match summaries.
- Diagnostic roles retain actor-only/session-only operational inspection through role-gated diagnostics.
- Verified same-session cross-actor rows do not leak into exact owner scope.

Validation:

```text
python3 scripts/run_session_owner_boundary_readiness.py
v30.session_owner_boundary_readiness.v1: passed (7/7) u2_session_owner_boundary_ready

pytest -q tests/unit/test_session_owner_boundary_readiness.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_session_owner_boundary_readiness_endpoint_is_read_only tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace
5 passed in 4.50s
```

Full pytest / synthetic all / full 518K: not run for U2; reserved for major gates.

### U3 Locale Terminology And Fallback Contract

Status: completed 2026-06-10.

Scope:

- Add Bazi terminology keys for zh/en/ko.
- Validate missing locale keys and fallback counts.
- Keep locale rendering as expression/projection only, never fact creation.

Completed:

- Added `v30.locale_terminology_readiness.v1`.
- Added `scripts/run_locale_terminology_readiness.py`.
- Added `GET /api/v30/admin/productization/locale-terminology-readiness`.
- Added `BAZI_TERMS`, `term_label`, and `v30.locale_terminology_contract.v1`.
- Added locale terminology contract to presentation layout.
- Localized domain-card labels and base-fact explanation labels through the terminology catalog.
- Verified zh/en/ko required Bazi terms have no missing keys and no fallback keys.
- Verified question-label fallback count is zero for supported locales.
- Verified locale projection does not change chart facts.

Validation:

```text
python3 scripts/run_locale_terminology_readiness.py
v30.locale_terminology_readiness.v1: passed (7/7) u3_locale_terminology_ready

pytest -q tests/unit/test_locale_terminology_readiness.py tests/unit/test_presentation_projection.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_locale_terminology_readiness_endpoint_is_read_only
11 passed in 4.85s
```

Full pytest / synthetic all / full 518K: not run for U3; reserved for major gates.

### U4 Terminal Contract Freeze

Status: completed 2026-06-10.

Scope:

- Freeze required projection fields for web/mobile/admin/lab.
- Validate compact mobile surface, practitioner review surface, admin operations surface, and lab diagnostics surface.

Completed:

- Added `v30.terminal_contract_freeze.v1`.
- Added `scripts/run_terminal_contract_freeze.py`.
- Added `GET /api/v30/admin/productization/terminal-contract-freeze`.
- Froze required top-level projection fields.
- Froze required reading-surface fields.
- Validated web user and mobile guest customer contracts are sanitized.
- Validated practitioner web keeps diagnostics without operator actions.
- Validated admin/lab terminals keep diagnostic density and operator actions.
- Verified terminal contracts do not mutate chart facts.

Validation:

```text
python3 scripts/run_terminal_contract_freeze.py
v30.terminal_contract_freeze.v1: passed (8/8) u4_terminal_contract_frozen

pytest -q tests/unit/test_terminal_contract_freeze.py tests/unit/test_presentation_projection.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_terminal_contract_freeze_endpoint_is_read_only
10 passed in 4.37s
```

Full pytest / synthetic all / full 518K: not run for U4; reserved for major gates.

### U5 Productization Closeout

Status: completed 2026-06-10.

Scope:

- Close U1-U4.
- Record remaining non-goals: full login, payment, organization permissions, complete UI redesign.
- Enter `U-S1 Productization Steady State`.

Completed:

- Added `v30.productization_closeout.v1`.
- Added `scripts/run_productization_closeout.py`.
- Added `GET /api/v30/admin/productization/closeout`.
- Accepted U1-U4 evidence.
- Recorded non-goals: full login, payment, membership, organization permissions, and complete UI redesign.
- Entered `U-S1 Productization Steady State`.

Validation:

```text
python3 scripts/run_productization_closeout.py
v30.productization_closeout.v1: passed (5/5) u5_productization_steady_state_ready

pytest -q tests/unit/test_productization_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_productization_closeout_endpoint_is_read_only
4 passed in 6.28s
```

Full pytest / synthetic all / full 518K: not run for U5; reserved for major gates.

## Mainline Rule

U1-U5 are complete for the current productization scope. The default next state is:

```text
U-S1 Productization Steady State
```

Do not reopen M1-M8 calculation modules for U work. Reopen productization only on new product requirements, projection contract failures, full login scope approval, or explicit UI redesign scope.
