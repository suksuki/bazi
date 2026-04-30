from __future__ import annotations

import json
from pathlib import Path

from v19.lab_interfaces import _default_validation_cases, _run_case, guided_question_diversity_audit
from v19.synthetic_validation import P10_GUIDED_SYNTHETIC_CASES, P11_GUIDED_SYNTHETIC_CASES, run_guided_synthetic_collision
from v19.synthetic_validation.guided_runner import _agent_data_for_case


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
    assert {batch["batch_key"] for batch in manifest["review_batches"]} >= {
        "p15.p14.r1_metadata_boundaries",
        "p15.p14.r2_source_version_review",
        "p15.p14.r3_archive_reference_only",
        "p21.r1_guided_question_structure_boundaries",
        "p21.r2_income_collision_review",
    }
    assert manifest["proposal_generation"]["stage"] == "P16_KNOWLEDGE_BATCH_PROPOSAL_DRAFTS"
    assert manifest["proposal_generation"]["eligible_batches"] == ["p15.p14.r1_metadata_boundaries"]
    assert manifest["proposal_validation"]["stage"] == "P17_PROPOSAL_SCHEMA_VALIDATION_RUNS"
    assert "approval" in manifest["proposal_validation"]["forbidden_outputs"]
    assert manifest["proposal_review_packets"]["stage"] == "P18_PROPOSAL_APPROVAL_REVIEW_PACKETS"
    assert "auto_approval" in manifest["proposal_review_packets"]["forbidden_outputs"]
    assert "R2_R3_ANALYST_REVIEW_BEFORE_PROPOSAL" in manifest["guardrails"]
    assert "P17_SCHEMA_VALIDATION_ONLY" in manifest["guardrails"]
    assert "P18_REVIEW_PACKET_ONLY" in manifest["guardrails"]


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


def test_p17_validates_p16_rule_and_question_proposal_drafts(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    archive.seed_current_knowledge_drafts()
    lab.seed_p14_knowledge_review_batches()
    p16 = lab.create_knowledge_batch_proposal_drafts("p15.p14.r1_metadata_boundaries", {"actor_role": "admin"})
    source_run_id = p16["item"]["run_id"]

    validated = lab.create_proposal_validation_run(
        {
            "actor_role": "admin",
            "source_run_id": source_run_id,
            "note": "P17 validation test.",
        }
    )

    assert validated["ok"]
    run = validated["item"]
    assert run["status"] == "validation_ready"
    assert run["summary"]["total"] == 7
    assert run["summary"]["passed"] == 7
    assert run["summary"]["failed"] == 0
    assert "P17_SCHEMA_VALIDATION_ONLY" in run["guardrails"]
    assert lab.list_proposal_validation_runs()["count"] == 1
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"validation_ready"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"validation_ready"}


def test_p17_records_validation_failures_without_approval_or_runtime_mutation(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab

    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    proposal = lab.create_bazi_rule_proposal(
        {
            "actor_role": "admin",
            "rule_id": "v19.p17.invalid.missing_contract",
            "domain": "structural_relation",
            "output_contract": {"signal": "", "value_set": [], "is_prediction": True},
            "guardrails": ["NO_RUNTIME_INFERENCE_MUTATION"],
        }
    )
    assert proposal["ok"]

    validated = lab.create_proposal_validation_run(
        {
            "actor_role": "admin",
            "proposal_ids": proposal["item"]["proposal_id"],
            "note": "P17 failure test.",
        }
    )

    assert validated["ok"] is False
    run = validated["item"]
    assert run["status"] == "validation_failed"
    assert run["summary"]["total"] == 1
    assert run["summary"]["failed"] == 1
    assert run["runtime_mutation"] is False
    assert run["approval_mutation"] is False
    assert run["version_mutation"] is False
    assert run["items"][0]["failed_checks"]


def test_p17_proposal_validation_ui_and_api_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "P17 Proposal Validation Runs",
        "createProposalValidationRun",
        "proposalValidationRunList",
    ]:
        assert token in admin_html
    assert "/api/lab/proposal-validation-runs" in admin_js
    assert "renderProposalValidationRuns" in admin_js
    assert "lab_proposal_validation_run_post" in server


def test_p18_creates_review_packet_from_validation_ready_proposals(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    archive.seed_current_knowledge_drafts()
    lab.seed_p14_knowledge_review_batches()
    p16 = lab.create_knowledge_batch_proposal_drafts("p15.p14.r1_metadata_boundaries", {"actor_role": "admin"})
    p17 = lab.create_proposal_validation_run({"actor_role": "admin", "source_run_id": p16["item"]["run_id"]})

    packet = lab.create_proposal_review_packet(
        {
            "actor_role": "admin",
            "validation_run_id": p17["item"]["validation_run_id"],
            "note": "P18 packet test.",
        }
    )

    assert packet["ok"]
    item = packet["item"]
    assert item["status"] == "approval_review_ready"
    assert item["summary"]["total"] == 7
    assert item["summary"]["validation_passed"] == 7
    assert item["approval_mutation"] is False
    assert item["version_mutation"] is False
    assert item["runtime_mutation"] is False
    assert "P18_REVIEW_PACKET_ONLY" in item["guardrails"]
    assert lab.list_proposal_review_packets()["count"] == 1
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"validation_ready"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"validation_ready"}


def test_p18_blocks_review_packet_when_validation_failed(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab

    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    proposal = lab.create_bazi_rule_proposal(
        {
            "actor_role": "admin",
            "rule_id": "v19.p18.invalid.packet",
            "domain": "structural_relation",
            "output_contract": {"signal": "", "value_set": [], "is_prediction": True},
            "guardrails": ["NO_RUNTIME_INFERENCE_MUTATION"],
        }
    )
    p17 = lab.create_proposal_validation_run({"actor_role": "admin", "proposal_ids": proposal["item"]["proposal_id"]})
    packet = lab.create_proposal_review_packet({"actor_role": "admin", "validation_run_id": p17["item"]["validation_run_id"]})

    assert packet["ok"] is False
    item = packet["item"]
    assert item["status"] == "blocked_by_validation"
    assert item["summary"]["validation_failed"] == 1
    assert item["recommended_decision"] == "fix_failed_validation_before_approval_review"
    assert lab.list_proposal_review_packets()["count"] == 1
    assert lab.list_bazi_rule_proposals()["items"][0]["status"] == "validation_failed"


def test_p18_review_packet_ui_and_api_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "P18 Proposal Review Packets",
        "createProposalReviewPacket",
        "proposalReviewPacketList",
    ]:
        assert token in admin_html
    assert "/api/lab/proposal-review-packets" in admin_js
    assert "renderProposalReviewPackets" in admin_js
    assert "lab_proposal_review_packet_post" in server


