# ABU Dream Runtime Ownership Trace 09

## 0. Containment receipt

```yaml
ABU-DREAM-GHOST-CONTAINMENT-09:
  status: COMPLETE
  STOP_WORK_ACKNOWLEDGED: true
  current_worktree_preserved: true
  further_visual_mutation: false
  asset_extraction_or_replacement: false
  legacy_delete: false
  report_only: ABU_DREAM_RUNTIME_OWNERSHIP_TRACE_09_REPORT.md
```

Audit date: `2026-07-24`

Audit mode: read-only source, asset, manifest, Hash, route, and fallback tracing.

No product code, CSS, component, asset, manifest, database, cache, build output, or
runtime state was changed during this audit. No test, build, service restart, Git
commit, push, or deployment was run. This report is the only authorized write.

## 1. Executive verdict

```yaml
MULTIPLE_RUNTIME_OWNER: CONFIRMED
LEGACY_GHOST_RISK: CONFIRMED
CURRENT_PRODUCT_ASSET_SOURCE: DIRECT_HARDCODED_PORCH_V5
GLOBAL_REGISTERED_PORCH_TARGET: DREAM_THREE_TREE_PORCH_V3
GLOBAL_REGISTERED_PORCH_TARGET_FILES: MISSING
CURRENT_PORCH_V5_FULL_BUNDLE_OWNER_ACCEPTANCE: NOT_PROVEN
CURRENT_PORCH_V5_BACKGROUND_OWNER_ACCEPTANCE: PROVEN_BY_MANIFEST
ABU_03_ACCEPTED_BASELINE: PRESENT_AND_PRODUCT_REACHABLE
SERVICE_WORKER_ASSET_RESURRECTION: NOT_PRESENT
EXACT_HISTORICAL_OLD_TREE_IDENTITY: ROOT_CAUSE_UNRESOLVED
```

The current Dream page is not owned by one framework-level scene registry.
The visible result is jointly determined by:

1. the server route and static mounts;
2. the served compiled `app.js`;
3. untracked TypeScript source used to produce that bundle;
4. a Dream-local hardcoded asset registry;
5. a separate global media registry;
6. a monolithic `DreamFirstVisitRuntime`;
7. direct render helpers;
8. nearly ten thousand lines of CSS containing several generations of the same
   selectors;
9. a separate Dream Abu resolver plus a separate global Abu motion registry;
10. baked-tree transition and hold-frame images.

`DreamStoryRuntime` and `dream_scene_director.ts` currently provide state metadata.
They do not own asset resolution, z-order, fallback policy, or rendering. The actual
presentation owner remains `DreamFirstVisitRuntime` plus direct HTML/CSS renderers.

The latest globally registered three-tree destination is
`DREAM_THREE_TREE_PORCH_V3`, but its referenced Manifest and files are absent and
were never tracked by Git. The actual browser bundle ignores that registration and
loads `porch-v5` directly. This is the principal ownership break.

## 2. Worktree and regression boundary

### 2.1 Git identity

```text
repo:
  /Users/liujin/DEV/AIProjects/bazi-v50-cag04-reconcile/qiazhi/v50

branch:
  codex/cag04-ra0-reconciliation

HEAD:
  71b36f61066266e23dfcdacdf64633732f2e9898

HEAD subject:
  test(v50): decouple snapshot gates from worktree state

HEAD time:
  2026-07-22T18:36:25+09:00
```

The Dream implementation and assets are almost entirely uncommitted after this
HEAD. `git ls-files` returns no tracked files under either:

```text
apps/product/static/l5/assets/dream/**
artifacts/abu-dream-world/**
```

Consequently Git cannot reconstruct a deleted `porch-v3`, `porch-v4`, or prior
review artifact set.

### 2.2 Relevant dirty boundary

The pre-existing worktree includes modifications to backend Dream services,
database contracts, navigation, frontend source, compiled static output, CSS,
media registries, Abu registries, tests, and documentation. It also contains
untracked Dream Runtime, game, navigation, asset, artifact, script, test, and
specification files.

The tracked visual-runtime diff alone is:

```text
9 files changed
17,180 insertions
2,624 deletions
```

The largest active presentation surfaces are:

