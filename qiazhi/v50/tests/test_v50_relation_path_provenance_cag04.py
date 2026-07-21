from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.graph import (
    AssertionLifecycle,
    NodeRef,
    PathAssertion,
    PathKey,
    ProvenanceRecord,
    RelationAssertion,
    RelationDirectionality,
    RelationKey,
    canonical_scene_scope_ref,
)
from core.life_case import (
    LifeCase,
    active_path_assertions,
    active_relation_assertions,
    append_path_assertion,
    append_relation_assertion,
    commit_baseline_life_case,
    relation_path_assertions_for_case,
)
from core.mingli_agent.contracts import ChartWorldInstance
from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.canonical_scene import CanonicalSceneOwner
from product.canvas_projection import ReadOnlySixPillarCanvasService
from product.product_store import MemoryProductStore
from product.theater_experiment import _snapshot_from_case_row
from test_v50_mingli_structural_experiment import _case_payload


ROOT = Path(__file__).resolve().parents[1]


def _node(
    component: str,
    *,
    scope: str = "natal",
    slot: str = "year",
    level: str = "stem",
    snapshot: str = "",
) -> NodeRef:
    return NodeRef(
        scene_ref="scene-scope:test",
        life_case_id="life-case-test",
        chart_version_id="chart-version-test",
        world_id="world-test",
        scope=scope,
        slot=slot,
        level=level,
        component=component,
        temporal_snapshot_ref=snapshot,
    )


def _provenance(*, producer_version: str, created_at: str = "2026-07-21T00:00:00+00:00") -> ProvenanceRecord:
    return ProvenanceRecord(
        source="reasoner_commit",
        producer_id="reasoner-test",
        producer_version=producer_version,
        evidence_refs=["fact-1"],
        source_refs=["insight-1"],
        created_at=created_at,
    )


def _relation_key(*, directionality: RelationDirectionality, participants: list[NodeRef]) -> RelationKey:
    return RelationKey(
        scene_ref="scene-scope:test",
        relation_type="generates" if directionality == RelationDirectionality.DIRECTED else "clashes",
        participant_refs=participants,
        directionality=directionality,
    )


def test_relation_key_normalizes_symmetric_but_preserves_directed_order() -> None:
    left = _node("甲")
    right = _node("丁", slot="month")

    symmetric_ab = _relation_key(
        directionality=RelationDirectionality.SYMMETRIC,
        participants=[left, right],
    )
    symmetric_ba = _relation_key(
        directionality=RelationDirectionality.SYMMETRIC,
        participants=[right, left],
    )
    directed_ab = _relation_key(
        directionality=RelationDirectionality.DIRECTED,
        participants=[left, right],
    )
    directed_ba = _relation_key(
        directionality=RelationDirectionality.DIRECTED,
        participants=[right, left],
    )

    assert symmetric_ab.relation_key == symmetric_ba.relation_key
    assert directed_ab.relation_key != directed_ba.relation_key
    assert directed_ab == RelationKey.model_validate(directed_ab.model_dump(mode="json"))


def test_hyperrelation_and_temporal_node_identities_are_stable_and_distinct() -> None:
    three = [_node("巳"), _node("酉", slot="month"), _node("丑", slot="day")]
    relation_a = RelationKey(
        scene_ref="scene-scope:test",
        relation_type="forms_triple_combination",
        participant_refs=three,
        directionality=RelationDirectionality.SYMMETRIC,
    )
    relation_b = RelationKey(
        scene_ref="scene-scope:test",
        relation_type="forms_triple_combination",
        participant_refs=list(reversed(three)),
        directionality=RelationDirectionality.SYMMETRIC,
    )
    natal = _node("甲")
    luck = _node("甲", scope="luck", slot="luck", snapshot="snapshot-luck-1")
    year = _node("甲", scope="year", slot="year", snapshot="snapshot-year-1")

    assert relation_a.arity == 3
    assert relation_a.relation_key == relation_b.relation_key
    assert len({natal.node_ref, luck.node_ref, year.node_ref}) == 3


