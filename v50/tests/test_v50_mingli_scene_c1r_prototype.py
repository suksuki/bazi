from __future__ import annotations

import json
import subprocess
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "archive/proofs/prototypes/mingli-scene-c1r"
RUNTIME = PROTOTYPE / "scene-runtime.js"
FIXTURE = ROOT / "archive/proofs/prototypes/mingli-lab-c2a/fixture.json"
CONTRACT = ROOT / "docs/archive/proofs/V50_C1R_MINGLI_SHARED_SCENE_PROTOTYPE.md"


@lru_cache(maxsize=1)
def _runtime_probe() -> dict[str, object]:
    script = f"""
import fs from "node:fs/promises";
import {{ compileSceneState, compileSceneCues, RENDER_PROFILES }} from {json.dumps(RUNTIME.as_uri())};
const fixture = JSON.parse(await fs.readFile({json.dumps(str(FIXTURE))}, "utf8"));
const officialYear = fixture.year_dial.findIndex((item) => item.source_mode === "official");
const partialVariant = fixture.variants.findIndex((item) => item.formal_path_reference.continuity_status === "partial");
const baseInput = {{
  mode: "formal",
  variantIndex: fixture.baseline_variant_index,
  yearIndex: officialYear,
  pathLens: "formal",
  draftNodes: ["day_stem", "hour_stem", "hour_branch"],
  selectedSemanticRef: "node:hour_branch",
}};
const profiles = Object.fromEntries(RENDER_PROFILES.map((renderProfile) => {{
  const scene = compileSceneState(fixture, {{...baseInput, renderProfile}});
  return [renderProfile, {{
    sceneStateId: scene.scene_state_id,
    semanticRefs: scene.visual_objects.map((item) => item.semantic_ref),
    selectedSemanticRef: scene.selected_semantic_ref,
    activePath: scene.active_path,
    userPathDraft: scene.user_path_draft,
  }}];
}}));
const partial = compileSceneState(fixture, {{
  ...baseInput,
  mode: "experiment",
  variantIndex: partialVariant,
  renderProfile: "theater",
  draftNodes: [],
}});
const hypothetical = compileSceneState(fixture, {{
  ...baseInput,
  mode: "experiment",
  yearIndex: 0,
  renderProfile: "xiangfa",
}});
console.log(JSON.stringify({{
  renderProfiles: RENDER_PROFILES,
  profiles,
  expectedNodeRefs: fixture.variants[fixture.baseline_variant_index].nodes.map((item) => `node:${{item.node_key}}`),
  partial: {{
    continuity: partial.active_path.continuity_status,
    cues: compileSceneCues(partial.active_path),
    segments: partial.active_path.segments,
  }},
  hypothetical: {{
    sceneStateId: hypothetical.scene_state_id,
    sourceMode: hypothetical.source_mode,
    temporalStage: hypothetical.temporal_stage,
    yearObject: hypothetical.visual_objects.find((item) => item.semantic_ref === "temporal:year"),
  }},
  visualObjects: hypothetical.visual_objects,
  metaphorBindings: hypothetical.metaphor_bindings,
}}));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_c1r_contract_freezes_shared_scene_as_projection_not_reasoner() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")

    assert "Mingli Scene Runtime" in contract
    assert "production_runtime_authorized: false" in contract
    assert "full_c2_authorized: false" in contract
    assert "The same `semantic_ref` identifies the same object" in contract
    assert "no LLM, TTS or generated Mingli explanation" in contract
    assert "no deployment to server 13" in contract


def test_c1r_frontend_reuses_real_anonymized_fixture_without_api_or_formal_writes() -> None:
    script = (PROTOTYPE / "prototype.js").read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    combined = script + runtime

    assert 'fetch("../mingli-lab-c2a/fixture.json"' in script
    for forbidden in ("/api/", "WebSocket", "EventSource", "life_case.write", "ChartVersion.write"):
        assert forbidden not in combined
    assert "formal_temporal_effect_available" in runtime
    assert "user_draft" in runtime


def test_c1r_preserves_one_semantic_world_selection_and_path_draft_across_profiles() -> None:
    payload = _runtime_probe()
    profiles = payload["profiles"]

    assert payload["renderProfiles"] == ["lab", "xiangfa", "theater"]
    scene_ids = {item["sceneStateId"] for item in profiles.values()}
    semantic_ref_sets = {tuple(item["semanticRefs"]) for item in profiles.values()}
    selections = {item["selectedSemanticRef"] for item in profiles.values()}
    drafts = {json.dumps(item["userPathDraft"], sort_keys=True) for item in profiles.values()}
    active_paths = {json.dumps(item["activePath"], sort_keys=True) for item in profiles.values()}

    assert len(scene_ids) == 1
    assert len(semantic_ref_sets) == 1
    assert selections == {"node:hour_branch"}
    assert len(drafts) == 1
    assert len(active_paths) == 1
    assert profiles["lab"]["userPathDraft"]["epistemic_status"] == "user_draft"


def test_c1r_composer_neither_drops_source_nodes_nor_reconstructs_extra_semantics() -> None:
    payload = _runtime_probe()
    actual_refs = set(payload["profiles"]["lab"]["semanticRefs"])
    expected_refs = {*payload["expectedNodeRefs"], "temporal:luck", "temporal:year"}

    assert actual_refs == expected_refs
    assert all(item["source_refs"] for item in payload["visualObjects"])
    assert all(item["epistemic_status"] in {"canonical", "hypothetical"} for item in payload["visualObjects"])


def test_c1r_metaphor_bindings_are_traceable_disclosed_and_never_formal_claims() -> None:
    bindings = _runtime_probe()["metaphorBindings"]
    allowed_types = {
        "canonical_symbol",
        "tradition_supported",
        "analyst_authored",
        "illustrative_only",
    }

    assert bindings
    assert all(item["binding_type"] in allowed_types for item in bindings)
    assert all(item["source_ref"].startswith("metaphor-binding:") for item in bindings)
    assert all(item["author"] == "deepbazi_curated" for item in bindings)
    assert all(item["disclosure_level"] == "member" for item in bindings)
    assert all("不增加" in item["mapping_explanation"] or "表现" in item["mapping_explanation"] for item in bindings)


def test_c1r_theater_stops_at_first_missing_segment_without_inventing_a_bridge() -> None:
    partial = _runtime_probe()["partial"]
    cues = partial["cues"]
    segments = partial["segments"]

    assert partial["continuity"] == "partial"
    assert [item["action"] for item in cues] == ["focus", "trace_path", "focus", "block_path"]
    assert cues[-1]["at_step"] == len(cues) - 1
    assert "停止" in cues[-1]["label"]
    assert segments[-1]["status"] == "missing"
    assert "原关系" in segments[-1]["label"]
    assert "未保留" in segments[-1]["label"]
    assert not any(item["action"] == "trace_path" for item in cues[cues.index(cues[-1]) + 1 :])


def test_c1r_hypothetical_year_remains_a_signal_without_fabricated_temporal_effect() -> None:
    hypothetical = _runtime_probe()["hypothetical"]

    assert hypothetical["sceneStateId"].endswith(":2024")
    assert hypothetical["sourceMode"] == "hypothetical"
    assert hypothetical["temporalStage"]["year_source_mode"] == "hypothetical"
    assert hypothetical["temporalStage"]["formal_temporal_effect_available"] is False
    assert hypothetical["yearObject"]["epistemic_status"] == "hypothetical"
    assert hypothetical["yearObject"]["source_refs"] == ["source:sandbox:year-dial:2024"]


def test_c1r_markup_exposes_three_profiles_semantic_hotspots_and_accessible_controls() -> None:
    html = (PROTOTYPE / "index.html").read_text(encoding="utf-8")
    script = (PROTOTYPE / "prototype.js").read_text(encoding="utf-8")

    assert 'id="sceneRoot"' in html
    assert 'role="tab"' in script
    assert 'data-profile="${profile}"' in script
    assert 'data-semantic-ref="${semanticRef}"' in script
    assert "从当前路径开始演时" in script
    assert "流年进入，但不虚构作用" in script
    assert "prefers-reduced-motion" in script
