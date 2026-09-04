from __future__ import annotations

import json

from abu_v60.media import (
    PROJECT_ROOT,
    load_verified_media_catalog,
    media_library_summary,
    runtime_media_manifest,
)


def test_home_shell_bundle_is_frozen_to_design_canonical() -> None:
    path = PROJECT_ROOT / "media/manifests/V108_HOME_SHELL_BASELINE_V1.v1.json"
    bundle = json.loads(path.read_text(encoding="utf-8"))

    assert bundle["frozen_design_commit"] == "a6cf762684e14514f58c8f45b82cca86d9a7ec4c"
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


def test_mingli_experience_bundles_are_bounded_to_current_product() -> None:
    branch = json.loads(
        (PROJECT_ROOT / "media/manifests/V128_MINGLI_BRANCH_GROWTH_BASELINE_V1.v1.json")
        .read_text(encoding="utf-8")
    )
    lab = json.loads(
        (PROJECT_ROOT / "media/manifests/V131_MINGLI_RESEARCH_LAB_BASELINE_V1.v1.json")
        .read_text(encoding="utf-8")
    )

    assert branch["boundaries"] == {
        "experience_canonical_only": True,
        "imports_mock_data": False,
        "imports_prototype_state": False,
        "runtime_data_authority": "V60_CANONICAL",
        "product_scope": "MINGLI_ONLY",
    }
    assert lab["boundaries"] == {
        "experience_canonical_only": True,
        "imports_mock_data": False,
        "imports_prototype_state": False,
        "runtime_data_authority": "V60_CANONICAL",
        "product_scope": "MINGLI_INTERNAL_LAB_ONLY",
    }


def test_media_library_is_hash_locked_to_the_reduced_runtime() -> None:
    catalog = load_verified_media_catalog()

    assert media_library_summary() == {
        "schema_version": "v60.media-library.001",
        "schema_ref": "media/schemas/media-catalog-v1.schema.json",
        "item_count": 13,
        "character_identity_count": 2,
        "primary_character_version": "ABU_CHARACTER_V60_V1",
        "runtime_registered_count": 11,
        "source_count": 13,
        "cue_bundle_count": 2,
        "audio_gap_cues": [],
        "owner_review_items": [],
    }
    assert {item["media_ref"] for item in catalog["items"]} == {
        "media.abu.v60.character-reference.v1",
        "media.abu.v60.seated-transparent.v1",
        "media.v60.life-world.reference.v1",
        "media.v60.login-life-tree-background.v1",
        "media.brand.abuknows-v60.primary-logo.v1",
        "media.abu.v60.seated-idle.v1",
        "media.dodo.v108.idle-transparent.v1",
        "media.experience.v108.home.day-background.v1",
        "media.experience.v108.home.night-background.v1",
        "media.experience.v108.home.day-logo.v1",
        "media.experience.v108.home.night-logo.v1",
        "media.experience.v108.home.profile-leaf.v1",
        "media.experience.v108.home.lab-flower.v1",
    }

    for item in catalog["items"]:
        assert item["source"]["path"].startswith("media/sources/")
        assert "/v1/source." in item["source"]["path"]
        assert not item["source"]["path"].startswith("v50/")
        assert item["source"]["authorization"].startswith("OWNER_APPROVED")


def test_current_character_identities_and_mingli_cues_are_the_only_registered_ones() -> None:
    catalog = load_verified_media_catalog()
    identities = {
        identity["character_version"]: identity
        for identity in catalog["character_identities"]
    }
    cues = {cue["cue_ref"]: cue for cue in catalog["cue_bundles"]}

    assert set(identities) == {"ABU_CHARACTER_V60_V1", "DODO_CHARACTER_V108_V1"}
    assert identities["ABU_CHARACTER_V60_V1"]["status"] == "PRIMARY_V60"
    assert identities["ABU_CHARACTER_V60_V1"]["motion_media_refs"] == [
        "media.abu.v60.seated-idle.v1"
    ]
    assert set(cues) == {"cue.mingli.abu-idle.v1", "cue.mingli.dodo-idle.v1"}
    assert all(cue["status"] == "RUNTIME_REGISTERED" for cue in cues.values())


def test_runtime_media_manifest_resolves_current_assets_and_cues() -> None:
    manifest = runtime_media_manifest()

    assert manifest["registry_version"] == "v60.runtime-media-registry.009"
    assert manifest["assets"]["brand_logo"]["asset_ref"] == (
        "brand.abuknows-v60.logo.transparent.v1"
    )
    assert manifest["assets"]["login_life_tree_background"]["url"] == (
        "/assets/brand/v60-life-tree-login-background-v1.png"
    )
    assert manifest["assets"]["home_day_background"]["sha256"] == (
        "4b9d3edc39c3a56b2acc2b7aff1faec122a26cbdf1b7cf2b5a66dafecd93b6b3"
    )
    assert manifest["assets"]["mingli_growth_day_video"]["url"] == (
        "/assets/v128/mingli-branch/mingli-branch-growth-day-v7.mp4"
    )
    assert manifest["cues"]["abu_idle"]["cue_ref"] == "cue.mingli.abu-idle.v1"
    assert manifest["cues"]["abu_idle"]["playback"] == "LOOP"
    assert manifest["cues"]["dodo_idle"]["cue_ref"] == "cue.mingli.dodo-idle.v1"
    assert (
        manifest["cues"]["dodo_idle"]["deliveries"]["VP9_ALPHA_WEBM"]["sha256"]
        == "b5f582af6a022fd3faebb202b6bcbf4efcb65474294b19898dcb26b14ddd3ea8"
    )