def test_p19_guided_questions_are_chart_specific_not_static_registry_top_five() -> None:
    top_key_sequences = []
    top_label_sequences = []
    for case in P11_GUIDED_SYNTHETIC_CASES[:20]:
        data = _agent_data_for_case(case)
        questions = data["guided_question_context"]["questions"]
        top_keys = [row["key"] for row in questions[:5]]
        top_labels = [row["label"]["zh"] for row in questions[:5]]
        top_key_sequences.append(tuple(top_keys))
        top_label_sequences.append(tuple(top_labels))
        assert "q_income_stability" in [row["key"] for row in questions[:10]]

    old_static_top = (
        "q_structure_overview",
        "q_day_master_month_anchor",
        "q_income_stability",
        "q_branch_relation_detail",
        "q_month_command_anchor",
    )
    assert old_static_top not in set(top_key_sequences)
    assert len(set(top_key_sequences)) >= 3
    assert len(set(top_label_sequences)) >= 8


def test_p20_guided_question_diversity_audit_measures_synthetic_matrix() -> None:
    result = guided_question_diversity_audit()

    assert result["status"] == "pass"
    assert result["matrix"] == "P11_SYNTHETIC_EXPANSION"
    assert result["case_count"] >= 20
    assert result["summary"]["top_key_sequence_count"] >= 3
    assert result["summary"]["top_label_sequence_count"] >= 8
    assert result["summary"]["old_static_top_present"] is False
    assert result["summary"]["income_stability_top10_count"] == result["case_count"]
    assert result["summary"]["failure_count"] == 0
    assert "AUDIT_ONLY" in result["guardrails"]
    assert all(item["top_labels"] for item in result["items"])


def test_p20_guided_question_diversity_audit_api_and_ui_are_wired() -> None:
    from fastapi.testclient import TestClient

    from v19.server import app

    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")

    for token in [
        "runQuestionDiversityAudit",
        "questionDiversityStatus",
        "questionDiversitySummary",
        "questionDiversityList",
    ]:
        assert token in admin_html

    assert "/api/lab/guided-question-diversity-audit" in admin_js
    assert "renderQuestionDiversityAudit" in admin_js

    client = TestClient(app)
    result = client.get("/api/lab/guided-question-diversity-audit?role=admin")

    assert result.status_code == 200
    payload = result.json()
    assert payload["status"] == "pass"
    assert payload["summary"]["old_static_top_present"] is False
    assert payload["summary"]["income_stability_top10_count"] == payload["case_count"]


def test_p21_knowledge_pack_loads_as_drafts_and_review_batches(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    pack_dir = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/packs"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", pack_dir)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    seeded = archive.seed_current_knowledge_drafts()

    assert seeded["count"] >= 67
    drafts = archive.list_knowledge_drafts(q="p21.")["items"]
    assert len(drafts) == 10
    assert {row["review_status"] for row in drafts} == {"pending"}
    assert len([row for row in drafts if row["risk_level"] == "R1"]) == 6
    assert len([row for row in drafts if row["risk_level"] == "R2"]) == 4

    batches = lab.seed_p21_knowledge_review_batches()

    assert batches["created_count"] == 2
    by_key = {row["batch_key"]: row for row in lab.list_knowledge_review_batches()["items"]}
    assert by_key["p21.r1_guided_question_structure_boundaries"]["summary"]["draft_count"] == 6
    assert by_key["p21.r2_income_collision_review"]["summary"]["draft_count"] == 4
    assert "NO_RUNTIME_MUTATION" in batches["guardrails"]

    blocked = lab.create_knowledge_batch_proposal_drafts("p21.r2_income_collision_review", {"actor_role": "admin"})

    assert blocked["ok"] is False
    assert blocked["code"] == "KNOWLEDGE_BATCH_PROPOSAL_BLOCKED"
    assert blocked["item"]["summary"]["blocked_count"] == 4
    assert lab.list_bazi_rule_proposals()["count"] == 0


def test_p21_knowledge_pack_manifest_api_and_ui_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    pack = json.loads((root / "docs/bazi_knowledge/packs/p21_guided_question_collision_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    assert pack["pack_id"] == "p21.guided_question_collision_knowledge_pack.v1"
    assert len(pack["knowledge_drafts"]) == 10
    assert "docs/bazi_knowledge/packs/p21_guided_question_collision_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert manifest["content_packs"][0]["pack_id"] == pack["pack_id"]
    assert "P21_NEW_CONTENT_PACKS_SEEDED_AS_DRAFTS_ONLY" in manifest["guardrails"]
    assert manifest["p21_review_packet_pipeline"]["stage"] == "P22_P21_R1_PROPOSAL_REVIEW_PACKET"
    assert "p21.r2_income_collision_review" in manifest["p21_review_packet_pipeline"]["blocked_until_review"]
    assert "P22_P21_R1_REVIEW_PACKET_ONLY" in manifest["guardrails"]

    for token in [
        "seedP21ReviewBatches",
        "生成 P21 Batches",
    ]:
        assert token in admin_html

    assert "/api/lab/knowledge-review-batches/seed-p21" in admin_js
    assert "lab_knowledge_review_batch_seed_p21_post" in server


def test_p22_p21_r1_pack_creates_validation_and_review_packet(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    result = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})

    assert result["ok"]
    assert result["status"] == "review_packet_ready"
    assert result["summary"]["r1_rule_proposal_count"] == 6
    assert result["summary"]["r1_question_proposal_count"] == 1
    assert result["summary"]["validation_total"] == 7
    assert result["summary"]["validation_failed"] == 0
    assert result["summary"]["review_packet_items"] == 7
    assert result["r2_gate"]["eligible"] is False
    assert result["summary"]["r2_blocked_count"] == 4
    assert "NO_RUNTIME_MUTATION" in result["guardrails"]
    assert lab.list_bazi_rule_proposals()["count"] == 6
    assert lab.list_guided_question_proposals()["count"] == 1
    assert lab.list_proposal_validation_runs()["count"] == 1
    assert lab.list_proposal_review_packets()["count"] == 1

    repeated = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})

    assert repeated["ok"]
    assert repeated["proposal_run"]["run_id"] == result["proposal_run"]["run_id"]
    assert repeated["review_packet"]["packet_id"] == result["review_packet"]["packet_id"]
    assert lab.list_proposal_validation_runs()["count"] == 1
    assert lab.list_proposal_review_packets()["count"] == 1


