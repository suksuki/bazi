# V60 First Slice Evidence

## Purpose

This document records reproducible engineering and product evidence for the
first V60 Dream-first vertical slice. It is an implementation receipt, not a
new authority contract.

## Runtime

```text
Local Owner URL: http://127.0.0.1:8060/experience
Python: 3.12.13
Backend: FastAPI + SQLAlchemy + PostgreSQL
Frontend: React + TypeScript + PixiJS
Primary database: qiazhi_v60
Disposable audit database: qiazhi_v60_browser_test
```

The main Owner database had zero Dream encounters and zero AnswerSeals after
the automated audit. Browser automation used only the disposable audit
database.

## Provenance chain

```text
v60-synthetic-case-yanzhou-v1
-> v60-chart-5fb55ca928efd6a59d61
-> v60-lifecase-f14d2e58029051b45434
-> v60-actor-yanzhou-v1
-> v60-life-tree-yanzhou-v1
-> v60-question-yanzhou-old-channel-v1
-> v60-world-event-yanzhou-channel-outcome-v1
```

The synthetic chart was recomputed by the V60 calendar engine as:

```text
辛未 丙申 丙辰 癸巳
```

The structural projection exposes only bounded six-harmony membership for 巳
and 申. It does not claim effective relation, capacity or life outcome.

## State proof

The disposable browser run produced:

```text
NPC AnswerSeal: flow_intermit
Human QA AnswerSeal: flow_intermit
WorldEvent: SETTLED at Tick 12
Future EventEvidence: 2
Outbox records: 1
StoryFruit: one record, version 3, REVEALED
Reveal: one record, SUPPORTED
```

The server process was stopped and restarted before a subsequent authenticated
snapshot. The same Encounter, Fruit and Reveal were restored from PostgreSQL.

## Browser audit

Command:

```bash
V60_AUDIT_SESSION_TOKEN=... npm --prefix web run audit:first-slice
```

Result:

```yaml
desktop_viewport: 1440x900
document_vertical_scroll: false
document_horizontal_scroll: false
console_errors: 0
failed_requests: 0
pre_reveal_future_evidence_leaks: 0
refresh_recovery: PASS
process_restart_recovery: PASS
```

Screenshots:

```text
.artifacts/first-slice/01-question-open.png
.artifacts/first-slice/02-answer-sealed.png
.artifacts/first-slice/03-fruit-matured.png
.artifacts/first-slice/04-revealed.png
.artifacts/first-slice/05-reconciled.png
.artifacts/first-slice/06-lab-same-case.png
.artifacts/first-slice/07-refresh-recovered.png
```

The Runtime audit JSON is:

```text
.artifacts/first-slice/runtime-audit.json
```

## Code quality

```text
Ruff: PASS
Pytest: 21 passed
TypeScript: PASS
Vite production build: PASS
Asset registry verification: 19 assets
```

## Asset authority

All first-slice tree organs are copied into V60 and read through the V60 asset
registry. The approved source package outer SHA-256 is:

```text
2bd3f4d277462eec9200622315e2124ddd8e9ed417f12603500dfc9adf777efc
```

The current V60 asset registry SHA-256 is:

```text
8c6f9a3554f3928b79eacdfd82796d486de5e8d7348e648cf5d4654a35063de4
```

The Media Catalog records six immutable source items, four Runtime-registered
items, two explicit Abu character identities and three audio/visual Cue
Bundles. ABU_03 remains in V60 Owner Review and is not present in the Runtime
delivery registry.

## Current visual assessment

The fixed tree remains the dominant scene. Two evidence leaves, one structure
branch and the flower are spatial organs rather than generic form buttons.
After answer sealing, the flower leaves the scene and a single mist-white
fruit occupies the same semantic position. The fruit remains sealed until the
independent world event settles.

The scene is acceptable for the first playable proof. Organ integration and
the compact Lab panel still need later art-direction refinement; neither is
being misreported as final production visual quality.
