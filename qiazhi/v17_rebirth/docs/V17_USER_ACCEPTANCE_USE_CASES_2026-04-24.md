# V17 User Acceptance Use Cases

Date: 2026-04-24

This document is the current smoke/acceptance checklist for the user-facing V17 system. It complements the automated test matrix in [TESTING.md](TESTING.md).

## Entry And Auth

| ID | Use Case | Expected Result | Automated Guard |
|---|---|---|---|
| AUTH-01 | Open `/login` on desktop Chrome | Branded entry screen, language selector, login/register switch, compact form | `frontend/tests/v17I18nUxContracts.test.ts` |
| AUTH-02 | Open `/login` on mobile Chrome | Single-column compact form without horizontal overflow | `pnpm run test:ci` build gate |
| AUTH-03 | Switch language on login/register | Chinese, English, and Korean labels resolve without fallback keys | `frontend/tests/v17I18nUxContracts.test.ts` |
| AUTH-04 | Submit an empty login form | Page-level localized required-field error appears; no browser native bubble | `V17_AuthScreen` noValidate contract |
| AUTH-05 | Login through `/api/auth/login` | Cookie session is set and user is redirected to the requested workspace | `tests/test_auth_api.py` |

## Oracle Input And Chart

| ID | Use Case | Expected Result | Automated Guard |
|---|---|---|---|
| ORACLE-01 | Enter solar birth data and start | Oracle stream starts and the natal input collapses into the workspace | `tests/test_stream_v17_decision_flow.py` |
| ORACLE-02 | Enter lunar birth data | Lunar date converts through the backend and produces a stable chart | `tests/test_lunar_calendar_conversion.py` |
| ORACLE-03 | Enter leap lunar month | Leap-month flag is preserved in the request and conversion path | `tests/test_lunar_calendar_conversion.py` |
| ORACLE-04 | Press `返回填写八字` | Running workspace returns to the birth-info input state | `frontend/tests/v17I18nUxContracts.test.ts` |

## Oracle Surfaces And Mobile

| ID | Use Case | Expected Result | Automated Guard |
|---|---|---|---|
| SURFACE-01 | View oracle on desktop | `命盘总览 / 深度解读 / 幕后观察` are stable top-level surfaces | `frontend/ARCHITECTURE.md` contract |
| SURFACE-02 | View oracle on mobile Chrome | Surfaces render as horizontal tab-like navigation, not oversized action buttons | `V17_SurfaceTabs` build gate |
| SURFACE-03 | Login as `user` | Admin and trace-only surfaces are hidden by access policy | `frontend/lib/accessControl.ts` + build gate |
| SURFACE-04 | Login as `manager` | Oracle core/auxiliary/trace access is available; admin console remains gated | `tests/test_auth_api.py` |
| SURFACE-05 | Login as `admin` | Full admin console, user management, DB/LLM/plugin panels are available | `tests/test_auth_api.py` |

## Verdict And LLM

| ID | Use Case | Expected Result | Automated Guard |
|---|---|---|---|
| VERDICT-01 | Press `掐指一算` | Button changes to `正在掐指一算` with lightweight loading animation | `frontend/tests/v17I18nUxContracts.test.ts` |
| VERDICT-02 | Generate Chinese verdict | Output is concise, judgment-like, and avoids long-form analysis | `tests/test_llm_micro_client_prompt.py` |
| VERDICT-03 | Generate English verdict | Prompt contains concise English contract and short judgement lines | `tests/test_llm_micro_client_prompt.py` |
| VERDICT-04 | Generate Korean verdict | Prompt contains Korean concise contract and short judgement lines | `tests/test_llm_micro_client_prompt.py` |
| VERDICT-05 | LLM stalls or reconnects | Lifecycle state remains visible and Decision Inbox lock releases only on a terminal frame | `frontend/tests/v17StreamGuards.test.ts` |

## Admin And Deployment

| ID | Use Case | Expected Result | Automated Guard |
|---|---|---|---|
| ADMIN-01 | Open DB bridge panel | `/api/v17-admin/db-bridge` routes to the frontend proxy and returns 401/403 when unauthenticated, not 404 | `scripts/check_v17_deploy.sh` |
| ADMIN-02 | Open LLM node panel | Admin panel resolves LLM node endpoints through same-origin proxy | `frontend build` |
| ADMIN-03 | Restart stack on 0.13 | Frontend and backend services restart, health checks pass | `scripts/update_v17_from_git.sh` |
| ADMIN-04 | Deploy behind `dblife.com` | `/login`, `/api/auth/login`, `/api/v17-admin/*`, and `/api/v17/*` route to the correct upstreams | `scripts/check_v17_deploy.sh` |

## Comprehensive Automated Gate

From repo root:

```bash
bash qiazhi/v17_rebirth/scripts/run_automated_tests.sh
```

This runs backend pytest, integration tests, plugin/relation gates, frontend ESLint, production build, and Vitest.
