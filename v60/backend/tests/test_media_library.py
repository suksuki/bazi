from __future__ import annotations

import json

from abu_v60.media import (
    PROJECT_ROOT,
    load_verified_media_catalog,
    media_library_summary,
    runtime_media_manifest,
)


def test_v108_home_shell_bundle_is_frozen_to_design_canonical() -> None:
    path = PROJECT_ROOT / "media/manifests/V108_HOME_SHELL_BASELINE_V1.v1.json"
    bundle = json.loads(path.read_text(encoding="utf-8"))

    assert bundle["frozen_design_commit"] == (
        "a6cf762684e14514f58c8f45b82cca86d9a7ec4c"
    )
    assert {asset["asset_id"] for asset in bundle["assets"]} == {
        "V108_HOME_DAY_BACKGROUND_V1",
        "V108_HOME_NIGHT_BACKGROUND_V1",
        "V108_HOME_DAY_LOGO_V1",
        "V108_HOME_NIGHT_LOGO_V1",
        "V108_HOME_PROFILE_LEAF_V1",
        "V108_HOME_LAB_FLOWER_V1",
    }
    assert all(asset["sha256"] for asset in bundle["assets"])
    assert bundle["boundaries"]["runtime_data_authority"] == "V60_CANONICAL"


def test_media_library_sources_deliveries_and_cues_are_hash_locked() -> None:
    catalog = load_verified_media_catalog()
    summary = media_library_summary()

    assert summary == {
        "schema_version": "v60.media-library.001",
        "schema_ref": "media/schemas/media-catalog-v1.schema.json",
        "item_count": 18,
        "character_identity_count": 3,
        "primary_character_version": "ABU_CHARACTER_V60_V1",
        "runtime_registered_count": 15,
        "source_count": 18,
        "cue_bundle_count": 6,
        "audio_gap_cues": ["cue.dream.follow-walk.v1"],
        "owner_review_items": ["media.dream.entry-transition.v1"],
    }
    assert {item["media_ref"] for item in catalog["items"]} == {
        "media.abu.seated-idle.v1",
        "media.abu.calm-follow-walk.v1",
        "media.dream.entry-transition.v1",
        "media.audio.morning-glints.v1",
        "media.abu.v60.character-reference.v1",
        "media.abu.v60.seated-transparent.v1",
        "media.abu.v60.seated-idle.v1",
        "media.abu.v60.guide-left.v1",
        "media.v60.life-world.reference.v1",
        "media.v60.life-world.clean.v1",
        "media.brand.abuknows-v60.primary-logo.v1",
        "media.dodo.v108.idle-transparent.v1",
        "media.experience.v108.home.day-background.v1",
        "media.experience.v108.home.night-background.v1",
        "media.experience.v108.home.day-logo.v1",
        "media.experience.v108.home.night-logo.v1",
        "media.experience.v108.home.profile-leaf.v1",
        "media.experience.v108.home.lab-flower.v1",
    }


def test_media_sources_are_local_immutable_revisions() -> None:
    catalog = load_verified_media_catalog()

    for item in catalog["items"]:
        assert item["source"]["path"].startswith("media/sources/")
        assert "/v1/source." in item["source"]["path"]
        assert not item["source"]["path"].startswith("v50/")
        assert item["source"]["authorization"].startswith("OWNER_APPROVED")


def test_unapproved_transition_is_not_runtime_published() -> None:
    catalog = load_verified_media_catalog()
    transition = next(
        item for item in catalog["items"] if item["media_ref"] == "media.dream.entry-transition.v1"
    )

    assert transition["library_status"] == "OWNER_REVIEW"
    assert transition["deliveries"] == []
    assert (
        transition["runtime_contract"]["runtime_publication"] == "BLOCKED_PENDING_V60_OWNER_REVIEW"
    )


