from __future__ import annotations

import json

from abu_v60.media import PROJECT_ROOT
from abu_v60.media.registry import sha256_file


def test_v60_idle_uses_owner_approved_segment_without_audio_or_crossfade() -> None:
    manifest_path = PROJECT_ROOT / "media" / "manifests" / "ABU_V60_SEATED_IDLE_LOOP_V1.v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["character_version"] == "ABU_CHARACTER_V60_V1"
    assert manifest["owner_decision"]["status"] == "OWNER_APPROVED_FOR_SEGMENTED_IDLE_POSTPROCESS"
    assert manifest["source"]["audio"] == "AAC_48KHZ_STEREO_REMOVED"
    assert manifest["selection"]["source_phase_match_frame"] == 54
    assert manifest["selection"]["crossfade_frames"] == 0
    assert manifest["motion_contract"]["mouth_open_frames"] == 0
    assert manifest["loop_validation"]["first_last_rgba_mae"] == 0
    assert manifest["loop_validation"]["first_last_png_identical"] is True
    assert manifest["anchor"]["observed_range"] == [704, 704]

    for delivery in manifest["deliveries"].values():
        path = PROJECT_ROOT / delivery["path"]
        assert path.is_file()
        assert sha256_file(path) == delivery["sha256"]