| File | Lines | Current role |
|---|---:|---|
| `apps/product/experience_shell/src/dream_runtime.ts` | 3,425 | state, API orchestration, input, navigation, animation, game, rendering coordination |
| `apps/product/experience_shell/src/dream_tree_world.ts` | 557 | porch, fixed tree, question map, questions, transitions |
| `apps/product/static/experience/app.js` | 6,618 | browser-served compiled owner |
| `apps/product/static/experience/styles.css` | 9,835 | every Dream generation's layout and final z-order |

### 2.3 Pre-stop incident ledger

Before the STOP directive, the current work session had already:

- created or replaced the current `porch-v5` background and three alpha tree actors;
- changed `dream_asset_registry.ts`, `dream_tree_world.ts`, `dream_runtime.ts`,
  `styles.css`, `index.html`, the runtime-foundation Manifest, and the compiled
  `app.js`;
- changed cache-busting URLs to `20260724-dream-porch-v5-r15`;
- removed an untracked `porch-v4` directory;
- removed some untracked Dream review artifact directories whose exact prior
  inventory can no longer be reconstructed from Git.

These facts are recorded rather than reverted. File modification times place the
`porch-v5` asset creation between `11:44` and `11:49 +09:00`, source edits around
`11:50`, compiled `app.js` at `12:06`, and `index.html` / `styles.css` at `12:14`.

## 3. `/experience` to final picture: actual runtime chain

### 3.1 Route and static owner

| Step | Actual owner | Evidence |
|---|---|---|
| `/experience` and every `/experience/dream/**` route | `apps/product/product_surface.py` | all routes return `apps/product/static/experience/index.html` |
| `/assets/**` | `product_surface.py` | mounted from `apps/product/static/l5/assets` |
| `/experience-static/**` | `product_surface.py` | mounted from `apps/product/static/experience` |
| browser CSS | `index.html` | `/experience-static/styles.css?v=20260724-dream-porch-v5-r15` |
| browser JS | `index.html` | `/experience-static/app.js?v=20260724-dream-porch-v5-r15` |

The browser executes `app.js`, not the TypeScript source. Source and compiled output
therefore form two mutable copies of the runtime unless rebuilt atomically.

### 3.2 End-to-end chain

```text
/experience
→ main.ts / compiled app.js
→ components.ts
→ dream_home_portal.ts
→ home-life-tree-no-abu-v1.png
→ Dream-local Abu Director selects v6 sleeping fallback
→ user command "enter-dream"
→ POST /api/v50/dream/visits
→ POST /api/v50/dream/visits/{visit}/enter
→ beginDreamEntryTransition()
→ ABU_03 one-shot overlay appended to document.body
→ route navigation to /experience/dream/visits/{visit}
→ resumeDreamEntryTransition()
→ bootDreamExperience()
→ DreamFirstVisitRuntime.boot()
→ GET visit / encounter / game content gate / game rounds
→ renderGrove() creates the legacy grove shell
→ renderGameLayer() overlays the game shell
→ no attempt: renderDreamTreePorch()
→ center tree selected twice / committed
→ tree-enter-clean.mp4 one-shot
→ POST select-tree
→ POST game round start
→ fixedTreeBud source displayed
→ because ENABLE_PHASE_B_TREE_QUESTIONS=false:
   renderDreamFixedTreeIdle()
```

Current selected-tree output is therefore the empty fixed-tree hold scene. The
question-node implementation remains compiled but is disabled by a constant.

### 3.3 Backend data owner remains separate and valid

The backend API remains under:

```text
apps/product/dream_api.py
prefix: /api/v50/dream
```

It delegates to the existing Dream service, navigation service, game service,
projection, stores, BlindRound, Seal, Reveal, EvaluationRecord, and KnowledgeSeed
owners. No visual asset URL is supplied by those backend owners. The frontend
chooses all current image and video URLs locally.

### 3.4 Actual presentation owner

| Claimed layer | Actual status |
|---|---|
| `DreamStoryRuntime` | state snapshot and allowed-command metadata |
| `dream_scene_director.ts` | maps business states to semantic scene IDs and asset intents |
| `DreamSceneRegistry` | does not exist as the sole runtime asset owner |
| `DreamExperienceDirector` | not the sole renderer |
| `DreamFirstVisitRuntime` | actual orchestration and presentation owner |
| `dream_tree_world.ts` | actual HTML and direct asset consumer |
| `dream_asset_registry.ts` | actual hardcoded visual URL owner |
| `app.js` | actual browser-executed copy |
| `styles.css` | actual composition, z-order, masking, position, and many direct URL owner |

## 4. Three-tree z-order and source trace

### 4.1 Live layer table

