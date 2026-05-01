from __future__ import annotations

from fastapi.testclient import TestClient

from v20.access.projection import project_runtime_for_role
from v20.access.roles import access_role_manifest
from v20.api.runtime import run_runtime_from_pillars
from v20.server import app


def test_v20_access_roles_define_projected_runtime_fields() -> None:
    manifest = access_role_manifest()
    roles = {row["role_key"]: row for row in manifest["roles"]}

    assert {"user", "analyst", "lab", "admin"} <= set(roles)
    assert "answer_text" in roles["user"]["allowed_runtime_fields"]
    assert "knowledge_refs" in roles["user"]["blocked_runtime_fields"]
    assert "feature_discovery" in roles["user"]["allowed_runtime_fields"]
    assert "portrait_intelligence" in roles["user"]["allowed_runtime_fields"]
    assert "feature_layer" in roles["analyst"]["allowed_runtime_fields"]
    assert "knowledge_semantic_model" in roles["analyst"]["allowed_runtime_fields"]
    assert "feature_discovery" in roles["analyst"]["allowed_runtime_fields"]
    assert "feature_discovery_validation" in roles["analyst"]["allowed_runtime_fields"]
    assert "portrait_intelligence_validation" in roles["analyst"]["allowed_runtime_fields"]
    assert "rule_candidate_support" in roles["analyst"]["allowed_runtime_fields"]
    assert "rule_candidate_validation" in roles["analyst"]["allowed_runtime_fields"]
    assert "rule_candidate_ranking" in roles["lab"]["allowed_runtime_fields"]
    assert "chart_graph" in roles["lab"]["allowed_runtime_fields"]
    assert manifest["runtime_mutation"] is False


def test_v20_user_projection_hides_internal_evidence_and_graphs() -> None:
    result = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="access.user",
        user_text="我想看流年触发",
        flow_year_pillar="庚子",
    )
    projected = project_runtime_for_role(result, "user")

    assert projected["role"]["role_key"] == "user"
    assert "answer_text" in projected
    assert "feature_layer" not in projected
    assert "knowledge_refs" not in projected
    assert "rule_candidate_support" not in projected
    assert "rule_candidate_validation" not in projected
    assert "chart_graph" not in projected
    assert "feature_discovery" in projected
    assert "feature_id" not in projected["feature_discovery"]["ranked_features"][0]
    assert "question_policy" not in projected["feature_discovery"]
    assert "portrait_intelligence" in projected
    assert "matched_feature_ids" not in projected["portrait_intelligence"]["axis_models"][0]["sub_axis_candidates"][0]
    assert "training_lane" not in projected["portrait_intelligence"]
    assert all("source_feature_ids" not in row for row in projected["questions"])
    assert all("source_feature_ids" not in row for row in projected["measurement_report"]["topics"])
    assert all("feature_ids" not in row for row in projected["portrait_projection"]["axes"])
    assert all("knowledge_links" not in row for row in projected["portrait_projection"]["axes"])
    assert all("feature_id" not in row for row in projected["portrait_projection"]["items"])
    assert all("knowledge_links" not in row for row in projected["portrait_projection"]["items"])


def test_v20_role_measure_endpoint_projects_by_role() -> None:
    client = TestClient(app)
    payload = {
        "year": "甲子",
        "month": "戊辰",
        "day": "甲午",
        "hour": "辛酉",
        "user_text": "我想看流年触发",
        "flow_year_pillar": "庚子",
    }

    user = client.post("/api/v20/measure/view/user", json=payload).json()
    analyst = client.post("/api/v20/measure/view/analyst", json=payload).json()
    roles = client.get("/api/v20/access/roles").json()

    assert user["version"] == "v20.role_runtime_view.v1"
    assert user["role"]["role_key"] == "user"
    assert "feature_layer" not in user
    assert analyst["role"]["role_key"] == "analyst"
    assert "feature_layer" in analyst
    assert "knowledge_semantic_model" in analyst
    assert "feature_discovery_validation" in analyst
    assert "portrait_intelligence_validation" in analyst
    assert roles["runtime_mutation"] is False
