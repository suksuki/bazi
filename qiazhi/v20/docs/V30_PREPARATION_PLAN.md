# V30 Preparation Plan

Updated: 2026-05-20

## Goal

V30 is a new independent runtime built from V20 lessons, not a V20 rename or in-place refactor.

The immediate goal is to freeze V20 as a reference implementation, extract reusable assets, define V30 contracts, and then start a clean `~/bazi/qiazhi/v30` codebase with independent service, database, Redis, runtime files, tests, and UI.

## Non-Negotiable Isolation

V30 must not disturb V20.

Required isolation:

| Area | V20 | V30 |
|---|---|---|
| Code root | `~/bazi/qiazhi/v20` | `~/bazi/qiazhi/v30` |
| Python package | `v20` | `v30` |
| Runtime files | `v20/.runtime/...` | `v30/.runtime/...` |
| API prefix | `/api/v20/...` | `/api/v30/...` |
| UI prefix | `/v20/ui/...` | `/v30/ui/...` |
| Postgres | `v20_*` tables/schema | `v30_*` tables/schema |
| Redis | `v20:*` or current V20 keys | `v30:*` only |
| Service profile | `linux_0_13` / V20 ports | V30 profile and ports only |
| Tests | `tests/test_v20_*` | `tests/test_v30_*` |
| Artifacts | V20 training paths | V30 training paths |

No V30 module may import `v20.*` at runtime. V20 may be used only as a reference during migration and by explicit offline conversion scripts.

## V20 Freeze Policy

V20 becomes the final reference branch for:

- Existing runtime behavior.
- Existing synthetic and replay cases.
- Existing training and pointer mechanisms.
- Existing UI/role projection lessons.

Allowed V20 work after this point:

- Documentation.
- Export scripts.
- Critical bug fixes that block V30 asset extraction.
- Read-only review and comparison tests.

Avoid:

- New V20 feature branches.
- More V20 question-system rewrites.
- More V20 UI expansion.
- More V20 training surfaces unless required to export stable assets.

## Preparation Work

### P0: Reference Snapshot

- Create a git tag or commit label for the current V20 reference state.
- Record current runtime smoke status.
- Save representative V20 runtime outputs for comparison.

Suggested reference cases:

- Output controls authority / 食神制杀.
- Wealth channel / 食伤生财.
- Resource supports self / 印星承身.
- Peer supports self / 比劫承身.
- Time-triggered clash or activation.
- Missing time context.
- Useful-god question.
- Relationship projection.
- Health boundary.
- Role visibility boundary.

### P1: Asset Review

Create a migration decision for each V20 subsystem:

- Reuse code directly.
- Reimplement from idea.
- Convert data only.
- Keep as reference only.
- Retire.

Primary output:

```text
docs/V30_FROM_V20_ASSET_REVIEW.md
```

### P2: V30 Contract

Define V30 data contracts before implementation:

- `ChartContext`
- `FeatureEvidence`
- `StructureState`
- `MainlineState`
- `QuestionIntent`
- `BaziQuestionAnchor`
- `AnswerContext`
- `RoleProjection`
- `LocaleRendering`
- `ClientPresentationModel`
- `ValidationCase`

Primary output:

```text
docs/V30_ARCHITECTURE_CONTRACT.md
```

### P3: Storage and Runtime Boundary

Define separate V30 persistence:

Suggested Postgres tables:

```text
v30_readings
v30_runtime_traces
v30_feedback_events
v30_validation_cases
v30_policy_pointers
v30_artifacts
```

Suggested Redis key prefix:

```text
v30:{env}:{resource}:{id}
```

Required runtime env variables:

```text
V30_DATABASE_URL
V30_REDIS_URL
V30_REDIS_PREFIX=v30
V30_RUNTIME_DIR=./.runtime
V30_HOST=127.0.0.1
V30_PORT=<not used by V20>
```

V30 must not read `V20_DATABASE_URL`, V20 Redis keys, or V20 runtime pointer files.

### P4: API and UI Model

Define a smaller API surface:

```text
POST /api/v30/readings
GET  /api/v30/readings/{reading_id}
GET  /api/v30/readings/{reading_id}/view?role=&locale=&client=
POST /api/v30/readings/{reading_id}/questions/{question_id}/answer
POST /api/v30/feedback
GET  /api/v30/admin/runs/{reading_id}/trace
```

Ordinary UI endpoints must return a presentation model, not the full runtime trace.

Target payload sizes:

- User view: under 80 KB.
- Practitioner view: under 160 KB.
- Admin trace: no strict small payload requirement, but paginated or sectioned when possible.

### P5: Initial V30 Scaffold

After contracts are agreed:

```text
~/bazi/qiazhi/v30/
  v30/
    core/
    structure/
    mainline/
    questions/
    answer/
    presentation/
    api/
    storage/
    validation/
    learning/
  frontend/
  tests/
  docs/
  scripts/
```

No file should be copied wholesale from V20 unless it has been explicitly marked as direct-reuse safe in the asset review.

## First V30 Milestone

The first V30 milestone is not parity with V20.

It is a minimal verified loop:

```text
ChartContext
-> FeatureEvidence
-> StructureState
-> MainlineState
-> AnchoredQuestion[]
-> AnswerContext
-> DeterministicAnswer
-> Role/Locale/Client ViewModel
```

Acceptance:

- No import from `v20.*`.
- No V20 DB table touched.
- No V20 Redis key touched.
- No V20 runtime file read or written.
- At least 10 converted V20 synthetic cases pass.
- User view questions all have bound anchors.
- LLM, if enabled later, receives only verified `AnswerContext`.