| layer_id | semantic_role | source_file / resolved URL | import owner | condition | final z-order | contains candidate tree pixels | status |
|---|---|---|---|---|---:|---|---|
| entry-cinematic | ABU_03 entry overlay | `/assets/dream/entry-transition-v1/abu_03_dream_entry_transition_v1_runtime_1080p.mp4` | `dream_entry_transition.ts` | fresh entry, non-reduced motion | 1000 | yes, final portion | KEEP_RUNTIME |
| entry-reduced | ABU_03 static fallback | `abu_03_dream_entry_transition_v1_last_frame.png` | `dream_entry_transition.ts` | reduced motion | 1000 | yes: center blue, side trees, Abu | CANONICAL_CANDIDATE with overlap risk |
| grove-background | legacy grove base | `grove-clean-approved-v5-e97ec6b5.png` | direct CSS URL | always inside `renderGrove()` | -4 | scenic/background trees only; no three candidates | CURRENT_BACKGROUND_CANDIDATE |
| grove-parallax | old terrain overlays | CSS gradients | `styles.css` | always | -3 | no | LEGACY_QUARANTINE_CANDIDATE |
| grove | old movement / Abu shell | no candidate tree image is currently inserted | `dream_runtime.ts` | always | 1 | no current candidate tree DOM | LEGACY_QUARANTINE_CANDIDATE |
| game-layer | gameplay overlay | HTML from `renderGameLayer()` | `dream_runtime.ts` | game rounds available | 120 after final cascade | depends on child | KEEP_RUNTIME, adapt presentation |
| porch-backdrop | visible porch plate | `grove-clean-approved-v5-e97ec6b5.png` | `dream_tree_world.ts` via local registry | no game attempt | 0 in shell | no candidate trees | CANONICAL_CANDIDATE |
| porch-mist / veils | transition masking | CSS spans | `dream_tree_world.ts` / CSS | porch | 4 / 8 | no | ADAPT_TO_REGISTRY |
| porch-actors | three alpha candidates | three `porch-v5/tree-*-actor-*.png` files | `dream_tree_world.ts` via local registry | no game attempt | slots 2 / 4 within target z=5 | yes | OWNER_DECISION_REQUIRED |
| porch-Abu | seated observer | ABU_01 WebM or poster | Dream-local Abu Director | porch | 14 | no | CANONICAL_CANDIDATE |
| tree-enter | selected-tree transition | `tree-enter-clean.mp4` | `dream_tree_world.ts` | `mediaCue=tree_enter` | 90 inside game layer | yes: baked tree and Abu | TRANSITIONAL_FALLBACK |
| fixed-tree-blur | blurred duplicate backing | `tree-question-map-full-preseal.png` | direct CSS URL | selected attempt, fixed idle | -2 inside stage | yes | ADAPT_TO_REGISTRY |
| fixed-tree-master | fixed empty scene | same `tree-question-map-full-preseal.png` | local registry + renderer | selected attempt | 1 | yes | OWNER_DECISION_REQUIRED |
| question-map-master | disabled question stage | selected porch actor image | `dream_runtime.ts` + `dream_tree_world.ts` | only if build constant becomes true | 0 | yes | LEGACY_QUARANTINE_CANDIDATE |

The fixed-tree scene renders the same baked image twice: a blurred cover copy from
CSS and a contained foreground `<img>`. This is intentional fill behavior, but it
means CSS is an independent asset owner.

### 4.2 Which backgrounds already contain trees

| File | Hash | Tree pixels |
|---|---|---|
| `porch-v5/grove-clean-approved-v5-e97ec6b5.png` | `e97ec6b5...ca54` | foreground frame trunk and distant scenic trees; no three candidate life trees |
| `entry-transition-v1/..._last_frame.png` | `31e57cde...612d` | center blue candidate, two side/background trees, and Abu baked into the image |
| `director-v2/tree-question-map-full-preseal.png` | `7901961a...1a55` | central fixed life tree, background forest trees, and Abu baked into the image |
| `director-v2/tree-observe-bud*.png/jpg` | see asset matrix | central fixed life tree and forest background baked |
| `director-v2/tree-flower-open*.png/jpg` | see asset matrix | tree, flower state, and forest background baked |
| `director-v2/fog-gate-three-trees-clean.mp4` | `9592d49c...426b` | three trees and Abu baked into the video |
| director reference `04-three_trees_revealed.png` | reference artifact | three trees, symbols, fruit, flower, and Abu baked |

