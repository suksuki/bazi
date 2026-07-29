from __future__ import annotations

import json
import subprocess

from abu_v60.media import PROJECT_ROOT
from abu_v60.media.registry import sha256_file


def test_v60_guide_left_is_one_clean_single_gesture() -> None:
    manifest_path = (
        PROJECT_ROOT
        / "media"
        / "manifests"
        / "ABU_V60_05_GUIDE_LEFT_ONCE_V1.v1.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["character_version"] == "ABU_CHARACTER_V60_V1"
    assert manifest["selection"]["source_start_frame_inclusive"] == 12
    assert manifest["selection"]["source_end_frame_exclusive"] == 116
    assert manifest["selection"]["delivery_frame_count"] == 104
    assert manifest["motion_contract"]["semantic_state"] == "GUIDE_LEFT"
    assert manifest["motion_contract"]["gesture_count"] == 1
    assert manifest["runtime_contract"]["playback"] == "PLAY_ONCE"
    assert (
        manifest["runtime_contract"]["return_action"]
        == "media.abu.v60.seated-idle.v1"
    )
    assert manifest["anchor"]["observed_range"] == [704, 704]


def test_v60_guide_left_excludes_the_right_window_before_alpha_delivery() -> None:
    manifest_path = (
        PROJECT_ROOT
        / "media"
        / "manifests"
        / "ABU_V60_05_GUIDE_LEFT_ONCE_V1.v1.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    exclusion = manifest["watermark_and_window"]

    assert exclusion["removed"] is True
    assert exclusion["retained_source_rect"] == [0, 0, 950, 720]
    assert exclusion["excluded_source_rect"] == [950, 0, 1280, 720]
    assert exclusion["source_actor_rightmost_pixel"] < 950
    assert exclusion["clearance_pixels"] >= 8


def test_v60_guide_left_deliveries_are_hash_locked_and_silent() -> None:
    manifest_path = (
        PROJECT_ROOT
        / "media"
        / "manifests"
        / "ABU_V60_05_GUIDE_LEFT_ONCE_V1.v1.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for delivery in manifest["deliveries"].values():
        path = PROJECT_ROOT / delivery["path"]
        assert path.is_file()
        assert sha256_file(path) == delivery["sha256"]

    webm = PROJECT_ROOT / manifest["deliveries"]["webm"]["path"]
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(webm),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert probe.stdout.strip() == ""
