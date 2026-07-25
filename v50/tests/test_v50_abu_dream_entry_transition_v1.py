from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "apps/product/experience_shell/src"
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/dream/entry-transition-v1"
PORCH_ROOT = ROOT / "apps/product/static/l5/assets/dream/porch-v5"
REVIEW_ROOT = (
    ROOT
    / "artifacts/abu-dream-world/entry-transition/abu-03-dream-entry-transition-v1/review"
)
SOURCE_SHA256 = "ca42b6e7c7ad1236cb3c35676471302d26401ae07fb2fc3550cf15fa2243e7f7"
RUNTIME_SHA256 = "76e3ddf69bb9f206fd6f3fc90969f3c0ede521e1a4a93579d79f28ac8ebd615d"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_abu_03_clean_master_and_runtime_are_traceable() -> None:
    manifest = _json(ASSET_ROOT / "manifest.json")
    source = ROOT / manifest["source"]["archived_path"]
    clean = ROOT / manifest["postprocess"]["clean_master_path"]
    runtime = ROOT / manifest["runtime"]["path"]

    assert manifest["asset_id"] == "ABU_03_DREAM_ENTRY_TRANSITION_V1"
    assert manifest["source"]["sha256"] == SOURCE_SHA256
    assert _sha256(source) == SOURCE_SHA256
    assert manifest["postprocess"]["watermark_removed"] is True
    assert manifest["postprocess"]["watermark_removal_method"] == "sixteen_by_nine_safe_crop"
    assert manifest["postprocess"]["audio_removed"] is True
    assert _sha256(clean) == manifest["postprocess"]["clean_master_sha256"]
    assert _sha256(runtime) == manifest["runtime"]["sha256"] == RUNTIME_SHA256


def test_abu_03_runtime_is_1080p_775_seconds_and_has_no_audio() -> None:
    runtime = ASSET_ROOT / "abu_03_dream_entry_transition_v1_runtime_1080p.mp4"
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,width,height,r_frame_rate",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(runtime),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(probe.stdout)

    assert [stream["codec_type"] for stream in payload["streams"]] == ["video"]
    assert payload["streams"][0]["width"] == 1920
    assert payload["streams"][0]["height"] == 1080
    assert payload["streams"][0]["r_frame_rate"] == "24/1"
    assert float(payload["format"]["duration"]) == 7.75


def test_porch_handoff_plate_remains_traceable() -> None:
    porch = _json(PORCH_ROOT / "manifest.json")

    assert porch["visual_master"] == "ABU_03_DREAM_ENTRY_TRANSITION_V1"
    assert porch["handoff"]["center_candidate"] == "dream_porch_blue_tree_actor_v5"
    assert porch["constraints"]["runtime_controls_rotation_and_selection"] is True
    assert porch["constraints"]["background_never_rotates"] is True
    assert porch["constraints"]["all_three_tree_actors_fade_together"] is True
    for actor in porch["actors"]:
        path = ROOT / actor["path"]
        assert path.is_file()
        assert _sha256(path) == actor["sha256"]
        assert actor["alpha"] is True


def test_retired_grove_and_tree_assets_cannot_return_to_runtime() -> None:
    retired = (
        "grove-background-v1.webp",
        "tree-mist-v1.webp",
        "tree-brook-v1.webp",
        "tree-ridge-v1.webp",
        "ghostOrbitGrove",
        "ghostTreeMist",
        "ghostTreeBrook",
        "ghostTreeRidge",
        "porch-blue-v3.webp",
        "porch-jade-v3.webp",
        "porch-amber-v3.webp",
        "porch-three-trees-clean-plate.png",
        "porch-three-trees-preseal.png",
        "porch-three-trees.png",
        "porch-blue-single-v4-230add93.png",
        "porch-jade-single-v4-fced62f3.png",
        "porch-amber-single-v4-3ba7358f.png",
    )
    runtime_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            SHELL / "dream_asset_registry.ts",
            SHELL / "dream_runtime.ts",
            SHELL / "dream_tree_world.ts",
            ROOT / "apps/product/static/experience/styles.css",
        )
    )
    for value in retired:
        assert value not in runtime_sources

    approved = ROOT / "apps/product/static/l5/assets/dream/porch-v5/manifest.json"
    manifest = _json(approved)
    background = manifest["background"]
    runtime = ROOT / background["path"]
    assert background["status"] == "OWNER_APPROVED"
    assert _sha256(runtime) == background["sha256"]
    assert len(manifest["actors"]) == 3
    assert all(actor["alpha"] is True for actor in manifest["actors"])
    assert "DREAM_RUNTIME_ASSETS.porchCleanBackdrop.source" in (
        SHELL / "dream_asset_registry.ts"
    ).read_text(encoding="utf-8")


def test_sleeping_abu_transition_crosses_navigation_and_fails_closed() -> None:
    main = (SHELL / "main.ts").read_text(encoding="utf-8")
    transition = (SHELL / "dream_entry_transition.ts").read_text(encoding="utf-8")
    styles = (ROOT / "apps/product/static/experience/styles.css").read_text(encoding="utf-8")

    assert "beginDreamEntryTransition" in main
    assert "resumeDreamEntryTransition" in main
    assert "if (!dreamStatus?.resumable)" not in main
    assert 'renderLoading("正在回到上次离开的林地")' not in main
    assert "entryTransition?.bindVisit(visit.visit_id)" in main
    assert "entryTransition?.cancel()" in main
    assert "HANDOFF_START_MS = 7_100" in transition
    assert "RUNTIME_END_MS = 7_750" in transition
    assert "routeVisitId !== state.visitId" in transition
    assert "dream-entry-cinematic-local-fog" in styles
    assert 'classList.add("is-masking-abu")' in transition
    assert 'classList.add("is-dream-entry-active")' in transition
    assert ".dream-entry-cinematic.is-handing-off" in styles


def test_owner_review_recording_covers_the_real_handoff() -> None:
    review = _json(REVIEW_ROOT / "manifest.json")
    recording = ROOT / review["recording"]["path"]
    mobile_evidence = ROOT / review["mobile_evidence"]["path"]

    assert review["review_status"] == "POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW"
    assert recording.is_file()
    assert _sha256(recording) == review["recording"]["sha256"]
    assert mobile_evidence.is_file()
    assert _sha256(mobile_evidence) == review["mobile_evidence"]["sha256"]
    assert review["mobile_evidence"]["css_viewport_width"] == 390
    assert review["mobile_evidence"]["document_scroll"] is False
    assert review["recording"]["audio"] is False
    assert review["verified_handoff"]["standing_and_seated_abu_overlap"] is False
    assert review["verified_handoff"]["center_tree_position_is_stable"] is True
    assert review["verified_handoff"]["ends_in_live_interactive_porch"] is True
    assert review["verified_handoff"]["runtime_owns_tree_rotation"] is True


def test_old_reference_is_not_registered_as_complete_home_entry() -> None:
    runtime = _json(
        ROOT / "apps/product/static/l5/assets/dream/runtime-foundation-v1/manifest.json",
    )
    old_master = next(
        item for item in runtime["prototype_masters"] if item["filename"] == "1000056881.mp4"
    )
    old_asset = next(
        item
        for item in runtime["registered_runtime_assets"]
        if item["asset_id"] == "dream_fog_gate_preselection_clean_v1"
    )

    assert old_master["complete_home_entry_transition"] is False
    assert old_master["runtime_intents"] == ["ghost_orbit_director_reference"]
    assert old_asset["intent"] == "director_reference"
    assert old_asset["status"] == "TRANSITIONAL_FALLBACK"
    assert old_asset["complete_home_entry_transition"] is False
