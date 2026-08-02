import asyncio

from abu_v60.db import engine
from abu_v60.main import _web_cache_control, app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text


async def _get(path: str):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://v60.test",
    ) as client:
        return await client.get(path)


def test_web_entry_revalidates_while_versioned_assets_are_immutable() -> None:
    assert _web_cache_control("/experience") == ("private, no-store, max-age=0, must-revalidate")
    assert _web_cache_control("/") == "private, no-store, max-age=0, must-revalidate"
    assert _web_cache_control("/assets/index-content-hash.js") == (
        "public, max-age=31536000, immutable"
    )
    assert _web_cache_control("/api/v60/bootstrap") is None


def test_manifest_has_no_v50_runtime_dependency() -> None:
    response = asyncio.run(_get("/api/v60/system/manifest"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["entry_experience"] == "PRIVATE_LIFE_TREE_HOME"
    assert payload["v50_runtime_dependency"] is False
    assert payload["authority"]["world_outcomes"] == "SYSTEM"
    assert payload["authority"]["interpretation"] == (
        "BOUNDED_REASONER_AND_SPECIALIST_MINGLI_AGENT"
    )
    assert payload["reasoner_runtime"]["status"] == "NOT_CONFIGURED"
    assert payload["reasoner_runtime"]["network_calls_enabled"] is False
    assert payload["engines"]["context"] == "v60.experience-context.003"
    assert payload["engines"]["mingli"] == "v60.mingli-cognitive-engine.039"
    assert payload["mingli_agent_runtime"]["status"] == "DISABLED"
    assert payload["mingli_agent_runtime"]["network_calls_enabled"] is False
    assert payload["mingli_agent_runtime"]["publication_allowed"] is False
    assert payload["mingli_agent_runtime"]["model_qualification_status"] == (
        "GEMMA4_PRODUCT_CANDIDATE_REQUIRES_OWNER_REVIEW"
    )
    assert payload["mingli_agent_runtime"]["reasoning_mode"] == "BLIND_READING"
    assert payload["mingli_agent_runtime"]["owner_review_allowed"] is True
    assert payload["mingli_agent_runtime"]["runtime_ref"] == ("v60.mingli-agent-runtime.022")
    assert payload["mingli_agent_runtime"]["packet_contract_ref"] == (
        "v60.mingli-agent-case-packet.003"
    )
    assert payload["mingli_agent_runtime"]["output_contract_ref"] == (
        "v60.mingli-agent-reading.005"
    )
    assert payload["mingli_agent_runtime"]["normalization_receipt_contract_ref"] == (
        "v60.mingli-agent-normalization-receipt.001"
    )
    assert payload["mingli_agent_runtime"]["adjudication_contract_ref"] == (
        "v60.mingli-agent-adjudication.009"
    )
    assert payload["mingli_agent_runtime"]["output_repair_contract_ref"] == (
        "v60.mingli-agent-output-repair.003"
    )
    assert payload["mingli_agent_runtime"]["method_adjudication"] == (
        "TYPED_CHECK_RULINGS_AND_SERVER_DERIVED_AGGREGATE"
    )
    profile = payload["mingli_agent_runtime"]["profile"]
    assert profile["agent_profile_ref"] == "v60.mingli-agent.whole-chart-cognition.021"
    assert profile["prompt_ref"] == "v60.prompt.mingli-agent-whole-chart.018"
    assert profile["prompt_view_version"] == "v60.mingli-agent-prompt-view.011"
    assert payload["mingli_agent_runtime"]["method_distillation_ref"] == (
        "v60.mingli-agent-method-distillation.003"
    )
    assert payload["mingli_agent_runtime"]["effective_root_method_ref"] == (
        "v60.mingli-effective-root-method.001"
    )
    assert payload["mingli_agent_runtime"]["regime_decision_contract_ref"] == (
        "v60.mingli-agent-regime-decision.001"
    )
    assert payload["mingli_agent_runtime"]["whole_chart_judgment_required"] is True
    assert payload["engines"]["story"] == "v60.life-story-engine.011"
    relation_effect_admission = payload["relation_effect_rule_admission"]
    assert relation_effect_admission["professional_rule_count"] == 0
    assert relation_effect_admission["admitted_effect_rule_profiles"] == []
    assert relation_effect_admission["runtime_effect_authority"] == "NONE"
    assert relation_effect_admission["policy"]["effect_conclusion_allowed"] is False
    assert relation_effect_admission["proposal"]["professionally_reviewed"] is False
    source_packages = payload["episode_source_packages"]
    assert source_packages["canonical_story"]["runtime_access"] == "ADMISSION_ONLY"
    assert {
        package["package_ref"] for package in source_packages["canonical_story"]["packages"]
    } == {
        "v60.episode-package.yanzhou-old-channel.v1",
        "v60.episode-package.yanzhou-wet-bank.v1",
        "v60.episode-package.yanzhou-shared-night-water.v1",
        "v60.episode-package.yanzhou-water-record.v1",
        "v60.episode-package.yanzhou-roster-duty.v1",
    }
    assert len(source_packages["canonical_story"]["transitions"]) == 4
    assert (
        source_packages["three_life_qualification"]["registry_version"]
        == "v60.episode-source-registry.003"
    )
    assert len(source_packages["three_life_qualification"]["packages"]) == 5
    assert len(source_packages["three_life_qualification"]["transitions"]) == 2


def test_health_binds_database_to_runtime_foundation() -> None:
    response = asyncio.run(_get("/api/v60/health"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["database"] == {
        "status": "ready",
        "foundation_version": "v60.foundation.028",
        "expected_foundation_version": "v60.foundation.028",
    }


def test_database_manifest_binds_current_mingli_agent_contracts() -> None:
    with engine.connect() as connection:
        manifest = connection.execute(
            text("SELECT manifest_json FROM platform.schema_manifest WHERE singleton_id = 1")
        ).scalar_one()
    assert manifest["schema_revision"] == "0036_mingli_model_trace"
    assert manifest["mingli_agent_packet_version"] == ("v60.mingli-agent-case-packet.003")
    assert manifest["mingli_agent_packet_compiler_version"] == (
        "v60.mingli-agent-packet-compiler.003"
    )
    assert manifest["mingli_agent_prompt_view_version"] == ("v60.mingli-agent-prompt-view.011")
    assert manifest["mingli_agent_reading_version"] == ("v60.mingli-agent-reading.005")
    assert manifest["mingli_agent_normalization_receipt_version"] == (
        "v60.mingli-agent-normalization-receipt.001"
    )
    assert manifest["mingli_agent_adjudication_version"] == ("v60.mingli-agent-adjudication.009")
    assert manifest["mingli_agent_output_repair_version"] == ("v60.mingli-agent-output-repair.003")
    assert manifest["mingli_agent_method_distillation_version"] == (
        "v60.mingli-agent-method-distillation.003"
    )
    assert manifest["mingli_agent_regime_contract_version"] == (
        "v60.mingli-agent-regime-decision.001"
    )
    assert manifest["mingli_agent_runtime_version"] == "v60.mingli-agent-runtime.022"
    assert manifest["mingli_effective_root_method_version"] == (
        "v60.mingli-effective-root-method.001"
    )
    assert manifest["mingli_stage_projection_version"] == (
        "v60.mingli-stage-projection.004"
    )
    assert manifest["mingli_corpus_qualification_version"] == (
        "v60.mingli-corpus-qualification.002"
    )
    assert manifest["mingli_case_materialization_version"] == (
        "v60.mingli-case-materialization.001"
    )
    assert manifest["mingli_synthetic_experiment_run_version"] == (
        "v60.mingli-synthetic-experiment-run.001"
    )
    assert manifest["mingli_synthetic_experiment_snapshot_version"] == (
        "v60.mingli-synthetic-experiment-snapshot.002"
    )
    assert manifest["mingli_synthetic_experiment_catalog_version"] == (
        "v60.mingli-synthetic-experiment-catalog.001"
    )
    assert manifest["mingli_synthetic_experiment_evaluator_version"] == (
        "v60.mingli-synthetic-experiment-evaluator.001"
    )
    assert manifest["mingli_synthetic_experiment_dev_gold_version"] == (
        "v60.mingli-synthetic-experiment-dev-gold.001"
    )
    assert manifest["mingli_reading_claim_graph_version"] == ("v60.mingli-reading-claim-graph.010")
    assert manifest["mingli_reading_summary_version"] == ("v60.mingli-reading-summary.006")


def test_case_workspace_requires_authentication() -> None:
    response = asyncio.run(_get("/api/v60/cases"))
    assert response.status_code == 401


def test_runtime_status_exposes_owner_integrity_without_case_content() -> None:
    response = asyncio.run(_get("/api/v60/system/runtime-status"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "READY"
    assert payload["canonical_write_owners"]["world"] == "world"
    assert payload["canonical_write_owners"]["dream"] == "dream-game"
    assert payload["integrity"] == {
        "invalid_dream_command_receipts": 0,
        "invalid_dream_return_attention_applications": 0,
        "invalid_dream_return_attention_selections": 0,
        "invalid_dream_private_inquiries": 0,
        "invalid_dream_personal_observation_tasks": 0,
        "invalid_dream_personal_observation_checkins": 0,
        "invalid_life_tree_admissions": 0,
        "invalid_relation_effect_evidence_material_records": 0,
        "invalid_relation_effect_evidence_request_receipts": 0,
        "invalid_world_actor_admissions": 0,
        "invalid_world_event_admissions": 0,
        "orphan_encounters": 0,
        "reveal_without_settled_world_event": 0,
        "unadmitted_life_trees": 0,
        "unadmitted_questions": 0,
        "unadmitted_world_actors": 0,
        "unadmitted_world_events": 0,
        "unhashed_question_organs": 0,
    }
    assert payload["episode_catalog"]["status"] == "READY"
    assert payload["episode_catalog"]["active_template_episode_count"] == 10
    assert payload["episode_catalog"]["active_episode_count"] == (
        10 + payload["episode_catalog"]["active_materialized_opportunity_count"]
    )
    assert payload["episode_catalog"]["active_transition_count"] == 6
    assert len(payload["episode_catalog"]["graph_hash"]) == 64
    assert payload["scene_registry"]["status"] == "READY"
    assert len(payload["scene_registry"]["scenes"]) == 6
    assert payload["media_runtime"]["status"] == "READY"
    assert payload["media_runtime"]["cues"]["abu_idle"]["cue_ref"] == ("cue.dream.abu-idle.v1")
    assert "case_ref" not in payload


def test_bootstrap_exposes_only_admitted_runtime_media_bindings() -> None:
    response = asyncio.run(_get("/api/v60/bootstrap"))
    assert response.status_code == 200
    media = response.json()["media"]

    assert set(media["assets"]) == {
        "brand_logo",
        "grove_background",
        "life_world_background",
        "home_day_background",
        "home_night_background",
        "home_day_logo",
        "home_night_logo",
        "home_profile_leaf",
        "home_lab_flower",
        "mingli_growth_day_video",
        "mingli_growth_day_start",
        "mingli_growth_day_poster",
        "mingli_growth_night_video",
        "mingli_growth_night_start",
        "mingli_growth_night_poster",
    }
    assert set(media["cues"]) == {"abu_idle", "abu_guide_left", "dodo_idle"}
    assert media["cues"]["abu_guide_left"]["trigger"] == (
        "NEW_ENCOUNTER_HAS_UNOBSERVED_LEFT_TREE_ORGAN"
    )
    assert media["cues"]["dodo_idle"]["trigger"] == ("DODO_VISIBLE_IN_MINGLI_NARRATION_STATE")
