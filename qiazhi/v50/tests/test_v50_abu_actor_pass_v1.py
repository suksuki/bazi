from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "apps/product/static/l5/assets/abu/v12-actor-pass"
EXPERIENCE_ROOT = ROOT / "apps/product/static/experience"
GALLERY = EXPERIENCE_ROOT / "internal-tools/abu-motion-gallery-v1"
THEATER = EXPERIENCE_ROOT / "internal-tools/abu-says-mingli-s0-v12"
SHARED = EXPERIENCE_ROOT / "shared/s0-v12-shared"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_actor_library_exposes_reusable_actions_without_mingli_authority() -> None:
    library = _json(ASSET_ROOT / "library.json")
    actions = {item["action_id"]: item for item in library["actions"]}

    assert set(actions) == {
        "abu_enter_and_notice_v1",
        "abu_turn_and_point_v1",
        "abu_stand_point_up_left_v1",
        "abu_stand_point_up_right_v1",
        "abu_notice_tension_v1",
        "abu_quiet_sit_reaction_v1",
        "abu_baseball_swing_v1",
        "abu_pachinko_jackpot_v1",
        "abu_ninja_disappear_throw_v1",
        "abu_face_change_transition_v1",
    }
    assert library["calibration"]["anchor"] == "bottom_center"
    assert library["calibration"]["stage_render_fps"] == 24
    assert library["governance"] == {
        "authoritative_index": "library.json",
        "source_inventory": "video-inventory.json",
        "runtime_registry": "../motion-registry.js",
        "product_reference_policy": "action_id_preferred",
        "lifecycle_states": ["candidate", "production", "retired"],
        "retired_assets_remain_traceable": True,
    }
    assert library["boundaries"] == {
        "creates_mingli_claim": False,
        "changes_scene_source": False,
        "changes_life_case": False,
        "used_by_s0_v12_only": False,
    }
    assert actions["abu_face_change_transition_v1"]["gaze_target"] == "semantic_world"
    assert actions["abu_stand_point_up_left_v1"]["safe_crop"] == "source_half_body"
    assert actions["abu_stand_point_up_right_v1"]["mirrored_from"] == "abu_stand_point_up_left_v1"
    assert actions["abu_ninja_disappear_throw_v1"]["gaze_target"] == "audience"
    assert actions["abu_ninja_disappear_throw_v1"]["safe_crop"] == "full_body_wide_action"
    assert all(
        actions[action_id]["gaze_target"] == "semantic_object"
        for action_id in {
            "abu_enter_and_notice_v1",
            "abu_turn_and_point_v1",
            "abu_stand_point_up_left_v1",
            "abu_stand_point_up_right_v1",
            "abu_notice_tension_v1",
        }
    )
    assert actions["abu_quiet_sit_reaction_v1"]["loop_mode"] == "loop"
    assert all(
        action["loop_mode"] == "one_shot"
        for action_id, action in actions.items()
        if action_id != "abu_quiet_sit_reaction_v1"
    )
    assert all(action["status"] == "production" for action in actions.values())
    assert all(action["label_zh"] for action in actions.values())
    assert all(action["description_zh"] for action in actions.values())
    assert all(action["product_role"] for action in actions.values())
    assert all(action["do_not_use_for"] for action in actions.values())
    assert actions["abu_face_change_transition_v1"]["product_role"] == "onecanvas_to_xiangfa_transition"
    assert actions["abu_ninja_disappear_throw_v1"]["product_role"] == "finale_playful_interlude"
    assert actions["abu_quiet_sit_reaction_v1"]["product_role"] == "default_companion_presence"
    assert actions["abu_baseball_swing_v1"]["product_role"] == "ambient_active_interlude"
    assert actions["abu_pachinko_jackpot_v1"]["product_role"] == "rare_finale_arcade_easter_egg"
    assert "财富或财运判断" in actions["abu_pachinko_jackpot_v1"]["do_not_use_for"]