The current clean `porch-v5` backdrop is not the source of duplicate candidate
trees. The overlap risk comes from tree-bearing transition/hold frames, direct
transparent actor layers, and multiple presentation owners.

## 5. Asset identity matrix

### 5.1 Registry conflict

| Registry | Current claim | Physical status | Runtime use |
|---|---|---|---|
| `config/media_asset_registry_v1.json` | `DREAM_THREE_TREE_PORCH_V3`, Manifest Hash `c06ab177...652d` | `porch-v3/manifest.json` absent | ignored by Dream frontend |
| `dream_asset_registry.ts` | direct `porch-v5` paths | present | active |
| compiled `app.js` | same direct `porch-v5` paths | present | active browser owner |
| runtime-foundation Manifest | `DREAM_THREE_TREE_PORCH_V5` | present | documentation/validation |
| `porch-v5/manifest.json` | clean background + 3 alpha actors | present | active through direct registry |

The global registered target and actual runtime target disagree.

### 5.2 Tree and background assets

| Classification | Path | SHA-256 | Geometry / Alpha | Product reachability | References |
|---|---|---|---|---|---|
| `CANONICAL_CANDIDATE` | `dream/porch-v5/grove-clean-approved-v5-e97ec6b5.png` | `e97ec6b5f856...eca54` | 1672x941, no alpha | `PRODUCT_REACHABLE` | TS registry, compiled bundle, CSS, two Manifests |
| `OWNER_DECISION_REQUIRED` | `dream/porch-v5/tree-blue-actor-v5-08170159.png` | `081701597f2f...dd85` | 1672x941, alpha | `PRODUCT_REACHABLE` | TS registry, bundle, Manifest |
| `OWNER_DECISION_REQUIRED` | `dream/porch-v5/tree-jade-actor-v5-9541d056.png` | `9541d056857d...6c2` | 1672x941, alpha | `PRODUCT_REACHABLE` | TS registry, bundle, Manifest |
| `OWNER_DECISION_REQUIRED` | `dream/porch-v5/tree-amber-actor-v5-1f98142a.png` | `1f98142ad58c...c11e` | 1672x941, alpha | `PRODUCT_REACHABLE` | TS registry, bundle, Manifest |
| `UNKNOWN_OWNER` | `dream/porch-v3/manifest.json` and bundle | expected Manifest `c06ab177...652d` | missing | `UNKNOWN` | global media registry only |
| `DERIVED_FROM_CANONICAL` | `director-v2/tree-question-map-full-preseal.png` | `7901961ad7d6...1a55` | 1280x720, no alpha | `PRODUCT_REACHABLE` | TS registry, bundle, CSS |
| `TRANSITIONAL_FALLBACK` | `director-v2/tree-enter-clean.mp4` | `573f50fbd831...178f` | 1280x720, 2.5s | `PRODUCT_REACHABLE` | selected-tree transition |
| `DERIVED_FROM_CANONICAL` | `director-v2/tree-observe-bud-preseal.png` | `d504c70b69ba...bad5d` | 1280x720 | metadata fallback only | TS registry / Manifest |
| `DERIVED_FROM_CANONICAL` | `director-v2/tree-observe-bud-mobile-preseal.jpg` | `1caa71b1df75...e86e` | 941x1672 | metadata fallback only | TS registry / Manifest |
| `DERIVED_FROM_CANONICAL` | `director-v2/tree-flower-open-preseal.png` | `97282c5f1afc...10ee` | 1280x720 | currently not selected | TS registry / Manifest |
| `DERIVED_FROM_CANONICAL` | `director-v2/tree-flower-open-mobile-preseal.jpg` | `6a6fa956dbea...2314` | 941x1672 | metadata fallback only | TS registry / Manifest |
| `DERIVED_FROM_CANONICAL` | `runtime-foundation-v1/home-life-tree-no-abu-v1.png` | `bbcf736264b3...dbb3` | 1280x720, no alpha | `PRODUCT_REACHABLE` at `/experience` | home portal |

Additional director-only files remain references or disabled-stage materials:

| File | SHA-256 | Runtime status |
|---|---|---|
| `fog-gate-preselection-clean.mp4` | `1cd70b6e...33c7` | registered reference, not current ABU_03 entry |
| `fog-gate-three-trees-clean.mp4` | `9592d49c...426b` | reference only, not current interactive porch |
| `flower-open-clean.mp4` | `cc26039d...1e44` | disabled question-stage transition |
| `fruit-reveal-reference-clean.mp4` | `f3fa1b1d...2710` | reveal reference |
| `tree-observe-bud.png` | `5f1027fb...4472` | superseded hold frame |
| `tree-flower-open.png` | `0e4066ff...6743` | superseded hold frame |

