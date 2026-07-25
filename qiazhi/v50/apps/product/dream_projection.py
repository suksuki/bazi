from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from experience.canonical_scene import CanonicalScene
from experience.compiler import canonical_hash
from experience.dream import (
    DREAM_PROJECTION_VERSION,
    DREAM_VERIFICATION_COORDINATE_VERSION,
    DreamEncounterProjection,
    DreamMirrorProjection,
    DreamRevealProjection,
    DreamSceneEligibilitySnapshot,
    DreamSceneGrant,
    DreamTreeCard,
    DreamTreeProjection,
    DreamVerificationBinding,
    DreamVerificationProjection,
    DreamVisit,
)
from product.dream_pilot import CANONICAL_NPC_SEEDS


WORK_PATH_MESSAGE = "当前暂无已确认主路径"


class DreamProjectionError(ValueError):
    pass


@dataclass(frozen=True)
class _RevealCandidate:
    private_semantic_ref: str
    target_object_ref: str
    reveal_kind: str
    visual_mode: str
    target_stage: str
    target_lens: str
    authorized_statement: str
    assertion_version: str


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
        visit: DreamVisit,
        grant: DreamSceneGrant,
        scene: CanonicalScene,
        canvas: dict[str, Any],
        onecanvas_view_ref: str,
        verification_state: str,
    ) -> DreamMirrorProjection:
        public_version = _public_source_version(grant=grant, scene=scene)
        projected_canvas = _public_canvas(
            canvas=canvas,
            grant=grant,
            scene=scene,
            public_version=public_version,
        )
        candidate = _select_reveal_candidate(scene=scene, canvas=canvas)
        current_view_ref = _onecanvas_view_ref(
            visit=visit,
            grant=grant,
            scene=scene,
            public_version=public_version,
            candidate=candidate,
        )
        focused = bool(
            verification_state == "focused"
            and candidate is not None
            and onecanvas_view_ref == current_view_ref
        )
        verification = _verification_projection(
            grant=grant,
            scene=scene,
            public_version=public_version,
            onecanvas_view_ref=onecanvas_view_ref,
            candidate=candidate if focused else None,
        )
        path_count = _committed_public_path_count(scene=scene, canvas=canvas)
        work_path_state = "available" if path_count else "unavailable_unconfirmed"
        content_hash = canonical_hash({
            "public_scene_ref": grant.public_scene_ref,
            "source_version": public_version,
            "source_kind": grant.subject_kind,
            "canvas": projected_canvas,
            "work_path_state": work_path_state,
            "verification": verification.model_dump(mode="json"),
        })
        return DreamMirrorProjection(
            public_scene_ref=grant.public_scene_ref,
            source_version=public_version,
            source_kind=grant.subject_kind,
            source_label_key=_source_label_key(grant),
            work_path_state=work_path_state,
            verification=verification,
            canvas=projected_canvas,
            content_hash=content_hash,
        )

    def reveal(
        self,
        *,
        visit: DreamVisit,
        grant: DreamSceneGrant,
        scene: CanonicalScene,
        canvas: dict[str, Any],
    ) -> DreamRevealProjection:
        public_version = _public_source_version(grant=grant, scene=scene)
        candidate = _select_reveal_candidate(scene=scene, canvas=canvas)
        view_ref = _onecanvas_view_ref(
            visit=visit,
            grant=grant,
            scene=scene,
            public_version=public_version,
            candidate=candidate,
        )
        reveal_ref = (
            _opaque_ref(
                public_scene_ref=grant.public_scene_ref,
                value=candidate.private_semantic_ref,
            )
            if candidate is not None
            else ""
        )
        payload = {
            "public_scene_ref": grant.public_scene_ref,
            "source_version": public_version,
            "source_kind": grant.subject_kind,
            "revealable_assertion_ref": reveal_ref,
            "reveal_kind": candidate.reveal_kind if candidate else "none",
            "visual_mode": candidate.visual_mode if candidate else "natural_contact_only",
            "authorized_statement": candidate.authorized_statement if candidate else "",
            "onecanvas_view_ref": view_ref,
            "target_stage": candidate.target_stage if candidate else "natal",
            "target_lens": candidate.target_lens if candidate else "overview",
        }
        return DreamRevealProjection(
            **payload,
            content_hash=canonical_hash(payload),
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
            resident_label=_resident_label(grant),
            autonomous_phase_ms=int(scene.identity.source_hash[:8], 16) % 60000,
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


def _resident_label(grant: DreamSceneGrant) -> str:
    if grant.subject_kind == "authorized_human":
        return "你的生命树"
    names = {item.npc_id: item.display_name for item in CANONICAL_NPC_SEEDS}
    return names.get(grant.subject_ref, "梦境居民")


def _select_reveal_candidate(
    *,
    scene: CanonicalScene,
    canvas: dict[str, Any],
) -> _RevealCandidate | None:
    for assertion in sorted(scene.path_assertions, key=lambda item: item.assertion_ref):
        if assertion.status != "committed":
            continue
        located = _locate_canvas_object(
            canvas=canvas,
            object_kind="path",
            object_ref=assertion.path_ref,
            target_lens="work_path",
        )
        if located is None:
            continue
        stage, _ = located
        return _RevealCandidate(
            private_semantic_ref=assertion.assertion_ref,
            target_object_ref=assertion.path_ref,
            reveal_kind="path",
            visual_mode="path_sequence",
            target_stage=stage,
            target_lens="work_path",
            authorized_statement=assertion.statement or "已确认主路径",
            assertion_version=canonical_hash(assertion),
        )

    for assertion in sorted(scene.relation_assertions, key=lambda item: item.assertion_ref):
        if assertion.status != "committed" or assertion.relation_state != "effective":
            continue
        relation = _find_canvas_spec_item(
            canvas=canvas,
            object_kind="relation",
            object_ref=assertion.relation_ref,
        )
        if relation is None:
            continue
        stage, relation_item = relation
        lens = _relation_lens(
            relation_type=str(relation_item.get("relation_type") or ""),
            stage=stage,
        )
        if _locate_canvas_object(
            canvas=canvas,
            object_kind="relation",
            object_ref=assertion.relation_ref,
            target_lens=lens,
        ) is None:
            continue
        relation_type = str(relation_item.get("relation_type") or "")
        return _RevealCandidate(
            private_semantic_ref=assertion.assertion_ref,
            target_object_ref=assertion.relation_ref,
            reveal_kind="relation",
            visual_mode=(
                "relation_sync"
                if _relation_is_symmetric(relation_type)
                else "relation_directional"
            ),
            target_stage=stage,
            target_lens=lens,
            authorized_statement=assertion.statement or str(relation_item.get("label") or ""),
            assertion_version=canonical_hash(assertion),
        )

    day_fact = next((item for item in scene.chart_facts if item.pillar_slot == "day"), None)
    natal = (canvas.get("stages") or {}).get("natal") or {}
    slots = ((natal.get("spec") or {}).get("semantic_slots") or [])
    day_slot = next(
        (
            item
            for item in slots
            if isinstance(item, dict) and item.get("slot_type") == "natal_day"
        ),
        None,
    )
    if day_fact is not None and isinstance(day_slot, dict) and day_slot.get("slot_ref"):
        return _RevealCandidate(
            private_semantic_ref=day_fact.fact_ref,
            target_object_ref=str(day_slot["slot_ref"]),
            reveal_kind="node",
            visual_mode="local_node",
            target_stage="natal",
            target_lens="overview",
            authorized_statement=(
                f"{day_fact.pillar_label} {day_fact.stem}{day_fact.branch}"
            ),
            assertion_version=canonical_hash(day_fact),
        )
    return None


def _locate_canvas_object(
    *,
    canvas: dict[str, Any],
    object_kind: str,
    object_ref: str,
    target_lens: str,
) -> tuple[str, dict[str, Any]] | None:
    located = _find_canvas_spec_item(
        canvas=canvas,
        object_kind=object_kind,
        object_ref=object_ref,
    )
    if located is None:
        return None
    stage_name, item = located
    stage = (canvas.get("stages") or {}).get(stage_name) or {}
    layer = next(
        (
            value
            for value in stage.get("layers") or []
            if isinstance(value, dict) and value.get("layer_id") == target_lens
        ),
        None,
    )
    if not isinstance(layer, dict):
        return None
    if object_kind == "path":
        allowed = layer.get("formal_path_refs") or []
    elif object_kind == "relation":
        allowed = layer.get("formal_relation_refs") or []
    else:
        allowed = [object_ref]
    return (stage_name, item) if object_ref in allowed else None


def _find_canvas_spec_item(
    *,
    canvas: dict[str, Any],
    object_kind: str,
    object_ref: str,
) -> tuple[str, dict[str, Any]] | None:
    key = {"path": "paths", "relation": "relations"}.get(object_kind, "nodes")
    ref_key = {"path": "path_ref", "relation": "relation_ref"}.get(
        object_kind,
        "node_ref",
    )
    for stage_name in canvas.get("stage_order") or ["natal", "luck", "year"]:
        stage = (canvas.get("stages") or {}).get(stage_name) or {}
        for item in (stage.get("spec") or {}).get(key) or []:
            if isinstance(item, dict) and item.get(ref_key) == object_ref:
                return str(stage_name), item
    return None


def _relation_lens(*, relation_type: str, stage: str) -> str:
    if stage != "natal":
        return "timing"
    if relation_type in {"roots", "stores", "reveals", "penetrates"}:
        return "roots_reveal"
    if relation_type in {
        "harmonizes",
        "clashes",
        "harms",
        "breaks",
        "punishes",
        "forms_half_combination",
        "forms_triple_combination",
        "forms_seasonal_combination",
    }:
        return "combination_conflict"
    return "five_element"


def _relation_is_symmetric(relation_type: str) -> bool:
    return relation_type in {
        "same_element_support",
        "harmonizes",
        "clashes",
        "harms",
        "breaks",
        "punishes",
        "forms_half_combination",
        "forms_triple_combination",
        "forms_seasonal_combination",
        "position_link",
    }


def _onecanvas_view_ref(
    *,
    visit: DreamVisit,
    grant: DreamSceneGrant,
    scene: CanonicalScene,
    public_version: str,
    candidate: _RevealCandidate | None,
) -> str:
    payload = {
        "visit_id": visit.visit_id,
        "viewer": visit.owner_user_id,
        "public_scene_ref": grant.public_scene_ref,
        "authorization_version": grant.authorization_version,
        "privacy_policy_version": grant.anonymization_policy_version,
        "source_version": public_version,
        "life_case_version": scene.identity.life_case_version,
        "coordinate_version": DREAM_VERIFICATION_COORDINATE_VERSION,
        "reveal_ref": candidate.private_semantic_ref if candidate else "",
        "assertion_version": candidate.assertion_version if candidate else "none",
        "target_stage": candidate.target_stage if candidate else "natal",
        "target_lens": candidate.target_lens if candidate else "overview",
    }
    return "dream-onecanvas-view-" + canonical_hash(payload)[:40]


def _verification_projection(
    *,
    grant: DreamSceneGrant,
    scene: CanonicalScene,
    public_version: str,
    onecanvas_view_ref: str,
    candidate: _RevealCandidate | None,
) -> DreamVerificationProjection:
    stage = candidate.target_stage if candidate else "natal"
    lens = candidate.target_lens if candidate else "overview"
    reveal_ref = (
        _opaque_ref(
            public_scene_ref=grant.public_scene_ref,
            value=candidate.private_semantic_ref,
        )
        if candidate
        else ""
    )
    return DreamVerificationProjection(
        state="focused" if candidate else "quiet_overview",
        onecanvas_view_ref=onecanvas_view_ref,
        revealable_assertion_ref=reveal_ref,
        reveal_kind=candidate.reveal_kind if candidate else "none",
        target_object_ref=(
            _opaque_ref(
                public_scene_ref=grant.public_scene_ref,
                value=candidate.target_object_ref,
            )
            if candidate
            else ""
        ),
        authorized_statement=candidate.authorized_statement if candidate else "",
        binding=DreamVerificationBinding(
            dream_projection_version=DREAM_PROJECTION_VERSION,
            source_version=public_version,
            assertion_version=_public_version_digest(
                public_scene_ref=grant.public_scene_ref,
                value=candidate.assertion_version if candidate else "none",
            ),
            life_case_version=_public_version_digest(
                public_scene_ref=grant.public_scene_ref,
                value=scene.identity.life_case_version,
            ),
            target_stage=stage,
            target_lens=lens,
        ),
    )


def _public_version_digest(*, public_scene_ref: str, value: str) -> str:
    return hashlib.sha256(f"{public_scene_ref}|{value}".encode()).hexdigest()


def _committed_public_path_count(
    *,
    scene: CanonicalScene,
    canvas: dict[str, Any],
) -> int:
    return sum(
        1
        for assertion in scene.path_assertions
        if assertion.status == "committed"
        and _locate_canvas_object(
            canvas=canvas,
            object_kind="path",
            object_ref=assertion.path_ref,
            target_lens="work_path",
        )
        is not None
    )


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
    allowed_path_refs = {
        item.path_ref
        for item in scene.path_assertions
        if item.status == "committed"
        and _locate_canvas_object(
            canvas=canvas,
            object_kind="path",
            object_ref=item.path_ref,
            target_lens="work_path",
        )
        is not None
    }
    projected["case_id"] = grant.public_scene_ref
    projected["role"] = "member"
    projected["path_availability"] = {
        "status": "available" if allowed_path_refs else "unavailable",
        "message": "正式主路径已确认" if allowed_path_refs else WORK_PATH_MESSAGE,
        "committed_path_count": len(allowed_path_refs),
        "candidate_path_count": 0,
        "legacy_unresolved_count": 0,
        "disclosure_level": "public",
        "professional_status": "confirmed" if allowed_path_refs else "not_confirmed",
        "diagnostic": None,
    }
    projected["renderer_policy"]["available_visibility_layers"] = ["formal", "focus"]
    for stage in projected.get("stages", {}).values():
        spec = stage.get("spec") or {}
        removed_paths = {
            str(item.get("path_ref") or "")
            for item in spec.get("paths") or []
            if isinstance(item, dict) and item.get("path_ref") not in allowed_path_refs
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
        spec["paths"] = [
            item
            for item in spec.get("paths") or []
            if isinstance(item, dict)
            and item.get("path_ref") in allowed_path_refs
            and (item.get("trace") or {}).get("epistemic_status") == "committed"
        ]
        allowed_paths = {
            str(item.get("path_ref") or "")
            for item in spec["paths"]
        }
        for layer in stage.get("layers") or []:
            if not isinstance(layer, dict):
                continue
            for key in ("relation_refs", "formal_relation_refs"):
                layer[key] = [
                    value for value in layer.get(key) or [] if value in allowed_relations
                ]
            for key in ("path_refs", "formal_path_refs"):
                layer[key] = [
                    value for value in layer.get(key) or [] if value in allowed_paths
                ]
            layer["count"] = (
                len(layer.get("formal_relation_refs") or [])
                + len(layer.get("formal_path_refs") or [])
            )
            layer["available"] = bool(layer["count"])
        context = stage.get("context") or {}
        context["committed_path_refs"] = [
            value
            for value in context.get("committed_path_refs") or []
            if value in allowed_paths
        ]
        for key in ("candidate_path_refs", "blocked_path_refs"):
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
        envelope["payload"]["path_assertions"] = [
            item
            for item in envelope["payload"].get("path_assertions") or []
            if isinstance(item, dict) and item.get("path_ref") in allowed_path_refs
        ]
    disclosure = envelope.get("role_disclosure") or {}
    if isinstance(disclosure, dict):
        disclosure["visible_path_assertion_refs"] = [
            item.assertion_ref
            for item in scene.path_assertions
            if item.status == "committed" and item.path_ref in allowed_path_refs
        ]

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