def test_each_actor_action_has_transparent_web_deliveries_and_traceable_source() -> None:
    library = _json(ASSET_ROOT / "library.json")
    inventory = _json(ASSET_ROOT / "video-inventory.json")
    inventory_hashes = {item["sha256"] for item in inventory["sources"]}

    for action in library["actions"]:
        manifest = _json(ASSET_ROOT / action["manifest"])
        assert manifest["status"] == "production"
        assert manifest["action_id"] == action["action_id"]
        assert manifest["transparent_background"] is True
        assert manifest["watermark_removed"] is True
        assert manifest["source"]["sha256"] in inventory_hashes
        expected_safe_crop = action.get("safe_crop", "full_body")
        assert manifest["actor_contract"]["safe_crop"] == expected_safe_crop
        assert manifest["actor_contract"]["background"] == "transparent"
        assert manifest["boundaries"]["creates_mingli_claim"] is False

        webp = ASSET_ROOT / action["animation"]
        webm = ASSET_ROOT / action["video"]
        poster = ASSET_ROOT / action["poster"]
        contact_sheet = ASSET_ROOT / action["contact_sheet"]
        assert webp.stat().st_size > 250_000
        assert webm.stat().st_size > 250_000
        assert poster.stat().st_size > 20_000
        assert contact_sheet.stat().st_size > 50_000
        assert webm.read_bytes()[:4] == b"\x1aE\xdf\xa3"
        assert Image.open(webp).n_frames == manifest["frame_count"]
        assert Image.open(poster).convert("RGBA").getchannel("A").getbbox() is not None


def test_motion_gallery_consumes_the_library_and_compares_all_actions() -> None:
    html = (GALLERY / "index.html").read_text(encoding="utf-8")
    script = (GALLERY / "app.js").read_text(encoding="utf-8")
    styles = (GALLERY / "styles.css").read_text(encoding="utf-8")

    assert "Abu Motion Library" in html
    assert 'const ROOT = "/assets/abu/v12-actor-pass/"' in script
    assert "library.json" in script
    assert "valley" in html and "ivory" in html and "checker" in html
    assert "display_scale" in script
    assert "action.label_zh" in script
    assert "action.description_zh" in script
    assert "action.product_role" in script
    assert 'class="motion-label"' in html
    assert 'class="description"' in html
    assert "object-fit: contain" in styles


def test_runtime_registry_places_new_actions_without_reading_outcome_semantics() -> None:
    registry = (ASSET_ROOT.parent / "motion-registry.js").read_text(encoding="utf-8")
    components = (ROOT / "apps/product/experience_shell/src/components.ts").read_text(encoding="utf-8")
    account_components = (ROOT / "apps/product/experience_shell/src/account_components.ts").read_text(encoding="utf-8")

    assert 'idle: "quiet_sit_reaction"' in registry
    assert 'baseball: "baseball_swing"' in registry
    assert 'arcade_easter_egg: "pachinko_jackpot"' in registry
    assert 'category: "ambient_restricted"' in registry
    assert '"wealth_or_fortune_reading"' in registry
    assert 'label: "挥一棒活动一下", weight: 2' in registry
    assert 'label: "偶尔玩一局弹子机", weight: 1' in registry
    quiet_asset = "/assets/abu/v12-actor-pass/quiet-sit-reaction/web/abu_quiet_sit_reaction_v1.webp"
    assert quiet_asset in components
    assert quiet_asset in account_components


def test_ninja_source_variants_are_traceable_but_only_full_body_seated_is_active() -> None:
    inventory = _json(ASSET_ROOT / "video-inventory.json")
    sources = {item["source_id"]: item for item in inventory["sources"]}
    review = _json(
        ROOT
        / "artifacts/abu-actor-pass-v1/source-contact-sheets/ninja/variant-review.json"
    )

    assert sources["ninja_sitting_full_body_start"]["quality"] == "selected_full_body_seated"
    assert sources["ninja_sitting_full_body_start"]["selected_ranges"] == [
        {"seconds": [0.0, 10.0], "action_id": "abu_ninja_disappear_throw_v1"}
    ]
    assert sources["ninja_standing_full_body_start"]["quality"] == "candidate_pose_hold"
    assert sources["ninja_half_body_start"]["quality"] == "candidate_framing_hold"
    assert review["selected_variant"] == "sitting_full_body"
    assert {item["status"] for item in review["variants"]} == {
        "selected_for_production",
        "candidate_pose_hold",
        "candidate_framing_hold",
    }
    for filename in (
        "abu_ninja_sitting_start_source.mp4",
        "abu_ninja_standing_start_source.mp4",
        "abu_ninja_half_body_start_source.mp4",
    ):
        assert (ROOT / "artifacts/abu-actor-pass-v1/source-videos" / filename).stat().st_size > 1_000_000


