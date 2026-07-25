from __future__ import annotations

import json
import struct
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
G1 = ROOT / "reports" / "abu-says-mingli-s0" / "g1"
G2 = ROOT / "reports" / "abu-says-mingli-s0" / "g2"
PROOFS = ROOT / "archive" / "proofs" / "prototypes"
SHARED = PROOFS / "s0-shared"
THEATER = PROOFS / "abu-says-mingli-s0"
XIANGFA = PROOFS / "xiangfa-s0-a"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _png_size(path: Path) -> tuple[int, int]:
    payload = path.read_bytes()
    assert payload[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", payload[16:24])


def test_visible_prototypes_consume_the_locked_g1_scene_source() -> None:
    assert _load(SHARED / "manifest.json") == _load(
        G1 / "s0_source_manifest_final_v1.json"
    )
    assert _load(SHARED / "scene-source.json") == _load(
        G1 / "s0_candidate_a_approved_teaching_projection_v1.json"
    )
    assert _load(SHARED / "narration.json") == _load(G1 / "s0_locked_copy_v1.json")

    theater_script = (THEATER / "app.js").read_text(encoding="utf-8")
    xiangfa_script = (XIANGFA / "app.js").read_text(encoding="utf-8")
    assert 'from "../s0-shared/scene-runtime.js"' in theater_script
    assert 'from "../s0-shared/scene-runtime.js"' in xiangfa_script


def test_scene_runtime_allows_only_the_four_approved_relations() -> None:
    runtime = (SHARED / "scene-runtime.js").read_text(encoding="utf-8")
    source = _load(SHARED / "scene-source.json")
    approved = {
        *source["approved_natal_path"]["relation_refs"],
        *(
            relation
            for stage in source["approved_temporal_stages"]
            for relation in stage["approved_relation_refs"]
        ),
    }

    assert approved == {
        "relation-yi-generates-ding",
        "relation-ding-acts-on-metal",
        "relation-luck-geng-controls-yi",
        "relation-year-bing-supports-ding",
    }
    for relation_ref in approved:
        assert relation_ref in runtime
    assert "relation-luck-zi" not in runtime
    assert "relation-year-wu" not in runtime


def test_theater_delivery_has_exact_audio_length_and_seven_hd_keyframes() -> None:
    audio = SHARED / "assets" / "s0-eric-temp-v1.wav"
    with wave.open(str(audio), "rb") as wav:
        duration = wav.getnframes() / wav.getframerate()
    assert 46.95 <= duration <= 47.05

    keyframes = sorted((G2 / "keyframes").glob("s0-keyframe-??.png"))
    assert len(keyframes) == 7
    assert {_png_size(path) for path in keyframes} == {(1920, 1080)}

    video = G2 / "video" / "abu-says-mingli-s0-v1.mp4"
    silent_video = G2 / "video" / "abu-says-mingli-s0-v1-silent.mp4"
    portrait = G2 / "screenshots" / "s0-portrait-preview-1080x1920.png"
    assert video.stat().st_size > 1_000_000
    assert silent_video.stat().st_size > 1_000_000
    assert _png_size(portrait) == (1080, 1920)


def test_xiangfa_is_one_layered_scene_with_three_modes_and_three_stages() -> None:
    html = (XIANGFA / "index.html").read_text(encoding="utf-8")
    css = (XIANGFA / "styles.css").read_text(encoding="utf-8")
    script = (XIANGFA / "app.js").read_text(encoding="utf-8")

    assert html.count("xiangfa-scene-base-v1.png") == 0
    assert css.count("xiangfa-scene-base-v1.png") == 1
    for mode in ("xiangfa", "skeleton", "overlay"):
        assert f'data-mode-value="{mode}"' in html
    for stage in ("original", "luck", "year"):
        assert f'data-stage-value="{stage}"' in html
    assert "relation-luck-geng-controls-yi" in script
    assert "relation-year-bing-supports-ding" in script
    assert _load(SHARED / "scene-source.json")["formal_state_write"] is False
