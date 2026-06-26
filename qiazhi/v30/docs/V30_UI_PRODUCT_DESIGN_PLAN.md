# V30 UI Product Design Plan

Updated: 2026-06-13

## Purpose

This document defines the V30 UI design direction before implementation.

The UI must align with the current V30 backend and module contracts:

- Core Bazi calculation comes first.
- UI stays concise, but exposes strong module-backed calculation.
- Multi-role, multi-locale, and multi-terminal projection use one V30 contract.
- Admin UI is separated from customer reading UI.
- V20 UI can be referenced for product lessons, but V30 must not copy V20 runtime coupling, route style, or monolithic frontend state.

## V20 Reference Lessons

V20 UI provides useful reference in these areas:

| V20 reference | Keep as product idea | Do not copy |
|---|---|---|
| Profile pages | Bazi profile management, profile-to-reading entry, owner/status metadata. | V20 profile route coupling and form-default mutation. |
| Workbench modes | Reading, practitioner calibration, admin observe as role-based surfaces. | One large workbench script controlling all modes. |
| Question chain UI | Grouped questions, active question, feedback buttons, answered memory. | V20-specific question keys/endpoints and hidden debug labels in customer UI. |
| Admin UI | DB, Redis, LLM, training, central brain, mainline status, task registry. | V20 endpoint names, V20 training task model, and broad inline diagnostics. |
| Training UI | Registry, current task, history, quality signals, publish preview. | Direct operator action without V30 pointer/release boundaries. |
| Multi-language labels | zh/en/ko product labels and Bazi terms. | Duplicated static dictionaries inside a single script. |

V30 should absorb V20's information architecture, not its implementation shape.

## Current V30 UI Contract

Existing V30 UI/API foundations:

```text
UI entry: /v30/ui
API prefix: /api/v30
Capabilities: GET /api/v30/ui/capabilities
Create reading: POST /api/v30/readings
View reading: GET /api/v30/readings/{reading_id}/view?role=&locale=&client=
Answer question: POST /api/v30/readings/{reading_id}/questions/{question_id}/answer
Hidden factor feedback: POST /api/v30/readings/{reading_id}/hidden-factor/feedback (legacy/admin-compatible; customer flow should use unified Q&A constraints)
History: GET /api/v30/readings/history
Admin gates: /api/v30/admin/...
```

Active interaction redesign:

```text
docs/V30_UNIFIED_INTERACTION_BRAIN_PLAN.md
```

Customer UI should not expose a separate hidden-factor form. Hidden-factor calibration is a constrained question type inside the same intelligent Q&A section.

Projection dimensions:

```text
role = guest | user | practitioner | admin
locale = zh | en | ko
client = web | mobile | admin
```

Stable view keys:

```text
reading_surface
chart_summary
mainline_card
structure_card
questions
answer_panel
actions
diagnostics
projection_contract
```

## UI Surfaces

V30 UI should be split into two shells.

### Reading Shell

Primary users:

- guest
- user
- practitioner

The Reading Shell question area should be one unified "智能问答" surface:

- Current recommended question.
- Structured controls rendered from `answer_constraints`.
- Optional note field.
- Answer panel with the current question shown above the answer.
- Historical Q&A list.

Hidden-factor discovery must appear as bounded choices such as years, repeated states, intensity, recurrence, and confidence. If the active question requires structured choices, invalid or free-text-only input should ask the user to reselect instead of submitting noisy calibration data.
- admin when doing a reading

Primary job:

```text
Create or open a Bazi profile
-> build deterministic chart
-> view core Bazi calculation
-> inspect practical reading
-> answer intelligent follow-up questions
-> preserve history and hidden-factor feedback
```

Suggested route:

```text
/v30/ui/reading
```

The existing `/v30/ui` can initially redirect to or render this shell.

### Admin Shell

Primary users:

- admin
- future analyst/lab roles if added later

Primary job:

```text
Observe system state
-> manage readings/traces/artifacts
-> inspect LLM state
-> run bounded training/validation gates
-> review module completion and next mainline task
```