def test_assertion_history_is_append_only_and_key_survives_producer_upgrade() -> None:
    relation_key = _relation_key(
        directionality=RelationDirectionality.DIRECTED,
        participants=[_node("甲"), _node("丁", slot="month")],
    )
    old = RelationAssertion(
        relation_key=relation_key,
        assertion_version="case-v1:baseline",
        status=AssertionLifecycle.COMMITTED,
        provenance=_provenance(producer_version="graph-v1"),
    )
    new = RelationAssertion(
        relation_key=relation_key,
        assertion_version="case-v2:baseline",
        status=AssertionLifecycle.COMMITTED,
        provenance=_provenance(producer_version="graph-v2"),
        supersedes=old.assertion_id,
    )
    history = append_relation_assertion([old], new)

    assert old.relation_key.relation_key == new.relation_key.relation_key
    assert old.assertion_id != new.assertion_id
    assert history == [old, new]
    assert active_relation_assertions(history) == [new]

    path_key = PathKey(
        scene_ref="scene-scope:test",
        node_refs=relation_key.participant_refs,
        relation_keys=[relation_key],
    )
    old_path = PathAssertion(
        path_key=path_key,
        assertion_version="case-v1:baseline",
        status=AssertionLifecycle.COMMITTED,
        provenance=_provenance(producer_version="path-v1"),
    )
    new_path = PathAssertion(
        path_key=path_key,
        assertion_version="case-v2:baseline",
        status=AssertionLifecycle.COMMITTED,
        provenance=_provenance(producer_version="path-v2"),
        supersedes=old_path.assertion_id,
    )
    path_history = append_path_assertion([old_path], new_path)
    assert path_history == [old_path, new_path]
    assert active_path_assertions(path_history) == [new_path]


def test_candidate_provenance_cannot_masquerade_as_formal_assertion() -> None:
    relation_key = _relation_key(
        directionality=RelationDirectionality.DIRECTED,
        participants=[_node("甲"), _node("丁", slot="month")],
    )
    graph_candidate = ProvenanceRecord(
        source="graph_candidate",
        producer_id="graph-v1",
        producer_version="graph-v1",
        evidence_refs=["fact-1"],
        source_refs=["graph-1"],
        created_at="2026-07-21T00:00:00+00:00",
    )

    with pytest.raises(ValueError, match="graph_candidate_provenance_requires_candidate_status"):
        RelationAssertion(
            relation_key=relation_key,
            assertion_version="case-v1:baseline",
            status=AssertionLifecycle.COMMITTED,
            provenance=graph_candidate,
        )
    with pytest.raises(ValueError, match="candidate_assertion_requires_graph_candidate_provenance"):
        PathAssertion(
            path_key=PathKey(
                scene_ref="scene-scope:test",
                node_refs=relation_key.participant_refs,
                relation_keys=[relation_key],
            ),
            assertion_version="case-v1:candidate",
            status=AssertionLifecycle.CANDIDATE,
            provenance=_provenance(producer_version="reasoner-v1"),
        )


def test_life_case_rejects_dangling_or_out_of_order_assertion_history() -> None:
    payload = _case_payload("case-cag04-invalid-history")
    world = ChartWorldInstance.model_validate(payload["world"])
    legacy_case = LifeCase.model_validate(payload["life_case"])
    committed, _ = commit_baseline_life_case(
        insight=legacy_case.baseline_insight,
        world=world,
        profile_id=None,
    )
    old = committed.relation_assertions[0]
    dangling = RelationAssertion(
        relation_key=old.relation_key,
        assertion_version="case-v2:baseline",
        status=AssertionLifecycle.COMMITTED,
        provenance=_provenance(producer_version="reasoner-v2"),
        supersedes="missing-assertion",
    )
    invalid = committed.model_dump(mode="json")
    invalid["relation_assertions"] = [
        old.model_dump(mode="json"),
        dangling.model_dump(mode="json"),
    ]
    with pytest.raises(ValueError, match="assertion_supersedes_unknown_history"):
        LifeCase.model_validate(invalid)

    replacement = RelationAssertion(
        relation_key=old.relation_key,
        assertion_version="case-v2:baseline",
        status=AssertionLifecycle.COMMITTED,
        provenance=_provenance(producer_version="reasoner-v2"),
        supersedes=old.assertion_id,
    )
    invalid["relation_assertions"] = [
        replacement.model_dump(mode="json"),
        old.model_dump(mode="json"),
    ]
    with pytest.raises(ValueError, match="assertion_supersedes_non_prior_history"):
        LifeCase.model_validate(invalid)


