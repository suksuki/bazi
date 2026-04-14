from __future__ import annotations

from app.logic.brain.assertion_tree import build_assertion_tree
from app.logic.brain.psv_engine import PSVSymbol
from app.services.helpers.metadata_projector_v12 import MetadataProjectorV12
from app.logic.brain.psv_engine import PSVEngine
from app.logic.brain.config import load_psv_runtime_config
from tests.unit.test_metadata_projector_v12 import _sample_bundle_1990_06_14_zhengguan


def test_assertion_tree_builds_fact_law_will_nodes() -> None:
    assertions = [
        {"assertion_id": "a0", "text": "财轴存在回撤压力", "evidence_refs": ["rule:psv.robber_wealth_pierce_ratio"]},
    ]
    psv = [
        PSVSymbol(
            axis="WEALTH",
            polarity="STRONG_NEGATIVE",
            strength=0.9,
            evidence=["rule:psv.robber_wealth_pierce_ratio"],
            fingerprint="f1",
        )
    ]
    tree = build_assertion_tree(version_id="v2.1", assertions=assertions, psv_list=psv, user_intention_id="seek_stability")
    nodes = tree.get("nodes") or []
    node_types = [str(x.get("node_type")) for x in nodes if isinstance(x, dict)]
    assert nodes and str(nodes[0].get("node_type")) == "FACT"
    assert str(nodes[-1].get("node_type")) == "SYNTHESIS"
    assert "FACT" in node_types
    assert "LAW" in node_types
    assert "WILL" in node_types


def test_assertion_tree_with_1990_sample_psv() -> None:
    bundle = _sample_bundle_1990_06_14_zhengguan()
    tri = MetadataProjectorV12().project(bundle)
    psv = PSVEngine(load_psv_runtime_config(None)).build(tri)
    tree = build_assertion_tree(
        version_id="v2.sample",
        assertions=[{"assertion_id": "a0", "text": "样本断言", "evidence_refs": ["sample.1990"]}],
        psv_list=psv,
        user_intention_id="seek_stability",
    )
    nodes = tree.get("nodes") or []
    assert len(nodes) >= 2