Suggested route:

```text
/v30/ui/admin
```

Admin can open a reading in the Reading Shell with `role=admin`.

## Reading Shell Information Architecture

### 1. User And Profile Rail

Purpose:

- Choose current actor/session.
- Select or create Bazi profile.
- Open history.
- Keep repeated readings organized.

Required UI:

- Current actor/session indicator.
- Profile list: display name, owner, birth summary, last reading status, tags.
- Create profile action.
- Open reading action.
- Recent reading list.

V30 contract dependencies:

- `actor_context`
- `/api/v30/readings/history`
- `reading_id`
- future profile storage contract

Initial implementation can use actor/session and reading history before a full durable profile table exists.

### 2. Birth Input And Chart Build

Purpose:

- Collect birth information.
- Show ready/pending/blocked state.
- Prevent fake chart facts.

Required UI:

- Calendar type: solar/lunar.
- Leap month toggle for lunar.
- Birth date.
- Birth time.
- Unknown hour toggle.
- Birth place.
- Timezone.
- True solar time toggle.
- Gender with unknown option.
- Target year.
- Submit/build chart.
- Conversion status and missing requirements.

Customer-facing output:

- Ready chart: four pillars and basic time context.
- Pending/blocked: clear reason and required next input.

V30 contract dependencies:

- `birth_input`
- `chart_build`
- `reading_surface.chart_status`
- `reading_surface.time_context`

### 3. Core Chart And Pillar Panel

Purpose:

- Make the user feel the system actually calculated Bazi, not only answered a chat prompt.

Required UI:

- Four pillars: year, month, day, hour.
- Day master.
- Ten gods per pillar.
- Hidden stems.
- Five-element distribution.
- Branch relations.
- Root/vault facts.
- Current luck cycle.
- Flow year.
- Flow month.
- Six-pillar context when available.

Role behavior:

- guest: compact pillar summary.
- user: readable chart facts and short explanations.
- practitioner: chart facts plus evidence ids and boundary notes.
- admin: full diagnostics through `diagnostics`, not customer surface.

V30 contract dependencies:

- `chart_summary`
- `reading_surface.core_bazi_reading`
- `reading_surface.time_context`
- `diagnostics.bazi_context` for diagnostic roles

### 4. Core Judgment Panel

Purpose:

- Expose the real M3-M5 module strength without dumping internals to normal users.

Required UI:

- Structure summary.
- Strength candidate.
- Structure pattern candidate.
- Useful-god candidate path.
- Ten-god energy band summary.
- Confidence/boundary text.
- Evidence count or readable evidence labels.

Role behavior:

- user: "current candidate path" and "why not fixed conclusion yet" in plain language.
- practitioner: candidate scores, competing paths, counter-evidence, unresolved requirements.
- admin: model signal summary, ranked decisions, policy versions, trace.

V30 contract dependencies:

- `mainline_card`
- `structure_card`
- `diagnostics.ranked_decisions`
- `diagnostics.model_signal_summary`
- `diagnostics.internal_bazi_context`

### 5. Practical Reading Panel

Purpose:

- Deliver the business result of Bazi calculation.

Required domains:

- overall summary
- career
- wealth
- relationship
- health
- timing

Each domain card should show:

- short takeaway
- basis summary
- timing note
- action prompt or calibration prompt
- boundary/uncertainty when needed

V30 contract dependencies:

- `reading_surface.reading_summary`
- `reading_surface.domain_cards`
- `answer_panel`

### 6. Intelligent Question Panel

Purpose:

- Ask chart-specific, module-backed follow-up questions.
- Build a continuous question-answer chain.
- Capture hidden-factor clues without changing chart facts.

Required UI:

- Visible next question.
- Structured answer options.
- Free-text answer.
- Confidence selector when supported.
- Feedback tags.
- Submit answer.
- Answer panel refresh.
- Question history.
- Known user signals summary.

Rules:

- Customer sees only `user_question` and suitable structured options.
- Internal calibration questions stay hidden unless practitioner/admin.
- Hidden factors are feedback clues, never deterministic chart facts.
- Question training tunes question strategy only.

