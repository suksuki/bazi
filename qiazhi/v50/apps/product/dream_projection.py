from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

from experience.canonical_scene import CanonicalScene
from experience.compiler import canonical_hash
from experience.dream import (
    DREAM_PROJECTION_VERSION,
    DreamEncounterProjection,
    DreamMirrorProjection,
    DreamSceneEligibilitySnapshot,
    DreamSceneGrant,
    DreamTreeCard,
    DreamTreeProjection,
    DreamVisit,
)


WORK_PATH_MESSAGE = "当前暂无已确认主路径"


class DreamProjectionError(ValueError):
    pass


class DreamProjectionCompiler:
    """Build disposable Dream views from role-filtered canonical sources."""

    def encounter(
        self,
        *,
        visit: DreamVisit,
        scenes: dict[str, tuple[DreamSceneGrant, CanonicalScene]],
    ) -> DreamEncounterProjection:
        cards = [
            self._tree_card(grant=grant, scene=scene)
            for scene_ref in visit.encounter_set.scene_refs
            for grant, scene in [scenes[scene_ref]]
        ]
        payload = {
            "projection_version": DREAM_PROJECTION_VERSION,
            "visit_id": visit.visit_id,
            "scene_versions": [item.source_version for item in cards],
            "tree_tokens": [item.model_dump(mode="json") for item in cards],
        }
        content_hash = canonical_hash(payload)
        return DreamEncounterProjection(
            projection_id=f"dream-encounter-{content_hash[:24]}",
            trees=cards,
            content_hash=content_hash,
        )

    def tree(
        self,
        *,
        grant: DreamSceneGrant,
        scene: CanonicalScene,
    ) -> DreamTreeProjection:
        card = self._tree_card(grant=grant, scene=scene)
        public_version = _public_source_version(grant=grant, scene=scene)
        visual_tokens = {
            "art_variant": card.art_variant,
            "primary_element": card.primary_element,
            "climate": card.climate_token,
            "relation_count": len(card.relation_tokens),
            "path_animation": "disabled",
            "semantic_owner": "CanonicalScene",
        }
        payload = {
            "source_ref": grant.public_scene_ref,
            "source_version": public_version,
            "source_kind": grant.subject_kind,
            "visual_tokens": visual_tokens,
            "relation_tokens": card.relation_tokens,
            "work_path_state": "unavailable_unconfirmed",
        }
        content_hash = canonical_hash(payload)
        return DreamTreeProjection(
            projection_id=f"dream-tree-{content_hash[:24]}",
            source_refs=[grant.public_scene_ref],
            source_versions={"canonical_scene": public_version},
            source_kind=grant.subject_kind,
            source_label_key=_source_label_key(grant),
            visual_tokens=visual_tokens,
            relation_tokens=card.relation_tokens,
            work_path_state="unavailable_unconfirmed",
            content_hash=content_hash,
        )

    def mirror(
        self,
        *,
        grant: DreamSceneGrant,
        scene: CanonicalScene,
        canvas: dict[str, Any],
    ) -> DreamMirrorProjection:
        public_version = _public_source_version(grant=grant, scene=scene)
        projected_canvas = _public_canvas(
            canvas=canvas,
            grant=grant,
            scene=scene,
            public_version=public_version,
        )
        content_hash = canonical_hash({
            "public_scene_ref": grant.public_scene_ref,
            "source_version": public_version,
            "source_kind": grant.subject_kind,
            "canvas": projected_canvas,
            "work_path_state": "unavailable_unconfirmed",
        })
        return DreamMirrorProjection(
            public_scene_ref=grant.public_scene_ref,
            source_version=public_version,
            source_kind=grant.subject_kind,
            source_label_key=_source_label_key(grant),
            work_path_state="unavailable_unconfirmed",
            canvas=projected_canvas,
            content_hash=content_hash,
        )

    def context(
        self,
        *,
        grant: DreamSceneGrant,
        scene: CanonicalScene,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        return _opaque_payload(
            context,
            public_scene_ref=grant.public_scene_ref,
            sensitive_values=_sensitive_values(grant=grant, scene=scene),
        )

    def resolve_canvas_ref(
        self,
        *,
        grant: DreamSceneGrant,
        canvas: dict[str, Any],
        public_ref: str,
    ) -> str:
        for candidate in _canvas_reference_values(canvas):
            if _opaque_ref(
                public_scene_ref=grant.public_scene_ref,
                value=candidate,
            ) == public_ref:
                return candidate
        raise DreamProjectionError("dream_canvas_object_not_disclosed")

    def _tree_card(
        self,
        *,
        grant: DreamSceneGrant,
        scene: CanonicalScene,
    ) -> DreamTreeCard:
        day = next(
            (item for item in scene.chart_facts if item.pillar_slot == "day"),
            None,
        )
        primary = str(day.stem_element if day else "") or "unknown"
        if primary not in {"wood", "fire", "earth", "metal", "water"}:
            primary = "unknown"
        variants = ("mist", "brook", "ridge")
        variant = variants[int(scene.identity.source_hash[:2], 16) % len(variants)]
        timing = scene.temporal_state
        climate = (
            "year_present"
            if timing.annual_pillar
            else "luck_present"
            if timing.luck_pillar
            else "quiet"
        )
        relation_tokens = [
            "relation_effective"
            for item in scene.relation_assertions
            if item.relation_state == "effective"
        ]
        return DreamTreeCard(
            scene_ref=grant.public_scene_ref,
            art_variant=variant,
            primary_element=primary,
            climate_token=climate,
            relation_tokens=relation_tokens,
            source_version=_public_source_version(grant=grant, scene=scene),
            source_kind=grant.subject_kind,
            source_label_key=_source_label_key(grant),
        )


def eligibility_snapshot(
    *,
    grant: DreamSceneGrant,
    scene: CanonicalScene,
) -> DreamSceneEligibilitySnapshot:
    return DreamSceneEligibilitySnapshot(
        grant_ref=grant.grant_id,
        public_scene_ref=grant.public_scene_ref,
        source_hash=scene.identity.source_hash,
        source_version=_public_source_version(grant=grant, scene=scene),
        authorization_version=grant.authorization_version,
        privacy_policy_version=grant.anonymization_policy_version,
        subject_kind=grant.subject_kind,
        subject_ref=grant.subject_ref,
    )


def _source_label_key(grant: DreamSceneGrant) -> str:
    return {
        "authorized_human": "dream.source.authorized_human",
        "canonical_npc": "dream.source.canonical_npc",
    }.get(grant.subject_kind, "dream.source.unclassified")


def _public_source_version(*, grant: DreamSceneGrant, scene: CanonicalScene) -> str:
    return hashlib.sha256(
        f"{grant.public_scene_ref}|{scene.identity.source_hash}|{DREAM_PROJECTION_VERSION}".encode()
    ).hexdigest()


def _public_canvas(
    *,
    canvas: dict[str, Any],
    grant: DreamSceneGrant,
    scene: CanonicalScene,
    public_version: str,
) -> dict[str, Any]:
    projected = deepcopy(canvas)
    projected["case_id"] = grant.public_scene_ref
    projected["role"] = "member"
    projected["path_availability"] = {
        "status": "unavailable",
        "message": WORK_PATH_MESSAGE,
        "committed_path_count": 0,
        "disclosure_level": "public",
        "professional_status": "not_confirmed",
    }
    projected["renderer_policy"]["available_visibility_layers"] = ["formal", "focus"]
    for stage in projected.get("stages", {}).values():
        spec = stage.get("spec") or {}
        removed_paths = {
            str(item.get("path_ref") or "")
            for item in spec.get("paths") or []
            if isinstance(item, dict)
        }
        spec["relations"] = [
            item
            for item in spec.get("relations") or []
            if isinstance(item, dict) and item.get("relation_state") != "potential"
        ]
        allowed_relations = {
            str(item.get("relation_ref") or "")
            for item in spec["relations"]
        }
        spec["paths"] = []
        for layer in stage.get("layers") or []:
            if not isinstance(layer, dict):
                continue
            for key in ("relation_refs", "formal_relation_refs"):
                layer[key] = [
                    value for value in layer.get(key) or [] if value in allowed_relations
                ]
            for key in ("path_refs", "formal_path_refs"):
                layer[key] = []
            layer["count"] = len(layer.get("formal_relation_refs") or [])
            layer["available"] = bool(layer["count"])
        context = stage.get("context") or {}
        for key in ("committed_path_refs", "candidate_path_refs", "blocked_path_refs"):
            context[key] = []
        context["disclosed_object_refs"] = [
            value
            for value in context.get("disclosed_object_refs") or []
            if value not in removed_paths
        ]
        stage["change_groups"] = [
            {
                **group,
                "items": [
                    item
                    for item in group.get("items") or []
                    if item.get("target_ref") not in removed_paths
                ],
                "count": len([
                    item
                    for item in group.get("items") or []
                    if item.get("target_ref") not in removed_paths
                ]),
            }
            for group in stage.get("change_groups") or []
            if isinstance(group, dict)
        ]
    envelope = projected.get("projection_envelope") or {}
    if isinstance(envelope.get("payload"), dict):
        envelope["payload"]["path_assertions"] = []
    disclosure = envelope.get("role_disclosure") or {}
    if isinstance(disclosure, dict):
        disclosure["visible_path_assertion_refs"] = []

    sensitive = _sensitive_values(grant=grant, scene=scene)
    result = _opaque_payload(
        projected,
        public_scene_ref=grant.public_scene_ref,
        sensitive_values=sensitive,
    )
    result["case_id"] = grant.public_scene_ref
    result["source"]["public_source_version"] = public_version
    serialized = json.dumps(result, ensure_ascii=False, sort_keys=True)
    leaked = [value for value in sensitive if value and value in serialized]
    if leaked:
        raise DreamProjectionError("dream_mirror_private_source_ref_leaked")
    if "potential" in serialized:
        raise DreamProjectionError("dream_member_projection_contains_potential_relation")
    return result


_REFERENCE_KEYS = {
    "case_id",
    "case_ref",
    "scene_id",
    "world_id",
    "life_case_id",
    "chart_version_id",
    "cognitive_record_id",
    "projection_id",
    "canvas_spec_id",
    "context_pack_id",
    "diff_spec_id",
}


def _opaque_payload(
    value: Any,
    *,
    public_scene_ref: str,
    sensitive_values: set[str],
    parent_key: str = "",
) -> Any:
    if isinstance(value, dict):
        return {
            key: _opaque_payload(
                item,
                public_scene_ref=public_scene_ref,
                sensitive_values=sensitive_values,
                parent_key=key,
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _opaque_payload(
                item,
                public_scene_ref=public_scene_ref,
                sensitive_values=sensitive_values,
                parent_key=parent_key,
            )
            for item in value
        ]
    if not isinstance(value, str) or not value:
        return value
    reference_field = (
        parent_key in _REFERENCE_KEYS
        or parent_key.endswith("_ref")
        or parent_key.endswith("_refs")
        or parent_key.endswith("_hash")
    )
    if reference_field:
        return _opaque_ref(public_scene_ref=public_scene_ref, value=value)
    result = value
    for sensitive in sorted(sensitive_values, key=len, reverse=True):
        if sensitive and sensitive in result:
            result = result.replace(
                sensitive,
                _opaque_ref(public_scene_ref=public_scene_ref, value=sensitive),
            )
    return result


def _opaque_ref(*, public_scene_ref: str, value: str) -> str:
    return "dream-ref-" + hashlib.sha256(
        f"{public_scene_ref}|{value}".encode()
    ).hexdigest()[:28]


def _sensitive_values(*, grant: DreamSceneGrant, scene: CanonicalScene) -> set[str]:
    identity = scene.identity
    return {
        grant.case_id,
        grant.grant_id,
        grant.authorized_by_ref,
        identity.case_ref,
        identity.scene_id,
        identity.chart_version_id,
        identity.world_id,
        identity.life_case_id,
        identity.source_hash,
    }


def _canvas_reference_values(value: Any, *, parent_key: str = "") -> set[str]:
    output: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            output.update(_canvas_reference_values(item, parent_key=key))
        return output
    if isinstance(value, list):
        for item in value:
            output.update(_canvas_reference_values(item, parent_key=parent_key))
        return output
    if isinstance(value, str) and value and (
        parent_key in _REFERENCE_KEYS
        or parent_key.endswith("_ref")
        or parent_key.endswith("_refs")
    ):
        output.add(value)
    return output


__all__ = [
    "DreamProjectionCompiler",
    "DreamProjectionError",
    "WORK_PATH_MESSAGE",
    "eligibility_snapshot",
]
