from __future__ import annotations

import json
from pathlib import Path

from v19.lab_interfaces import _default_validation_cases, _run_case
from v19.synthetic_validation import P10_GUIDED_SYNTHETIC_CASES, P11_GUIDED_SYNTHETIC_CASES, run_guided_synthetic_collision


def test_p10_guided_synthetic_collision_cases_pass() -> None:
    result = run_guided_synthetic_collision(P10_GUIDED_SYNTHETIC_CASES)

    assert result["status"] == "pass"
    assert result["summary"]["total"] >= 12
    assert result["summary"]["failed"] == 0
    assert "SYNTHETIC_CASES_ONLY" in result["boundaries"]
    assert "ANALYST_REVIEW_REQUIRED_FOR_ACTIVATION" in result["boundaries"]
    assert len(result["collision_review"]["stable_structures"]) == result["summary"]["total"]
    for item in result["cases"]:
        assert item["structure_label"]
        assert "q_income_stability" in item["observed"]["wealth_question_keys"]
        assert item["baseline_vs_kb_augmented"]["evidence_delta"]["mutation_check"] == "routing_stable"

    expected_knowledge_cases = [case for case in P10_GUIDED_SYNTHETIC_CASES if case.expected_knowledge_ids]
    assert expected_knowledge_cases
    by_case = {item["case_id"]: item for item in result["cases"]}
    for case in expected_knowledge_cases:
        delta = by_case[case.case_id]["baseline_vs_kb_augmented"]["evidence_delta"]["added_knowledge_ids"]
        for knowledge_id in case.expected_knowledge_ids:
            assert knowledge_id in delta


def test_guided_synthetic_collision_reports_evolution_candidates_on_failure() -> None:
    broken = P10_GUIDED_SYNTHETIC_CASES[0].to_dict()
    broken["case_id"] = "syn.guided.expected_collision_failure"
    broken["expected_knowledge_ids"] = ["p10.nonexistent_knowledge"]

    result = run_guided_synthetic_collision([broken])

    assert result["status"] == "fail"
    assert result["evolution_report"]["proposal_count"] == 1
    assert result["evolution_report"]["audit_count"] == 1
    assert result["evolution_report"]["audit_records"][0]["review_status"] == "analyst_review_required"
    assert result["evolution_report"]["audit_records"][0]["attribution_layer"] == "knowledge"
    assert result["evolution_report"]["draft_suggestions"][0]["target"] == "knowledge_seed_draft"
    assert result["evolution_report"]["draft_suggestions"][0]["draft_type"] == "knowledge_seed"
    assert result["evolution_report"]["items"][0]["proposal_scope"] == "draft_only_requires_analyst_review"


def test_p11_guided_synthetic_expansion_cases_pass() -> None:
    result = run_guided_synthetic_collision(P11_GUIDED_SYNTHETIC_CASES)

    assert result["status"] == "pass"
    assert result["summary"]["total"] >= 20
    assert result["summary"]["failed"] == 0
    assert result["evolution_report"]["audit_count"] == 0
    required_focus = {
        "branch_clash_harm_collision",
        "branch_combination_break_collision",
        "three_harmony_three_meeting_layered_collision",
        "ten_god_visible_hidden_conflict",
        "income_wealth_visible_clashed",
        "income_wealth_visible_bound",
        "time_trigger_relation_no_natal_mutation",
    }
    assert required_focus <= {case.collision_focus for case in P11_GUIDED_SYNTHETIC_CASES}
    for item in result["cases"]:
        assert item["structure_label"]
        assert item["observed"]["standardized_knowledge_tags"]
        assert "q_income_stability" in item["observed"]["wealth_question_keys"]
        assert item["baseline_vs_kb_augmented"]["evidence_delta"]["mutation_check"] == "routing_stable"


def test_p11_review_ui_wires_synthetic_collision_failure_loop() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")

    for token in [
        "runSyntheticCollision",
        "syntheticCollisionStatus",
        "syntheticCollisionFailures",
        "syntheticCollisionDrafts",
    ]:
        assert token in admin_html

    assert "/api/lab/synthetic-collision/run" in admin_js
    assert "renderSyntheticCollisionReview" in admin_js
    assert "attribution_layer" in admin_js
    assert "draft_type" in admin_js


def test_p11_synthetic_collision_api_endpoint_runs_matrix() -> None:
    from fastapi.testclient import TestClient

    from v19.server import app

    client = TestClient(app)
    result = client.post("/api/lab/synthetic-collision/run?role=admin", json={})

    assert result.status_code == 200
    payload = result.json()
    assert payload["matrix"] == "P11_SYNTHETIC_EXPANSION"
    assert payload["run"]["status"] == "pass"
    assert payload["run"]["summary"]["total"] >= 20
    assert payload["run"]["evolution_report"]["guardrails"] == ["NO_AUTO_LEARNING", "NO_AUTO_RULE_PROMOTION", "ANALYST_REVIEW_REQUIRED"]


