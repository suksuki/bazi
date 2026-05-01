from __future__ import annotations

from fastapi.testclient import TestClient

from v20.api.runtime import run_runtime_from_pillars
from v20.features.schema import FeatureLayer
from v20.knowledge.catalog import build_knowledge_catalog
from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.ranking import KnowledgeRetrievalPolicy, knowledge_retrieval_manifest, rank_knowledge_units
from v20.knowledge.retrieval import retrieve_knowledge
from v20.server import app


def test_v20_knowledge_retrieval_policy_reorders_reviewed_units_only() -> None:
    units = default_knowledge_units()
    boosted = rank_knowledge_units(
        units,
        KnowledgeRetrievalPolicy(
            policy_id="test.boost.health",
            domain_weights={"health": 0.6},
            source="test",
            status="draft",
        ),
    )

    assert boosted[0].domain == "health"
    assert {unit.knowledge_id for unit in boosted} == {unit.knowledge_id for unit in units}
    assert all(unit.status == "reviewed" for unit in boosted)


def test_v20_knowledge_retrieval_policy_manifest_blocks_rule_truth() -> None:
    manifest = knowledge_retrieval_manifest()

    assert manifest["runtime_mutation"] is False
    assert "direct_rule_truth" in manifest["blocked_learning_outputs"]
    assert "EMBEDDING_RECALL_MUST_PASS_REVIEW_FILTER" in manifest["guardrails"]


def test_v20_knowledge_retrieval_policy_endpoint_and_runtime_context_only() -> None:
    client = TestClient(app)
    manifest = client.get("/api/v20/knowledge/retrieval-policy").json()
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="knowledge-rank")

    assert manifest["runtime_mutation"] is False
    assert result["knowledge_report"]["mode"] == "feature_spine_reviewed_knowledge_retrieval"
    assert all(row["reviewed"] is True for row in result["knowledge_refs"])


def test_v20_retrieve_knowledge_accepts_policy_without_creating_refs() -> None:
    report = retrieve_knowledge(
        FeatureLayer(version="test", features=()),
        requested_domains=("health",),
        ranking_policy=KnowledgeRetrievalPolicy(domain_weights={"health": 0.6}),
    )

    assert report.refs
    assert report.refs[0].domain == "health"
    assert all(ref.reviewed for ref in report.refs)


def test_v20_knowledge_catalog_reports_coverage_and_hooks() -> None:
    catalog = build_knowledge_catalog()

    assert catalog["status"] == "ready"
    assert catalog["runtime_mutation"] is False
    assert catalog["unit_count"] >= 12
    assert {"strength", "useful_god", "element", "time"} <= {
        row["domain"] for row in catalog["domains"]
    }
    assert "feature.useful_god.candidate_paths" in catalog["feature_hooks"]
    assert "q_useful_god_evidence_gaps" in catalog["question_hooks"]
    assert not catalog["duplicate_ids"]


def test_v20_knowledge_catalog_endpoint_is_read_only() -> None:
    client = TestClient(app)
    response = client.get("/api/v20/knowledge/catalog")

    assert response.status_code == 200
    data = response.json()
    assert data["runtime_mutation"] is False
    assert data["audit"]["status"] == "pass"