V30 contract dependencies:

- `questions`
- `reading_surface.next_question`
- `reading_surface.visible_next_question_id`
- `answer_panel`
- `interaction_state`
- `diagnostics.question_dialogue_graph`
- `diagnostics.adaptive_question_diagnostics`

## Admin Shell Information Architecture

### 1. System Overview

Required UI:

- API health.
- Runtime repository/cache status.
- Current environment.
- Current module completion gate.
- Current next mainline task.
- Recent validation status.
- Recent errors or blocked states.

Useful endpoints:

- `/api/v30/health`
- `/api/v30/admin/mainline/main-module-completion-review`
- `/api/v30/admin/mainline/selection`
- `/api/v30/admin/mainline/selection-after-release-pause`

### 2. Reading And Trace Management

Required UI:

- Search readings by actor/session/reading id.
- Open user/practitioner/admin projection side by side.
- View trace.
- View hidden factor state.
- View question outcomes.
- View answer refresh result.

Useful endpoints:

- `/api/v30/readings/history`
- `/api/v30/readings/{reading_id}`
- `/api/v30/readings/{reading_id}/view`
- `/api/v30/admin/runs/{reading_id}/trace`
- `/api/v30/admin/runs/{reading_id}/question-replay`
- `/api/v30/readings/{reading_id}/hidden-factor/state`

### 3. DB And Artifact Management

Required UI:

- Runtime readings/traces.
- Validation artifacts.
- 518K artifacts.
- Policy candidates.
- Quarantine records.

Initial rule:

- View/search/export first.
- No destructive action in the first Admin UI version.

Useful endpoints:

- `/api/v30/admin/validation/artifacts`
- `/api/v30/admin/validation/518k/artifacts`
- `/api/v30/admin/policies/lineage`
- `/api/v30/admin/policies/question/comparison`

### 4. LLM Management

Required UI:

- Provider readiness.
- Current config status.
- Last smoke result.
- Fallback/drift rejection state.
- Prompt/context pack view.
- Role/locale output acceptance.

Rules:

- LLM never produces chart facts.
- LLM context must be task-specific, not a growing global prompt dump.
- Live provider smoke is explicit-only.

Useful endpoints:

- `/api/v30/admin/llm/bazi-context-prompt-readiness`
- `/api/v30/admin/llm/bazi-answer-generator-readiness`
- `/api/v30/admin/llm/bazi-output-acceptance-readiness`
- `/api/v30/admin/llm/bazi-training-synthetic-readiness`
- `/api/v30/admin/llm/bazi-role-locale-production-smoke`
- `/api/v30/admin/llm/bazi-closeout`

### 5. Training UI

Required UI:

- Run bounded training.
- Show training families.
- Show extracted signals.
- Show candidate preview.
- Show failed-candidate quarantine.
- Show policy comparison.
- Show lineage and rollback metadata.

Rules:

- Routine UI may run targeted training gates.
- Pointer promotion must be explicit.
- Training cannot mutate deterministic chart facts.

Useful endpoints:

- `/api/v30/admin/training/run`
- `/api/v30/admin/training/system-closeout`
- `/api/v30/admin/training/candidate-quarantine`
- `/api/v30/admin/policies/question/comparison`
- `/api/v30/admin/policies/lineage`

### 6. Synthetic And Validation UI

Required UI:

- Synthetic tier status.
- Interaction loop status.
- Training pipeline status.
- Real-case calibration status.
- Business acceptance status.
- 518K sample/shard/full boundary.

Rules:

- Full pytest, synthetic all, full 518K, release gates are major-node actions.
- Routine UI defaults to targeted validation only.

Useful endpoints:

- `/api/v30/admin/validation/synthetic-coverage-manifest`
- `/api/v30/admin/validation/518k/readiness-matrix`
- `/api/v30/admin/business/real-bazi-acceptance`
- `/api/v30/admin/business/reading-regression-pack`
- `/api/v30/admin/business/answer-refresh-regression`
- `/api/v30/admin/business/boundary-blocked-input-regression`
- `/api/v30/admin/business/api-contract-freeze`
- `/api/v30/admin/business/acceptance-closeout`
- `/api/v30/admin/business/steady-state`