def test_p12_controlled_promotion_creates_rule_candidate_and_gates_active_record(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab

    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    candidate = lab.create_synthetic_promotion_candidate(
        {
            "case_id": "syn.guided.expected_collision_failure",
            "target": "rule_db_structured_fact_draft",
            "draft_type": "rule_draft",
            "attribution_layer": "rule",
            "failure_types": ["relation_type_missing"],
            "knowledge_tags": ["ku:branch_relation"],
            "suggested_action": "draft_structured_rule_or_relation_mapping_then_rerun_collision",
        }
    )

    assert candidate["ok"]
    reviewed = lab.review_synthetic_promotion_candidate(
        candidate["item"]["candidate_id"],
        {"decision": "needs_rule", "actor_role": "admin", "note": "Create controlled rule proposal."},
    )

    assert reviewed["ok"]
    assert reviewed["item"]["status"] == "proposal_created"
    proposal_id = reviewed["downstream"]["proposal_id"]
    assert reviewed["downstream"]["kind"] == "bazi_rule_proposal"

    validated = lab.validate_bazi_rule_proposal(proposal_id)
    assert validated["passed"]
    approved = lab.approve_bazi_rule_proposal(proposal_id, {"actor_role": "admin", "note": "Approved after P12 review."})
    assert approved["ok"]
    version = lab.record_bazi_rule_version({"included_proposals": proposal_id, "activated_by_role": "admin", "note": "P12 gated record."})
    assert version["ok"]
    assert version["item"]["p12_regression_gate"]["passed"] is True
    assert version["item"]["p12_regression_gate"]["summary"]["total"] >= 20
    assert "P12_SYNTHETIC_REGRESSION_REQUIRED" in version["item"]["guardrails"]


def test_p12_review_ui_wires_controlled_promotion_queue() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")

    for token in [
        "syntheticPromotionDecision",
        "syntheticPromotionStatus",
        "syntheticPromotionList",
        "reloadSyntheticPromotions",
    ]:
        assert token in admin_html

    assert "/api/lab/synthetic-promotions" in admin_js
    assert "Create Promotion Candidate" in admin_js
    assert "reviewSyntheticPromotion" in admin_js
    assert "P11 regression required" in admin_js


def test_p13_governance_release_records_versioned_artifacts(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab

    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    created = lab.create_bazi_rule_proposal(
        {
            "actor_role": "admin",
            "rule_id": "v19.synthetic.p13.release.sample",
            "domain": "structural_relation",
            "input_contract": {"required": ["chart", "guided_question_context"]},
            "condition": {"source": "p13_test", "relation_type": "structural_context"},
            "output_contract": {"signal": "structure_context", "value_set": ["present", "absent"], "is_prediction": False},
            "reasoning_path": ["read reviewed proposal", "emit structural context only"],
            "guardrails": ["NO_RUNTIME_INFERENCE_MUTATION"],
            "rationale": "P13 release test proposal.",
        }
    )
    assert created["ok"]
    proposal_id = created["item"]["proposal_id"]
    assert lab.validate_bazi_rule_proposal(proposal_id)["passed"]
    assert lab.approve_bazi_rule_proposal(proposal_id, {"actor_role": "admin"})["ok"]
    version = lab.record_bazi_rule_version({"included_proposals": proposal_id, "activated_by_role": "admin"})
    assert version["ok"]

    release = lab.create_governance_release(
        {
            "bazi_rule_version_ids": version["item"]["version_id"],
            "note": "P13 manifest test.",
            "actor_role": "admin",
        }
    )

    assert release["ok"]
    item = release["item"]
    assert item["status"] == "release_record"
    assert item["runtime_mutation"] is False
    assert item["summary"]["artifact_count"] == 1
    assert item["summary"]["by_artifact_type"]["bazi_rule_versions"] == 1
    assert item["p13_regression_gate"]["passed"] is True
    assert item["p13_regression_gate"]["summary"]["total"] >= 20
    assert "P11_SYNTHETIC_REGRESSION_REQUIRED" in item["guardrails"]


def test_p13_governance_release_ui_and_api_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "Governance Release Manifest",
        "releaseRuleVersionIds",
        "createGovernanceRelease",
        "governanceReleaseList",
    ]:
        assert token in admin_html

    assert "/api/lab/governance-releases" in admin_js
    assert "renderGovernanceReleases" in admin_js
    assert "P11 gate" in admin_js
    assert "lab_governance_release_post" in server


def test_p14_bazi_knowledge_expansion_draft_seeds_are_review_gated() -> None:
    root = Path(__file__).resolve().parents[2]
    payload = json.loads((root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    rows = payload["knowledge_drafts"]
    by_id = {row["knowledge_id"]: row for row in rows}
    p14_ids = [knowledge_id for knowledge_id in by_id if knowledge_id.startswith("p14.")]

    assert payload["seed_id"] == "v19.current_bazi_knowledge_draft_seeds.p14.v1"
    assert len(p14_ids) == 10
    assert len(by_id) == len(rows)
    for knowledge_id in [
        "p14.ten_god.peer_family_boundary.v1",
        "p14.ten_god.output_family_boundary.v1",
        "p14.ten_god.wealth_family_boundary.v1",
        "p14.ten_god.officer_family_boundary.v1",
        "p14.ten_god.resource_family_boundary.v1",
        "p14.month_command.seasonal_groups_boundary.v1",
        "p14.stem_combination.no_transformation_boundary.v1",
        "p14.branch_penalty.versioned_source_boundary.v1",
        "p14.twelve_growth_phase.boundary.v1",
        "p14.useful_god.boundary.v1",
    ]:
        row = by_id[knowledge_id]
        assert row["risk_level"] in {"R1", "R2", "R3"}
        assert "fortune" in row["forbidden_usage"] or "active_inference" in row["forbidden_usage"]

    assert by_id["p14.twelve_growth_phase.boundary.v1"]["risk_level"] == "R3"
    assert by_id["p14.useful_god.boundary.v1"]["risk_level"] == "R3"


def test_p14_seed_current_preserves_existing_knowledge_draft_review_state(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive

    seed_file = tmp_path / "seeds.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)

    seed_file.write_text(
        json.dumps(
            {
                "knowledge_drafts": [
                    {
                        "knowledge_id": "p14.review_state.test",
                        "domain": "ten_god",
                        "category": "ten_god",
                        "title": "Review State Test",
                        "statement": "Initial statement.",
                        "risk_level": "R1",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert archive.seed_current_knowledge_drafts()["imported_count"] == 1
    reviewed = archive.update_knowledge_draft_review(
        "p14.review_state.test",
        {"review_status": "proposal_ready", "note": "Reviewed by analyst.", "actor_role": "analyst"},
    )
    assert reviewed["item"]["review_status"] == "proposal_ready"

    seed_file.write_text(
        json.dumps(
            {
                "knowledge_drafts": [
                    {
                        "knowledge_id": "p14.review_state.test",
                        "domain": "ten_god",
                        "category": "ten_god",
                        "title": "Review State Test",
                        "statement": "Updated statement.",
                        "risk_level": "R1",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert archive.seed_current_knowledge_drafts()["updated_count"] == 1
    rows = archive.list_knowledge_drafts(q="p14.review_state.test")["items"]

    assert rows[0]["statement"] == "Updated statement."
    assert rows[0]["review_status"] == "proposal_ready"
    assert rows[0]["review_note"] == "Reviewed by analyst."


def test_p15_p14_review_batches_group_drafts_without_status_mutation(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    assert archive.seed_current_knowledge_drafts()["count"] >= 57
    seeded = lab.seed_p14_knowledge_review_batches()

    assert seeded["created_count"] == 3
    batches = lab.list_knowledge_review_batches()["items"]
    by_key = {item["batch_key"]: item for item in batches}
    assert by_key["p15.p14.r1_metadata_boundaries"]["summary"]["draft_count"] == 6
    assert by_key["p15.p14.r2_source_version_review"]["summary"]["draft_count"] == 2
    assert by_key["p15.p14.r3_archive_reference_only"]["summary"]["draft_count"] == 2
    assert all("NO_DRAFT_STATUS_MUTATION" in item["guardrails"] for item in batches)

    p14_rows = archive.list_knowledge_drafts(q="p14.")["items"]
    assert {row["review_status"] for row in p14_rows} == {"pending"}


def test_p15_knowledge_base_v2_catalog_manifest_is_valid() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))

    assert manifest["manifest_id"] == "v19.bazi_knowledge_base.v2.catalog"
    assert manifest["status"] == "catalog_manifest_only"
    assert "NO_RUNTIME_MUTATION" in manifest["guardrails"]
    assert {layer["layer"] for layer in manifest["layers"]} >= {
        "L0_source_archive",
        "L2_knowledge_unit_drafts",
        "L3_review_batches",
        "L5_governance_release_manifest",
    }
    assert {batch["batch_key"] for batch in manifest["review_batches"]} == {
        "p15.p14.r1_metadata_boundaries",
        "p15.p14.r2_source_version_review",
        "p15.p14.r3_archive_reference_only",
    }
    assert manifest["proposal_generation"]["stage"] == "P16_KNOWLEDGE_BATCH_PROPOSAL_DRAFTS"
    assert manifest["proposal_generation"]["eligible_batches"] == ["p15.p14.r1_metadata_boundaries"]
    assert "R2_R3_ANALYST_REVIEW_BEFORE_PROPOSAL" in manifest["guardrails"]


def test_p15_review_batch_ui_and_api_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "Knowledge Review Batches",
        "seedP14ReviewBatches",
        "kbReviewBatchList",
    ]:
        assert token in admin_html
    assert "/api/lab/knowledge-review-batches" in admin_js
    assert "renderKnowledgeReviewBatches" in admin_js
    assert "lab_knowledge_review_batch_seed_p14_post" in server


def test_p16_r1_review_batch_generates_rule_and_question_proposal_drafts(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    assert archive.seed_current_knowledge_drafts()["count"] >= 57
    assert lab.seed_p14_knowledge_review_batches()["created_count"] == 3

    created = lab.create_knowledge_batch_proposal_drafts(
        "p15.p14.r1_metadata_boundaries",
        {"actor_role": "admin", "note": "P16 R1 test."},
    )

    assert created["ok"]
    run = created["item"]
    assert run["status"] == "proposal_drafts_created"
    assert run["summary"]["rule_proposal_count"] == 6
    assert run["summary"]["question_proposal_count"] == 1
    assert "NO_RUNTIME_MUTATION" in run["guardrails"]
    assert lab.list_knowledge_batch_proposal_runs()["count"] == 1
    assert lab.list_bazi_rule_proposals()["count"] == 6
    assert lab.list_guided_question_proposals()["count"] == 1

    for item in lab.list_bazi_rule_proposals()["items"]:
        validated = lab.validate_bazi_rule_proposal(item["proposal_id"])
        assert validated["passed"]
        assert item["evidence"]["source"] == "knowledge_review_batch"
        assert item["output_contract"]["is_prediction"] is False

    question = lab.list_guided_question_proposals()["items"][0]
    assert question["proposed_metadata"]["source"] == "p16_knowledge_batch_proposal"
    assert lab.validate_guided_question_proposal(question["proposal_id"])["passed"]

    p14_rows = archive.list_knowledge_drafts(q="p14.")["items"]
    assert {row["review_status"] for row in p14_rows} == {"pending"}


def test_p16_blocks_r2_r3_batches_until_analyst_source_review(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    archive.seed_current_knowledge_drafts()
    lab.seed_p14_knowledge_review_batches()

    r2 = lab.create_knowledge_batch_proposal_drafts("p15.p14.r2_source_version_review", {"actor_role": "admin"})
    r3 = lab.create_knowledge_batch_proposal_drafts("p15.p14.r3_archive_reference_only", {"actor_role": "admin"})

    assert r2["ok"] is False
    assert r2["code"] == "KNOWLEDGE_BATCH_PROPOSAL_BLOCKED"
    assert r2["item"]["status"] == "blocked"
    assert r2["item"]["summary"]["blocked_count"] == 2
    assert r3["ok"] is False
    assert r3["item"]["status"] == "blocked"
    assert r3["item"]["summary"]["blocked_count"] == 2
    assert lab.list_bazi_rule_proposals()["count"] == 0
    assert lab.list_guided_question_proposals()["count"] == 0
    assert lab.list_knowledge_batch_proposal_runs()["count"] == 2


def test_p16_batch_proposal_ui_and_api_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "P16 Batch Proposal Drafts",
        "createKbBatchProposalDrafts",
        "kbBatchProposalRunList",
    ]:
        assert token in admin_html
    assert "/api/lab/knowledge-batch-proposal-runs" in admin_js
    assert "renderKnowledgeBatchProposalRuns" in admin_js
    assert "proposal-drafts" in admin_js
    assert "lab_knowledge_review_batch_proposal_drafts_post" in server


def test_lab_default_validation_cases_are_synthetic_explicit_pillars() -> None:
    cases = _default_validation_cases()

    assert cases
    assert all("chart" in case for case in cases)
    assert all("input" not in case for case in cases)
    assert all("NO_BIRTHDATE" in case["guardrails"] for case in cases)
    assert all(_run_case(case)["passed"] for case in cases)