def test_life_case_rejects_candidate_assertion_and_commit_owns_formal_assertions() -> None:
    payload = _case_payload("case-cag04-commit")
    world = ChartWorldInstance.model_validate(payload["world"])
    legacy_case = LifeCase.model_validate(payload["life_case"])
    committed, receipt = commit_baseline_life_case(
        insight=legacy_case.baseline_insight,
        world=world,
        profile_id=None,
    )

    assert receipt.passed is True
    assert committed.relation_assertions
    assert committed.path_assertions
    assert all(item.status == AssertionLifecycle.COMMITTED for item in committed.relation_assertions)
    assert all(item.status == AssertionLifecycle.COMMITTED for item in committed.path_assertions)

    candidate = RelationAssertion(
        relation_key=committed.relation_assertions[0].relation_key,
        assertion_version="case-v1:candidate",
        status=AssertionLifecycle.CANDIDATE,
        provenance=ProvenanceRecord(
            source="graph_candidate",
            producer_id="graph-v1",
            producer_version="graph-v1",
            evidence_refs=["fact-1"],
            source_refs=["graph-1"],
            created_at="2026-07-21T00:00:00+00:00",
        ),
    )
    invalid = committed.model_dump(mode="json")
    invalid["relation_assertions"] = [candidate.model_dump(mode="json")]
    with pytest.raises(ValueError, match="life_case_cannot_own_candidate_relation"):
        LifeCase.model_validate(invalid)


def test_legacy_case_migrates_only_exact_refs_and_marks_unresolved_without_guessing() -> None:
    payload = _case_payload("case-cag04-legacy")
    life_case = LifeCase.model_validate(payload["life_case"])
    world = ChartWorldInstance.model_validate(payload["world"])

    relations, paths = relation_path_assertions_for_case(life_case=life_case, world=world)
    assert relations
    assert len(paths) == 1
    assert paths[0].status == AssertionLifecycle.COMMITTED
    assert paths[0].provenance.source == "legacy_exact_import"

    unresolved_payload = deepcopy(payload["life_case"])
    baseline = unresolved_payload["baseline_insight"]
    baseline["basis"]["chart_fact_refs"] = ["missing-fact"]
    for step in baseline["reasoning_path"]:
        step["source_refs"] = ["missing-fact"]
    unresolved_case = LifeCase.model_validate(unresolved_payload)
    unresolved_relations, unresolved_paths = relation_path_assertions_for_case(
        life_case=unresolved_case,
        world=world,
    )
    assert unresolved_relations == []
    assert len(unresolved_paths) == 1
    assert unresolved_paths[0].status == AssertionLifecycle.LEGACY_UNRESOLVED
    assert unresolved_paths[0].path_key is None
    assert unresolved_paths[0].unresolved_reason


def test_canonical_scene_canvas_and_theater_share_one_formal_path_identity() -> None:
    case_id = "case-cag04-cross-projection"
    user_id = "user-cag04"
    payload = _case_payload(case_id)
    store = MemoryAgentCaseStore()
    store.save(case_id=case_id, user_id=user_id, profile_id=None, payload=payload)

    owner = CanonicalSceneOwner(case_store=store)
    onecanvas = owner.issue_projection(
        case_id=case_id,
        participant_id=user_id,
        account_role="member",
        projection_kind="onecanvas",
    )
    abu = owner.issue_projection(
        case_id=case_id,
        participant_id=user_id,
        account_role="member",
        projection_kind="abu",
    )
    formal_path = onecanvas.payload["path_assertions"][0]
    assert formal_path == abu.payload["path_assertions"][0]

    canvas = ReadOnlySixPillarCanvasService(case_store=store).issue(
        case_id=case_id,
        participant_id=user_id,
        account_role="member",
    )
    canvas_path = canvas["stages"]["natal"]["spec"]["paths"][0]
    theater = _snapshot_from_case_row(case_id=case_id, row=payload)

    assert canvas_path["path_ref"] == formal_path["path_ref"]
    assert theater.approved_paths[0].path_ref == formal_path["path_ref"]
    assert set(canvas_path["relation_refs"]) == set(formal_path["relation_refs"])
    assert formal_path["assertion_ref"] in canvas_path["trace"]["commitment_refs"]


