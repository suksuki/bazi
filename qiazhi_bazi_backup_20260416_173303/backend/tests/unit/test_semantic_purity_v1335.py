from __future__ import annotations

from app.skills.final_verdict_parts.semantic_purity import semantic_purity_ok
from app.semantic_translator.aliasing import alias_fact_ids_in_text


def test_semantic_purity_rejects_sys_core() -> None:
    out = "此命见 sys.core.physics 之征。"
    assert semantic_purity_ok(out) is False


def test_semantic_purity_rejects_fact_id() -> None:
    out = "【证据】一、冲合见于 Fact_ID=cp_scan_0。"
    assert semantic_purity_ok(out) is False


def test_aliasing_removes_fact_id_marker_from_prompt_text() -> None:
    src = "证据行：Fact_ID=cp_scan_0；次证据 Fact_ID:node_2"
    out = alias_fact_ids_in_text(src)
    assert "Fact_ID" not in out
    assert "证据锚点-" in out