def test_p22_p21_review_packet_api_and_ui_are_wired(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient

    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab
    from v19.server import app

    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "P22 P21 Review Packet",
        "createP21ReviewPacket",
        "p21ReviewPacketList",
    ]:
        assert token in admin_html

    assert "/api/lab/p21/review-packet" in admin_js
    assert "renderP21ReviewPacket" in admin_js
    assert "lab_p21_review_packet_post" in server

    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    client = TestClient(app)
    response = client.post("/api/lab/p21/review-packet?role=admin", json={"actor_role": "admin"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "review_packet_ready"
    assert payload["summary"]["validation_failed"] == 0
    assert payload["r2_gate"]["eligible"] is False


def test_p23_records_review_packet_decision_without_approval_mutation(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    result = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})
    packet_id = result["review_packet"]["packet_id"]

    decision = lab.record_proposal_review_packet_decision(
        packet_id,
        {
            "actor_role": "analyst",
            "decision": "approve_candidate",
            "note": "Analyst review recorded for P21 R1; approval must remain a separate action.",
        },
    )

    assert decision["ok"]
    assert "P23_DECISION_LEDGER_ONLY" in decision["guardrails"]
    packet = decision["item"]
    assert packet["status"] == "approval_review_ready"
    assert packet["decision_status"] == "decision_recorded"
    assert packet["decision_summary"]["total"] == 1
    assert packet["decision_summary"]["latest_decision"] == "approve_candidate"
    assert packet["latest_decision_record"]["approval_mutation"] is False
    assert packet["latest_decision_record"]["version_mutation"] is False
    assert packet["latest_decision_record"]["runtime_mutation"] is False
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"validation_ready"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"validation_ready"}
    assert lab.list_bazi_rule_versions()["count"] == 0
    assert lab.list_guided_question_library_versions()["count"] == 0
    assert lab.lab_status()["counts"]["proposal_review_packet_decisions"] == 1


def test_p23_review_packet_decision_api_and_ui_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))

    for token in [
        "proposalPacketDecision",
        "proposalPacketDecisionNote",
        "记录 P23 Decision",
    ]:
        assert token in admin_html or token in admin_js
    assert "/api/lab/proposal-review-packets/${encodeURIComponent(packetId)}/decisions" in admin_js
    assert "recordProposalReviewPacketDecision" in admin_js
    assert "lab_proposal_review_packet_decision_post" in server
    assert manifest["proposal_review_packet_decisions"]["stage"] == "P23_REVIEW_PACKET_DECISION_LEDGER"
    assert "NO_PROPOSAL_STATUS_CHANGE" in manifest["proposal_review_packet_decisions"]["forbidden_outputs"]
    assert "P23_DECISION_LEDGER_ONLY" in manifest["guardrails"]


def test_p24_item_decisions_and_approval_preflight_without_mutation(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    result = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})
    packet_id = result["review_packet"]["packet_id"]
    packet = lab.list_proposal_review_packets()["items"][0]
    proposal_ids = [row["proposal_id"] for row in packet["items"]]

    blocked = lab.create_proposal_review_approval_preflight(packet_id, {"actor_role": "analyst"})

    assert blocked["ok"] is False
    assert blocked["item"]["status"] == "approval_preflight_blocked"
    assert blocked["item"]["summary"]["missing_item_decision_count"] == len(proposal_ids)
    assert "P24_APPROVAL_PREFLIGHT_ONLY" in blocked["guardrails"]

    decisions = [
        {
            "proposal_id": proposal_id,
            "decision": "approve_candidate",
            "note": "Item-level approval candidate recorded for preflight only.",
        }
        for proposal_id in proposal_ids
    ]
    decision_result = lab.record_proposal_review_packet_decision(packet_id, {"actor_role": "analyst", "decisions": decisions})
    ready = lab.create_proposal_review_approval_preflight(packet_id, {"actor_role": "analyst"})

    assert decision_result["ok"]
    assert ready["ok"]
    assert ready["item"]["status"] == "approval_preflight_ready"
    assert ready["item"]["summary"]["ready_item_count"] == len(proposal_ids)
    assert ready["item"]["summary"]["failed_checks"] == 0
    assert all(row["ready_for_approval"] for row in ready["item"]["items"])
    assert ready["item"]["approval_mutation"] is False
    assert ready["item"]["version_mutation"] is False
    assert ready["item"]["runtime_mutation"] is False
    listed = lab.list_proposal_review_packets()["items"][0]
    assert listed["approval_preflight_summary"]["total"] == 2
    assert listed["approval_preflight_summary"]["latest_status"] == "approval_preflight_ready"
    assert all((row.get("latest_review_decision") or {}).get("decision") == "approve_candidate" for row in listed["items"])
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"validation_ready"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"validation_ready"}
    assert lab.list_bazi_rule_versions()["count"] == 0
    assert lab.list_guided_question_library_versions()["count"] == 0
    assert lab.lab_status()["counts"]["proposal_review_approval_preflights"] == 2


def test_p24_approval_preflight_api_and_ui_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))

    assert "P24 item decision / preflight ledger only" in admin_html
    assert "记录条目 Decision" in admin_js
    assert "运行 P24 Preflight" in admin_js
    assert "/api/lab/proposal-review-packets/${encodeURIComponent(packetId)}/approval-preflight" in admin_js
    assert "runProposalReviewApprovalPreflight" in admin_js
    assert "lab_proposal_review_packet_approval_preflight_post" in server
    assert manifest["proposal_review_approval_preflight"]["stage"] == "P24_ITEM_DECISION_APPROVAL_PREFLIGHT"
    assert "P24_APPROVAL_PREFLIGHT_ONLY" in manifest["guardrails"]


