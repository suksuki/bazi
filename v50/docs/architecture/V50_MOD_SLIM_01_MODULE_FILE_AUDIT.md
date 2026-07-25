# V50 MOD-SLIM-01 Module and Large-file Audit

Status: `INVENTORY CLOSED / MOD-SLIM-02 CLOSED_PASS`

Baseline: `af9b8287`

Closeout implementation: through `a2163569`

Scope: tracked V50 Python, TypeScript, JavaScript and CSS source. Generated
runtime data, caches, reports, archived evidence, tests and media are excluded.

## 1. Result

The repository does have large files, but line count is not the primary defect.
The actionable defect is a smaller set of active files that combine several
authority or application responsibilities. Generated bundles, frozen review
fixtures and retiring shells must not be mechanically split.

```text
source files scanned                         223
files over 500 lines                          40
files over 1,000 lines                        14

active runtime source files                  134
active runtime files over 500 lines           27
active runtime files over 1,000 lines         10

high-confidence mixed-responsibility files     9
unreachable product Python modules              0
PostgreSQL DDL definition owners                1
PostgreSQL DDL executors                         1
explicit transitional adapters/read fallbacks   5
```

The active-runtime count excludes offline scripts, generated Experience output,
R1 locked assets, internal tools and design studies. It still includes the L5
shell because `/` and `/app` currently serve it.

### MOD-SLIM-02 closeout

```text
source files over 500 lines                  40 -> 37
source files over 1,000 lines                14 ->  9
active runtime files over 500 lines          27 -> 24
active runtime files over 1,000 lines        10 ->  5
high-confidence mixed-responsibility files    9 ->  0
```

All nine mixed-responsibility files were separated by authority boundary. The
remaining active files over 1,000 lines are the HTTP-only Agent router, the
presentation-only Experience stylesheet, and three L5/old-Theater legacy
bundles. FLOW-SLIM-02 later retired the L5 page, JavaScript and stylesheet as
one unit after moving account and profile parity into the Experience Shell.
Theater media remains independently reachable and does not restore L5 ownership.

## 2. Largest 20 Source Files