### 5.3 ABU_03 identity

| File | SHA-256 | Metadata | Reachability |
|---|---|---|---|
| runtime MP4 | `76e3ddf69bb9...615d` | 1920x1080, H264, 7.75s, no audio | `PRODUCT_REACHABLE` |
| first frame | `9a3a63cbd3b2...56d8` | 1920x1080 | poster |
| last frame | `31e57cde8f35...612d` | 1920x1080 | reduced-motion fallback |
| Manifest | `51377d9de08c...1b5b` | handoff at 7.1s | registry evidence |

ABU_03 is present, wired, and not deleted. It is overlaid at `z-index: 1000`.

### 5.4 Dream-relevant Abu assets

| Classification | Asset | SHA-256 | Reachability / owner |
|---|---|---|---|
| `TRANSITIONAL_FALLBACK` | v6 sleep WebP | `b7bedc1ae0e9...646c8` | home sleeping portal through Dream-local Director |
| `TRANSITIONAL_FALLBACK` | v6 sleep poster | `9f956151354f...24a5` | reduced-motion home portal |
| `CANONICAL_CANDIDATE` | ABU_01 WebM | `a63cfd680f27...ec7` | porch through Dream-local Director |
| `CANONICAL_CANDIDATE` | ABU_01 WebP | `3b8adb105db8...ed8` | underlying grove `ABU_WAIT` direct fallback |
| `CANONICAL_CANDIDATE` | ABU_01 poster | `6aa0b95c6b7f...702` | reduced motion |
| `TRANSITIONAL_FALLBACK` | ABU_02 WebM | `576094e3c291...cfd` | defined for guide, current guide role not called |
| `TRANSITIONAL_FALLBACK` | ABU_02 WebP | `f2e8047d2dc5...218` | underlying grove `ABU_WALK` direct fallback |
| `TRANSITIONAL_FALLBACK` | ABU_02 poster | `b8a3083f2534...d1d3` | reduced motion |
| `UNKNOWN_OWNER` | dream-standard-cycle WebM | `14aec7265daf...259` | global motion registry default; not current Dream route |
| `UNKNOWN_OWNER` | dream-standard-cycle WebP | `292cfa118d85...efb` | product surfaces outside current Dream route |
| `UNKNOWN_OWNER` | dream-standard-cycle poster | `c0a01c139e06...6e1c` | duplicated by seated-observe poster |
| `UNKNOWN_OWNER` | dream-seated-observe WebM | `b745e403c31d...2900` | global registry only |
| `UNKNOWN_OWNER` | dream-stand-and-return WebM | `32371b269594...45b` | global registry only |

There are two Abu registries:

```text
Dream-local:
  dream_abu_motion_director.ts + dream_asset_registry.ts

Global:
  assets/abu/motion-registry.js
  assets/abu/v12-actor-pass/library.json
  config/media_asset_registry_v1.json
```

The Dream route does not resolve its Abu role through the global default registry.

## 6. Old tree and fallback reachability

### 6.1 Known retired names

The following historical names are absent from the filesystem and have no current
product-source reference. They occur only in a forbidden list and tests:

```text
porch-blue-single-v4-230add93.png
porch-jade-single-v4-fced62f3.png
porch-amber-single-v4-3ba7358f.png
grove-background-v1.webp
tree-mist-v1.webp
tree-brook-v1.webp
tree-ridge-v1.webp
porch-blue-v3.webp
porch-jade-v3.webp
porch-amber-v3.webp
porch-three-trees-clean-plate.png
porch-three-trees-preseal.png
porch-three-trees.png
```

Reachability: `UNREACHABLE_PROVEN` in the current filesystem and current source.

Their exact historical Hashes and the precise screenshot-to-file identity cannot
be recovered because the assets were untracked and are now absent.

### 6.2 Product-reachable fallback paths

