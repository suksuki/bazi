# V50 Lean & Consolidation — L0/L1 Closeout

L0 and L1 made the active system smaller without changing Mingli behavior.

| Measure | Before | After |
|---|---:|---:|
| Measured repository | 1,558,363,161 B | 445,823,001 B |
| Measured files | 3,750 | 1,131 |
| Artifacts | 1,310,326,438 B | 197,037,198 B |
| Experience static | 39,753,473 B | 20,077,730 B |
| Runtime-exposed prototypes | 11 | 5 |
| Archived proofs | 0 | 6 |
| Exact duplicate runtime media | 309,700,981 B | 0 B |
| Visible current-authority docs | 11 | 5 |
| Full regression | 408 pass / 1 fail | 413 pass / 0 fail |

The active Experience surface now contains one Canvas candidate, one isolated
Xiangfa validation route, two internal tools, and one locked shared scene. Six
superseded prototypes moved to `archive/proofs/prototypes` and no longer ship
from the runtime static tree.

Regenerable frames, intermediate QA, expanded review packs and superseded ZIPs
were removed. Final videos, source videos, keyframes, contact sheets, final
review ZIPs and frozen scene sources remain. The exact retention decision is in
`config/v50_lean_l1_manifest_v1.json`.

The main Experience bundle remained 79,264 bytes; L1 did not claim a bundle
optimization it did not perform. A post-cleanup application-build probe is
21.74 ms median / 32.31 ms p95 and becomes the honest L2 baseline because no
pre-cleanup probe was captured.

Full regression is green at `413 passed`. L2 authority consolidation, full C2,
RA1 and production deployment were not started.