| File | Lines | Responsibilities | Formal owner | Production chain | Decision | Split risk | Required regression |
|---|---:|---:|---|---|---|---|---|
| Retired L5 JavaScript bundle (historical Git) | 3,425 | 7 | Former L5 presentation | No | **Retired whole in FLOW-SLIM-02** | Closed | auth, profile, Case, Abu and narration parity moved to Experience Shell |
| Retired L5 stylesheet bundle (historical Git) | 2,996 | 6 | Former L5 presentation | No | **Retired with L5 in FLOW-SLIM-02** | Closed | desktop and mobile parity moved to Experience Shell |
| `packages/core/mingli_agent/reasoner.py` | 2,837 | 6 | `MingliAgent` cognition | Yes | **Split by responsibility**, retain one facade | Very high | model mocks, baseline/domain cognition, review, citation and full regression |
| `apps/product/static/experience/styles.css` | 2,074 | 4 | Experience Shell presentation | Yes: `/experience` | Split only by Shell, World, Workbench/Lab and responsive ownership | Medium | desktop, 390px, visual snapshots, no overflow |
| `apps/product/static/experience/design-studies/life-script-workspace-v1/styles.css` | 1,889 | 1 | Isolated design study | No formal runtime caller | **Retire/archive whole** after preserving approved design tokens | Low | design-study evidence only |
| `apps/product/agent_api.py` | 1,880 | 6 | Agent HTTP projection; commands remain owned by `BaselineCaseCommandService` | Yes | **Split route families and request contracts**, do not duplicate command logic | Very high | all agent endpoints, auth, progressive jobs, Case hash, command parity |
| `apps/product/static/experience/active/onecanvas-r1/prototype.js` | 1,445 | 5 | R1 locked review fixture | Review-only reachable | **Freeze, then retire whole** after replacement parity; never split in place | Very high | R1 20/20 hash and interaction fixtures |
| `apps/product/canvas_projection.py` | 1,389 | 5 | `ReadOnlySixPillarCanvasService` | Yes | **Split projection stages**; no semantic inference may move to UI | Very high | deterministic Spec/Diff, role absence, relation/path identity, Case hash |
| `scripts/v50_run_vnext_phase0_benchmark.py` | 1,299 | 4 | Offline benchmark runner | No | Keep as tool; extract shared runner only when a second consumer exists | Medium | benchmark lockfile, hashes and dataset isolation |
| `apps/product/static/l5/theater.js` | 1,280 | 5 | Retiring Theater client | Yes: `/theater` | **Retire whole** after Theater replacement parity | High | session, performance, audio, participant/studio flows |
| `packages/experience/canvas.py` | 1,141 | 5 | Canvas contract/compiler package | Yes | **Split contracts, sandbox, compiler/diff and disclosure**, preserve facade | High | C0 fixtures, deterministic hashes, role filtering, mobile/desktop semantic parity |
| `packages/core/state/contracts.py` | 1,132 | 6 | Research-state schema families | Research/Lab, not formal cognition | Split only by stable schema family when consumers converge | High | schema export/hash, research fixtures, all state consumers |
| `packages/core/life_case/service.py` | 1,128 | 5 | `LifeCase` formal cognition owner | Yes | **Split command families, projection and legacy reader**; LifeCase remains owner | Very high | Case hash, append-only versions, evidence/timing/monthly flows, role projection |
| `apps/product/static/experience/app.js` | 1,021 | 4 | Generated Experience bundle | Yes: `/experience` | **Never hand-split or edit**; change `experience_shell/src` | Low if regenerated | byte-identical build, TypeScript strict check |
| `apps/product/experience_shell/src/contracts.generated.ts` | 850 | 0 | Generated Pydantic projection | Build-time contract | **Never hand-split or edit** | High if manual | schema drift command and byte-identical regeneration |
| `packages/core/mingli_agent/fact_review.py` | 759 | 3 | Epistemic fact review | Yes | Keep now; split detectors from policy only with behavioral corpus | High | fact integrity, modality, citation and reliability fixtures |
| `packages/core/state/theme_discovery.py` | 739 | 3 | Research theme projection | Research/Lab | Keep until Lab consumers settle; split only on promotion | Medium | theme synthetic fixtures and state contracts |
| `packages/core/life_case/relation_path.py` | 727 | 4 | LifeCase relation/path provenance | Yes | Separate legacy exact-import adapter only after migration evidence | Very high | stable keys, lifecycle, legacy unresolved, historical Case reads |
| `apps/product/static/experience/internal-tools/abu-says-mingli-s0-v12/app.js` | 704 | 4 | S0 review prototype | Public review surface, not formal product | Keep isolated; retire when canonical Theater consumes the same Scene | Medium | media playback, subtitles, mobile composition, semantic binding |

## 3. Mixed-responsibility Files Below the Top 20

Nine files are high-confidence split candidates because they cross two or more
of API, orchestration, storage, formal commands or projection boundaries:

| File | Mixed responsibilities | Decision |
|---|---|---|
| `packages/core/mingli_agent/reasoner.py` | model transport, prompts, pipeline, repair, review, normalization | Split first only after a behavior corpus is locked |
| `apps/product/agent_api.py` | request contracts, routes, jobs, command orchestration, public projection | Split endpoint families around the existing command owner |
| `apps/product/canvas_projection.py` | Case adapter, graph projection, paths, temporal layers, display metadata | Split pure projection stages; do not create another Scene owner |
| `packages/core/life_case/service.py` | formal commands, evidence, timing, revision, projection/compatibility | Split command families and read projection |
| `apps/product/product_store.py` | account/profile validation, mapping, session and PostgreSQL persistence | Separate mapping/validation from store implementation without a second repository |
| `apps/product/agent_case_store.py` | persistence and legacy compatibility row synthesis | Extract/delete compatibility reader after legacy read parity |
| `apps/product/app.py` | composition root, profile/auth routes, static routes, legacy measurement | Keep composition root; move route groups, not ownership |
| `apps/product/theater_api.py` | HTTP contracts, session commands, performance/audio delivery | Split transport from Theater application service |
| `apps/product/experience_shell/src/main.ts` | boot/data load, navigation state, DOM binding, narration controls | Keep at 359 lines now; split by mode controller only if it grows |

