from __future__ import annotations

import hashlib

import pytest

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import (
    build_bazi_material_store,
    build_source_manifestation_evidence,
)
from core.graph import (
    MingliRelationState,
    NodeRef,
    RelationActivationState,
    RelationDirectionality,
    RelationFactState,
    RelationKey,
    adapt_legacy_relation_assertion,
    build_mingli_graph_from_material_store,
    compile_graph_relation_facts,
    relation_fact_from_key,
    restore_relation_fact,
    withdraw_relation_fact,
)
from core.graph.provenance import (
    AssertionLifecycle,
    ProvenanceRecord,
    RelationAssertion,
)
from core.graph.relation_facts import assess_relation_fact_legality
from product.agent_case_store import MemoryAgentCaseStore
from product.canvas_projection import ReadOnlySixPillarCanvasService
from test_v50_mingli_structural_experiment import _case_payload


def _birth(*, reading_id: str) -> BirthInputCanonical:
    return BirthInputCanonical(
        birth_input_id=f"birth:{reading_id}",
        gender="unknown",
        calendar_type="solar",
        birth_date="2000-01-01",
        birth_time="12:00",
        timezone="Asia/Shanghai",
        year_pillar="甲戌",
        month_pillar="甲戌",
        day_pillar="庚辰",
        hour_pillar="壬午",
        input_quality="synthetic_fixture",
        pillar_fact_source="structurally_legal_hypothetical",
    )


def _graph_fact_fixture(*, profile_b: bool = False):
    reading_id = "rgm02-profile-b" if profile_b else "rgm02-graph"
    birth = _birth(reading_id=reading_id)
    if profile_b:
        birth = birth.model_copy(update={
            "year_pillar": "甲子",
            "month_pillar": "乙丑",
        })
    store = build_bazi_material_store(
        reading_id=reading_id,
        birth_input=birth,
        calendar=normalize_birth_input(birth),
    )
    source_bundle = (
        build_source_manifestation_evidence(store=store)
        if profile_b
        else None
    )
    graph = build_mingli_graph_from_material_store(
        store,
        source_manifestation_evidence=source_bundle,
    )
    node_refs = {
        node.node_id: _node_ref_from_graph_node(node)
        for node in graph.nodes
    }
    relation_keys = {
        edge.edge_id: RelationKey(
            scene_ref="scene:rgm02",
            relation_type=edge.edge_type.value,
            participant_refs=[
                node_refs[node_id] for node_id in edge.participant_node_ids
            ],
            directionality=edge.directionality,
            scope="natal",
        )
        for edge in graph.edges
    }
    source_hash = hashlib.sha256(
        f"{graph.graph_id}:{graph.source_store_id}".encode("utf-8")
    ).hexdigest()
    facts = compile_graph_relation_facts(
        graph=graph,
        relation_keys_by_edge_id=relation_keys,
        world_lineage="world:rgm02",
        source_snapshot_ref="snapshot:rgm02:natal:v1",
        source_snapshot_hash=source_hash,
    )
    return graph, node_refs, relation_keys, facts


def _node_ref_from_graph_node(node) -> NodeRef:
    slot = node.position.split("_", 1)[0]
    level = (
        "hidden_stem"
        if node.node_type.value == "hidden_stem"
        else node.node_type.value
    )
    return NodeRef(
        scene_ref="scene:rgm02",
        life_case_id="life-case:rgm02",
        chart_version_id="chart:rgm02:v1",
        world_id="world:rgm02",
        scope="natal",
        slot=slot,
        level=level,
        component=node.label,
    )


def _temporal_node(*, scope: str, slot: str, component: str) -> NodeRef:
    return NodeRef(
        scene_ref="scene:rgm02",
        life_case_id="life-case:rgm02",
        chart_version_id="chart:rgm02:v1",
        world_id="world:rgm02",
        scope=scope,
        slot=slot,
        level="branch",
        component=component,
        temporal_snapshot_ref=(
            "" if scope == "natal" else f"snapshot:rgm02:{scope}:v1"
        ),
    )


