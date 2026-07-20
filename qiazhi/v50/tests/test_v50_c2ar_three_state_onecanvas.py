from __future__ import annotations

import json
import subprocess
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = (
    ROOT
    / "apps"
    / "product"
    / "static"
    / "experience"
    / "active"
    / "onecanvas-r1"
)
RUNTIME = PROTOTYPE / "onecanvas-runtime.js"
FIXTURE = PROTOTYPE / "fixture.json"
CONTRACT = ROOT / "docs/archive/proofs/V50_C2AR_ONECANVAS_THREE_STATE_INTEGRATION.md"
C1R_CONTRACT = ROOT / "docs/archive/proofs/V50_C1R_MINGLI_SHARED_SCENE_PROTOTYPE.md"


@lru_cache(maxsize=1)
def _runtime_probe() -> dict[str, object]:
    script = f"""
import fs from "node:fs/promises";
import {{
  compileOneCanvasCues,
  createOneCanvasModel,
  metaphorBindingFor,
}} from {json.dumps(RUNTIME.as_uri())};
const fixture = JSON.parse(await fs.readFile({json.dumps(str(FIXTURE))}, "utf8"));
const model = createOneCanvasModel(fixture);
const formal = {{
  mode: "formal",
  axis: "day",
  index: fixture.baseline_candidate_index.day,
  yearIndex: model.officialYearIndex,
  draftNodes: [],
}};
const nodes = model.nodesFor(formal);
const path = model.pathFor(formal);
const missingPath = {{
  epistemic_status: "user_draft",
  node_keys: ["year_stem", "month_stem", "day_stem"],
  segments: [
    {{from_key: "year_stem", to_key: "month_stem", label: "相生", status: "available"}},
    {{from_key: "month_stem", to_key: "day_stem", label: "缺少关系", status: "missing"}},
    {{from_key: "day_stem", to_key: "hour_stem", label: "不应播放", status: "available"}},
  ],
}};
console.log(JSON.stringify({{
  semanticRefs: nodes.map((item) => item.semantic_ref),
  bindings: nodes.map((item) => metaphorBindingFor(item)),
  formalCues: compileOneCanvasCues(path),
  missingCues: compileOneCanvasCues(missingPath),
}}));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_three_state_contract_freezes_one_world_not_three_pages() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    c1r = C1R_CONTRACT.read_text(encoding="utf-8")

    assert "Mingli OneCanvas / 一图三态" in contract
    assert "理 = semantic skeleton" in contract
    assert "象 = visual mapping" in contract
    assert "时 = temporal behavior" in contract
    assert "primary_canvas_count: 1" in contract
    assert "semantic_node_count: 12" in contract
    assert "production_deployment: false" in contract
    assert "product_gate: deferred_to_onecanvas_integration" in c1r


def test_three_state_keeps_available_semantic_refs_and_never_invents_luck() -> None:
    probe = _runtime_probe()
    refs = probe["semanticRefs"]
    bindings = probe["bindings"]

    assert len(refs) == 10
    assert len(set(refs)) == 10
    assert "node:luck_stem" not in refs
    assert "node:luck_branch" not in refs
    assert [item["semantic_ref"] for item in bindings] == refs
    assert all(item["author"] == "deepbazi_curated" for item in bindings)
    assert all(item["source_ref"].startswith("metaphor-binding:") for item in bindings)
    assert all("不增加" in item["mapping_explanation"] or "可追踪" in item["mapping_explanation"] for item in bindings)


def test_three_state_cues_enter_time_then_trace_existing_path() -> None:
    cues = _runtime_probe()["formalCues"]

    assert [item["action"] for item in cues[:3]] == [
        "show_natal",
        "enter_luck",
        "enter_annual",
    ]
    assert [item["temporal_stage"] for item in cues[:3]] == [0, 1, 2]
    assert all(item["action"] in {"focus_node", "trace_path", "block_path"} for item in cues[3:])


def test_three_state_playback_stops_at_first_missing_relation() -> None:
    cues = _runtime_probe()["missingCues"]
    actions = [item["action"] for item in cues]

    assert actions == [
        "show_natal",
        "enter_luck",
        "enter_annual",
        "focus_node",
        "trace_path",
        "focus_node",
        "block_path",
    ]
    assert cues[-1]["node_keys"] == ["month_stem", "day_stem"]
    assert "停止" in cues[-1]["label"]


def test_renderer_uses_one_canvas_continuous_expression_and_in_scene_playback() -> None:
    script = (PROTOTYPE / "prototype.js").read_text(encoding="utf-8")
    components = (PROTOTYPE / "onecanvas-components.js").read_text(encoding="utf-8")
    stylesheet = (PROTOTYPE / "styles.css").read_text(encoding="utf-8")
    combined = script + components + stylesheet

    assert components.count('class="canvas-field"') == 1
    assert 'data-action="expression-ratio"' in script
    assert 'class="node-glyph-layer"' in components
    assert 'class="node-motif-layer"' in components
    assert 'class="temporal-stage-track"' in script
    assert "currentPlaybackCues" in script
    assert "pausePlayback(true)" in script
    assert "renderProfile" not in script
    assert "profile-tab" not in combined
    assert "Path Studio" not in combined


def test_expression_axis_does_not_mutate_experiment_snapshot_or_path_draft() -> None:
    script = (PROTOTYPE / "prototype.js").read_text(encoding="utf-8")

    clone_body = script.split("function currentRenderSnapshot", 1)[0]
    assert "expressionRatio" in script
    assert "expressionRatio" not in clone_body.split("function formalSnapshot", 1)[1].split("function experimentSnapshot", 1)[0]
    assert "draftNodes" in script
    assert "selectedKey" in script
    assert "saved: { a: null, b: null }" in script


def test_three_state_frontend_does_not_infer_mingli_or_write_formal_state() -> None:
    runtime = RUNTIME.read_text(encoding="utf-8")
    script = (PROTOTYPE / "prototype.js").read_text(encoding="utf-8")
    combined = runtime + script

    for forbidden in (
        "resolve_ten_god",
        "STEM_ELEMENTS",
        "BRANCH_ELEMENTS",
        "calculateLuck",
        "inferRelation",
        "WebSocket",
        "EventSource",
        "LLM",
        "TTS",
        "life_case.write",
    ):
        assert forbidden not in combined
    assert "/api/v50/experience/onecanvas/target-compile" in combined
    assert "formal_state_writes" not in combined


def test_three_state_mobile_reuses_same_canvas_and_has_reduced_motion_boundary() -> None:
    stylesheet = (PROTOTYPE / "styles.css").read_text(encoding="utf-8")
    script = (PROTOTYPE / "prototype.js").read_text(encoding="utf-8")

    assert "@media (max-width: 620px)" in stylesheet
    assert ".scene-dimensions" in stylesheet
    assert ".temporal-stage-track" in stylesheet
    assert "prefers-reduced-motion: reduce" in stylesheet
    assert 'window.matchMedia("(prefers-reduced-motion: reduce)")' in script
