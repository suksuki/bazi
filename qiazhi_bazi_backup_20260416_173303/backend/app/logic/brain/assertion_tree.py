"""V12 M4：Assertion Tree 碎片化生成。"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.logic.brain.psv_engine import PSVSymbol


class AssertionNode(BaseModel):
    model_config = {"extra": "forbid"}

    node_id: str
    node_type: str
    text: str
    evidence_refs: List[str] = Field(default_factory=list)


class AssertionTree(BaseModel):
    model_config = {"extra": "forbid"}

    protocol: str = "assertion_tree.v1"
    root_id: str = "root"
    nodes: List[AssertionNode] = Field(default_factory=list)
    edges: List[Dict[str, str]] = Field(default_factory=list)


def build_assertion_tree(
    *,
    version_id: str,
    assertions: List[Dict[str, Any]],
    psv_list: List[PSVSymbol],
    user_intention_id: str = "",
) -> Dict[str, Any]:
    """FACT 节点在 ``nodes`` 列表中居前；SYNTHESIS 根节点置末（缝合槽）。"""
    nodes: List[AssertionNode] = []
    edges: List[Dict[str, str]] = []

    for idx, row in enumerate(assertions):
        aid = str((row or {}).get("assertion_id") or f"a{idx}")
        txt = str((row or {}).get("text") or "").strip()
        refs = [str(x) for x in ((row or {}).get("evidence_refs") or []) if str(x).strip()]
        nodes.append(AssertionNode(node_id=f"fact-{aid}", node_type="FACT", text=txt, evidence_refs=refs))
        edges.append({"from": "root", "to": f"fact-{aid}", "label": "supports"})

    for idx, s in enumerate(psv_list):
        node_id = f"law-{idx}"
        nodes.append(
            AssertionNode(
                node_id=node_id,
                node_type="LAW",
                text=f"{s.axis}:{s.polarity}({s.strength:.2f})",
                evidence_refs=[str(x) for x in (s.evidence or [])[:4]],
            )
        )
        edges.append({"from": "root", "to": node_id, "label": "constrains"})

    if str(user_intention_id or "").strip():
        nodes.append(
            AssertionNode(
                node_id="will-0",
                node_type="WILL",
                text=f"user_intention={str(user_intention_id).strip()}",
                evidence_refs=["arbiter_bias.user_intention_id"],
            )
        )
        edges.append({"from": "root", "to": "will-0", "label": "guides"})

    nodes.append(
        AssertionNode(
            node_id="root",
            node_type="SYNTHESIS",
            text=f"version={version_id} | synthesis_slot=deterministic_stub",
            evidence_refs=[],
        )
    )

    return AssertionTree(nodes=nodes, edges=edges).model_dump()


__all__ = ["AssertionNode", "AssertionTree", "build_assertion_tree"]