def _legality_node(*, level: str, slot: str, component: str) -> NodeRef:
    return NodeRef(
        scene_ref="scene:rgm02",
        life_case_id="life-case:rgm02",
        chart_version_id="chart:rgm02:v1",
        world_id="world:rgm02",
        scope="natal",
        slot=slot,
        level=level,
        component=component,
    )


def _fact(
    relation_key: RelationKey,
    *,
    state: MingliRelationState,
    stage: str,
):
    return relation_fact_from_key(
        relation_key=relation_key,
        relation_state=state,
        world_lineage="world:rgm02",
        source_snapshot_ref=f"snapshot:rgm02:{stage}:v1",
        source_snapshot_hash=hashlib.sha256(stage.encode("utf-8")).hexdigest(),
        producer_id="rgm02-test",
        producer_version="rgm02-test.v1",
        evidence_refs=[f"evidence:{stage}"],
        mechanism_ref="relation-fact-test",
        temporal_stage=stage,
        valid_from_stage=f"{stage}:v1",
    )


def test_lab_legality_policy_separates_direct_mediated_and_cross_layer_edges() -> None:
    visible_direct = _fact(
        RelationKey(
            scene_ref="scene:rgm02",
            relation_type="controls",
            participant_refs=[
                _legality_node(level="stem", slot="hour", component="庚"),
                _legality_node(level="stem", slot="month", component="乙"),
            ],
            directionality=RelationDirectionality.DIRECTED,
            scope="natal",
        ),
        state=MingliRelationState.STRUCTURAL,
        stage="natal",
    )
    hidden_potential = _fact(
        RelationKey(
            scene_ref="scene:rgm02",
            relation_type="controls",
            participant_refs=[
                _legality_node(
                    level="hidden_stem",
                    slot="hour",
                    component="庚",
                ),
                _legality_node(level="stem", slot="month", component="乙"),
            ],
            directionality=RelationDirectionality.DIRECTED,
            scope="natal",
        ),
        state=MingliRelationState.POTENTIAL,
        stage="natal",
    )
    illegal_cross_layer = _fact(
        RelationKey(
            scene_ref="scene:rgm02",
            relation_type="controls",
            participant_refs=[
                _legality_node(level="branch", slot="hour", component="申"),
                _legality_node(level="stem", slot="month", component="乙"),
            ],
            directionality=RelationDirectionality.DIRECTED,
            scope="natal",
        ),
        state=MingliRelationState.STRUCTURAL,
        stage="natal",
    )
    containment = _fact(
        RelationKey(
            scene_ref="scene:rgm02",
            relation_type="stores",
            participant_refs=[
                _legality_node(level="branch", slot="hour", component="申"),
                _legality_node(
                    level="hidden_stem",
                    slot="hour",
                    component="庚",
                ),
            ],
            directionality=RelationDirectionality.DIRECTED,
            scope="natal",
        ),
        state=MingliRelationState.STRUCTURAL,
        stage="natal",
    )
    positional = _fact(
        RelationKey(
            scene_ref="scene:rgm02",
            relation_type="position_link",
            participant_refs=[
                _legality_node(level="stem", slot="hour", component="庚"),
                _legality_node(level="branch", slot="hour", component="申"),
            ],
            directionality=RelationDirectionality.SYMMETRIC,
            scope="natal",
        ),
        state=MingliRelationState.STRUCTURAL,
        stage="natal",
    )

    direct_result = assess_relation_fact_legality(visible_direct)
    hidden_result = assess_relation_fact_legality(hidden_potential)
    illegal_result = assess_relation_fact_legality(illegal_cross_layer)
    containment_result = assess_relation_fact_legality(containment)
    positional_result = assess_relation_fact_legality(positional)

    assert direct_result.legality_class == "legal_direct"
    assert direct_result.default_path_eligible is True
    assert direct_result.provenance_status == "complete"
    assert hidden_result.legality_class == "unsupported"
    assert hidden_result.default_path_eligible is False
    assert "manifestation_or_mediation_evidence" in (
        hidden_result.missing_requirements
    )
    assert illegal_result.legality_class == "illegal_cross_layer"
    assert illegal_result.provenance_status == "illegal"
    assert illegal_result.inventory_visible is False
    assert containment_result.legality_class == "containment"
    assert containment_result.inventory_visible is True
    assert containment_result.default_path_eligible is False
    assert positional_result.legality_class == "positional"
    assert positional_result.inventory_visible is True
    assert positional_result.default_path_eligible is False