## Role Visibility Matrix

| Surface | guest | user | practitioner | admin |
|---|---|---|---|---|
| Birth input | limited | full | full | full |
| Bazi profile list | own/session only | own/session only | client/session scoped | all diagnostic scope |
| Four pillars | compact | full readable | full + evidence | full + diagnostics |
| Luck/flow/six-pillar | summary | full readable | full + boundary | full + trace |
| Ten-god/five-element facts | summary | readable | detailed | diagnostic |
| Ranked decisions | hidden as internals | readable candidate path | candidates + counter-evidence | full payload |
| Practical reading | preview | full | full + evidence | full + diagnostics |
| Smart questions | limited | full visible questions | visible + calibration | visible + internal |
| Hidden factor state | no raw state | feedback only | diagnostic summary | full diagnostic |
| LLM status | hidden or simple fallback | simple status | provider/fallback summary | full LLM diagnostics |
| Training signals | hidden | hidden | hidden by default | visible |
| Policy pointers | hidden | hidden | hidden by default | visible |

## Terminal Layout

### Web

- Left rail: profile/history.
- Main content: birth input, chart, practical reading.
- Right rail: question chain and answer panel.
- Practitioner/admin can open diagnostics drawer.

### Mobile

- Top: profile/current reading.
- Tabs: Input, Chart, Reading, Questions.
- Bottom action bar: build chart, submit answer, save profile.
- Diagnostics hidden except admin client.

### Admin

- Side navigation: Overview, Readings, DB/Artifacts, LLM, Training, Validation, Mainline.
- Dense tables and status panels.
- Reading projection can open in a split panel.

## Design Principles

- Core chart facts must be visible before question interaction.
- Cards may be used for repeated domain/profile rows; avoid card-inside-card layouts.
- Customer UI should avoid raw ids, policy payloads, training language, and debug labels.
- Practitioner/admin UI may show internal ids, but they must be grouped under diagnostics.
- Every action should map to a V30 endpoint and contract.
- Empty and blocked states are first-class; never fake a ready chart.
- Locale changes must not change chart facts.
- Role changes must not change chart facts.
- Client changes must not change chart facts.

## First Implementation Milestones

### UI1 Reading Shell Foundation

- Route shell.
- Role/locale/client controls.
- BirthInput form.
- Reading view refresh.
- Mobile/web layout split.
- No admin management yet.

Status 2026-06-10: implemented first pass.

- Reading Shell now uses a left profile/role rail, central Bazi workbench, and right question dock.
- Visual style is concise and Bazi-oriented: paper surface, ink text, jade actions, cinnabar pillar emphasis, and restrained gold labels.
- BirthInput form now includes actor/session/profile fields so later profile management can attach without changing the reading contract.
- Core result order is chart/calculation first, then time context, practical domain cards, answer panel, and intelligent questions.
- This pass does not implement the Admin Shell yet.

### UI2 Profile And History Layer

- Actor/session controls.
- Reading history list.
- Temporary profile abstraction over readings.
- Open existing reading.

Status 2026-06-10: implemented first pass.

- Reading Shell left rail now includes a history panel.
- History is loaded through `/api/v30/readings/history` using the current `actor_id` and `session_id`.
- Users can open an existing reading from the history list and refresh the current projection with the active role/locale/client.
- This version intentionally treats history rows as lightweight Bazi profile records until a durable profile table is introduced.
- No destructive history or profile operations are exposed.

### UI3 Core Bazi Reading Page

- Four pillars.
- Luck/flow/six-pillar.
- Ten-god/five-element facts.
- Domain reading cards.
- Candidate path summary.

Status 2026-06-10: implemented first pass.

