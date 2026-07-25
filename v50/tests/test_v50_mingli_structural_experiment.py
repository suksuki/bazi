from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.product_store import MemoryProductStore
from core.contracts import BirthInputCanonical
from core.contracts.professional_review import ProfessionalReviewOverlay
from core.life_case.contracts import (
    ChartVersionRef,
    FormalInsight,
    InsightBasis,
    InsightProvenance,
    InsightUncertainty,
    LifeCase,
    ReasoningPathStep,
)
from core.mingli_agent import compile_chart_world
from core.mingli_agent.contracts import (
    CognitiveHypothesis,
    DiscriminatingProbe,
    EpistemicReviewReceipt,
    MingliCognitiveDraft,
    MingliCognitiveRecord,
    SalientPhenomenon,
    WorkPathReasoning,
)
from core.mingli_agent.path_bridge import bind_structured_path_candidate
from experience.experiments import (
    MechanismEdge,
    MechanismNode,
    MechanismPath,
    PillarVisual,
    apply_single_node_ablation,
    create_sandbox_state,
    issue_mechanism_snapshot,
    restore_sandbox,
)


def _birth() -> BirthInputCanonical:
    return BirthInputCanonical(
        birth_input_id="birth-structural-experiment",
        name="结构实验",
        gender="male",
        calendar_type="solar",
        birth_date="1987-05-12",
        birth_time="18:00",
        birth_location="上海",
        timezone="Asia/Shanghai",
        year_pillar="丁巳",
        month_pillar="乙巳",
        day_pillar="乙丑",
        hour_pillar="乙酉",
        input_quality="confirmed",
    )


def _case_payload(case_id: str) -> dict[str, object]:
    birth = _birth()
    world = compile_chart_world(reading_id=case_id, birth_input=birth)
    path_fact = next(item for item in world.facts if item.category == "candidate_path")
    now = datetime.now(timezone.utc).isoformat()
    record_id = "record-structural-experiment"
    probe = DiscriminatingProbe(
        probe_id="probe-1",
        question="现实中你更常主动输出，还是等待环境支持？",
        purpose="区分输出路径是否稳定",
        distinguishes_hypothesis_refs=["h1"],
        options=["主动输出", "等待支持"],
        expected_updates={"主动输出": "strengthen", "等待支持": "weaken"},
    )
    work_path, _ = bind_structured_path_candidate(
        work_path=WorkPathReasoning(
            path_statement="已批准路径用于本次结构实验。",
            source=["结构起点"],
            transformations=["关系转换"],
            target=["结构目标"],
            body_function_relation="只作为已批准路径读取。",
            closure="conditional",
            success_conditions=["路径关系保留"],
            failure_conditions=["关键关系断开"],
            evidence_refs=[path_fact.fact_id],
            origin="system_enumerated",
            candidate_path_refs=[path_fact.fact_id],
        ),
        world=world,
    )
    cognition = MingliCognitiveDraft(
        first_look="先看丁火与巳酉丑之间的结构连接。",
        whole_chart_thesis="当前主假设是输出路径能否承接金局压力。",
        salient_phenomena=[
            SalientPhenomenon(
                phenomenon_id="s1",
                observation="巳酉丑形成结构连接",
                why_it_matters="决定路径能否闭合",
                evidence_refs=[path_fact.fact_id],
            )
        ],
        hypotheses=[
            CognitiveHypothesis(
                hypothesis_id="h1",
                name="输出承压",
                thesis="输出节点参与承接结构压力。",
                rank=1,
                status="primary",
                supporting_evidence_refs=[path_fact.fact_id],
                confidence="medium",
            )
        ],
        selected_hypothesis_id="h1",
        work_path=work_path,
        useful_god_reasoning=[],
        portrait=[],
        prior_predictions=[],
        next_probe=probe,
        unresolved_questions=["现实含义仍需专业推理"],
        evidence_refs=[path_fact.fact_id],
    )
    review = EpistemicReviewReceipt(
        passed=True,
        fact_traceability_rate=1.0,
        model="fixture-model",
        disposition="reliable",
        commit_eligible=True,
        gate_version="fixture-gate.v1",
    )
    record = MingliCognitiveRecord(
        record_id=record_id,
        case_id=case_id,
        world_id=world.world_id,
        created_at=now,
        model="fixture-model",
        cognition=cognition,
        review=review,
        reliability_disposition="reliable",
    )
    professional_overlay = ProfessionalReviewOverlay(
        overlay_id=f"professional-review-fixture-{case_id}",
        cognitive_record_ref=record_id,
        assertions_hash="c" * 64,
        raw_output_hash="d" * 64,
        raw_source_kind="fixture_raw_payload",
        persistence_status="persisted",
        professional_release_status="passed",
        reviewer="fixture-professional-review",
        created_at=now,
    )
    insight = FormalInsight(
        insight_id="insight-structural-experiment",
        case_id=case_id,
        case_version="v1",
        type="baseline",
        claim="输出路径能否保持闭合，是当前整盘认知的核心。",
        scope={"temporal_scope": "natal"},
        basis=InsightBasis(chart_fact_refs=[path_fact.fact_id]),
        reasoning_path=[
            ReasoningPathStep(
                premise="系统已枚举并由认知记录选中该候选路径",
                conclusion="允许把它作为结构实验对象",
                source_refs=[path_fact.fact_id],
            )
        ],
        conditions=["路径中的关系成立"],
        counter_signals=["路径在关键节点处断开"],
        uncertainty=InsightUncertainty(level="medium", reasons=["现实含义仍需验证"]),
        provenance=InsightProvenance(
            reasoner_id="fixture-reasoner",
            reasoner_version="v1",
            theory_version="fixture-theory",
            model_version="fixture-model",
            context_hash="a" * 64,
            generated_at=now,
            source_record_id=record_id,
        ),
        status="committed",
        epistemic_state="reliable",
        source_review_gate="fixture-gate.v1",
        persistence_status="persisted",
        professional_release_status="passed",
        professional_review_overlay=professional_overlay,
    )
    life_case = LifeCase(
        life_case_id="life-case-structural-experiment",
        case_id=case_id,
        case_version="v1",
        chart_version=ChartVersionRef(
            version_id="chart-v1",
            world_id=world.world_id,
            chart_hash="b" * 64,
            created_at=now,
        ),
        baseline_insight=insight,
        created_at=now,
        updated_at=now,
    )
    return {
        "case_id": case_id,
        "birth_input": birth.model_dump(mode="json"),
        "world": world.model_dump(mode="json"),
        "record": record.model_dump(mode="json"),
        "life_case": life_case.model_dump(mode="json"),
    }