def test_new_standard_baseball_and_pachinko_sources_are_registered_and_archived() -> None:
    inventory = _json(ASSET_ROOT / "video-inventory.json")
    sources = {item["source_id"]: item for item in inventory["sources"]}

    assert sources["quiet_sit_reaction_cute_standard"]["quality"] == "selected_standard_character_motion"
    assert sources["baseball_swing"]["selected_ranges"] == [
        {"seconds": [0.067, 10.0], "action_id": "abu_baseball_swing_v1"}
    ]
    assert "first_mismatched_closeup_frame" in sources["baseball_swing"]["removed_regions"]
    assert sources["pachinko_jackpot"]["quality"] == "selected_restricted_context"
    assert "fortune" in " ".join(sources["pachinko_jackpot"]["notes"])

    for filename in (
        "abu_quiet_sit_reaction_source.mp4",
        "abu_baseball_swing_source.mp4",
        "abu_pachinko_jackpot_source.mp4",
    ):
        assert (ROOT / "artifacts/abu-actor-pass-v1/source-videos" / filename).stat().st_size > 1_000_000


def test_s0_v12_changes_only_actor_performance_and_keeps_scene_source_locked() -> None:
    html = (THEATER / "index.html").read_text(encoding="utf-8")
    script = (THEATER / "app.js").read_text(encoding="utf-8")
    styles = (THEATER / "styles.css").read_text(encoding="utf-8")
    renderer = (ROOT / "tools/render_s0_v12.mjs").read_text(encoding="utf-8")
    shared_manifest = _json(SHARED / "manifest.json")
    shared_source = _json(SHARED / "scene-source.json")

    assert "s0-v12-shared/scene-runtime.js" in script
    assert "s0-v11-eric-mix.wav" in html
    assert "abu_enter_and_notice_v1" in script
    assert "abu_turn_and_point_v1" in script
    assert "abu_notice_tension_v1" in script
    assert "abu_face_change_transition_v1" in script
    assert "abu_ninja_disappear_throw_v1" in script
    assert "abu_quiet_sit_reaction_v1" in script
    assert "abu_baseball_swing_v1" in script
    assert "abu_pachinko_jackpot_v1" in script
    assert 'const FINALE_ACTIONS = ["breakdance", "faceChange", "ninja", "baseball", "pachinko"]' in script
    assert "FINALE_ACTION_WEIGHTS" in script
    assert "pickRandomFinaleAction" in script
    assert "FINALE_SLEEP_AFTER_MS = 28000" in script
    assert 'get("finaleAction")' in script
    assert 'showFinaleActor("sleep")' in script
    assert "scheduleRandomFinaleAction" in script
    assert "registerFinaleActivity" in script
    assert '"pointermove", "mousemove", "pointerover", "wheel"' in script
    assert 'get("finaleSleepAfterMs")' in script
    assert 'xiangfaFrame.addEventListener("pointerenter", registerFinalePointerActivity' in script
    assert 'event.data?.type === "deepbazi:xiangfa-activity"' in script
    assert 'data-finale-action="ninja"' in styles
    assert 'data-finale-action="baseball"' in styles
    assert 'data-finale-action="pachinko"' in styles
    assert 'actor: "faceChange"' in script
    assert script.count("travel: {duration: 1.65") == 4
    assert 'travel: {duration: 2.85, moveRatio: .66, settleFacing: "front", settleAt: .72}' in script
    assert 'const effectiveActor = isTravelling ? "enter" : scene.actor' in script
    assert 'abuActor.dataset.locomotion = String(isTravelling)' in script
    assert "travelProgress / (scene.travel?.moveRatio || 1)" in script
    assert "hasSettledFacing ? scene.travel.settleFacing : travelFacing" in script
    assert 'void abuVideo.play().catch(() => {})' in script
    assert script.count('image: "/assets/abu/v12-actor-pass/') == 8
    assert 'get("actorMedia") === "webp"' in script
    assert "/iPad|iPhone|iPod/.test(navigator.userAgent)" in script
    assert 'navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1' in script
    assert "function actionUsesVideo(action)" in script
    assert 'USE_ALPHA_IMAGE_FALLBACK ? "animated-webp" : "image"' in script
    assert "if (actionUsesVideo(action))" in script
    assert "background: transparent" in styles
    assert "app.js?v=20260722-actor-v14" in html
    assert 'playbackScale: .82' in script
    assert 'position: {wide: 12, compact: 18}, travel: {duration: 1.65, from: {wide: 6, compact: 13}}' in script
    assert 'position: {wide: 1, compact: 0}, travel: {duration: 1.65}' in script
    assert 'id: "morph", start: 38.5, end: 43.5' in script
    assert "transition: left" not in styles
    assert "z-index: 28" in styles
    assert "transition: transform .7s ease" not in styles
    assert "rgba(226,233,224,.76)" in styles
    assert "backdrop-filter: blur(8px) saturate(.72) brightness(1.04)" in styles
    assert 'id="xiangfaHandoff"' in html
    assert 'id="xiangfaFrame"' in html
    assert "embed=theater&stage=year&mode=xiangfa" in html
    assert "deepbazi:xiangfa-state" in script
    assert "deepbazi:xiangfa-engaged" in script
    assert '.theater[data-scene="finale"] .xiangfa-handoff' in styles
    assert "subtitle.textContent = narration.narration" in script
    assert 'id="subtitleText"' in html
    assert '.theater[data-scene="finale"] .subtitle { opacity: 0; }' not in styles
    assert "abu_taoist_divination" not in html + script
    assert "S0_FPS || 24" in renderer
    assert shared_manifest["source_mode"] == shared_source["source_mode"]
    assert shared_manifest["allowed_path_ref"] == shared_source["observed_natal_path"]["path_ref"]
    assert shared_source["observed_natal_path"]["path_ref"] == "path-observed-jia-ding-geng"