- Core Bazi Reading now renders deterministic fact integrity before any question interaction.
- Four pillars are emphasized as the top calculation result.
- `base_fact_explanations` are surfaced as readable explanation cards for day master, ten gods, five elements, and roots/vaults.
- Five-element distribution is shown as weighted bars instead of raw chips.
- Visible ten gods and hidden ten gods are separated into structured rows.
- M5 strength / structure / useful-god candidates are shown as bounded candidate-path cards with confidence and boundary text.
- Practical domain summaries remain visible before the question dock.

Validation 2026-06-10:

```text
node --check frontend/app.js
passed

pytest -q tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/unit/test_presentation_projection.py::test_customer_reading_surface_hides_internal_bazi_context
3 passed

python3 -m compileall -q v30
passed
```

Known validation note:

- Full `tests/unit/test_presentation_projection.py` currently has two pre-existing question-order expectations that still assume career is first; current question policy can rank relationship first. UI3 does not change backend question ranking.

### UI4 Intelligent Question UX

- Visible next question.
- Structured options.
- Free-text answer.
- Answer panel refresh.
- Question history.
- Role-gated calibration visibility.

Status 2026-06-10: implemented first pass.

- The right-side question dock now has a single current-question card driven by `reading_surface.next_question` or the top ranked `questions[]` item.
- Structured options and free-text answers are submitted through the existing answer API without changing deterministic chart facts.
- The answer panel refreshes after submission and keeps a local question chain so the user can see the current interaction path.
- Hidden-factor feedback has a dedicated form for special years and repeated states; it writes to `/api/v30/readings/{reading_id}/hidden-factor/feedback`.
- `interaction_state` returned by answer/feedback calls is retained by the UI so known signals can be summarized without exposing internal calibration payloads to normal users.
- Candidate questions remain visible as a compact queue, while internal diagnostics stay under diagnostic projections.

Validation 2026-06-10:

```text
node --check frontend/app.js
passed

pytest -q tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace
2 passed

python3 -m compileall -q v30
passed
```

Known validation note:

- `tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading` currently fails on a stale LLM draft version expectation: the test expects `v30.llm_answer_draft_call.v1`, while the runtime now emits `v30.bazi_llm_answer_draft_call.v1`. UI4 did not change that backend namespace.

### UI5 Admin Shell Foundation

- Admin navigation.
- System overview.
- Reading/trace lookup.
- Main module completion review.

Status 2026-06-10: implemented first pass.

- `/v30/ui/?role=admin&surface=admin` now renders a dedicated Admin Shell instead of the customer Reading Shell.
- Admin navigation includes Overview, Main Modules, Reading / Trace, and Contracts.
- System overview reads health, UI capabilities, mainline selection, and main-module completion review.
- Main Modules renders the module completion matrix and review checks from `/api/v30/admin/mainline/main-module-completion-review`.
- Reading / Trace supports admin projection lookup and trace lookup by `reading_id`, plus role-gated admin history search by actor/session.
- Contracts lists UI/API capabilities and endpoint readiness.
- Admin endpoint requests have client-side timeouts so slow observability endpoints appear as partial readiness instead of blocking the whole shell.
- The first Admin Shell is read-only: it does not delete data, mutate chart facts, run heavy validation, run live LLM smoke, or promote policy pointers.

Validation 2026-06-10:

```text
node --check frontend/app.js
passed

pytest -q tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace
2 passed

python3 -m compileall -q v30
passed
```

Runtime note:

- 9030 was restarted after this pass so the latest static UI and current admin routes are served. `/api/v30/admin/mainline/main-module-completion-review` can still be slow in the live environment; the Admin Shell treats it as partial readiness when it exceeds the UI timeout.

### UI6 Admin LLM / Training / Validation

- LLM readiness and smoke status.
- Training run/candidate/quarantine.
- Synthetic/business/518K validation panels.

Status 2026-06-10: implemented first pass.