`experience_shell/src/components.ts` is 640 lines and is also a useful
presentation split: World, Workbench, Lab and shared primitives. It is not an
authority defect, so it follows the five core splits above.

## 4. Duplicate Authority and Legacy Findings

### Schema and database

- Python Pydantic models are the Experience contract source; JSON Schema and
  TypeScript are generated projections.
- `deploy/postgres_v50_schema.sql` is the only PostgreSQL DDL definition.
- `product.database_schema.migrate_product_database_schema` is the only explicit executor.
- No store-local DDL or second schema owner remains.
- Each PostgreSQL store calls the read-only version checker during process
  construction. Schema changes require the explicit migration command; a
  mismatch prevents service startup.

### Transitional adapters/read fallbacks

The five explicit compatibility boundaries are:

1. `product/theater_envelope.py` — Canonical Scene to old Theater envelope;
2. `product/onecanvas_timing_adapter.py` — canonical timing to OneCanvas shape;
3. `core/state/bazi_adapter.py` — formal facts to research-state projection;
4. `product/agent_case_store.py::_compatibility_case_row` — old read shape;
5. `core/life_case/service.py::formal_projection_record` — old `RunRecord`
   read-only fallback.

`CanonicalScene.EnvelopeFallback` is role-filtered projection metadata, and
Canvas `_refs(..., fallback=...)` completes provenance references. Neither is a
second fact owner. They must remain tested but should not be counted as formal
fact fallbacks.

### Reachability and retirement

- Static import analysis found all 26 `product.*` Python modules reachable from
  the production composition root; there is no safe Python deletion based only
  on missing imports.
- The Life Script design study has no formal runtime caller. Archive/retire it
  after its approved visual tokens and screenshots are retained.
- R1 OneCanvas and S0 are direct review/evidence surfaces. They are not new
  product authorities and should be retired as complete units after parity and
  retention gates, not split into more modules.
- L5 and legacy Theater are still live routes. They are retirement candidates,
  not refactor candidates.

## 5. Ordered Slimming Slices

Each slice must be an independent commit and preserve formal Case hashes.

1. **MOD-SLIM-02 Reasoner boundaries** — extract model gateway, prompt builders,
   pipeline and review/normalization behind the current `MingliAgent` facade.
2. **MOD-SLIM-03 Agent API** — split endpoint families and request contracts;
   all writes still delegate to `BaselineCaseCommandService`/LifeCase.
3. **MOD-SLIM-04 Canvas projection** — separate Case input, semantic projection,
   temporal projection and display metadata.
4. **MOD-SLIM-05 LifeCase service** — separate formal command families from
   role projection and isolate the legacy reader.
5. **MOD-SLIM-06 Contract families** — split Canvas and research-state contracts
   only after generated schema parity is proven.
6. **MOD-SLIM-07 Route retirement** — switch and then delete L5, old Theater and
   review-only surfaces after usage, parity and rollback evidence.

Every slice must retain:

```text
LifeCase as the only formal cognition owner
CanonicalSceneOwner as the only scene owner
one PostgreSQL schema definition and one executor
client inability to submit formal chart/relation/path facts
R1 20/20 locked asset hashes
RA0 Universe hash and CAL-01 fixtures
V40 zero changes
full regression and performance parity
```

## 6. Decision

The nine authoritative/runtime mixed-responsibility modules are now resolved.
Their public facades preserve imports while validation, persistence,
projection, transport and orchestration have separate owners. The remaining
large legacy bundles are retirement work tied to route migration, not further
split work.

The deployed UI remains a unified Review Build shell. Life Tree, Abu Dream
World and the complete Mingli Lab are not represented as final visual/product
completion by this audit.
