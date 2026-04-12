from __future__ import annotations

import base64
import json

from app.skills.final_verdict_parts.evidence_chunking import format_plugin_evidence_chunks
from app.skills.final_verdict_parts.verdict_fingerprint import append_verdict_fingerprint_html_comment


def test_format_plugin_evidence_chunks_high_reasoning_keeps_long_fields() -> None:
    long_claim = "x" * 200
    plugin_outputs = {
        "demo.plugin": {"payload": {"evidence": [{"claim": long_claim, "detail": "d"}]}}
    }
    short_lines = format_plugin_evidence_chunks(plugin_outputs, high_reasoning=False)
    long_lines = format_plugin_evidence_chunks(plugin_outputs, high_reasoning=True)
    assert short_lines and all(len(x) < 250 for x in short_lines)
    assert long_lines and any(long_claim in x for x in long_lines)


def test_format_plugin_evidence_chunks_flattens_dict_items() -> None:
    plugin_outputs = {
        "demo.plugin": {
            "payload": {
                "evidence": [
                    {"claim": "现金流承压", "detail": "偏财过旺"},
                    "plain string slice",
                ]
            }
        }
    }
    lines = format_plugin_evidence_chunks(plugin_outputs)
    assert any("证据切片.demo.plugin" in x for x in lines)
    assert any("现金流" in x for x in lines)


def test_fingerprint_roundtrip_in_html_comment() -> None:
    md = "### 核心气象\nok\n"
    physics = {
        "by_pillar": {
            "year": {"raw_energy": 1.5},
            "month": {"raw_energy": 2.0},
            "day": {"raw_energy": 0.5},
            "hour": {"raw_energy": 1.0},
        },
        "meta": {"enabled_plugins": ["classical.blind_school.v1", "sys.core.physics"]},
    }
    meta = {"pillars": {"year": {"stem": "甲", "branch": "子", "energy_value": 80}}}
    out = append_verdict_fingerprint_html_comment(md, physics_tensor=physics, metadata=meta)
    assert "<!--qiazhi-fingerprint:v1 " in out
    assert out.strip().endswith("-->")
    tail = out.split("<!--qiazhi-fingerprint:v1 ", 1)[1].rsplit("-->", 1)[0].strip()
    pad = "=" * (-len(tail) % 4)
    raw = base64.urlsafe_b64decode(tail + pad)
    fp = json.loads(raw.decode("utf-8"))
    assert fp["schema"] == "qiazhi.verdict_fingerprint.v1"
    assert fp["pillar_energy_snapshot"]["year"]["raw_energy"] == 1.5
    assert "classical.blind_school.v1" in fp["active_plugins"]
