# V50 Deep Cleanup and Large-file Governance v1

> Status: `FIRST_CONSOLIDATION_SLICE_COMPLETE`
>
> Date: `2026-07-19`
>
> Production deployment: `NOT REQUESTED`

## 0. Decision

V50 needs a deep cleanup, but not a deletion campaign and not a rewrite from
zero. The repository contains four different things that must be treated
differently:

```text
current product and domain authority
frozen technical proofs
active-retiring runtime
evidence, generated data and media masters
```

The cleanup rule is:

> Remove duplicate authority immediately; archive superseded decisions;
> retire old runtime by usage evidence; preserve professional evidence and
> source media; split active files only along stable responsibility boundaries.

## 1. First Slice Completed

### 1.1 Authority cleanup

- Graph v1 relations now enter the World as
  `experimental_tool_observation`, not `neutral_relation`.
- authority mapping is exhaustive; an unknown authority raises an error rather
  than silently becoming production.
- the independent pattern first look has regression coverage proving that Graph
  v1 observations are absent.
- the runtime authority audit now checks this invariant.

### 1.2 Dependency cleanup

- production code no longer imports `scripts.*`;
- OneCanvas and Mingli Lab builders moved into `apps/product` application
  modules;
- old script paths remain as five-line CLI compatibility wrappers;
- the architecture purification audit permanently rejects future
  `production -> scripts` imports.

### 1.3 Calendar and DaYun convergence

Canonical deterministic owners now exist for:

```text
Jiazi and pillar dependency catalog
year-to-month legal choices
day-to-hour legal choices
annual Ganzhi
DaYun direction
structural DaYun sequence
exact DaYun sequence and current period
```

World compilation, personal timing, OneCanvas and fixture generation consume
these owners instead of keeping separate implementations.

### 1.4 Documentation cleanup

- completed execution plans and superseded architecture/product proposals were
  moved under `docs/archive/`;
- C1, C1R, old C2A and predecessor C2A-R proof documents were moved to
  `docs/archive/proofs/`;
- current authority remains limited to the four canonical entry points and the
  explicitly listed active contracts in `docs/README.md`;
- archived documents retain archaeological and regression value but cannot
  authorize implementation.

### 1.5 Disposable and generated artifacts

- repository caches and compiled Python residue were removed;
- four unreferenced Abu sample frames were removed;
- referenced animation masters, web assets, posters and transition anchors were
  retained;
- the OneCanvas generated fixture was changed from pretty-printed JSON to
  compact JSON, reducing it from about `4.90 MB` to `2.94 MB` without changing
  semantics.

## 2. What Was Deliberately Not Deleted

### Reports

`reports/` contains blind-run evidence, acceptance material, voice review audio
and intermediate checkpoints. File age alone is not sufficient proof that an
artifact is disposable. Reports need a separate manifest-led retention pass;
they must not be bulk deleted or deduplicated in a way that breaks hashes and
review provenance.

### Abu animation assets

Large animated WebP and opening-scene assets are referenced production media.
Source, transition anchor and delivery copies serve different roles. Future
optimization should produce measured delivery variants and preserve visual
parity, transparency, anchor position and browser fallback.

### Legacy L5 shell

The legacy shell is still served at `/` and `/app`. Its large JavaScript and CSS
are not candidates for a cleanup refactor. They should be retired after route
usage, replacement parity, migration and rollback evidence exist.

### Frozen prototypes

C1, C1R and old C2A remain useful as Inspector, semantic identity proof and
functional fixture. They receive no new independent product behavior, but their
fixtures and tests remain until the canonical Scene Compiler replaces them.

## 3. Large-file Decisions

| File | Current size | Decision | Timing |
|---|---:|---|---|
| `static/l5/app.js` | 3425 lines | retire, do not split | after root-route parity |
| `static/l5/styles.css` | 2996 lines | retire, do not redesign | with legacy shell |
| `core/mingli_agent/reasoner.py` | 2837 lines | split by model client, stage orchestration, prompts, normalization and semantic checks | after professional baseline lock |
| `product/agent_api.py` | 2010 lines | split request contracts, route groups and projection helpers | next application-consolidation slice |
| `core/life_case/service.py` | 1148 lines | split baseline/domain, reality evidence, temporal review and projection | after typed provenance contract |
| `core/state/contracts.py` | 1132 lines | keep temporarily; split by stable schema family only | when research-state consumers converge |
| `experience/canvas.py` | 1043 lines | split contracts, compiler, diff, disclosure and context, with a compatibility facade | before Scene Compiler convergence |
| OneCanvas `prototype.js` | 1109 lines | split commands, state/history, playback and render orchestration | after R1 human behavior is frozen |
| OneCanvas `fixture.json` | 2.94 MB compact | keep generated and compact; later replace static delivery with server compile/cache | after canonical Scene API |