def test_audio_visual_pairing_is_explicit_and_honest_about_gaps() -> None:
    catalog = load_verified_media_catalog()
    cues = {cue["cue_ref"]: cue for cue in catalog["cue_bundles"]}

    arrival = cues["cue.dream.grove-arrival.v1"]
    assert arrival["visual_media_ref"] == "media.abu.v60.seated-idle.v1"
    assert arrival["audio_media_refs"] == ["media.audio.morning-glints.v1"]

    walk = cues["cue.dream.follow-walk.v1"]
    assert walk["audio_media_refs"] == []
    assert walk["status"] == "AUDIO_GAP"
    assert "audio_gap" in walk
    assert cues["cue.dream.abu-idle.v1"]["status"] == "RUNTIME_REGISTERED"
    assert cues["cue.dream.abu-guide-left.v1"]["status"] == "RUNTIME_REGISTERED"
    assert cues["cue.mingli.dodo-idle.v1"]["status"] == "RUNTIME_REGISTERED"


def test_v60_character_identity_is_primary_and_legacy_cartoon_is_retained() -> None:
    catalog = load_verified_media_catalog()
    identities = {
        identity["character_version"]: identity for identity in catalog["character_identities"]
    }

    assert identities["ABU_CHARACTER_V60_V1"]["status"] == "PRIMARY_V60"
    assert identities["ABU_CHARACTER_V60_V1"]["primary_for_new_v60_generation"]
    assert identities["ABU_CHARACTER_V60_V1"]["motion_media_refs"] == [
        "media.abu.v60.guide-left.v1",
        "media.abu.v60.seated-idle.v1"
    ]
    assert identities["ABU_CHARACTER_V1"]["status"] == "RETAINED_COMPATIBILITY"
    assert not identities["ABU_CHARACTER_V1"]["primary_for_new_v60_generation"]
    assert identities["DODO_CHARACTER_V108_V1"]["status"] == (
        "FROZEN_V108_BASELINE_COMPATIBILITY"
    )
    assert not identities["DODO_CHARACTER_V108_V1"][
        "primary_for_new_v60_generation"
    ]


def test_runtime_media_manifest_resolves_hash_locked_assets_and_cues() -> None:
    manifest = runtime_media_manifest()

    assert manifest["registry_version"] == "v60.runtime-media-registry.004"
    assert manifest["assets"]["brand_logo"]["asset_ref"] == (
        "brand.abuknows-v60.logo.transparent.v1"
    )
    assert manifest["assets"]["life_world_background"]["url"] == (
        "/assets/dream/v60-life-world-clean-v1.png"
    )
    assert manifest["assets"]["home_day_background"]["sha256"] == (
        "4b9d3edc39c3a56b2acc2b7aff1faec122a26cbdf1b7cf2b5a66dafecd93b6b3"
    )
    assert manifest["assets"]["home_profile_leaf"]["url"] == (
        "/assets/v108/life-leaf-v1.webp"
    )
    assert manifest["assets"]["mingli_growth_day_video"]["sha256"] == (
        "d056fa04688e93180e0e428b2ab1049a4e70fe993632fe10f256849f25f1f2f6"
    )
    assert manifest["assets"]["mingli_growth_night_poster"]["url"] == (
        "/assets/v108/mingli-branch/mingli-branch-growth-night-v3-poster.webp"
    )
    assert manifest["cues"]["abu_idle"]["cue_ref"] == "cue.dream.abu-idle.v1"
    assert manifest["cues"]["abu_idle"]["playback"] == "LOOP"
    assert manifest["cues"]["abu_guide_left"]["playback"] == "PLAY_ONCE"
    assert manifest["cues"]["dodo_idle"]["cue_ref"] == "cue.mingli.dodo-idle.v1"
    assert manifest["cues"]["dodo_idle"]["deliveries"]["VP9_ALPHA_WEBM"][
        "sha256"
    ] == "b5f582af6a022fd3faebb202b6bcbf4efcb65474294b19898dcb26b14ddd3ea8"
    assert manifest["cues"]["abu_guide_left"]["deliveries"][
        "VP9_ALPHA_WEBM"
    ]["sha256"] == (
        "3452a67fef266dc3509d7d6db74fa9224349535e06ba29a3888419855a38aa67"
    )
