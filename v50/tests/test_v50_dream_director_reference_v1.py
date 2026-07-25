from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = (
    ROOT
    / "artifacts/abu-dream-world/director-reference/dream-encounter-01/v1"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_three_dream_references_are_archived_cleaned_and_registered() -> None:
    registry = _json(ASSET_ROOT / "registry.json")
    references = {item["reference_id"]: item for item in registry["references"]}

    assert registry["status"] == "registered_reference_only"
    assert registry["abu_character_reference"] == {
        "status": "candidate_not_canonical",
        "preferred_reference_id": "dream_ref_fog_gate_three_trees_v1",
        "traits": [
            "round_face",
            "short_muzzle",
            "compact_body",
            "soft_eye_placement",
            "red_scarf",
        ],
        "note_zh": "梦境版阿布候选造型参考；尚未替代正式角色模型表。",
    }
    assert set(references) == {
        "dream_ref_life_tree_growth_v1",
        "dream_ref_fog_gate_three_trees_v1",
        "dream_ref_tree_structure_response_v1",
    }
    assert registry["boundaries"] == {
        "runtime_authorized": False,
        "creates_mingli_claim": False,
        "changes_canonical_scene": False,
        "creates_path_assertion": False,
        "final_product_video": False,
        "use_as_animation_spec_reference": True,
    }

    for reference in references.values():
        source = ASSET_ROOT / reference["source"]["archived_file"]
        master = ASSET_ROOT / reference["clean_master"]["file"]
        contact_sheet = ASSET_ROOT / reference["contact_sheet"]["file"]
        assert source.stat().st_size > 2_000_000
        assert master.stat().st_size > 3_000_000
        assert reference["source"]["sha256"] == _sha256(source)
        assert reference["source"]["watermark_present"] is True
        assert reference["clean_master"]["sha256"] == _sha256(master)
        assert reference["clean_master"]["watermark_removed"] is True
        assert reference["clean_master"]["probe"]["streams"][0]["width"] == 1280
        assert reference["clean_master"]["probe"]["streams"][0]["height"] == 720
        assert len(reference["segments"]) == 4
        assert Image.open(contact_sheet).size == (1600, 720)


def test_all_director_segments_are_traceable_and_cover_each_master_once() -> None:
    registry = _json(ASSET_ROOT / "registry.json")

    for reference in registry["references"]:
        expected_start = 0.0
        for segment in reference["segments"]:
            assert segment["seconds"][0] == expected_start
            assert segment["seconds"][1] > segment["seconds"][0]
            expected_start = segment["seconds"][1]
            video = ASSET_ROOT / segment["video"]
            keyframe = ASSET_ROOT / segment["keyframe"]
            assert video.stat().st_size > 100_000
            assert segment["video_sha256"] == _sha256(video)
            assert segment["keyframe_sha256"] == _sha256(keyframe)
            assert Image.open(keyframe).size == (1280, 720)
        assert expected_start == 10.0


def test_global_media_registry_points_to_the_locked_dream_reference_registry() -> None:
    global_registry = _json(ROOT / "config/media_asset_registry_v1.json")
    pointer = global_registry["dream_director_reference"]
    registry = ROOT / pointer["registry"]

    assert pointer["status"] == "reference_only_not_runtime"
    assert pointer["runtime_authorized"] is False
    assert pointer["sha256"] == _sha256(registry)
