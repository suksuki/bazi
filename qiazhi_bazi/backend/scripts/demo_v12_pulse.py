#!/usr/bin/env python3
"""
V12.0 全链路脉冲演示：ActiveProbing ↔ BrainHub(PSV/SemanticAuditor) ↔ AssertionTree。

样本：1990-06-14 庚午年 / 壬午月 / 庚子日 / 丙子时（正官格 mock，庚金身弱语境）。

用法（在 backend 目录）::

  python3 scripts/demo_v12_pulse.py
"""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))
os.environ.setdefault("DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://test:test@127.0.0.1:5432/test"))

from app.logic.brain.active_probing import evaluate_active_probing
from app.logic.brain.assertion_tree import build_assertion_tree
from app.logic.brain.hub import BrainHub, BrainHubPulseState
from tests.unit.test_metadata_projector_v12 import _sample_bundle_1990_06_14_zhengguan


def _log(msg: str) -> None:
    print(msg, flush=True)


def _transition(
    log: List[Tuple[str, str, str]],
    state: BrainHubPulseState,
    reason: str,
    current: List[BrainHubPulseState],
) -> None:
    prev = current[0]
    current[0] = state
    log.append((prev.value, state.value, reason))
    _log(f"[Pulse] {prev.value} -> {state.value} | {reason}")


def _print_psv_manifest(psv_list: Any, title: str) -> None:
    _log("")
    _log(f"=== {title} ===")
    for s in psv_list:
        _log(f"  - {s.axis}: {s.polarity}  strength={s.strength:.4f}")
        for ev in (s.evidence or [])[:5]:
            _log(f"      evidence: {ev}")