def test_graph_adapter_preserves_repeated_coordinates_and_hidden_explosion() -> None:
    graph, node_refs, relation_keys, facts = _graph_fact_fixture()
    repeated = [
        ref for ref in node_refs.values()
        if ref.component == "甲" and ref.level == "stem"
    ]
    hidden_edges = [
        edge for edge in graph.edges
        if any(
            node_refs[node_id].level == "hidden_stem"
            for node_id in edge.participant_node_ids
        )
    ]

    assert {item.slot for item in repeated} == {"year", "month"}
    assert len({item.node_ref for item in repeated}) == 2
    assert len(facts) == len(graph.edges)
    assert len({item.fact_key.fact_key for item in facts.values()}) == len(facts)
    assert hidden_edges
    assert all(
        any(
            participant.level == "hidden_stem"
            for participant in facts[
                relation_keys[edge.edge_id].relation_key
            ].fact_key.participant_refs
        )
        for edge in hidden_edges
    )


def test_profile_b_edges_are_wrapped_as_evidence_without_effect_authority() -> None:
    graph, _, keys, facts = _graph_fact_fixture(profile_b=True)
    profile_edges = [
        edge
        for edge in graph.edges
        if edge.attributes.get("evidence_family")
        == "bounded_source_manifestation_profile_b"
    ]

    assert profile_edges
    for edge in profile_edges:
        fact = facts[keys[edge.edge_id].relation_key]
        assert fact.fact_key.school_profile_id
        assert fact.fact_key.school_profile_version
        assert fact.effect_resolution_ref == ""
        assert fact.disclosure_manifest["effect"] == "not_available"


def test_temporal_identity_n_ary_authority_and_joint_activation_are_distinct() -> None:
    natal = _temporal_node(scope="natal", slot="month", component="午")
    luck = _temporal_node(scope="luck", slot="luck", component="子")
    year = _temporal_node(scope="year", slot="year", component="午")
    natal_key = RelationKey(
        scene_ref="scene:rgm02",
        relation_type="clashes",
        participant_refs=[natal, luck],
        directionality=RelationDirectionality.SYMMETRIC,
        scope="luck",
    )
    joint_key = RelationKey(
        scene_ref="scene:rgm02",
        relation_type="joint_activation",
        participant_refs=[natal, luck, year],
        directionality=RelationDirectionality.SYMMETRIC,
        scope="year",
    )
    luck_fact = _fact(
        natal_key,
        state=MingliRelationState.TIME_ACTIVATED,
        stage="luck",
    )
    joint_fact = _fact(
        joint_key,
        state=MingliRelationState.TIME_ACTIVATED,
        stage="year",
    )

    assert luck_fact.activation_state == RelationActivationState.TEMPORALLY_ACTIVATED
    assert joint_fact.activation_state == RelationActivationState.TEMPORALLY_ACTIVATED
    assert len(joint_fact.fact_key.participant_refs) == 3
    assert len(joint_fact.fact_key.participant_roles) == 3
    assert luck_fact.fact_key.fact_key != joint_fact.fact_key.fact_key