def test_p25_controlled_approval_requires_preflight_and_is_idempotent(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    result = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})
    packet_id = result["review_packet"]["packet_id"]
    packet = lab.list_proposal_review_packets()["items"][0]
    proposal_ids = [row["proposal_id"] for row in packet["items"]]

    blocked = lab.execute_proposal_review_packet_approval(packet_id, {"actor_role": "admin"})

    assert blocked["ok"] is False
    assert blocked["code"] == "P25_APPROVAL_PREFLIGHT_NOT_READY"
    assert blocked["item"]["status"] == "controlled_approval_blocked"
    assert "P25_CONTROLLED_APPROVAL_ONLY" in blocked["guardrails"]
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"validation_ready"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"validation_ready"}

    lab.record_proposal_review_packet_decision(
        packet_id,
        {
            "actor_role": "analyst",
            "decisions": [
                {"proposal_id": proposal_id, "decision": "approve_candidate", "note": "P25 gate candidate."}
                for proposal_id in proposal_ids
            ],
        },
    )
    preflight = lab.create_proposal_review_approval_preflight(packet_id, {"actor_role": "analyst"})
    approved = lab.execute_proposal_review_packet_approval(packet_id, {"actor_role": "admin", "note": "P25 controlled approval test."})
    repeated = lab.execute_proposal_review_packet_approval(packet_id, {"actor_role": "admin", "note": "P25 repeated approval test."})

    assert preflight["ok"]
    assert approved["ok"]
    assert approved["item"]["status"] == "controlled_approval_executed"
    assert approved["item"]["summary"]["approved_count"] == len(proposal_ids)
    assert approved["item"]["summary"]["rule_approved_count"] == 6
    assert approved["item"]["summary"]["question_approved_count"] == 1
    assert approved["item"]["auto_approval"] is False
    assert approved["item"]["version_mutation"] is False
    assert approved["item"]["runtime_mutation"] is False
    assert repeated["ok"]
    assert repeated["reused"] is True
    assert repeated["item"]["approval_execution_id"] == approved["item"]["approval_execution_id"]
    listed = lab.list_proposal_review_packets()["items"][0]
    assert listed["approval_execution_summary"]["total"] == 2
    assert listed["approval_execution_summary"]["latest_status"] == "controlled_approval_executed"
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"approved"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"approved"}
    assert lab.list_bazi_rule_versions()["count"] == 0
    assert lab.list_guided_question_library_versions()["count"] == 0
    assert lab.lab_status()["counts"]["proposal_review_approval_executions"] == 2


def test_p25_controlled_approval_api_and_ui_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))

    assert "执行 P25 Approval" in admin_js
    assert "executeProposalReviewApproval" in admin_js
    assert "/api/lab/proposal-review-packets/${encodeURIComponent(packetId)}/controlled-approval" in admin_js
    assert "lab_proposal_review_packet_controlled_approval_post" in server
    assert manifest["proposal_review_controlled_approval"]["stage"] == "P25_CONTROLLED_APPROVAL_EXECUTION_GATE"
    assert "P25_CONTROLLED_APPROVAL_ONLY" in manifest["guardrails"]


def test_p26_new_knowledge_pack_seeds_and_ingests_rule_db(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    seeded = archive.seed_current_knowledge_drafts()
    p26_drafts = archive.list_knowledge_drafts(q="p26.")["items"]
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p26_rules = rule_db.list_bazi_rules(q="p26.")["items"]

    assert seeded["count"] >= 79
    assert len(p26_drafts) == 12
    assert ingested["ok"]
    assert ingested["rule_count"] >= 77
    assert len(p26_rules) == 12
    assert all(row["engine_enabled"] is False for row in p26_rules)
    assert all(row["engine_adapter_status"] == "candidate_waiting_synthetic_acceptance" for row in p26_rules)
    assert all(row["status"] == "active_in_rule_db" for row in p26_rules)


def test_p26_converts_p25_approved_proposals_to_versions_and_rule_db(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    result = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})
    packet_id = result["review_packet"]["packet_id"]
    proposal_ids = [row["proposal_id"] for row in lab.list_proposal_review_packets()["items"][0]["items"]]
    lab.record_proposal_review_packet_decision(
        packet_id,
        {
            "actor_role": "analyst",
            "decisions": [{"proposal_id": proposal_id, "decision": "approve_candidate"} for proposal_id in proposal_ids],
        },
    )
    lab.create_proposal_review_approval_preflight(packet_id, {"actor_role": "analyst"})
    lab.execute_proposal_review_packet_approval(packet_id, {"actor_role": "admin"})

    p26 = lab.execute_p26_knowledge_to_rules({"actor_role": "admin", "enable_engine": True})
    repeated = lab.execute_p26_knowledge_to_rules({"actor_role": "admin", "enable_engine": True})

    assert p26["ok"]
    assert p26["summary"]["p26_draft_count"] == 12
    assert p26["summary"]["approved_rule_proposals_consumed"] == 6
    assert p26["summary"]["approved_question_proposals_consumed"] == 1
    assert p26["summary"]["rule_db_rule_count"] >= 77
    assert p26["rule_version"]["rule_count"] == 6
    assert p26["question_version"]["question_count"] == 1
    assert "P26_KNOWLEDGE_TO_RULES_FAST_PATH" in p26["guardrails"]
    assert lab.list_bazi_rule_versions()["count"] == 1
    assert lab.list_guided_question_library_versions()["count"] == 1
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"active_record"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"active_record"}
    assert len(rule_db.list_bazi_rules(q="p26.")["items"]) == 12
    assert repeated["ok"]
    assert repeated["summary"]["approved_rule_proposals_consumed"] == 0
    assert repeated["summary"]["approved_question_proposals_consumed"] == 0
    assert lab.list_bazi_rule_versions()["count"] == 1
    assert lab.list_guided_question_library_versions()["count"] == 1


def test_p26_knowledge_to_rules_api_manifest_and_ui_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p26_rule_conversion_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    assert pack["pack_id"] == "p26.rule_conversion_knowledge_pack.v1"
    assert len(pack["knowledge_drafts"]) == 12
    assert "docs/bazi_knowledge/packs/p26_rule_conversion_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert manifest["content_packs"][1]["pack_id"] == pack["pack_id"]
    assert manifest["knowledge_to_rules_fast_path"]["stage"] == "P26_KNOWLEDGE_TO_RULES_FAST_PATH"
    assert "P26_KNOWLEDGE_TO_RULES_FAST_PATH" in manifest["guardrails"]
    assert "executeP26KnowledgeToRules" in admin_html
    assert "/api/lab/p26/knowledge-to-rules" in admin_js
    assert "lab_p26_knowledge_to_rules_post" in server


def test_p27_domain_completion_pack_directories_and_smart_gate_wiring() -> None:
    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p27_domain_completion_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for path in [
        "docs/bazi_knowledge/ten_god/ten_god_units_v1.md",
        "docs/bazi_knowledge/strength/strength_units_v1.md",
        "docs/bazi_knowledge/time_context/time_context_units_v1.md",
        "docs/bazi_knowledge/pattern/pattern_units_v1.md",
    ]:
        assert (root / path).exists()

    assert pack["pack_id"] == "p27.domain_completion_knowledge_pack.v1"
    assert len(pack["knowledge_drafts"]) == 40
    assert "docs/bazi_knowledge/packs/p27_domain_completion_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert manifest["content_packs"][2]["pack_id"] == pack["pack_id"]
    assert manifest["smart_rule_activation_gate"]["stage"] == "P27_SMART_RULE_ACTIVATION_GATE"
    assert "P27_SMART_RULE_ACTIVATION_GATE" in manifest["guardrails"]
    assert "executeP27SmartRuleGate" in admin_html
    assert "/api/lab/p27/smart-rule-gate" in admin_js
    assert "lab_p27_smart_rule_gate_post" in server