- Admin Shell now includes LLM, Training, and Validation tabs.
- LLM tab reads Bazi context/prompt readiness, answer generator readiness, output acceptance, training/synthetic readiness, role/locale smoke, and closeout endpoints.
- Training tab reads system closeout and candidate quarantine, and exposes bounded `/api/v30/admin/training/run` with explicit family selection.
- Training UI does not perform policy pointer promotion; it only calls the existing bounded training endpoint.
- Validation tab reads synthetic coverage, validation artifacts, 518K readiness/artifacts, business acceptance, and business steady-state status.
- All UI6 admin fetches use client-side timeouts so slow observability gates show partial readiness instead of blocking the whole admin shell.
- Full pytest, synthetic all, live LLM smoke, full 518K, and pointer writes remain major-node or explicit-operator actions, not default UI actions.

Validation 2026-06-10:

```text
node --check frontend/app.js
passed

pytest -q tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace
2 passed

python3 -m compileall -q v30
passed

curl /api/v30/admin/llm/bazi-context-prompt-readiness
returned v30.bazi_llm_context_prompt_readiness.v1, 10/10 checks passed

curl /api/v30/admin/validation/artifacts?limit=2
returned postgres artifact search results
```

Runtime note:

- `/api/v30/admin/training/system-closeout` was slow in the live 9030 environment during this pass and was treated as a slow observability endpoint. The UI timeout keeps the Training tab usable and reports partial readiness.

### UI7 Shell Closeout

Status 2026-06-10: implemented first pass.

- The top bar now exposes stable Reading and Admin entry points.
- Admin Shell supports deep links through `?role=admin&surface=admin&tab=...` for `overview`, `modules`, `readings`, `llm`, `training`, `validation`, and `contracts`.
- UI1-UI6 now form a complete first usable V30 UI surface:
  - customer Bazi calculation and reading flow
  - profile/history projection
  - core Bazi chart facts and candidate decisions
  - intelligent question and hidden-factor feedback
  - admin system/reading/trace/module review
  - admin LLM/training/validation observation
- This closeout does not change runtime API contracts and does not run full pytest, synthetic all, live LLM smoke, full 518K, or policy pointer writes.

Validation 2026-06-10:

```text
node --check frontend/app.js
pytest -q tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace
python3 -m compileall -q v30
```

### UI8 Multi-Step Reading Navigation

Status 2026-06-10: implemented first pass.

- Reading Shell no longer presents all calculation, reading, and question surfaces as one long mixed page.
- Customer reading now uses a four-step workflow:
  - `1 出生资料`: actor/session/profile and BirthInput.
  - `2 命盘`: role surface, summary, core chart facts, four pillars, five elements, ten gods, M5 candidate path, six-pillar/luck/flow context.
  - `3 解读`: concise business reading, domain cards, answer panel, and quick options.
  - `4 问答`: answer panel, intelligent question card, structured options, free-text answer, local turn chain, and hidden-factor feedback.
- Direct URLs support `?step=input|chart|reading|questions`; successful BirthInput creation and history opening move to `chart`.
- Admin Shell keeps its existing tab navigation and is not mixed into the customer reading workflow.
- This change is frontend-only and preserves the existing `/api/v30` contracts.

Validation 2026-06-10:

```text
node --check frontend/app.js
passed

pytest -q tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace
2 passed

python3 -m compileall -q v30
passed

curl /v30/ui/?role=user&step=chart
returned static shell

curl /v30/ui/?role=admin&surface=admin&tab=training
returned static shell
```

### UI9 Product Navigation, Auth, And Profile Pages

Status 2026-06-10: implemented first pass.

- Top navigation now exposes first-class entries for 登录, 档案, 测算, Admin, and 训练.
- Added minimal V30 product auth API:
  - `POST /api/v30/auth/register`
  - `POST /api/v30/auth/login`
  - `GET /api/v30/auth/session`
  - `POST /api/v30/auth/logout`
- Added minimal Bazi profile API:
  - `GET /api/v30/profiles`
  - `POST /api/v30/profiles`