def test_canonical_scene_cache_invalidates_when_formal_assertion_history_changes() -> None:
    case_id = "case-cag04-cache-revision"
    user_id = "user-cag04-cache-revision"
    payload = _case_payload(case_id)
    store = MemoryAgentCaseStore()
    store.save(case_id=case_id, user_id=user_id, profile_id=None, payload=payload)
    owner = CanonicalSceneOwner(case_store=store)
    before = owner.issue_projection(
        case_id=case_id,
        participant_id=user_id,
        account_role="member",
        projection_kind="onecanvas",
    )

    life_case = LifeCase.model_validate(payload["life_case"])
    world = ChartWorldInstance.model_validate(payload["world"])
    relation_history, path_history = relation_path_assertions_for_case(
        life_case=life_case,
        world=world,
    )
    old_path = path_history[0]
    replacement = PathAssertion(
        path_key=old_path.path_key,
        assertion_version=f"{life_case.case_version}:baseline-revision-2",
        status=AssertionLifecycle.COMMITTED,
        provenance=_provenance(
            producer_version="reasoner-revision-2",
            created_at="2026-07-21T01:00:00+00:00",
        ),
        supersedes=old_path.assertion_id,
        statement="同一逻辑路径的新正式版本",
    )
    revised_case = life_case.model_copy(update={
        "relation_assertions": relation_history,
        "path_assertions": [*path_history, replacement],
    })
    revised_payload = deepcopy(payload)
    revised_payload["life_case"] = revised_case.model_dump(mode="json")
    store.save(
        case_id=case_id,
        user_id=user_id,
        profile_id=None,
        payload=revised_payload,
    )

    after = owner.issue_projection(
        case_id=case_id,
        participant_id=user_id,
        account_role="member",
        projection_kind="onecanvas",
    )
    assert after.projection_hash != before.projection_hash
    assert after.payload["path_assertions"][0]["assertion_ref"] == replacement.assertion_id
    assert old_path.assertion_id not in after.semantic_refs


def test_role_disclosure_and_client_boundary_do_not_reintroduce_formal_paths() -> None:
    case_id = "case-cag04-client-boundary"
    payload = _case_payload(case_id)
    store = MemoryAgentCaseStore()
    product_store = MemoryProductStore()
    app = create_product_app(product_store=product_store, agent_case_store=store)
    client = TestClient(app)
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "CAG04",
            "email": "cag04@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    user_id = registered.json()["account"]["user_id"]
    store.save(case_id=case_id, user_id=user_id, profile_id=None, payload=payload)
    owner = CanonicalSceneOwner(case_store=store)

    guest = owner.issue_projection(
        case_id=case_id,
        participant_id=user_id,
        account_role="guest",
        projection_kind="onecanvas",
    )
    member = owner.issue_projection(
        case_id=case_id,
        participant_id=user_id,
        account_role="member",
        projection_kind="onecanvas",
    )
    assert guest.payload["path_assertions"] == []
    assert member.payload["path_assertions"]

    attempted = client.post(
        f"/api/v50/experience/cases/{case_id}/canvas",
        json={
            "relation_assertions": [{"status": "committed"}],
            "path_assertions": [{"status": "committed"}],
        },
    )
    assert attempted.status_code in {404, 405}
    unchanged = store.get(case_id=case_id, user_id=user_id)
    assert unchanged is not None
    assert unchanged["life_case"] == payload["life_case"]


def test_anonymous_and_fuzzy_path_reconnection_code_is_removed() -> None:
    canvas_source = (ROOT / "apps/product/canvas_projection.py").read_text(encoding="utf-8")
    theater_source = (ROOT / "apps/product/theater_experiment.py").read_text(encoding="utf-8")

    assert "_edge_matches_fact" not in canvas_source
    assert "path-committed-" not in canvas_source
    assert "_legacy_path_signature" not in theater_source
    assert "abs(candidate.path_score" not in theater_source
    assert "committed_path_not_exactly_available" in theater_source