def test_withdraw_restore_and_replay_keep_append_only_stable_identity() -> None:
    key = RelationKey(
        scene_ref="scene:rgm02",
        relation_type="clashes",
        participant_refs=[
            _temporal_node(scope="natal", slot="month", component="午"),
            _temporal_node(scope="luck", slot="luck", component="子"),
        ],
        directionality=RelationDirectionality.SYMMETRIC,
        scope="luck",
    )
    first = _fact(key, state=MingliRelationState.TIME_ACTIVATED, stage="luck")
    replay = _fact(key, state=MingliRelationState.TIME_ACTIVATED, stage="luck")
    withdrawn = withdraw_relation_fact(
        first,
        withdrawn_by_ref="epoch:luck-ended",
        valid_to_stage="luck:v1:end",
    )
    restored = restore_relation_fact(
        withdrawn,
        source_snapshot_ref="snapshot:rgm02:natal-restored:v2",
        source_snapshot_hash=hashlib.sha256(b"natal-restored").hexdigest(),
        evidence_refs=["evidence:natal-restored"],
        valid_from_stage="natal:restored:v2",
    )

    assert first.replay_hash == replay.replay_hash
    assert first.revision_ref == replay.revision_ref
    assert withdrawn.revision_number == 2
    assert withdrawn.supersedes_ref == first.revision_ref
    assert withdrawn.withdrawn_by_ref == "epoch:luck-ended"
    assert restored.revision_number == 3
    assert restored.supersedes_ref == withdrawn.revision_ref
    assert restored.withdrawn_by_ref == ""
    assert restored.valid_to_stage == ""
    assert restored.activation_state == RelationActivationState.NATAL_PRESENT


def test_effective_fact_state_is_unrepresentable_and_legacy_effect_is_downgraded() -> None:
    with pytest.raises(ValueError):
        RelationFactState("EFFECTIVE")

    key = RelationKey(
        scene_ref="scene:rgm02",
        relation_type="generates",
        participant_refs=[
            _temporal_node(scope="natal", slot="year", component="甲"),
            _temporal_node(scope="natal", slot="month", component="丁"),
        ],
        directionality=RelationDirectionality.DIRECTED,
    )
    legacy = RelationAssertion.model_validate({
        "version": "deepbazi.relation_assertion.v1",
        "relation_key": key.model_dump(mode="json"),
        "assertion_version": "legacy:v1",
        "status": AssertionLifecycle.COMMITTED.value,
        "provenance": ProvenanceRecord(
            source="legacy_exact_import",
            producer_id="legacy-importer",
            producer_version="legacy.v1",
            evidence_refs=["legacy:evidence"],
            source_refs=["legacy:source"],
            created_at="2026-07-27T00:00:00+00:00",
        ).model_dump(mode="json"),
        "relation_state": MingliRelationState.EFFECTIVE.value,
        "mechanism_ref": "legacy_exact_relation",
    })
    fact = adapt_legacy_relation_assertion(
        assertion=legacy,
        world_lineage="world:rgm02",
        source_snapshot_ref="snapshot:legacy:v1",
        source_snapshot_hash=hashlib.sha256(b"legacy").hexdigest(),
    )

    assert fact.fact_state != RelationFactState.RELATION_CANDIDATE
    assert fact.effect_resolution_ref == ""
    assert fact.disclosure_manifest["legacy_assertion"] == (
        "read_only_not_professional_authority"
    )


def test_onecanvas_consumes_relation_fact_revisions_for_natal_and_timing() -> None:
    case_id = "case-rgm02-onecanvas"
    user_id = "user-rgm02-onecanvas"
    store = MemoryAgentCaseStore()
    store.save(
        case_id=case_id,
        user_id=user_id,
        profile_id=None,
        payload=_case_payload(case_id),
    )

    payload = ReadOnlySixPillarCanvasService(case_store=store).issue(
        case_id=case_id,
        participant_id=user_id,
        account_role="practitioner",
    )
    natal = payload["stages"]["natal"]["spec"]["relations"]
    luck_added_refs = {
        item["target_ref"]
        for item in payload["stages"]["luck"]["diff"]["added_relations"]
    }
    luck = [
        item
        for item in payload["stages"]["luck"]["spec"]["relations"]
        if item["relation_ref"] in luck_added_refs
    ]

    assert natal and all(item["relation_fact_ref"] for item in natal)
    assert luck and all(item["relation_fact_ref"] for item in luck)
    assert {
        item["professional_state"] for item in natal
    }.issubset({"fact_present", "structural_candidate", "legacy_read_only"})
    assert any(
        item["professional_state"] == "temporally_activated"
        for item in luck
    )