- Added 登录/注册 page at `/v30/ui/?page=auth`.
- Added 八字档案 page at `/v30/ui/?page=profiles`.
- Product auth accepts V30 PBKDF2 passwords and V20 stored password hashes for imported accounts.
- Profile records store BirthInput metadata only; chart facts are still computed by the existing reading runtime.
- V20 profile migration maps legacy `year/month/day/hour/minute` into V30 `birth_date` and `birth_time`.
- Profile entries can prefill the multi-step reading workflow for calculation.
- Admin and training are visible as top-level navigation entries, while training still uses bounded V30 admin endpoints and does not promote policy pointers by default.

Boundary:

- This is a lightweight product account/session layer over the existing `actor_id/session_id` contract.
- V20 product data migration is a one-time data operation, not a persistent admin feature.
- Imported V20 users use their original stored password hash; V30 login verifies it without exposing the hash.
- It does not introduce organization permissions, payment, membership, OAuth, or production-grade identity policy.
- It does not mutate chart facts, ranked decisions, hidden-factor state, or policy pointers.

### UI10 Structure Dynamics In Reading Page

Status 2026-06-10: implemented first pass.

- The Reading Shell 解读 step now exposes `reading_surface.structure_dynamics` as a first-class module-backed section.
- The section projects M3 dynamic structure paths, conflict/resolution families, mechanism counts, domain path counts, and top paths in customer-safe language.
- Normal users see a `customer_summary` projection; practitioner/admin projections can inspect the same section at `diagnostic` detail level through the role contract.
- The projection is explicitly bounded as reading context, not a fixed geju verdict, event verdict, chart fact mutation, or raw model-score dump.
- The frontend renders structure dynamics between the reading summary and domain cards so it supports the actual Bazi interpretation path.

Validation 2026-06-10:

```text
python3 -m compileall -q v30
passed

node --check frontend/app.js
passed

pytest -q tests/unit/test_presentation_projection.py tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params
7 passed
```

### UI11 Admin Runtime DB / Redis / LLM Configuration

Status 2026-06-10: implemented first pass.

- Admin Shell now has a dedicated `DB / Redis` tab for V30 runtime database and cache configuration.
- Added V30-native admin runtime endpoints:
  - `GET /api/v30/admin/runtime/config`
  - `GET /api/v30/admin/runtime/db`
  - `POST /api/v30/admin/runtime/db/config`
  - `POST /api/v30/admin/runtime/db/apply-schema`
  - `GET /api/v30/admin/runtime/redis`
  - `POST /api/v30/admin/runtime/redis/config`
  - `GET /api/v30/admin/runtime/llm`
  - `POST /api/v30/admin/runtime/llm/config`
  - `POST /api/v30/admin/runtime/llm/test`
- DB status shows active repository, V30 Postgres connection, table counts, missing schema tables, and no secret values.
- Redis status shows configured URL presence, ping, DB index, V30 keyspace, and key count. Redis remains cache, not authority.
- LLM admin page can save V30 LLM config, probe runtime status/models, and run a connectivity test.
- DB/Redis config saves are marked restart-required because repository/cache are bound at app startup. LLM config is read at call time.
- Measurement page now uses the configured LLM path when enabled; provider plain-text output can be wrapped into the required Bazi output schema and still passes drift/acceptance gates before replacing the rule answer.

Live verification 2026-06-10 on `9030`:

```text
GET /api/v30/health
repository=postgres, redis_cache=true

GET /api/v30/admin/runtime/db
status=connected, database=qiazhi_v30, schema_table_count=7

GET /api/v30/admin/runtime/redis
status=connected, ping=true

GET /api/v30/admin/runtime/llm
status=ready, provider=ollama_native, model=gemma4:latest

POST /api/v30/admin/runtime/llm/test
status=ok

POST /api/v30/readings
status=ready, chart facts deterministic

GET /api/v30/readings/{reading_id}/view?role=admin
answer_panel.source=llm_bazi_answer_draft
llm_metadata.status=accepted
```

## Default Validation For UI Work

Routine UI tasks should run targeted checks only:

```text
node --check frontend/app.js
pytest -q tests/test_v30_scaffold.py::test_ui_capabilities_expose_projection_params tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace
python3 -m compileall -q v30
```

Full pytest, synthetic all, 518K sample, and live browser smoke are reserved for larger UI milestones.