def test_s0_mobile_theater_can_start_with_or_without_sound_and_keeps_controls_visible() -> None:
    html = (THEATER / "index.html").read_text(encoding="utf-8")
    script = (THEATER / "app.js").read_text(encoding="utf-8")
    styles = (THEATER / "styles.css").read_text(encoding="utf-8")
    renderer = (ROOT / "tools/render_s0_v12.mjs").read_text(encoding="utf-8")

    assert 'id="theaterEntry"' in html
    assert 'id="startSoundButton"' in html
    assert 'id="startMutedButton"' in html
    assert 'id="soundLabel"' in html
    assert 'id="mobileChart"' in html
    assert 'id="mobileNatalPillars"' in html
    assert 'id="mobileTemporalPillars"' in html
    assert 'class="mobile-path"' in html
    assert 'class="pillar-group natal-group"' in script
    assert 'class="pillar-group temporal-group"' in script
    assert "function renderMobilePillar" in script
    assert "有声播放" in html
    assert "静音观看" in html

    assert "function timelinePlaying()" in script
    assert "function timelineTime()" in script
    assert "fallbackPlaying = true" in script
    assert 'playTimeline({sound: true})' in script
    assert 'playTimeline({sound: false})' in script
    assert "s0_audio_unavailable_using_visual_clock" in script
    assert 'playbackClock: fallbackPlaying ? "visual_fallback" : "audio"' in script
    assert 'theater.dataset.format = format' in script

    assert "height: 100dvh" in styles
    assert "env(safe-area-inset-bottom)" in styles
    assert ".transport .mute { display: flex; }" in styles
    assert ".transport .mute { display: none; }" not in styles
    assert '.theater:not([data-started="true"]) .transport' in styles
    assert '.theater[data-started="true"] .theater-entry' in styles
    assert '.theater[data-scene="luck"] .source-link path' in styles
    assert "@keyframes mobileArrowTravel" in styles
    assert '.theater[data-scene="year"] .mobile-path-node.fire' in styles
    assert '.theater.capture[data-format="portrait"] .canvas' in styles
    assert '.theater.capture[data-format="portrait"] .mobile-chart' in styles
    assert '.theater.capture[data-format="portrait"] .mobile-path' in styles
    assert '.theater.capture[data-format="portrait"] .subtitle' in styles
    assert 'grid-template-columns: repeat(4, minmax(0, 1fr))' in styles
    assert '.theater:not(.capture)[data-scene="finale"] .finale' in styles
    assert '.theater[data-scene="finale"] .subtitle { left: 142px' in styles
    assert '.theater.capture[data-format="portrait"][data-scene="finale"] .abu-actor { bottom: 116px' in styles

    assert 'portrait: {width: 1080, height: 1920' in renderer
    assert 'landscape: {width: 1920, height: 1080' in renderer
    assert "unknown_s0_profile" in renderer