| Path | Trigger | Reachability | Risk |
|---|---|---|---|
| ABU_03 last frame | `prefers-reduced-motion` | `PRODUCT_REACHABLE` | frame contains trees and Abu; can overlap the interactive porch during handoff |
| ABU_01 WebP | underlying grove and error state constants choose fallback before poster | `PRODUCT_REACHABLE` | bypasses WebM and Dream role renderer |
| ABU_02 WebP | fog / movement constant chooses fallback before poster | `PRODUCT_REACHABLE` | direct source path, separate from Director role |
| fixed tree mobile JPG | declared in asset metadata | `UNREACHABLE_PROVEN` in current renderer | metadata is not an actual load fallback |
| tree-enter poster PNG | declared in asset metadata | `UNREACHABLE_PROVEN` in current renderer | video decode failure has no fail-closed handler |
| porch preload | image `load` and `error` both resolve | `PRODUCT_REACHABLE` | missing/corrupt assets do not block rendering |
| game-round retry | re-enters visit once, then sets rounds to `[]` | `PRODUCT_REACHABLE` | exposes old grove path; current grove contains stale logic but no current tree markup |

### 6.3 Browser, build, and restore paths

- No service worker, Workbox bundle, or app cache implementation exists under the
  product tree.
- No code reads Dream asset URLs from `localStorage` or `sessionStorage`.
- Session storage restores visit navigation, entry transition, control lease,
  pending departure, pending game action, question-map state, return seed state,
  and scene clock. It does not restore old image URLs.
- The browser may keep an already-loaded old page and bundle alive until reload.
- `index.html` uses a query-string cache key, but the compiled file is edited in
  place. A cache-key bump is a manual second operation.
- `app.js` and the untracked TypeScript source can diverge.
- StaticFiles provides the current physical asset for a URL; there is no server
  fallback from a missing porch path to another porch.

Therefore a service worker or hidden browser asset cache is not the primary ghost
mechanism. The proven mechanism is competing source owners plus direct hardcoded
paths and stale presentation code.

## 7. Last Owner-reviewed three-tree identity

The evidence resolves into three distinct levels:

1. **ABU_03 baseline** is real and present.
   Its last frame Hash is `31e57cde...612d`.
2. **Owner-approved clean background** is real and present.
   `grove-clean-approved-v5-e97ec6b5.png`, Hash `e97ec6b5...ca54`.
3. **Complete three-tree bundle** is not currently bound to one recoverable
   Owner-approved identity.

The global registry names:

```text
DREAM_THREE_TREE_PORCH_V3
manifest:
  missing://apps/product/static/l5/assets/dream/porch-v3/manifest.json
expected manifest SHA-256:
  c06ab177a22b38cb413bf2ac3b33a93e14f7c1ac4531612666f6628d585b652d
```

That file and directory are absent. No Git history contains them.

The current full trio is:

```text
blue:  081701597f2f4dfaf422215204f7a607d27fcb9ec05c473a7edf52180923dd85
jade:  9541d056857df81b6f753e99ee68e4113808c47a060bef77b65d9714f69ec6c2
amber: 1f98142ad58c8f9b207c780844ab04bd0733d91a01a8c15465359910e1e7c11e
```

Its Manifest status is `POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW`, not a proven
full-bundle approval.

Formal status:

```yaml
accepted_asset_bundle: OWNER_LOCK_PENDING_REPO_RESOLUTION
background_identity: RESOLVED
three_actor_identity: RESOLVED_BUT_NOT_OWNER_ACCEPTED
previous_registered_v3_identity: MANIFEST_HASH_ONLY_FILES_MISSING
```

## 8. Existing visual comparison index

No new screenshots or extracted images were produced. Existing evidence:

| Purpose | Existing path | SHA-256 / note |
|---|---|---|
| original director three-tree reference | `artifacts/abu-dream-world/director-reference/dream-encounter-01/v1/keyframes/dream_ref_fog_gate_three_trees_v1/04-three_trees_revealed.png` | baked three-tree reference |
| accepted entry last frame | `apps/product/static/l5/assets/dream/entry-transition-v1/abu_03_dream_entry_transition_v1_last_frame.png` | `31e57cde...612d` |
| current clean grove | `apps/product/static/l5/assets/dream/porch-v5/grove-clean-approved-v5-e97ec6b5.png` | `e97ec6b5...ca54` |
| current fixed tree | `apps/product/static/l5/assets/dream/encounter-01-v1/director-v2/tree-question-map-full-preseal.png` | `7901961a...1a55` |
| Owner background reference screenshot | `/var/folders/_3/smgvfv_577ldt0mm_zmrfw3w0000gn/T/codex-clipboard-a3bcfd92-0d62-44a2-a7b5-b9bcd630ec00.png` | `67077b02...21b`, 3024x1600 |
| intermediate three-tree screenshot | `/var/folders/_3/smgvfv_577ldt0mm_zmrfw3w0000gn/T/codex-clipboard-44870451-294f-45ad-b6d4-0e40d98713e7.png` | `968cb51c...6cef`, 3014x1602 |
| separated-actor request screenshot | `/var/folders/_3/smgvfv_577ldt0mm_zmrfw3w0000gn/T/codex-clipboard-9540bae5-d69a-4cdb-a36f-6214ac16d715.png` | `d677441b...e4d`, 3024x1704 |
| latest pre-stop composition screenshot | `/var/folders/_3/smgvfv_577ldt0mm_zmrfw3w0000gn/T/codex-clipboard-34c2e41f-006d-47de-8848-df7c5c34137a.png` | `ce14d760...696`, 2944x1572 |

