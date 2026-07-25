from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from experience.canonical_scene import CanonicalScene
from experience.dream import DreamSceneGrant
from experience.dream_game import (
    BlindRoundDefinition,
    ContentPackAudit,
    DREAM_GAME_EVALUATION_POLICY_VERSION,
    DREAM_FLOWER_PROTOCOL_VERSION,
    DREAM_GAME_PROJECTION_POLICY_VERSION,
    DREAM_GAME_REVEAL_POLICY_VERSION,
    DREAM_GAME_SIMULATED_NAMESPACE,
    DREAM_GAME_V50_NAMESPACE,
    FrozenProjectionManifest,
    HypothesisNodeOption,
    HypothesisRelationOption,
    ImmutableDreamSourceSnapshot,
    MaturedFruitContentPack,
    MaturedFruitSlot,
    OutcomeEvidence,
    ProblemQuestionRecord,
    SystemJudgmentSeal,
)
from product.dream_question_story import (
    QuestionStoryError,
    compile_active_question_story,
    compile_flower_for_spec,
    select_active_bundle_spec,
)


ROOT = Path(__file__).resolve().parents[2]
SIMULATED_PACK_PATH = (
    ROOT / "data" / "validation" / "fixtures" / "dream_problem_flower_simulated_v1.json"
)
SIX_LENSES = [
    "overview",
    "five_element",
    "combination_conflict",
    "roots_reveal",
    "timing",
    "work_path",
]
V50_CANONICAL_PROVIDER_VERSION = "dream-v50-canonical-provider.v3"


class DreamGameContentError(ValueError):
    pass