def main() -> int:
    pulse_log: List[Tuple[str, str, str]] = []
    hub_state: List[BrainHubPulseState] = [BrainHubPulseState.HUB_IDLE]

    bundle = _sample_bundle_1990_06_14_zhengguan()
    metadata = copy.deepcopy(bundle["metadata"])
    physics_tensor = copy.deepcopy(bundle["physics_tensor"])
    user_intention = str(bundle.get("user_intention") or "")

    hub = BrainHub()
    _log("========== V12.0 E2E Pulse Demo ==========")
    _log("样本：1990-06-14 庚午 / 壬午 / 庚子 / 丙子（mock 正官格）")

    # --- 流程 A：主动追问（persistence 缺婚姻偏置 + 日支子午冲）---
    pl = dict(metadata.get("persistence_layer") or {})
    for k in ("marriage_palace_bias", "emotional_axis_ack", "marriage_axis_profile"):
        pl.pop(k, None)
    metadata["persistence_layer"] = pl

    ap = evaluate_active_probing(
        physics_tensor=physics_tensor,
        plugin_outputs=dict(physics_tensor.get("plugin_outputs") or {}),
        metadata=metadata,
    )
    _transition(pulse_log, BrainHubPulseState.PROBE_OFFERED, "active_probing: 子午冲×情感宫位且婚姻偏置缺失", hub_state)
    _log("")
    _log("--- 流程 A：ActiveProbing ---")
    _log(f"should_probe={ap.should_probe} block_mode={ap.block_mode} reason={ap.reason_code}")
    if ap.interrupt:
        _log(f"InterruptRequest: id={ap.interrupt.interrupt_id} code={ap.interrupt.reason_code} state={ap.interrupt.state}")
        _log(f"  evidence_refs={ap.interrupt.evidence_refs}")

    if not ap.interrupt or ap.interrupt.reason_code != "M3_ZI_WU_MARRIAGE_PALACE_PROBE":
        _log("ERROR: 预期触发 M3_ZI_WU_MARRIAGE_PALACE_PROBE")
        return 2

    # --- 流程 B：意志注入与局部重算（模拟用户回复）---
    user_reply = "目前处于职场转折期，优先求名"
    _transition(pulse_log, BrainHubPulseState.BIAS_ACK_INGESTED, f"用户回复已入账: {user_reply!r}", hub_state)

    md_pl = dict(metadata.get("persistence_layer") or {})
    md_pl["marriage_palace_bias"] = {
        "ack": True,
        "source": "demo_v12_pulse",
        "note": "职场转折期优先求名，情感主轴降级",
    }
    md_pl["bias_ack_tokens"] = [
        {
            "token_id": "ack-demo-001",
            "interrupt_id": ap.interrupt.interrupt_id if ap.interrupt else "",
            "kind": "M3_RESUME",
            "payload": {"user_reply": user_reply},
        }
    ]
    metadata["persistence_layer"] = md_pl
    metadata["bias_ack_tokens"] = list(md_pl["bias_ack_tokens"])

    user_intention = "seek_fame"
    bundle2: Dict[str, Any] = {
        "metadata": metadata,
        "physics_tensor": physics_tensor,
        "user_intention": user_intention,
    }
    meta_pt = physics_tensor.setdefault("meta", {})
    if isinstance(meta_pt, dict):
        ic = dict(meta_pt.get("intention_context") or {})
        ic["active_intention"] = "seek_fame"
        ic["user_reply_last"] = user_reply
        meta_pt["intention_context"] = ic

    ctx2 = hub.build_context(
        metadata=bundle2["metadata"],
        physics_tensor=bundle2["physics_tensor"],
        user_intention=bundle2["user_intention"],
    )
    _transition(
        pulse_log,
        BrainHubPulseState.LOCAL_RECOMPUTE_REQUESTED,
        "BrainHub.build_context 重投影 + PSV 重算（seek_fame × 正官格）",
        hub_state,
    )
    _print_psv_manifest(ctx2.psv_list, "PSV 基调清单（流程 B 后，用于监军）")

    # --- 流程 C：SemanticAuditor 对撞 LLM 幻觉 ---
    hallucination = (
        "此盘财官双美，近期财源广进、大发横财，可放手投机暴富。"
    )
    audit = hub.audit(hallucination, ctx2.psv_list)
    _transition(pulse_log, BrainHubPulseState.AUDIT_GATE, f"semantic_auditor: {audit.audit_state} ({audit.reason_code})", hub_state)
    _log("")
    _log("--- 流程 C：SemanticAuditor ---")
    _log(f"narrative={hallucination}")
    _log(f"audit_state={audit.audit_state} reason_code={audit.reason_code}")
    _log(f"matched_rules={audit.matched_rules}")
    if audit.conflict_excerpt:
        _log(f"conflict_excerpt={audit.conflict_excerpt}")

    if audit.audit_state != "REJECT":
        _log("ERROR: 预期对「财源广进/大发横财」拒稿（WEALTH 负向轴）")
        return 3

    # --- 流程 D：AssertionTree ---
    assertions = [
        {
            "assertion_id": "f1",
            "text": "子午冲牵动日支，情感宫位能量波动需与事业意志对齐。",
            "evidence_refs": ["pillars.day_branch", "topology:zi_wu"],
        },
        {
            "assertion_id": "f2",
            "text": "财轴呈比劫穿透高压，叙事忌宣称暴富式利好。",
            "evidence_refs": ["rule:psv.robber_wealth_pierce_ratio"],
        },
    ]
    tree = build_assertion_tree(
        version_id="demo-v12-pulse",
        assertions=assertions,
        psv_list=ctx2.psv_list,
        user_intention_id=user_intention,
    )
    _transition(pulse_log, BrainHubPulseState.ASSERTION_TREE_MATERIALIZED, "assertion_tree.v1 已物化", hub_state)

    nodes = tree.get("nodes") or []
    _log("")
    _log("--- 流程 D：AssertionTree ---")
    _log(f"nodes_order: {[n.get('node_type') for n in nodes if isinstance(n, dict)]}")
    _log(f"first_node={nodes[0] if nodes else {}}")
    _log(f"last_synthesis={nodes[-1] if nodes else {}}")
    _log("tree_json=" + json.dumps(tree, ensure_ascii=False, indent=2))

    _log("")
    _log("--- BrainHub 状态迁移摘要 ---")
    for prev, nxt, r in pulse_log:
        _log(f"  {prev} -> {nxt}  |  {r}")

    tri = ctx2.tri
    ack_n = len(tri.arbiter_bias.bias_ack_tokens or [])
    _log("")
    _log(f"ArbiterBias.bias_ack_tokens 条数（投影）: {ack_n}")
    if ack_n < 1:
        _log("WARN: bias_ack_token 未进入三色投影，请检查 persistence/metadata。")
        return 4

    _log("")
    _log("========== Demo 完成 ==========")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
