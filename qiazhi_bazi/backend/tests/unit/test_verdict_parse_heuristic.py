from __future__ import annotations

from app.skills.final_verdict_parts.verdict_parse import parse_verdict_anchor_layer


def test_parse_anchor_merges_heuristic_when_llm_refs_missing() -> None:
    md = {
        "pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day": {"stem": "戊", "branch": "午"},
            "hour": {"stem": "庚", "branch": "申"},
        },
        "conflict_matrix": {"points": [{"id": "cp_x", "kind": "clash", "detail": "子午冲", "positions": []}]},
    }
    obj = {
        "assertions": [
            {"assertion_id": "a0", "text": "子午冲导致气场震荡，年支子水与午火对立。", "evidence_refs": []},
        ]
    }
    out = parse_verdict_anchor_layer(obj, verdict_body="", version_id="v2.test", metadata=md)
    rows = out["assertions"]
    assert len(rows) == 1
    refs = set(rows[0]["evidence_refs"])
    assert "year.branch" in refs or "branch.子" in refs
    assert "conflict_matrix.cp_x" in refs


def test_parse_anchor_heuristic_from_plain_string_items() -> None:
    md = {"pillars": {"day": {"stem": "乙", "branch": "酉"}}, "conflict_matrix": {"points": []}}
    obj = {"assertions": ["日柱乙酉偏枯"]}
    out = parse_verdict_anchor_layer(obj, verdict_body="", version_id="v1", metadata=md)
    assert out["assertions"][0]["evidence_refs"]