def _qualified_path_evidence() -> dict[str, object]:
    return {
        "segment_validity": "complete",
        "direction_coherence": "coherent",
        "temporal_coherence": "not_evaluated",
        "root_support": "not_evaluated",
        "reveal_support": "not_evaluated",
        "blocking": "none_detected",
        "closure": "closed",
        "provenance_quality": "high",
        "reason_refs": ["fixture:path-evidence"],
    }


def test_single_node_ablation_invalidates_only_incident_edges_and_paths() -> None:
    now = datetime.now(timezone.utc)
    nodes = [
        MechanismNode(node_id=node_id, label=node_id.upper(), node_type="stem", visual_anchor_id=node_id)
        for node_id in ("a", "b", "c", "d")
    ]
    edges = [
        MechanismEdge(edge_id="ab", from_node_id="a", to_node_id="b", relation_type="generates", path_eligibility="eligible", eligibility_reason_refs=["fixture:eligible"]),
        MechanismEdge(edge_id="bc", from_node_id="b", to_node_id="c", relation_type="controls", path_eligibility="eligible", eligibility_reason_refs=["fixture:eligible"]),
        MechanismEdge(edge_id="ad", from_node_id="a", to_node_id="d", relation_type="generates", path_eligibility="eligible", eligibility_reason_refs=["fixture:eligible"]),
    ]
    pillars = [
        PillarVisual(
            pillar_id=f"pillar-{index}",
            label=label,
            stem="甲",
            branch="子",
            stem_node_id="a",
            branch_node_id="b",
            visual_anchor_id=f"pillar-{index}",
        )
        for index, label in enumerate(("年柱", "月柱", "日柱", "时柱"))
    ]
    approved = MechanismPath(
        path_ref="approved",
        path_kind="approved",
        display_label="A → B → C",
        node_ids=["a", "b", "c"],
        edge_ids=["ab", "bc"],
        relation_types=["generates", "controls"],
        validation_state="qualified",
        evidence=_qualified_path_evidence(),
        claim_refs=["claim-1"],
    )
    competing = MechanismPath(
        path_ref="competing",
        path_kind="competing",
        display_label="A → D",
        node_ids=["a", "d"],
        edge_ids=["ad"],
        relation_types=["generates"],
        validation_state="qualified",
        evidence=_qualified_path_evidence(),
    )
    snapshot = issue_mechanism_snapshot(
        snapshot_id="snapshot-1",
        case_id="case-1",
        chart_version="chart-v1",
        life_case_version="life-v1",
        cognitive_record_id="record-v1",
        pillars=pillars,
        nodes=nodes,
        edges=edges,
        approved_paths=[approved],
        competing_paths=[competing],
        issued_at=now,
    )
    sandbox = create_sandbox_state(
        participant_run_id="run-1",
        snapshot=snapshot,
        predicted_key_node_id="b",
    )
    modified, result = apply_single_node_ablation(snapshot=snapshot, sandbox=sandbox, node_id="b")
    restored = restore_sandbox(modified)

    assert result.deterministic_changes.invalidated_edges == ["ab", "bc"]
    assert result.deterministic_changes.affected_paths == ["approved"]
    assert result.deterministic_changes.unaffected_paths == ["competing"]
    assert result.deterministic_changes.invalidated_claim_refs == ["claim-1"]
    assert result.reasoning_required is True
    assert result.writes_life_case is False
    assert restored.status == "restored"
    assert restored.comparison_mode == "baseline"