The temporary screenshots are evidence only. They are not registered runtime
assets and must not be treated as canonical bundle components.

## 9. Falsifiable root-cause chain

### 9.1 Proven current chain

```text
global media registry points to missing porch-v3
→ Dream frontend never reads that registry
→ dream_asset_registry.ts hardcodes porch-v5
→ compiled app.js duplicates those hardcoded paths
→ index.html serves the compiled bundle directly
→ dream_tree_world.ts renders all three alpha actors
→ styles.css positions and transforms them through several generations of selectors
→ ABU_03 / tree-enter / fixed-tree images also contain baked tree pixels
→ no one owner validates the final layer composition
→ visually old or duplicate trees can reappear despite a nominal registry change
```

This chain is falsifiable by changing no product behavior and checking:

- the global registry path is absent;
- the browser bundle contains the v5 URLs;
- the DOM renderer creates three v5 actor `<img>` elements;
- CSS directly references the v5 backdrop and fixed-tree source;
- no service worker is registered.

### 9.2 Exact historical identity

```text
ROOT_CAUSE_UNRESOLVED
```

The exact filename and Hash of the specific rejected transparent tree seen before
the current `porch-v5` rewrite cannot be proven. The possible historical
`porch-v3` / `porch-v4` files were untracked and are absent. The current forbidden
asset list preserves names but not their Hashes.

The current visible alpha actors are not loaded through a fallback. They are loaded
directly from the active v5 hardcoded registry. Calling them a browser-cache
resurrection would be inaccurate.

## 10. Ghost-code evidence

The CSS contains multiple generations of the same presentation selectors:

```text
.dream-tree-porch-camera definitions: 6
.dream-tree-porch-tree definitions: 23
.dream-game-layer.is-tree-world definitions: 3
.dream-tree-world-shell definitions: 13
.dream-question-tree-stage definitions: 4
```

Later declarations override earlier ones by cascade, including comments and blocks
for:

- the original first-visit grove;
- `DREAM-TREE-WORLD-UX-RECONSTRUCTION`;
- `DREAM-ENCOUNTER-VISUAL-QA-REBUILD-02`;
- `Ghost Orbit V2`;
- `ABU_03 dream entry`;
- `Canonical porch V5`.

`DreamFirstVisitRuntime` also retains movement, tree hit masks, own-tree recognition,
tree-distance detection, root mirror, and free-roam logic. The current `renderGrove`
does not insert matching `.dream-life-tree` elements, while the game overlay takes
over the route. This is stale executable logic, not merely old documentation.

The disabled question-map implementation is still compiled and includes:

- tree nodes;
- fruit markup;
- fixed-tree companion Abu;
- OneCanvas overlay;
- question generation.

It is currently stopped only by:

```text
ENABLE_PHASE_B_TREE_QUESTIONS = false
```

## 11. Target ownership contract

This report proposes no implementation, only the minimum ownership boundary.

```text
DreamExperienceDirector
→ DreamSceneRegistry
→ DreamThreeTreeAssetBundle
→ components receive only scene_id / bundle_id
→ fail closed when the bundle is missing, unapproved, or Hash-mismatched
```

### 11.1 `DreamSceneRegistry`

Sole owner of:

- `scene_id`;
- approved `bundle_id`;
- business-state compatibility;
- source and derived Manifest Hashes;
- DesktopProfile and MobileProfile;
- z-order contract;
- transition handoff contract;
- reduced-motion policy;
- required asset status;
- fail-closed behavior.

It must not contain V50 facts or create a second Dream Runtime.

### 11.2 `DreamThreeTreeAssetBundle`

