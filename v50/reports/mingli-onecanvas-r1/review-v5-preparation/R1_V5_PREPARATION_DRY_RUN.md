# R1 v5 Human Review Preparation Dry Run

```yaml
date: 2026-07-20
status: PREPARATION_BLOCKED
machine_prerequisite: PASS
human_sessions_started: false
participants_recruited: false
final_review_build_frozen: false
blocker: ZERO_MANY_SOLVER_OUTCOMES_NOT_EXPOSED
```

## Purpose

This was a product-surface dry run before recruiting the two analysts and five
first-time users required by the R1 v5 protocol. It did not re-test L2's Mingli
algorithms and it was not a human product review.

## Environment

```text
route:
http://127.0.0.1:8053/experience-static/active/onecanvas-r1/index.html?r1ReviewDryRun=1

git HEAD:
88da895bb860c25fd6166ac4fa9717cf7102a1e8

review build candidate aggregate SHA-256:
f218526975f5b3304724b7dab7bfe7023a13502ac23ed318313096187f47e6e6

fixture SHA-256:
840382c0c27b9e1786fad625ca3acd8fb05a513ae63e4bee0ec05299e24a320a

exercised browser:
Google Chrome 150.0.7871.125

recorded but not exercised in this dry run:
Safari 26.5.2 (21624.2.5.11.8)
```

The worktree was not clean, so the candidate is identified by its explicit
asset/contract manifest rather than by `git HEAD` alone. It is not the frozen
human-review build.

Verification after the authority-document alignment:

```text
focused L2/R1 authority regression: 36 passed
full regression: 435 passed
```

## What the Active Surface Can Do

The route exposes the expected R1 authority controls:

- formal versus Sandbox mode;
- Qian, Kun and unknown gender states;
- compatible Gregorian birth-year anchors;
- year/day edits and dependent month/hour controls;
- derived DaYun display;
- Gregorian annual observation;
- undo, redo and reset.

These are sufficient for part of the protocol, but not for the full v5 task
set.

## Blocking Contract Gap

The core constraint owner already returns:

```text
no_solution
single_solution
multiple_solutions
```

The active product chain currently reduces that contract:

1. `prototype.js::requestTargetCompile` posts one complete four-pillar target.
2. `experience_api.py::/onecanvas/target-compile` calls the product wrapper.
3. `onecanvas_structural.py::resolve_pillar_target` rejects `no_solution` and
   requires `single_solution` with a selected variant.
4. The browser therefore has no product state for candidate comparison,
   conflicts or server-provided releasable constraints.

Consequences:

- R1 Task 4, explicit multiple-solution choice, cannot be executed.
- R1 Task 5, no-solution explanation and constraint release, cannot be
  executed.
- Recruiting participants now would produce an invalid review rather than
  evidence about the approved protocol.

## Classification

```text
L2 algorithm defect: no
new Mingli feature: no
R1 application/presentation contract gap: yes
authority risk if ignored: silent reduction of 0/1/many to the happy path
```

The correction may expose only server-owned `ChartResolution` data. JavaScript
must not recreate chart legality, rank candidates professionally, fabricate a
fallback chart or silently select the first result.

## Gate Decision

```yaml
L2: CLOSED_PASS
R1_v5_machine_gate: PASS
R1_human_product_gate: PREPARATION_BLOCKED
review_build_frozen: false
RA1: BLOCKED
Theater: BLOCKED
Xiangfa_feature_expansion: BLOCKED
production: BLOCKED
```

The next permitted change is narrowly scoped to R1 consumption and
presentation of the existing Solver's zero/many outcomes. After that change,
the preparation dry run must be repeated, the build manifest hash-locked, and
only then may human sessions begin.
