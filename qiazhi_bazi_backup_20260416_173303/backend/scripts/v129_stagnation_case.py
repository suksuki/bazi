#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://test:test@127.0.0.1:5432/test"))
os.environ.setdefault("QIAZHI_SKIP_DISSENT_LEDGER_PERSIST", "1")

from app.logic.brain.hub import BrainHub
from tests.unit.test_metadata_projector_v12 import _sample_bundle_1990_06_14_zhengguan


def main() -> int:
    sample = _sample_bundle_1990_06_14_zhengguan()
    md = copy.deepcopy(sample.get("metadata") or {})
    pt = copy.deepcopy(sample.get("physics_tensor") or {})
    hub = BrainHub()
    conflict_points = ((md.get("conflict_matrix") or {}).get("points") or []) if isinstance(md.get("conflict_matrix"), dict) else []
    orchestration = hub.orchestrate(
        conflict_points=[{"kind": str((x or {}).get("kind") or ""), "detail": str((x or {}).get("detail") or "")} for x in conflict_points],
        verified_facts=["VF_01", "VF_02", "VF_03"],
        user_confirmed=False,
        self_abs=0.95,
        output_vector_present=False,
    )
    print("=== V12.9 stagnation case ===")
    print(f"seed_key={orchestration.seed_key}")
    print(f"flow_state={orchestration.flow_state}")
    print(f"probe_query={orchestration.probe_query}")
    print(f"htn_plan={json.dumps(orchestration.htn_plan, ensure_ascii=False)}")
    fb = hub.assimilate_feedback({"text": "是的，很准，最近就是严重内耗"})
    print(f"feedback_assimilated={json.dumps(fb, ensure_ascii=False)}")
    if not fb.get("confirmed"):
        return 2
    md.setdefault("persistence_layer", {})
    bh = dict((md.get("persistence_layer") or {}).get("brain_hub") or {})
    confirmed = list(bh.get("confirmed_facts") or [])
    confirmed.append(dict(fb.get("fact") or {}))
    bh["confirmed_facts"] = confirmed
    md["persistence_layer"]["brain_hub"] = bh
    ctx = hub.build_context(metadata=md, physics_tensor=pt, user_intention="seek_stability")
    print(f"psv_count={len(ctx.psv_list)} sacred_weight={confirmed[-1].get('weight')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