One immutable bundle must bind:

- clean background;
- exactly three candidate tree actors;
- each actor Hash and alpha requirement;
- center/left/right layout profiles;
- ground-contact metadata;
- ABU_03 handoff target;
- Abu role and approved asset ID;
- mist and occlusion layers;
- Owner acceptance record;
- cutover version.

Components must not contain raw asset paths. CSS must not introduce independent
background URLs.

## 12. Containment and retirement plan

No item below is deleted or changed in this audit.

### `KEEP_RUNTIME`

- backend LifeCase, DreamProjection, consent, visit, control lease, navigation;
- BlindRound, double Seal, Reveal, EvaluationRecord, KnowledgeSeed;
- `ABU_03_DREAM_ENTRY_TRANSITION_V1`;
- Return / Recovery / Departure controllers;
- server-side authorization and fail-closed boundaries.

### `ADAPT_TO_REGISTRY`

- `dream_story_runtime.ts`;
- `dream_scene_director.ts`;
- `dream_asset_registry.ts`;
- `dream_tree_world.ts`;
- the presentation portion of `dream_runtime.ts`;
- `config/media_asset_registry_v1.json`;
- compiled bundle generation;
- CSS scene composition;
- Dream-local Abu role resolution.

### `QUARANTINE_FROM_PRODUCT_GRAPH`

- current v5 actor trio until Owner bundle decision;
- old free-roam grove presentation and hit-mask logic;
- disabled question-map presentation;
- all earlier porch selector generations;
- direct CSS asset URLs;
- original director videos as reference-only material;
- baked-tree fallback frames where they can overlap interactive actors.

### `DELETE_AFTER_CUTOVER`

- overridden legacy CSS blocks after selector ownership is proven;
- stale free-roam visual code after the new Director owns the same navigation states;
- duplicate source-path constants in compiled and source layers;
- direct asset fallbacks made obsolete by registry fail-closed handling;
- obsolete generated output only after reproducible rebuild and Owner validation.

### `OWNER_DECISION_REQUIRED`

- recover or formally supersede `DREAM_THREE_TREE_PORCH_V3`;
- accept or reject the full v5 actor trio;
- accept the current fixed-tree hold image as a baseline;
- replace or retain v6 sleeping Abu fallback;
- choose one Abu registry as the runtime identity owner;
- decide which earlier visual review artifacts must be restored before deletion.

## 13. Required answers

### 1. `/experience` to final picture

Traced in Sections 3 and 4. The final browser owner is the served `app.js` plus
`styles.css`; the supposed Director is not the sole owner.

### 2. Every three-tree layer

Traced in Section 4. The current visible candidates are three v5 alpha PNG actors
over one v5 clean backdrop, with ABU_03 and tree-enter baked-tree transitions at
higher layers.

### 3. Which background already contains trees

The v5 clean backdrop has only scenic trees, not three candidate trees. ABU_03 last
frame, fixed-tree hold frames, and director-reference videos contain baked candidate
or central life trees.

### 4. How old transparent trees revived

The currently visible transparent trees are not loaded through an old fallback.
They are direct v5 imports in `dream_asset_registry.ts` and compiled `app.js`.
Historical retired names are absent. Exact prior rejected-tree identity is
`ROOT_CAUSE_UNRESOLVED` because untracked files were removed.

### 5. Paths, Hashes, references

Recorded in Sections 5 and 6.

### 6. Last Owner-reviewed new three trees

There is no complete, physically recoverable, Owner-locked bundle in the current
repo. The global registry points to missing v3. The v5 background is approved, but
the v5 actor trio remains awaiting Owner review.

### 7. Isolation and deletion boundary

Recorded in Section 12. Nothing is authorized for deletion before a versioned
registry cutover and Owner visual acceptance.

## 14. Final audit status

```yaml
ABU_DREAM_RUNTIME_OWNERSHIP_TRACE_09:
  status: COMPLETE
  runtime_owner_count: MULTIPLE
  active_browser_owner: STATIC_APP_JS_PLUS_CSS
  semantic_director_is_actual_renderer: false
  global_asset_registry_matches_runtime: false
  registered_porch_v3_present: false
  porch_v5_background_present: true
  porch_v5_actor_bundle_owner_accepted: false
  forbidden_old_asset_files_present: false
  service_worker_present: false
  exact_historical_old_tree_hash: UNKNOWN
  repair_authorized: false
  deletion_authorized: false
```