The first safe large-file split is already complete:

```text
CLI wrappers
→ application fixture builders
→ canonical pillar-cycle and DaYun domain modules
```

This removed dependency inversion and duplicate algorithms without changing the
professional reasoning chain.

## 4. Why the Largest Files Are Not All Split Now

Line-count-only splitting creates cosmetic modules while preserving the same
coupling. Several active files sit directly on pending product or professional
gates:

- splitting OneCanvas before R1 review can change the interaction baseline;
- splitting the Reasoner before blind adjudication makes professional
  regression harder to attribute;
- splitting LifeCase before provenance contracts can freeze the wrong storage
  boundary;
- splitting legacy L5 invests in a surface scheduled for retirement.

Therefore a file over 800 lines requires review and a file over 1500 lines must
have a split or retirement plan, but implementation follows authority gates.

## 5. Cleanup Matrix

| Area | Keep | Extract / adapt | Archive / freeze | Delete |
|---|---|---|---|---|
| Chart and calendar | deterministic facts | shared pillar and DaYun services | old helper locations | duplicate helpers after parity |
| Cognition | LLM Reasoner behavior | prompts, normalization and checks later | old benchmark runbooks | no professional evidence |
| Relation / path | v1 replay adapter | future versioned V2 | experimental authority claims | only after consumer parity |
| LifeCase | formal revisions | typed provenance adapter | historical shapes read-only | blocked write shapes |
| Canvas | C0 contracts and R1 candidate | canonical Scene Compiler | C1/C1R/C2A proofs | duplicate product evolution |
| UI | Experience Shell and R1 candidate | shared components | legacy root active-retiring | caches and dead samples |
| Docs | current four entry points | explicit governing links | superseded plans and proofs | generated residue only |
| Reports | locked evidence | retention manifest later | completed checkpoints | only manifest-approved disposable runs |
| Media | masters and referenced delivery | optimized variants later | former versions if unreferenced | temporary samples and caches |

## 6. Next Cleanup Slices

### Slice 2 — after R1 human product gate

```text
freeze observed OneCanvas behavior
→ split prototype controller by command/state/playback/render responsibility
→ keep one user product surface
→ preserve Inspector and fixture tests only
```

### Slice 3 — before Scene Compiler convergence

```text
split Canvas contracts/compiler/diff/disclosure/context
→ introduce compatibility facade
→ prove role-filtered absence and deterministic output
```

### Slice 4 — after professional baseline adjudication

```text
lock Reasoner behavior corpus
→ extract model transport and prompts
→ extract local normalization and semantic checks
→ compare outputs before and after split
```

### Slice 5 — route retirement

```text
observe legacy usage
→ prove Experience parity
→ migrate critical actions
→ switch root with rollback
→ remove L5 runtime and legacy API readers
```

## 7. Gates and Boundaries

This cleanup does not authorize:

- Relation Atlas or Path Core V2 implementation;
- a React or whole-frontend rewrite;
- rewriting historical LifeCase cognition;
- deleting reports or professional review evidence;
- deploying OneCanvas to production;
- treating machine regression as R1 product or Mingli professional approval.

Current stage remains:

```yaml
deep_cleanup_slice_1: COMPLETE
authority_leak_machine_fix: PASS
production_to_scripts_dependency: CLOSED
canonical_calendar_and_dayun_service: ACTIVE
documentation_authority_cleanup: COMPLETE
large_file_governance: FROZEN
architecture_consolidation_gate: NOT_PASSED
R1_human_product_gate: PENDING
professional_blind_gate: PENDING
production_release: BLOCKED
```

## 8. Machine Verification

```yaml
focused_cleanup_and_authority_regression: 103_passed
full_python_regression: 376_passed
experience_typescript_typecheck: PASS
architecture_purification_audit: PASS
runtime_authority_audit: PASS
production_imports_scripts: 0
production_deployment: false
```

These results prove behavioral and architecture preservation for this cleanup
slice. They do not satisfy the pending R1 human product gate or professional
Mingli blind gate.