def canonical_json_hash(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def immutable_model_hash(payload: dict[str, Any]) -> str:
    clean = deepcopy(payload)
    clean.pop("immutable_hash", None)
    return canonical_json_hash(clean)


def load_content_pack(path: Path = SIMULATED_PACK_PATH) -> MaturedFruitContentPack:
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DreamGameContentError("dream_game_content_pack_unreadable") from exc
    _validate_source_pack(source)
    payload = deepcopy(source)
    payload.pop("schema_version", None)
    payload["original_timestamp_manifest_hash"] = canonical_json_hash(
        payload.pop("original_timestamp_manifest")
    )
    payload["cutoff_material_manifest_hash"] = canonical_json_hash(
        payload.pop("cutoff_material_manifest")
    )
    payload["chain_of_custody_manifest_hash"] = canonical_json_hash(
        payload.pop("chain_of_custody_manifest")
    )
    payload["immutable_hash"] = "0" * 64
    try:
        parsed = MaturedFruitContentPack.model_validate(payload)
    except ValueError as exc:
        raise DreamGameContentError("dream_game_content_pack_schema_invalid") from exc
    return parsed.model_copy(update={
        "immutable_hash": immutable_model_hash(parsed.model_dump(mode="json")),
    })


def audit_content_pack(
    pack: MaturedFruitContentPack,
    *,
    now: datetime | None = None,
) -> ContentPackAudit:
    issues: list[str] = []
    if pack.immutable_hash != immutable_model_hash(pack.model_dump(mode="json")):
        issues.append("immutable_hash_mismatch")
    if pack.evidence_class != "V50_CANONICAL" and len(pack.slots) != 3:
        issues.append("three_slot_pilot_required")
    if pack.evidence_class == "SIMULATED":
        if pack.namespace != DREAM_GAME_SIMULATED_NAMESPACE:
            issues.append("simulated_namespace_invalid")
        if pack.release_eligible or pack.verified_real_gate_contribution:
            issues.append("simulated_real_gate_contamination")
    elif pack.evidence_class == "V50_CANONICAL":
        if pack.namespace != DREAM_GAME_V50_NAMESPACE:
            issues.append("v50_canonical_namespace_invalid")
        if (
            pack.development_only
            or pack.release_eligible
            or pack.verified_real_gate_contribution
        ):
            issues.append("v50_canonical_real_gate_contamination")
    if pack.content_state == "REVOKED":
        issues.append("content_revoked")
    resulting_state = "REVOKED" if pack.content_state == "REVOKED" else (
        "PUBLISHABLE" if not issues else "DRAFT"
    )
    return ContentPackAudit(
        pack_id=pack.pack_id,
        evidence_class=pack.evidence_class,
        resulting_state=resulting_state,
        passed=not issues,
        issue_codes=issues,
        projection_manifest_hash=canonical_json_hash({
            "pack_id": pack.pack_id,
            "pack_version": pack.pack_version,
            "pack_hash": pack.immutable_hash,
            "slot_ids": [item.slot_id for item in pack.slots],
            "evidence_class": pack.evidence_class,
        }),
        verified_real_gate_contribution=(
            pack.verified_real_gate_contribution if not issues else 0
        ),
        audited_at=now or datetime.now(timezone.utc),
    )


def compile_simulated_round(
    *,
    pack: MaturedFruitContentPack,
    slot: MaturedFruitSlot,
    grant: DreamSceneGrant,
    resident_label: str,
    canvas: dict[str, Any],
    now: datetime | None = None,
) -> tuple[BlindRoundDefinition, SystemJudgmentSeal, OutcomeEvidence]:
    audit = audit_content_pack(pack)
    if not audit.passed or pack.evidence_class != "SIMULATED":
        raise DreamGameContentError("dream_game_simulated_pack_not_publishable")
    current = now or datetime.now(timezone.utc)
    spec = _natal_spec(canvas)
    allowed_nodes = _allowed_nodes(spec)
    allowed_relations = _allowed_relations(spec, allowed_nodes=allowed_nodes)
    source = canvas.get("source") if isinstance(canvas.get("source"), dict) else {}
    source_scene_hash = grant.authorized_source_hash
    source_scene_version = str(source.get("public_source_version") or grant.authorization_version)
    source_life_case_version = str(source.get("life_case_version") or "unknown")
    frozen_canvas = deepcopy(canvas)
    projection_input = {
        "scene_ref": grant.public_scene_ref,
        "scene_hash": source_scene_hash,
        "scene_version": source_scene_version,
        "life_case_version": source_life_case_version,
        "question_id": slot.question.question_id,
        "question_version": slot.question.question_version,
        "knowledge_cutoff": slot.question.knowledge_cutoff.isoformat(),
        "canvas_hash": canonical_json_hash(frozen_canvas),
        "policy": DREAM_GAME_PROJECTION_POLICY_VERSION,
    }
    projection_input_hash = canonical_json_hash(projection_input)
    projection_payload = {
        "input_manifest_hash": projection_input_hash,
        "canvas": frozen_canvas,
        "allowed_nodes": [item.model_dump(mode="json") for item in allowed_nodes],
        "allowed_relations": [item.model_dump(mode="json") for item in allowed_relations],
    }
    projection_hash = canonical_json_hash(projection_payload)
    frozen = FrozenProjectionManifest(
        knowledge_cutoff=slot.question.knowledge_cutoff,
        clock_domain=slot.question.clock_domain,
        source_scene_ref=grant.public_scene_ref,
        source_scene_version=source_scene_version,
        source_scene_hash=source_scene_hash,
        source_life_case_version=source_life_case_version,
        canvas_snapshot=frozen_canvas,
        allowed_nodes=allowed_nodes,
        allowed_relations=allowed_relations,
        input_manifest=projection_input,
        input_manifest_hash=projection_input_hash,
        projection_hash=projection_hash,
    )
    round_id = f"dream-round-{canonical_json_hash({'pack': pack.pack_id, 'slot': slot.slot_id, 'scene': grant.public_scene_ref})[:32]}"
    system_seal_id = f"dream-system-seal-{canonical_json_hash({'round': round_id, 'kind': 'system'})[:32]}"
    system_manifest = {
        "round_definition_ref": round_id,
        "frozen_projection_hash": projection_hash,
        "question_ref": slot.question.question_id,
        "knowledge_cutoff": slot.question.knowledge_cutoff.isoformat(),
        "policy_versions": {
            "projection": DREAM_GAME_PROJECTION_POLICY_VERSION,
            "evaluation": DREAM_GAME_EVALUATION_POLICY_VERSION,
            "reveal": DREAM_GAME_REVEAL_POLICY_VERSION,
        },
    }
    system_payload = {
        "seal_id": system_seal_id,
        "round_id": round_id,
        "projection_hash": projection_hash,
        "selected_outcome_option_id": slot.system_outcome_option_id,
        "confidence_basis_points": slot.system_confidence_basis_points,
        "formal_path_assertion_refs": [],
        "candidate_path_refs": [item.relation_ref for item in allowed_relations if not item.formal],
        "reasoning_summary": slot.system_reasoning_summary,
        "strongest_alternative": slot.system_strongest_alternative,
        "disconfirmation_condition": slot.system_disconfirmation_condition,
        "model_version": "deterministic.simulated-content-pack.v1",
        "prompt_version": "none",
        "reasoner_version": "frozen-fixture-system-judgment.v1",
        "knowledge_versions": [pack.pack_version, source_scene_version],
        "input_manifest": system_manifest,
        "input_manifest_hash": canonical_json_hash(system_manifest),
        "generated_at": current,
        "sealed_at": current,
    }
    system_payload["immutable_hash"] = immutable_model_hash(system_payload)
    system_seal = SystemJudgmentSeal.model_validate(system_payload)
    published_at = current + timedelta(microseconds=1)
    round_payload = {
        "round_id": round_id,
        "round_version": "1",
        "pack_id": pack.pack_id,
        "pack_version": pack.pack_version,
        "slot_id": slot.slot_id,
        "namespace": pack.namespace,
        "resident_scene_ref": grant.public_scene_ref,
        "resident_label": resident_label,
        "event_family": slot.event_family,
        "evidence_class": pack.evidence_class,
        "development_only": pack.development_only,
        "release_eligible": pack.release_eligible,
        "verified_real_gate_contribution": pack.verified_real_gate_contribution,
        "content_state": pack.content_state,
        "question": slot.question,
        "frozen_projection": frozen,
        "flower_protocol_version": "single-answer-immediate-fruit.v1",
        "system_judgment_seal_ref": system_seal.seal_id,
        "system_judgment_commitment_hash": system_seal.immutable_hash,
        "sealed_at": system_seal.sealed_at,
        "published_at": published_at,
    }
    round_payload["immutable_hash"] = immutable_model_hash(
        _jsonable(round_payload)
    )
    round_definition = BlindRoundDefinition.model_validate(round_payload)
    evidence_payload = {
        "evidence_id": f"dream-outcome-{canonical_json_hash({'round': round_id, 'domain': 'isolated'})[:32]}",
        "round_id": round_id,
        "evidence_class": "SIMULATED",
        "verification_status": "VERIFIED",
        "resolved_option_id": slot.simulated_outcome_option_id,
        "outcome_summary": slot.simulated_outcome_summary,
        "evidence_items": slot.simulated_evidence_items,
        "chain_of_custody_manifest_hash": pack.chain_of_custody_manifest_hash,
        "occurred_at": slot.question.outcome_window_end,
        "verified_at": slot.question.outcome_window_end + timedelta(seconds=1),
    }
    evidence_payload["immutable_hash"] = immutable_model_hash(
        _jsonable(evidence_payload)
    )
    return (
        round_definition,
        system_seal,
        OutcomeEvidence.model_validate(evidence_payload),
    )


def compile_v50_canonical_encounter(
    *,
    entries: list[tuple[DreamSceneGrant, CanonicalScene, str, dict[str, Any]]],
    published_at: datetime | None = None,
) -> tuple[
    list[MaturedFruitContentPack],
    list[tuple[BlindRoundDefinition, SystemJudgmentSeal, OutcomeEvidence]],
]:
    """Compile one immutable three-tree encounter from authorized V50 sources."""
    if len(entries) != 3:
        raise DreamGameContentError("dream_game_three_v50_scenes_required")
    packs: list[MaturedFruitContentPack] = []
    compiled: list[
        tuple[BlindRoundDefinition, SystemJudgmentSeal, OutcomeEvidence]
    ] = []
    for grant, scene, label, canvas in entries:
        entry_manifest = {
            "public_scene_ref": grant.public_scene_ref,
            "authorization_version": grant.authorization_version,
            "authorized_source_hash": grant.authorized_source_hash,
            "scene_source_hash": scene.identity.source_hash,
            "life_case_version": scene.identity.life_case_version,
            "source_updated_at": scene.identity.source_updated_at.isoformat(),
            "canvas_hash": canonical_json_hash(canvas),
        }
        pack_digest = canonical_json_hash({
            "provider_version": V50_CANONICAL_PROVIDER_VERSION,
            "entry": entry_manifest,
        })
        created_at = max(scene.identity.source_updated_at, grant.updated_at)
        slot = _v50_slot(
            scene=scene,
            slot_id=f"v50-canonical-slot-{pack_digest[:20]}",
            canvas=canvas,
        )
        pack_payload = {
            "pack_id": f"dream-v50-pack-{pack_digest[:32]}",
            "pack_version": V50_CANONICAL_PROVIDER_VERSION,
            "namespace": DREAM_GAME_V50_NAMESPACE,
            "evidence_class": "V50_CANONICAL",
            "content_state": "PUBLISHABLE",
            "development_only": False,
            "release_eligible": False,
            "verified_real_gate_contribution": 0,
            "explicit_authorization_ref": "",
            "deidentification_policy_version": "dream-scene-grant.v1",
            "original_timestamp_manifest_hash": canonical_json_hash({
                "source_updated_at": [entry_manifest["source_updated_at"]],
            }),
            "cutoff_material_manifest_hash": canonical_json_hash(entry_manifest),
            "chain_of_custody_manifest_hash": canonical_json_hash({
                "provider": V50_CANONICAL_PROVIDER_VERSION,
                "source_chain": [
                    "CanonicalScene",
                    "ReadOnlySixPillarCanvas",
                    "ImmutableDreamSourceSnapshot",
                ],
            }),
            "withdrawal_policy_version": "dream-scene-grant-revocation.v1",
            "slots": [slot],
            "immutable_hash": "0" * 64,
            "created_at": created_at,
        }
        pack = MaturedFruitContentPack.model_validate(pack_payload)
        pack = pack.model_copy(update={
            "immutable_hash": immutable_model_hash(pack.model_dump(mode="json")),
        })
        audit = audit_content_pack(pack, now=created_at)
        if not audit.passed:
            raise DreamGameContentError(
                "dream_game_v50_pack_invalid:" + ",".join(audit.issue_codes)
            )
        packs.append(pack)
        compiled.append(compile_v50_canonical_round(
            pack=pack,
            slot=slot,
            grant=grant,
            scene=scene,
            resident_label=label,
            canvas=canvas,
            published_at=published_at,
        ))
    return packs, compiled


def compile_v50_canonical_round(
    *,
    pack: MaturedFruitContentPack,
    slot: MaturedFruitSlot,
    grant: DreamSceneGrant,
    scene: CanonicalScene,
    resident_label: str,
    canvas: dict[str, Any],
    published_at: datetime | None = None,
) -> tuple[BlindRoundDefinition, SystemJudgmentSeal, OutcomeEvidence]:
    audit = audit_content_pack(pack, now=scene.identity.source_updated_at)
    if not audit.passed or pack.evidence_class != "V50_CANONICAL":
        raise DreamGameContentError("dream_game_v50_pack_not_publishable")
    if scene.identity.source_hash != grant.authorized_source_hash:
        raise DreamGameContentError("dream_game_v50_source_authorization_changed")

    captured_at = max(scene.identity.source_updated_at, grant.updated_at)
    snapshot = _v50_source_snapshot(
        grant=grant,
        scene=scene,
        canvas=canvas,
        captured_at=captured_at,
    )
    # From this point onward all derived content is reconstructed from the
    # immutable payload, not from the live LifeCase or scene objects.
    frozen_scene = CanonicalScene.model_validate(snapshot.snapshot_payload["scene"])
    frozen_canvas = deepcopy(snapshot.snapshot_payload["canvas"])
    spec = _natal_spec(frozen_canvas)
    allowed_nodes = _allowed_nodes(spec)
    allowed_relations = _allowed_relations(
        spec,
        allowed_nodes=allowed_nodes,
        allow_simulated_candidates=False,
    )
    round_id = (
        "dream-v50-round-"
        + canonical_json_hash({
            "pack_id": pack.pack_id,
            "slot_id": slot.slot_id,
            "source_snapshot_id": snapshot.source_snapshot_id,
            "flower_protocol_version": DREAM_FLOWER_PROTOCOL_VERSION,
        })[:32]
    )
    try:
        story = compile_active_question_story(
            round_id=round_id,
            snapshot=snapshot,
            scene=frozen_scene,
            allowed_nodes=allowed_nodes,
            allowed_relations=allowed_relations,
            expected_flower_question=slot.question,
        )
    except QuestionStoryError as exc:
        raise DreamGameContentError(str(exc)) from exc
    question_set = story.question_bundle
    flower_truth = story.flower_truth
    if (
        slot.system_outcome_option_id
        != flower_truth.selected_outcome_option_id
        or slot.system_reasoning_summary != flower_truth.summary
    ):
        raise DreamGameContentError("dream_game_question_story_slot_truth_mismatch")
    projection_input = {
        "source_snapshot_id": snapshot.source_snapshot_id,
        "snapshot_hash": snapshot.snapshot_hash,
        "question_set_id": question_set.question_set_id,
        "question_set_hash": question_set.immutable_hash,
        "policy": DREAM_GAME_PROJECTION_POLICY_VERSION,
    }
    projection_payload = {
        "input_manifest_hash": canonical_json_hash(projection_input),
        "canvas": frozen_canvas,
        "allowed_nodes": [item.model_dump(mode="json") for item in allowed_nodes],
        "allowed_relations": [
            item.model_dump(mode="json") for item in allowed_relations
        ],
    }
    projection_hash = canonical_json_hash(projection_payload)
    frozen = FrozenProjectionManifest(
        knowledge_cutoff=snapshot.cutoff_at,
        clock_domain="v50.canonical_scene.source_updated_at",
        source_scene_ref=grant.public_scene_ref,
        source_scene_version=snapshot.source_scene_version,
        source_scene_hash=snapshot.source_hash,
        source_life_case_version=snapshot.source_life_case_version,
        source_snapshot_id=snapshot.source_snapshot_id,
        cutoff_verification_status="VERIFIED_AS_OF_SOURCE_VERSION",
        canvas_snapshot=frozen_canvas,
        allowed_nodes=allowed_nodes,
        allowed_relations=allowed_relations,
        input_manifest=projection_input,
        input_manifest_hash=canonical_json_hash(projection_input),
        projection_hash=projection_hash,
    )
    outcome_option = flower_truth.selected_outcome_option_id
    path_refs = list(flower_truth.formal_path_assertion_refs)
    legacy_refs = list(flower_truth.candidate_path_refs)
    system_seal_id = (
        "dream-system-seal-"
        + canonical_json_hash({"round": round_id, "kind": "v50-canonical"})[:32]
    )
    system_manifest = {
        "source_snapshot_id": snapshot.source_snapshot_id,
        "source_snapshot_hash": snapshot.snapshot_hash,
        "question_set_id": question_set.question_set_id,
        "question_set_hash": question_set.immutable_hash,
        "frozen_projection_hash": projection_hash,
        "provider_version": V50_CANONICAL_PROVIDER_VERSION,
    }
    system_payload = {
        "seal_id": system_seal_id,
        "round_id": round_id,
        "projection_hash": projection_hash,
        "selected_outcome_option_id": outcome_option,
        "confidence_basis_points": 10000,
        "formal_path_assertion_refs": path_refs,
        "candidate_path_refs": legacy_refs,
        "reasoning_summary": flower_truth.summary,
        "strongest_alternative": (
            "若权威事实或 Assertion 在未来版本中变化，应创建新题组，"
            "不得改写本快照中的判断。"
        ),
        "disconfirmation_condition": (
            "本快照中的权威引用经完整性审计证明与封存内容不一致。"
        ),
        "model_version": "deterministic.v50-canonical-snapshot.v1",
        "prompt_version": "none",
        "reasoner_version": V50_CANONICAL_PROVIDER_VERSION,
        "knowledge_versions": [
            snapshot.source_scene_version,
            question_set.question_set_version,
        ],
        "input_manifest": system_manifest,
        "input_manifest_hash": canonical_json_hash(system_manifest),
        "generated_at": captured_at,
        "sealed_at": captured_at,
        "immutable_hash": "0" * 64,
    }
    system_payload["immutable_hash"] = immutable_model_hash(system_payload)
    system_seal = SystemJudgmentSeal.model_validate(system_payload)
    round_published_at = max(
        published_at or captured_at + timedelta(microseconds=1),
        captured_at + timedelta(microseconds=1),
    )
    flower_owner_ref = (
        grant.authorized_by_ref
        if grant.subject_kind == "authorized_human"
        else grant.subject_ref
    )
    round_payload = {
        "round_id": round_id,
        "round_version": "2",
        "pack_id": pack.pack_id,
        "pack_version": pack.pack_version,
        "slot_id": slot.slot_id,
        "namespace": pack.namespace,
        "resident_scene_ref": grant.public_scene_ref,
        "resident_label": resident_label,
        "event_family": slot.event_family,
        "evidence_class": pack.evidence_class,
        "development_only": pack.development_only,
        "release_eligible": pack.release_eligible,
        "verified_real_gate_contribution": pack.verified_real_gate_contribution,
        "content_state": pack.content_state,
        "question": slot.question,
        "frozen_projection": frozen,
        "source_snapshot": snapshot,
        "question_set": question_set,
        "system_judgment_seal_ref": system_seal.seal_id,
        "system_judgment_commitment_hash": system_seal.immutable_hash,
        "flower_protocol_version": DREAM_FLOWER_PROTOCOL_VERSION,
        "flower_owner_ref": flower_owner_ref or grant.authorized_by_ref,
        "answer_close_at": round_published_at + timedelta(days=7),
        "outcome_due_at": (
            round_published_at + timedelta(days=14)
            if question_set.reveal_policy == "ASSERTION_REVEAL"
            else max(
                round_published_at + timedelta(days=7),
                slot.question.outcome_window_end,
            )
        ),
        "sealed_at": system_seal.sealed_at,
        "published_at": round_published_at,
        "immutable_hash": "0" * 64,
    }
    round_payload["immutable_hash"] = immutable_model_hash(round_payload)
    round_definition = BlindRoundDefinition.model_validate(round_payload)
    evidence_payload = {
        "evidence_id": (
            "dream-outcome-"
            + canonical_json_hash({
                "round": round_id,
                "source_snapshot": snapshot.source_snapshot_id,
            })[:32]
        ),
        "round_id": round_id,
        "evidence_class": "V50_CANONICAL",
        "verification_status": "VERIFIED",
        "resolved_option_id": outcome_option,
        "outcome_summary": flower_truth.summary,
        "evidence_items": (
            list(flower_truth.evidence_refs)
            or [f"source_snapshot:{snapshot.source_snapshot_id}"]
        ),
        "chain_of_custody_manifest_hash": pack.chain_of_custody_manifest_hash,
        "occurred_at": snapshot.cutoff_at,
        "verified_at": captured_at,
        "immutable_hash": "0" * 64,
    }
    evidence_payload["immutable_hash"] = immutable_model_hash(evidence_payload)
    return (
        round_definition,
        system_seal,
        OutcomeEvidence.model_validate(evidence_payload),
    )


def _v50_source_snapshot(
    *,
    grant: DreamSceneGrant,
    scene: CanonicalScene,
    canvas: dict[str, Any],
    captured_at: datetime,
) -> ImmutableDreamSourceSnapshot:
    payload = {
        "scene": scene.model_dump(mode="json"),
        "canvas": deepcopy(canvas),
    }
    snapshot_hash = canonical_json_hash(payload)
    source_snapshot_id = f"dream-source-snapshot-{snapshot_hash[:40]}"
    return ImmutableDreamSourceSnapshot(
        source_snapshot_id=source_snapshot_id,
        cutoff_at=scene.identity.source_updated_at,
        cutoff_verification_status="VERIFIED_AS_OF_SOURCE_VERSION",
        source_scene_ref=grant.public_scene_ref,
        source_scene_version=(
            f"{scene.identity.compiler_version}:{scene.identity.life_case_version}"
        ),
        source_hash=scene.identity.source_hash,
        source_life_case_version=scene.identity.life_case_version,
        source_updated_at=scene.identity.source_updated_at,
        authorization_version=grant.authorization_version,
        captured_at=captured_at,
        snapshot_payload=payload,
        snapshot_hash=snapshot_hash,
    )


def _v50_slot(
    *,
    scene: CanonicalScene,
    slot_id: str,
    canvas: dict[str, Any],
) -> MaturedFruitSlot:
    cutoff = scene.identity.source_updated_at
    spec_payload = _natal_spec(canvas)
    allowed_nodes = _allowed_nodes(spec_payload)
    allowed_relations = _allowed_relations(
        spec_payload,
        allowed_nodes=allowed_nodes,
        allow_simulated_candidates=False,
    )
    try:
        story_spec = select_active_bundle_spec(
            scene=scene,
            allowed_nodes=allowed_nodes,
            allowed_relations=allowed_relations,
        )
        question, flower_truth = compile_flower_for_spec(
            scene=scene,
            spec=story_spec,
            cutoff_at=cutoff,
        )
    except QuestionStoryError as exc:
        raise DreamGameContentError(str(exc)) from exc
    return MaturedFruitSlot(
        slot_id=slot_id,
        event_family="V50_QUESTION_STORY",
        question=question,
        system_outcome_option_id=flower_truth.selected_outcome_option_id,
        system_confidence_basis_points=10000,
        system_reasoning_summary=flower_truth.summary,
        system_strongest_alternative=(
            "后续权威版本可能产生不同判断，但不能追溯改写当前 Cutoff。"
        ),
        system_disconfirmation_condition=(
            "封存快照中的权威引用、题组依赖或版本完整性被证明无效。"
        ),
    )


def _validate_source_pack(source: Any) -> None:
    if not isinstance(source, dict):
        raise DreamGameContentError("dream_game_content_pack_not_object")
    required = {
        "pack_id",
        "pack_version",
        "namespace",
        "evidence_class",
        "content_state",
        "original_timestamp_manifest",
        "cutoff_material_manifest",
        "chain_of_custody_manifest",
        "slots",
    }
    if required - set(source):
        raise DreamGameContentError("dream_game_content_pack_fields_missing")
    if source.get("evidence_class") == "SIMULATED":
        if source.get("namespace") != DREAM_GAME_SIMULATED_NAMESPACE:
            raise DreamGameContentError("dream_game_simulated_namespace_invalid")
        if source.get("release_eligible") or source.get("verified_real_gate_contribution"):
            raise DreamGameContentError("dream_game_simulated_release_forbidden")
    for key in (
        "original_timestamp_manifest",
        "cutoff_material_manifest",
        "chain_of_custody_manifest",
    ):
        if not isinstance(source.get(key), dict) or not source[key]:
            raise DreamGameContentError(f"dream_game_{key}_missing")
    slots = source.get("slots")
    if not isinstance(slots, list) or len(slots) != 3:
        raise DreamGameContentError("dream_game_three_slots_required")


def _natal_spec(canvas: dict[str, Any]) -> dict[str, Any]:
    stages = canvas.get("stages") if isinstance(canvas.get("stages"), dict) else {}
    natal = stages.get("natal") if isinstance(stages.get("natal"), dict) else {}
    spec = natal.get("spec") if isinstance(natal.get("spec"), dict) else {}
    if not spec:
        raise DreamGameContentError("dream_game_canvas_spec_unavailable")
    return spec


def _allowed_nodes(spec: dict[str, Any]) -> list[HypothesisNodeOption]:
    slots = {
        str(item.get("slot_ref")): str(item.get("label") or "")
        for item in spec.get("semantic_slots", [])
        if isinstance(item, dict) and item.get("slot_ref")
    }
    nodes: list[HypothesisNodeOption] = []
    for item in spec.get("nodes", []):
        if not isinstance(item, dict) or not item.get("node_ref"):
            continue
        node_type = str(item.get("node_type") or "unknown")
        layer = node_type if node_type in {"stem", "branch", "hidden_stem", "timing"} else "unknown"
        nodes.append(HypothesisNodeOption(
            node_ref=str(item["node_ref"]),
            label=str(item.get("label") or "未命名节点"),
            pillar_label=slots.get(str(item.get("semantic_slot_ref") or ""), ""),
            layer=layer,
        ))
    if not nodes:
        raise DreamGameContentError("dream_game_canvas_nodes_unavailable")
    return sorted(nodes, key=lambda item: (item.pillar_label, item.layer, item.node_ref))


def _allowed_relations(
    spec: dict[str, Any],
    *,
    allowed_nodes: list[HypothesisNodeOption],
    allow_simulated_candidates: bool = True,
) -> list[HypothesisRelationOption]:
    node_refs = {item.node_ref for item in allowed_nodes}
    relations: list[HypothesisRelationOption] = []
    for item in spec.get("relations", []):
        if not isinstance(item, dict):
            continue
        source = str(item.get("source_ref") or item.get("source_node_ref") or "")
        target = str(item.get("target_ref") or item.get("target_node_ref") or "")
        relation_ref = str(item.get("relation_ref") or "")
        trace = item.get("trace") if isinstance(item.get("trace"), dict) else {}
        committed = bool(trace.get("commitment_refs")) and trace.get("epistemic_status") in {
            "committed",
            "effective",
            "structural",
        }
        if relation_ref and source in node_refs and target in node_refs and committed:
            relations.append(HypothesisRelationOption(
                relation_ref=relation_ref,
                label=str(item.get("label") or item.get("relation_type") or "已确认关系"),
                source_node_ref=source,
                target_node_ref=target,
                formal=True,
                evidence_class="formal_pre_cutoff",
            ))
    if relations:
        return relations[:12]
    if not allow_simulated_candidates:
        return []
    stems = [item for item in allowed_nodes if item.layer == "stem"]
    candidates: list[HypothesisRelationOption] = []
    for source, target in zip(stems, stems[1:3]):
        relation_ref = f"simulated-candidate:{canonical_json_hash({'source': source.node_ref, 'target': target.node_ref})[:24]}"
        candidates.append(HypothesisRelationOption(
            relation_ref=relation_ref,
            label=f"候选观察：{source.label} → {target.label}",
            source_node_ref=source.node_ref,
            target_node_ref=target.node_ref,
            formal=False,
            evidence_class="simulated_candidate",
        ))
    return candidates


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


__all__ = [
    "DreamGameContentError",
    "SIMULATED_PACK_PATH",
    "SIX_LENSES",
    "audit_content_pack",
    "canonical_json_hash",
    "compile_simulated_round",
    "compile_v50_canonical_encounter",
    "compile_v50_canonical_round",
    "immutable_model_hash",
    "load_content_pack",
]
