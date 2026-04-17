# V17 Rebirth Constitution

## Scope

- Active workspace: `v17_rebirth/` only.
- Allowed legacy dependency: `core/physics` as read-only reference.
- Forbidden migration: any legacy narrative, UI, or business orchestration logic.

## Core Architectural Laws

1. **Narrative Pipeline First**
   - Every user-facing sentence must flow through:
   - `NarrativeSanitizer -> SemanticFusion -> render_text`.
2. **Will Collapse**
   - User intent is a first-class signal (`will_proxy`) and must bias narrative tone in real time.
3. **Protocol Lock**
   - Frontend renders only `payload.render_text`.
   - Frames missing `render_text` are treated as invalid signal.
4. **Bridge, Not Clone**
   - Infrastructure can reuse DB/LLM connection capability only.
   - Every V17 write operation must include `origin = "v17_origin"`.

## V17 Narrative Frame Contract (Draft)

```json
{
  "timestamp": "ISO-8601",
  "layer": "NARRATOR|SNAPSHOT|ACTION_TAKEN",
  "payload": {
    "render_text": "human-readable narrative sentence",
    "god_rings": {
      "god_of_use": [],
      "god_of_taboo": []
    },
    "will_proxy": "stable|aggressive"
  }
}
```

## Boot Sequence (Current Milestone)

- [x] Create vacuum workspace `v17_rebirth`.
- [x] Implement backend `RealtimeNarrativePipeline` skeleton.
- [x] Implement frontend `V17_PurpleVerdictCard` protocol-locked renderer.
- [x] Implement infrastructure bridges for DB/Admin/LLM configuration.

## V17.1 First Pure Verdict Drill

- Read-only physics adapter: `backend/adapters/physics_adapter.py`
- First pure verdict experiment: `backend/experiments/first_pure_verdict.py`
- WebStream render demo: `frontend/components/V17_WebStreamDemo.tsx`

Run (module mode):

`PYTHONPATH=/home/hlsystem/bazi/qiazhi python3 -m v17_rebirth.backend.experiments.first_pure_verdict`

## Systemd Deployment (V17.2)

- Unit files:
  - `deploy/systemd/v17-backend.service`
  - `deploy/systemd/v17-frontend.service`
- One-time install:
  - `scripts/install_systemd_services.sh`
- Restart both services:
  - `scripts/restart_v17_stack.sh`
