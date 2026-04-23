from __future__ import annotations

from v17_rebirth.testing.parameter_candidate_runner import (
    build_current_parameter_experiment_report,
    build_parameter_experiments_from_report,
)


def test_candidate_runner_turns_hotspot_report_into_dry_run_experiment() -> None:
    experiments = build_parameter_experiments_from_report(
        {
            "protocol": "v17.synthetic_tuning_bridge.v1",
            "audits": [{"case_id": "real.audit.demo"}],
            "parameter_candidate_plan": [
                {
                    "candidate_id": "candidate::relation_formation.sanhe",
                    "parameter_family": "relation_formation.sanhe",
                    "issue_count": 2,
                    "recommended_action": "review_relation_family_factor_and_visibility_gate",
                    "safety_gate": "manual_review_required",
                    "synthetic_cases": ["l1.relation.sanhe.month_visible"],
                }
            ],
        }
    )

    assert len(experiments) == 1
    experiment = experiments[0]
    assert experiment["protocol"] == "v17.parameter_candidate_runner.v1"
    assert experiment["application_mode"] == "dry_run_plan_only"
    assert experiment["parameter_family"] == "relation_formation.sanhe"
    assert experiment["candidate_patch"]["patch_mode"] == "review_only"
    assert "REL_FAMILY_BASE_FACTOR_SANHE" in experiment["candidate_patch"]["parameters_to_review"]
    assert "must_not_change_config_without_explicit_approval" in experiment["safety_gates"]


def test_current_parameter_experiment_report_is_well_formed_when_green() -> None:
    report = build_current_parameter_experiment_report()

    assert report["protocol"] == "v17.parameter_candidate_runner.v1"
    assert report["state"] in {"no_experiment_needed", "manual_review_required"}
    assert isinstance(report["experiments"], list)
    if report["experiments"]:
        assert report["experiments"][0]["application_mode"] == "dry_run_plan_only"