def test_topic01_api_runs_private_experiment_and_never_modifies_life_case(monkeypatch) -> None:
    monkeypatch.delenv("V50_DATABASE_URL", raising=False)
    product_store = MemoryProductStore()
    case_store = MemoryAgentCaseStore()
    app = create_product_app(product_store=product_store, agent_case_store=case_store)
    client = TestClient(app)
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "结构实验用户",
            "email": "structure-lab@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200
    user_id = registered.json()["account"]["user_id"]
    case_id = "case-topic01-structural"
    payload = _case_payload(case_id)
    case_store.save(case_id=case_id, user_id=user_id, profile_id=None, payload=payload)
    life_case_before = deepcopy(case_store.get(case_id=case_id, user_id=user_id)["life_case"])

    created = client.post(
        "/api/v50/theater/sessions",
        json={"topic_id": "topic-01-irreplaceable-node", "topic_version": "1.0.0", "mode": "solo"},
    )
    assert created.status_code == 200, created.text
    session_id = created.json()["session"]["session_id"]
    joined = client.post(
        f"/api/v50/theater/sessions/{session_id}/join",
        json={"case_id": case_id, "disclosure_level": "approved_insights"},
    )
    assert joined.status_code == 200, joined.text
    run_id = joined.json()["participant_run"]["participant_run_id"]
    token = joined.json()["access_token"]
    advanced = client.post(
        f"/api/v50/theater/sessions/{session_id}/participant/advance",
        json={"participant_run_id": run_id, "access_token": token, "event": "next"},
    )
    assert advanced.status_code == 200, advanced.text
    query = {"participant_run_id": run_id, "access_token": token}
    loaded = client.get(
        f"/api/v50/theater/sessions/{session_id}/participant/experiment",
        params=query,
    )
    assert loaded.status_code == 200, loaded.text
    body = loaded.json()
    assert body["snapshot"]["approved_paths"]
    assert body["visual_spec"]["stable_layout"] is True
    node_id = body["snapshot"]["approved_paths"][0]["node_ids"][0]
    predicted = client.post(
        f"/api/v50/theater/sessions/{session_id}/participant/experiment/predict",
        json={**query, "node_id": node_id},
    )
    ablated = client.post(
        f"/api/v50/theater/sessions/{session_id}/participant/experiment/ablate",
        json={**query, "node_id": node_id},
    )
    restored = client.post(
        f"/api/v50/theater/sessions/{session_id}/participant/experiment/restore",
        json=query,
    )
    repeated_ablation = client.post(
        f"/api/v50/theater/sessions/{session_id}/participant/experiment/ablate",
        json={**query, "node_id": node_id},
    )
    saved = client.post(
        f"/api/v50/theater/sessions/{session_id}/participant/experiment/save",
        json={**query, "observation": "这条路径在起点处断开。", "open_question": "现实中如何表现？"},
    )

    assert predicted.status_code == 200, predicted.text
    assert ablated.status_code == 200, ablated.text
    assert ablated.json()["sandbox_result"]["authority"] == "deterministic_structure"
    assert ablated.json()["sandbox_result"]["reasoning_required"] is True
    assert restored.status_code == 200, restored.text
    assert restored.json()["sandbox_state"]["status"] == "restored"
    assert repeated_ablation.status_code == 409
    assert repeated_ablation.json()["detail"] == "single_node_ablation_already_completed"
    assert saved.status_code == 200, saved.text
    assert saved.json()["topic_exploration"]["writes_life_case"] is False
    assert saved.json()["topic_exploration"]["restored_original"] is True
    assert saved.json()["llm_used"] is False
    assert saved.json()["reasoner_used"] is False
    assert case_store.get(case_id=case_id, user_id=user_id)["life_case"] == life_case_before