def test_p27_smart_gate_seeds_rule_candidates_and_activates_low_risk_after_regression(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    seeded = archive.seed_current_knowledge_drafts()
    p27_drafts = archive.list_knowledge_drafts(q="p27.")["items"]
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p27_rules = rule_db.list_bazi_rules(q="p27.")["items"]

    assert seeded["count"] >= 119
    assert len(p27_drafts) == 40
    assert ingested["ok"]
    assert len(p27_rules) == 40
    assert all(row["engine_enabled"] is False for row in p27_rules)

    dry_run = lab.execute_p27_smart_rule_activation({"actor_role": "admin", "activate": False, "limit": 12})
    assert dry_run["ok"]
    assert dry_run["status"] == "dry_run"
    assert dry_run["summary"]["p27_draft_count"] == 40
    assert dry_run["summary"]["candidate_count"] >= 12
    assert dry_run["summary"]["selected_count"] == 12
    assert dry_run["summary"]["activated_count"] == 0
    assert dry_run["pre_regression"]["status"] == "pass"

    activated = lab.execute_p27_smart_rule_activation({"actor_role": "admin", "activate": True, "limit": 6})
    p27_rules_after = rule_db.list_bazi_rules(q="p27.")["items"]

    assert activated["ok"]
    assert activated["status"] == "activated"
    assert activated["summary"]["activated_count"] == 6
    assert activated["summary"]["rolled_back_count"] == 0
    assert activated["post_regression"]["status"] == "pass"
    assert sum(1 for row in p27_rules_after if row["engine_enabled"] is True) == 6
    assert all(row["risk_level"] == "R1" for row in p27_rules_after if row["engine_enabled"] is True)

    repeated_dry_run = lab.execute_p27_smart_rule_activation({"actor_role": "admin", "activate": False, "limit": 12})
    p27_rules_after_repeated_dry_run = rule_db.list_bazi_rules(q="p27.")["items"]

    assert repeated_dry_run["ok"]
    assert sum(1 for row in p27_rules_after_repeated_dry_run if row["engine_enabled"] is True) == 6


def test_p28e_ten_god_interaction_pack_seeds_and_ingests_rule_db(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive

    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p28e_ten_god_interaction_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    p28e_knowledge_ids = {item["knowledge_id"] for item in pack["knowledge_drafts"]}
    seeded = archive.seed_current_knowledge_drafts()
    p28e_drafts = [row for row in archive.list_knowledge_drafts(q="p28.interaction.")["items"] if row["knowledge_id"] in p28e_knowledge_ids]
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p28e_rules = [row for row in rule_db.list_bazi_rules(q="p28.interaction.")["items"] if row["knowledge_id"] in p28e_knowledge_ids]

    assert pack["pack_id"] == "p28e.ten_god_interaction_knowledge_pack.v1"
    assert len(pack["knowledge_drafts"]) == 24
    assert "docs/bazi_knowledge/packs/p28e_ten_god_interaction_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert manifest["content_packs"][3]["pack_id"] == pack["pack_id"]
    assert seeded["count"] >= 143
    assert len(p28e_drafts) == 24
    assert ingested["ok"]
    assert len(p28e_rules) == 24
    assert {row["category"] for row in p28e_rules} == {"ten_god_interaction", "ten_god_interaction_mechanism"}
    assert all(row["domain"] == "ten_god_relation" for row in p28e_rules)
    assert all(row["engine_enabled"] is False for row in p28e_rules)
    assert all(row["engine_adapter_status"] == "candidate_waiting_synthetic_acceptance" for row in p28e_rules)
    assert all(any(token in row["forbidden_usage"] for token in ["fortune", "direct_fortune_output"]) for row in p28e_rules)


def test_p28f_ten_god_conflict_family_pack_seeds_and_ingests_rule_db(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive

    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p28f_ten_god_conflict_family_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    topic = (root / "docs/bazi_knowledge/interaction/ten_god_conflict_constraint_mixed_topic_v1.md").read_text(encoding="utf-8")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    seeded = archive.seed_current_knowledge_drafts()
    p28f_drafts = archive.list_knowledge_drafts(q="p28.interaction.")["items"]
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p28f_rules = [row for row in rule_db.list_bazi_rules(q="p28.interaction.")["items"] if row["knowledge_id"] in {item["knowledge_id"] for item in pack["knowledge_drafts"]}]

    assert pack["pack_id"] == "p28f.ten_god_conflict_family_knowledge_pack.v1"
    assert len(pack["knowledge_drafts"]) == 20
    assert "docs/bazi_knowledge/packs/p28f_ten_god_conflict_family_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert manifest["content_packs"][4]["pack_id"] == pack["pack_id"]
    for token in ["伤官见官", "官杀攻身", "财滋杀", "合杀留官"]:
        assert token in topic
    assert seeded["count"] >= 163
    assert len(p28f_drafts) >= 44
    assert ingested["ok"]
    assert len(p28f_rules) == 20
    assert {row["category"] for row in p28f_rules} == {"ten_god_interaction", "ten_god_interaction_mechanism"}
    assert all(row["domain"] == "ten_god_relation" for row in p28f_rules)
    assert all(row["engine_enabled"] is False for row in p28f_rules)
    assert all(any(token in row["forbidden_usage"] for token in ["fortune", "direct_fortune_output"]) for row in p28f_rules)


def test_p28g_ten_god_conflict_matrix_covers_all_candidates(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES, run_p28g_ten_god_conflict_matrix

    root = Path(__file__).resolve().parents[2]
    p28e = json.loads((root / "docs/bazi_knowledge/packs/p28e_ten_god_interaction_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    p28f = json.loads((root / "docs/bazi_knowledge/packs/p28f_ten_god_conflict_family_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    p31b = json.loads((root / "docs/bazi_knowledge/packs/p31b_all_knowledge_directory_completion_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    result = run_p28g_ten_god_conflict_matrix()
    p31b_interactions = [item for item in p31b["knowledge_drafts"] if str(item["knowledge_id"]).startswith("p31b.interaction.")]
    expected_ids = {item["knowledge_id"] for item in p28e["knowledge_drafts"] + p28f["knowledge_drafts"] + p31b_interactions}

    assert result["status"] == "pass"
    assert result["summary"]["total"] == 24
    assert result["summary"]["expected_rule_count"] == 48
    assert result["summary"]["covered_rule_count"] == 48
    assert result["summary"]["engine_enabled_count"] == 0
    assert set(result["coverage"]["expected_knowledge_ids"]) == expected_ids
    assert {case["family"] for case in P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES} == {
        "direct_conflict",
        "constraint_deprivation",
        "mixed_structure",
        "selection_rescue",
    }
    assert result["summary"]["by_activation_tier"]["condition_model_needed"] == 20
    assert "NO_RULE_ACTIVATION" in result["guardrails"]
    assert "docs/v19/V19_P28G_TEN_GOD_CONFLICT_SYNTHETIC_MATRIX.md" in manifest["created_from"]


def test_p28h_ten_god_conflict_review_table_marks_rule_boundaries() -> None:
    from v19.synthetic_validation import build_p28h_ten_god_conflict_review_table

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    report = (root / "docs/v19/V19_P28H_TEN_GOD_CONFLICT_REVIEW_TABLE.md").read_text(encoding="utf-8")
    result = build_p28h_ten_god_conflict_review_table()
    by_title = {row["title"]: row for row in result["items"]}

    assert result["status"] == "review_ready"
    assert result["summary"]["total"] == 24
    assert result["summary"]["existence_rule_candidate_count"] == 24
    assert result["summary"]["fast_path_candidate_count"] == 4
    assert result["summary"]["condition_model_required_count"] == 20
    assert result["summary"]["mechanism_hold_count"] == 24
    assert result["summary"]["archive_only_verdict_count"] == 24
    assert by_title["伤官见官"]["activation_decision"] == "existence_fast_path_candidate"
    assert by_title["官杀攻身"]["activation_decision"] == "condition_model_required_before_activation"
    assert by_title["印化杀"]["activation_decision"] == "condition_model_required_before_activation"
    assert by_title["财官相生"]["activation_decision"] == "condition_model_required_before_activation"
    assert "官非灾祸" in by_title["伤官见官"]["archive_only_verdicts"]
    assert "禄刃 / 控制压力模型未完成" in by_title["官杀攻身"]["condition_model_gaps"]
    assert all(row["mechanism_decision"] == "hold_for_condition_model" for row in result["items"])
    assert "docs/v19/V19_P28H_TEN_GOD_CONFLICT_REVIEW_TABLE.md" in manifest["created_from"]
    assert manifest["p28h_ten_god_conflict_review_table"]["fast_path_candidate_count"] == 4
    assert "P28I" in report


def test_p28i_ten_god_fast_path_gate_activates_precise_existence_rules(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.bazi_guided_questions import build_guided_question_answer, build_guided_question_context, guided_answer_to_plain_text
    from v19.synthetic_validation import run_p28i_ten_god_fast_path_gate
    from v19.synthetic_validation.ten_god_conflict_matrix import P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    dry_run = run_p28i_ten_god_fast_path_gate(activate=False)
    activated = run_p28i_ten_god_fast_path_gate(activate=True)
    active_rules = [row for row in rule_db.list_bazi_rules(q="p28.interaction.")["items"] if row["engine_enabled"] is True]
    active_ids = {row["knowledge_id"] for row in active_rules}

    assert dry_run["status"] == "dry_run_pass"
    assert dry_run["summary"]["fast_path_candidate_count"] == 4
    assert dry_run["summary"]["eligible_count"] == 4
    assert dry_run["summary"]["signal_audit_status"] == "pass"
    assert all(row["matched_fast_path_signal_ids"] == [row["expected_knowledge_id"]] for row in dry_run["signal_audit"]["cases"])
    assert activated["status"] == "activated"
    assert activated["summary"]["activation_updated_count"] == 4
    assert active_ids == set(dry_run["selected_ids"])
    assert all(row["category"] == "ten_god_interaction" for row in active_rules)
    assert not any(row["category"] == "ten_god_interaction_mechanism" and row["engine_enabled"] for row in rule_db.list_bazi_rules(q="p28.interaction.")["items"])

    case = next(row for row in P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES if row["case_id"] == "syn.p28g.shangguan_see_official")
    agent_data = {"chart": case["chart"], "time_context": case["time_context"], "inference_context": {}}
    context = build_guided_question_context(agent_data)
    question_keys = [row["key"] for row in context["questions"]]
    answer = build_guided_question_answer({**agent_data, "guided_question_context": context, "knowledge_context": {"items": []}}, "kbq_ten_god_interaction_boundary", "当前命中的伤官见官应该如何按结构层阅读？")
    text = guided_answer_to_plain_text(answer, "zh")

    assert "kbq_ten_god_interaction_boundary" in question_keys
    assert "q_ten_god_metadata" in question_keys
    assert answer["source_signal_category"] == "ten_god_interaction"
    assert "伤官" in text
    assert "正官" in text
    for forbidden in ["官非", "灾祸", "事业不顺", "发财", "破财"]:
        assert forbidden not in text
    assert "docs/v19/V19_P28I_TEN_GOD_FAST_PATH_GATE.md" in manifest["created_from"]
    assert manifest["p28i_ten_god_fast_path_gate"]["fast_path_candidate_count"] == 4
    assert manifest["p28i_ten_god_fast_path_gate"]["activation_result"] == "dry_run_pass_and_activation_ready"


def test_p28j_ten_god_mechanism_condition_models_batch_all_remaining_candidates(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import build_p28j_ten_god_mechanism_condition_models

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    result = build_p28j_ten_god_mechanism_condition_models()
    by_title = {row["title"]: row for row in result["models"]}

    assert result["status"] == "condition_models_ready_activation_blocked"
    assert result["summary"]["mechanism_candidate_count"] == 20
    assert result["summary"]["condition_model_count"] == 20
    assert result["summary"]["activation_ready_count"] == 0
    assert result["summary"]["activation_blocked_count"] == 20
    assert result["summary"]["by_family"] == {
        "direct_conflict": 3,
        "constraint_deprivation": 6,
        "mixed_structure": 1,
        "selection_rescue": 10,
    }
    assert result["summary"]["axis_coverage"]["source_layer"] == 20
    assert result["summary"]["axis_coverage"]["capacity_strength"] == 20
    assert all("p28k_synthetic_pair_regression_required" in row["activation_blockers"] for row in result["models"])
    assert all(row["engine_enabled"] is False for row in result["models"])
    assert "resource_controls_output_target" in {axis["key"] for axis in by_title["枭神夺食"]["condition_axes"]}
    assert "wealth_feeds_pressure_boundary" in {axis["key"] for axis in by_title["财滋杀"]["condition_axes"]}
    assert "combine_effectiveness_and_keep_remove_path" in {axis["key"] for axis in by_title["合杀留官"]["condition_axes"]}
    assert "blade_control_pressure_model" in {axis["key"] for axis in by_title["羊刃驾杀"]["condition_axes"]}
    assert "seal_transform_kill_capacity" in {axis["key"] for axis in by_title["印化杀"]["condition_axes"]}
    assert "wealth_official_continuity" in {axis["key"] for axis in by_title["财官相生"]["condition_axes"]}
    assert result["next_batch"]["minimum_required_pairs"] >= 111
    assert "docs/v19/V19_P28J_TEN_GOD_MECHANISM_CONDITION_MODELS.md" in manifest["created_from"]
    assert "docs/v19/V19_P28J_FRAMEWORK_ADAPTATION_REVIEW.md" in manifest["created_from"]
    assert manifest["p28j_ten_god_mechanism_condition_models"]["mechanism_candidate_count"] == 20
    assert manifest["v19_framework_adaptation_review"]["decision"] == "extend_current_framework_do_not_replace_now"


def test_p28k_ten_god_mechanism_eval_dataset_and_regression_are_strict(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import build_p28k_ten_god_mechanism_eval_dataset, run_p28k_ten_god_mechanism_regression

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    dataset = build_p28k_ten_god_mechanism_eval_dataset()
    regression = run_p28k_ten_god_mechanism_regression()
    samples_by_mechanism = {}
    for sample in dataset["samples"]:
        samples_by_mechanism.setdefault(sample["source_mechanism_id"], []).append(sample)

    assert dataset["status"] == "eval_dataset_ready_no_rule_activation"
    assert dataset["summary"]["mechanism_count"] == 20
    assert dataset["summary"]["sample_count"] == 172
    assert dataset["summary"]["by_polarity"] == {
        "positive": 66,
        "negative": 66,
        "distractor_time": 20,
        "distractor_hidden": 20,
    }
    assert dataset["summary"]["min_samples_per_mechanism"] == 8
    assert dataset["summary"]["complex_mechanism_count"] == 3
    assert all({"case_id", "source_mechanism_id", "polarity", "expected_signal", "forbidden_signals", "expected_question_keys", "forbidden_text", "condition_axes_expected", "audit_tags"} <= set(sample) for sample in dataset["samples"])
    assert all(len(rows) in {8, 12} for rows in samples_by_mechanism.values())
    assert len([rows for rows in samples_by_mechanism.values() if len(rows) == 12]) == 3
    assert all(sample["expected_signal"] == sample["source_mechanism_id"] for sample in dataset["samples"] if sample["polarity"] == "positive")
    assert all(sample["source_mechanism_id"] in sample["forbidden_signals"] for sample in dataset["samples"] if sample["polarity"] != "positive")
    assert all(any(axis["expected"] == "blocked" for axis in sample["condition_axes_expected"]) for sample in dataset["samples"] if sample["polarity"] != "positive")

    assert regression["status"] == "pass"
    assert regression["summary"]["sample_count"] == 172
    assert regression["summary"]["sample_failed"] == 0
    assert regression["summary"]["false_positive_count"] == 0
    assert regression["summary"]["forbidden_text_failure_count"] == 0
    assert regression["summary"]["activation_updated_count"] == 0
    assert "docs/v19/V19_P28K_TEN_GOD_MECHANISM_EVAL_DATASET.md" in manifest["created_from"]
    assert manifest["p28k_ten_god_mechanism_eval_dataset"]["sample_count"] == 172
    assert manifest["p28k_ten_god_mechanism_eval_dataset"]["activation_allowed"] is False


def test_p28l_ten_god_mechanism_signal_gate_is_shadow_only(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import run_p28l_ten_god_mechanism_signal_gate

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    gate = run_p28l_ten_god_mechanism_signal_gate()

    assert gate["status"] == "shadow_gate_pass_no_activation"
    assert gate["summary"]["mechanism_count"] == 20
    assert gate["summary"]["sample_count"] == 172
    assert gate["summary"]["shadow_signal_pass_count"] == 20
    assert gate["summary"]["false_positive_count"] == 0
    assert gate["summary"]["missed_positive_count"] == 0
    assert gate["summary"]["production_activation_deferred_count"] == 20
    assert gate["summary"]["activation_updated_count"] == 0
    assert all(row["shadow_decision"] == "shadow_signal_ready" for row in gate["mechanisms"])
    assert all(row["production_decision"] == "production_activation_deferred" for row in gate["mechanisms"])
    assert all(row["engine_enabled"] is False for row in gate["mechanisms"])
    assert not any(row["matched_signal_ids"] for row in gate["samples"] if row["polarity"] != "positive")
    assert all(row["matched_signal_ids"] == [row["source_mechanism_id"]] for row in gate["samples"] if row["polarity"] == "positive")
    assert "docs/v19/V19_P28L_TEN_GOD_MECHANISM_SIGNAL_GATE.md" in manifest["created_from"]
    assert manifest["p28l_ten_god_mechanism_signal_gate"]["shadow_signal_pass_count"] == 20
    assert manifest["p28l_ten_god_mechanism_signal_gate"]["activation_allowed"] is False


def test_p29_ten_god_mechanism_internal_scoring_ranks_without_activation(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import run_p29_ten_god_mechanism_internal_scoring

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    scoring = run_p29_ten_god_mechanism_internal_scoring()

    assert scoring["status"] == "internal_scoring_ready_no_activation"
    assert scoring["summary"]["mechanism_count"] == 20
    assert scoring["summary"]["rank_ready_count"] == 20
    assert scoring["summary"]["blocked_count"] == 0
    assert scoring["summary"]["activation_updated_count"] == 0
    assert scoring["summary"]["p28l_status"] == "shadow_gate_pass_no_activation"
    assert all(row["scoring_decision"] == "rank_ready" for row in scoring["scores"])
    assert all(row["activation_allowed"] is False for row in scoring["scores"])
    assert all(row["user_output_allowed"] is False for row in scoring["scores"])
    assert all(row["internal_rank_score"] >= 75 for row in scoring["scores"])
    assert [row["rank"] for row in scoring["scores"]] == list(range(1, 21))
    assert "docs/v19/V19_P29_TEN_GOD_MECHANISM_INTERNAL_SCORING.md" in manifest["created_from"]
    assert manifest["p29_ten_god_mechanism_internal_scoring"]["rank_ready_count"] == 20
    assert manifest["p29_ten_god_mechanism_internal_scoring"]["user_facing_probability_allowed"] is False


def test_p30_ten_god_mechanism_arbitration_controls_focus_and_backlog(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import run_p30_ten_god_mechanism_arbitration

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    arbitration = run_p30_ten_god_mechanism_arbitration()

    assert arbitration["status"] == "arbitration_ready_no_activation"
    assert arbitration["summary"]["scenario_count"] == 5
    assert arbitration["summary"]["scenario_pass_count"] == 5
    assert arbitration["summary"]["blocked_count"] == 0
    assert arbitration["summary"]["primary_focus_count"] == 5
    assert arbitration["summary"]["migration_backlog_count"] == 5
    assert arbitration["summary"]["activation_updated_count"] == 0
    assert arbitration["migration_policy"]["decision"] == "dual_track_forward_first_then_backfill"
    assert all(row["primary_focus"]["mechanism_id"].startswith("p28.interaction.") for row in arbitration["scenarios"])
    assert all("user_facing_probability" in row["forbidden_outputs"] for row in arbitration["scenarios"])
    assert all(row["status"] == "pass" for row in arbitration["scenarios"])
    assert {row["decision"] for row in arbitration["migration_backlog"]} >= {"migrate_before_activation", "defer_until_topic_coverage_complete"}
    assert "docs/v19/V19_P30_TEN_GOD_MECHANISM_ARBITRATION.md" in manifest["created_from"]
    assert manifest["p30_ten_god_mechanism_arbitration"]["scenario_count"] == 5
    assert manifest["p30_ten_god_mechanism_arbitration"]["legacy_migration_policy"] == "dual_track_forward_first_then_backfill"


def test_p31_all_knowledge_coverage_audit_reads_catalog_and_new_framework_tracks() -> None:
    from v19.knowledge_base_audit import run_p31_all_knowledge_coverage_audit

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    audit = run_p31_all_knowledge_coverage_audit()

    assert audit["status"] == "audit_ready_gaps_found"
    assert audit["summary"]["taxonomy_item_count"] == 154
    assert audit["summary"]["knowledge_draft_count"] == 234
    assert audit["summary"]["by_taxonomy_status"] == {"已有": 25, "部分": 125, "归档": 4}
    assert audit["summary"]["drafts_by_domain"]["pattern"] == 16
    assert audit["summary"]["drafts_by_domain"]["blind"] == 5
    assert audit["summary"]["drafts_by_domain"]["palace"] == 7
    assert audit["directory_report"]["existing_directory_count"] == 33
    assert audit["directory_report"]["missing_directory_count"] == 0
    assert "pattern/regular" in audit["directory_report"]["existing_directories"]
    assert "blind/lifa" in audit["directory_report"]["existing_directories"]
    assert "palace" in audit["directory_report"]["existing_directories"]
    assert "career" in audit["directory_report"]["existing_directories"]
    assert "rule_db" in audit["directory_report"]["existing_directories"]
    assert audit["framework_fit"]["by_track"]["condition_model_eval_gate"] > 40
    assert audit["migration_policy"]["decision"] == "dual_track_forward_first_then_backfill"
    assert "docs/v19/V19_P31_ALL_KNOWLEDGE_COVERAGE_AUDIT.md" in manifest["created_from"]
    assert "docs/v19/V19_P31B_ALL_KNOWLEDGE_DIRECTORY_COMPLETION.md" in manifest["created_from"]
    assert manifest["p31_all_knowledge_coverage_audit"]["knowledge_draft_count"] == 234
    assert manifest["p31a_all_knowledge_foundation_gap_pack"]["draft_count"] == 35
    assert manifest["p31b_all_knowledge_directory_completion"]["draft_count"] == 36


def test_p31a_foundation_gap_pack_seeds_and_keeps_runtime_disabled(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive

    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p31a_all_knowledge_foundation_gap_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    seeded = archive.seed_current_knowledge_drafts()
    p31a_drafts = archive.list_knowledge_drafts(q="p31a.")["items"]
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p31a_rules = rule_db.list_bazi_rules(q="p31a.")["items"]

    assert pack["pack_id"] == "p31a.all_knowledge_foundation_gap_pack.v1"
    assert len(pack["knowledge_drafts"]) == 35
    assert seeded["count"] == 234
    assert len(p31a_drafts) == 35
    assert ingested["rule_count"] >= 232
    assert len(p31a_rules) == 35
    assert {row["domain"] for row in p31a_drafts} >= {"blind", "palace", "pattern", "luck_flow", "geo_context", "strength", "core_structure"}
    assert all(row["engine_enabled"] is False for row in p31a_rules)
    assert all(any(token in row["forbidden_usage"] for token in ["fortune", "direct_fortune_output"]) for row in p31a_rules)


def test_p31b_directory_completion_pack_removes_missing_directories_and_stays_shadow_only(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.knowledge_base_audit import run_p31_all_knowledge_coverage_audit

    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p31b_all_knowledge_directory_completion_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    audit = run_p31_all_knowledge_coverage_audit()
    seeded = archive.seed_current_knowledge_drafts()
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p31b_drafts = archive.list_knowledge_drafts(q="p31b.")["items"]
    p31b_rules = rule_db.list_bazi_rules(q="p31b.")["items"]

    assert pack["pack_id"] == "p31b.all_knowledge_directory_completion_pack.v1"
    assert len(pack["knowledge_drafts"]) == 36
    assert audit["directory_report"]["missing_directories"] == []
    assert audit["summary"]["by_taxonomy_status"].get("缺失", 0) == 0
    assert seeded["count"] == 234
    assert ingested["rule_count"] >= 232
    assert len(p31b_drafts) == 36
    assert len(p31b_rules) == 36
    assert {row["domain"] for row in p31b_drafts} >= {
        "career",
        "relationship",
        "health",
        "rule_db",
        "lab",
        "timing",
        "useful_god",
        "branch_advanced",
    }
    assert all(row["engine_enabled"] is False for row in p31b_rules)
    assert all(any(token in row["forbidden_usage"] for token in ["fortune", "auto_approval", "runtime_activation"]) for row in p31b_rules)


def test_lab_default_validation_cases_are_synthetic_explicit_pillars() -> None:
    cases = _default_validation_cases()

    assert cases
    assert all("chart" in case for case in cases)
    assert all("input" not in case for case in cases)
    assert all("NO_BIRTHDATE" in case["guardrails"] for case in cases)
    assert all(_run_case(case)["passed"] for case in cases)
