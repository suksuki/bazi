from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abu_v60.media.registry import PROJECT_ROOT, load_verified_assets, sha256_file

CATALOG_PATH = PROJECT_ROOT / "media" / "catalog.json"
CATALOG_SCHEMA_PATH = PROJECT_ROOT / "media" / "schemas" / "media-catalog-v1.schema.json"
CATALOG_SCHEMA_VERSION = "v60.media-library.001"
REQUIRED_POLICIES = {
    "sources_are_immutable",
    "new_revision_never_overwrites_old_revision",
    "runtime_registry_is_release_projection",
    "source_audio_is_never_embedded_in_actor_alpha_video",
    "owner_review_required_for_runtime_publication",
    "watermark_work_requires_owner_authorized_source",
}


class MediaCatalogError(ValueError):
    pass


def _verified_file(*, relative_path: str, expected_hash: str, label: str) -> Path:
    path = PROJECT_ROOT / relative_path
    if not path.is_file():
        raise MediaCatalogError(f"{label} is missing: {relative_path}")
    actual_hash = sha256_file(path)
    if actual_hash != expected_hash:
        raise MediaCatalogError(
            f"{label} hash mismatch for {relative_path}: "
            f"expected {expected_hash}, got {actual_hash}"
        )
    return path


def load_verified_media_catalog() -> dict[str, Any]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if catalog.get("schema_version") != CATALOG_SCHEMA_VERSION:
        raise MediaCatalogError("unsupported V60 media catalog schema")
    schema_ref = str(catalog.get("schema_ref", ""))
    if schema_ref != str(CATALOG_SCHEMA_PATH.relative_to(PROJECT_ROOT)):
        raise MediaCatalogError("media catalog does not reference the canonical schema")
    _verified_file(
        relative_path=schema_ref,
        expected_hash=sha256_file(CATALOG_SCHEMA_PATH),
        label="media catalog schema",
    )
    policy = catalog.get("policy", {})
    missing_policies = REQUIRED_POLICIES - set(policy)
    if missing_policies:
        raise MediaCatalogError(
            f"media catalog lacks required policies: {sorted(missing_policies)}"
        )
    disabled_policies = sorted(key for key in REQUIRED_POLICIES if policy[key] is not True)
    if disabled_policies:
        raise MediaCatalogError(f"media catalog disables required policies: {disabled_policies}")
    lifecycle = set(catalog["lifecycle"])
    runtime_assets = {
        (str(asset["asset_ref"]), str(asset["asset_version"])): asset
        for asset in load_verified_assets()
    }

    character_versions: set[str] = set()
    primary_character_versions: list[str] = []
    for identity in catalog["character_identities"]:
        character_version = str(identity["character_version"])
        if character_version in character_versions:
            raise MediaCatalogError(f"duplicate character identity: {character_version}")
        character_versions.add(character_version)
        if identity["primary_for_new_v60_generation"]:
            primary_character_versions.append(character_version)
    if len(primary_character_versions) != 1:
        raise MediaCatalogError("exactly one primary V60 character identity is required")

    media_by_ref: dict[str, dict[str, Any]] = {}
    revision_keys: set[tuple[str, str]] = set()
    for item in catalog["items"]:
        media_ref = str(item["media_ref"])
        revision_key = (str(item["asset_id"]), str(item["revision"]))
        if media_ref in media_by_ref:
            raise MediaCatalogError(f"duplicate media_ref: {media_ref}")
        if revision_key in revision_keys:
            raise MediaCatalogError(f"duplicate asset revision: {revision_key}")
        if item["library_status"] not in lifecycle:
            raise MediaCatalogError(
                f"unknown lifecycle state for {media_ref}: {item['library_status']}"
            )
        media_by_ref[media_ref] = item
        revision_keys.add(revision_key)
        character_version = item.get("character_version")
        if character_version is not None and character_version not in character_versions:
            raise MediaCatalogError(
                f"{media_ref} uses an unknown character identity: {character_version}"
            )

        source = item["source"]
        if not str(source["path"]).startswith(
            f"media/sources/{item['asset_id']}/{item['revision']}/"
        ):
            raise MediaCatalogError(f"{media_ref} source is outside its immutable revision")
        if not str(source["authorization"]).startswith("OWNER_APPROVED"):
            raise MediaCatalogError(f"{media_ref} lacks Owner source authorization")
        _verified_file(
            relative_path=str(source["path"]),
            expected_hash=str(source["sha256"]),
            label=f"{media_ref} source",
        )
        _verified_file(
            relative_path=str(item["process_manifest_path"]),
            expected_hash=str(item["process_manifest_sha256"]),
            label=f"{media_ref} process manifest",
        )

        for collection_name in ("masters", "review_artifacts"):
            for artifact in item.get(collection_name, []):
                _verified_file(
                    relative_path=str(artifact["path"]),
                    expected_hash=str(artifact["sha256"]),
                    label=f"{media_ref} {collection_name}",
                )

        deliveries = item.get("deliveries", [])
        if item["library_status"] == "RUNTIME_REGISTERED" and not deliveries:
            raise MediaCatalogError(f"{media_ref} has no runtime deliveries")
        for delivery in deliveries:
            _verified_file(
                relative_path=str(delivery["path"]),
                expected_hash=str(delivery["sha256"]),
                label=f"{media_ref} delivery",
            )
            runtime_key = (
                str(delivery["asset_ref"]),
                str(delivery["asset_version"]),
            )
            runtime_asset = runtime_assets.get(runtime_key)
            if runtime_asset is None:
                raise MediaCatalogError(
                    f"{media_ref} delivery is absent from runtime registry: {runtime_key}"
                )
            if (
                runtime_asset["runtime_path"] != delivery["path"]
                or runtime_asset["sha256"] != delivery["sha256"]
            ):
                raise MediaCatalogError(
                    f"{media_ref} delivery disagrees with runtime registry: {runtime_key}"
                )

    for identity in catalog["character_identities"]:
        media_refs = [
            identity.get("identity_reference_media_ref"),
            identity["runtime_poster_media_ref"],
            *identity["motion_media_refs"],
        ]
        for media_ref in media_refs:
            if media_ref is not None and str(media_ref) not in media_by_ref:
                raise MediaCatalogError(
                    f"{identity['character_version']} references unknown media: {media_ref}"
                )

    cue_refs: set[str] = set()
    for cue in catalog["cue_bundles"]:
        cue_ref = str(cue["cue_ref"])
        if cue_ref in cue_refs:
            raise MediaCatalogError(f"duplicate cue_ref: {cue_ref}")
        cue_refs.add(cue_ref)
        visual = media_by_ref.get(str(cue["visual_media_ref"]))
        if visual is None:
            raise MediaCatalogError(f"{cue_ref} has unknown visual media")
        if str(visual["media_kind"]).startswith("AUDIO_"):
            raise MediaCatalogError(f"{cue_ref} visual media is audio")
        if cue["status"] == "RUNTIME_REGISTERED" and (
            visual["library_status"] != "RUNTIME_REGISTERED"
        ):
            raise MediaCatalogError(f"{cue_ref} uses an unpublished visual asset")
        for audio_ref in cue.get("audio_media_refs", []):
            audio = media_by_ref.get(str(audio_ref))
            if audio is None:
                raise MediaCatalogError(f"{cue_ref} has unknown audio media: {audio_ref}")
            if not str(audio["media_kind"]).startswith("AUDIO_"):
                raise MediaCatalogError(f"{cue_ref} audio reference is not audio: {audio_ref}")
            if cue["status"] == "RUNTIME_REGISTERED" and (
                audio["library_status"] != "RUNTIME_REGISTERED"
            ):
                raise MediaCatalogError(f"{cue_ref} uses unpublished audio: {audio_ref}")

    return catalog


def media_library_summary() -> dict[str, Any]:
    catalog = load_verified_media_catalog()
    items = catalog["items"]
    cue_bundles = catalog["cue_bundles"]
    return {
        "schema_version": catalog["schema_version"],
        "schema_ref": catalog["schema_ref"],
        "item_count": len(items),
        "character_identity_count": len(catalog["character_identities"]),
        "primary_character_version": next(
            identity["character_version"]
            for identity in catalog["character_identities"]
            if identity["primary_for_new_v60_generation"]
        ),
        "runtime_registered_count": sum(
            item["library_status"] == "RUNTIME_REGISTERED" for item in items
        ),
        "source_count": len(items),
        "cue_bundle_count": len(cue_bundles),
        "audio_gap_cues": [cue["cue_ref"] for cue in cue_bundles if cue["status"] == "AUDIO_GAP"],
        "owner_review_items": [
            item["media_ref"] for item in items if item["library_status"] == "OWNER_REVIEW"
        ],
    }
