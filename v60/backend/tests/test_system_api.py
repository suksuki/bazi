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

    assert payload["product_version"] == "0.2.0"
    assert payload["entry_experience"] == "MINGLI_HOME"
    assert payload["v50_runtime_dependency"] is False
    assert payload["engines"] == {
        "decision": "v60.cognitive-decision-kernel.004",
        "mingli": "v60.mingli-cognitive-engine.051",
    }
    assert payload["architecture"]["product_units"] == ["unit-mingli", "unit-abu"]
    assert payload["architecture"]["entry_flow"] == [
        "AUTH",
        "CHART",
        "MINGLI_READING",
        "ABU_SAYS",
    ]
    assert payload["architecture"]["internal_surfaces_registered"] is False
    assert payload["public_product_exposure"] == {
        "policy_version": "v60.public-product-exposure.003",
        "public_units": ["MINGLI_READING", "ABU_SAYS"],
        "lab": {
            "status": "INTERNAL_ONLY",
            "public_entry_allowed": False,
            "public_route_allowed": False,
        },
    }
    assert payload["authority"] == {
        "chart": "DETERMINISTIC_LOCAL_SYSTEM",
        "interpretation": "LOCAL_QWEN_WITH_LOCAL_NORMALIZATION",
        "expression": "SAME_READING_ONLY",
        "consent": "HUMAN",
        "formal_commit": "EPISTEMIC_GATE",
    }

    focused = payload["mingli_focused_runtime"]
    assert focused["runtime_ref"] == "v60.mingli-focused-runtime.001"
    assert focused["generation_mode"] == "PROGRESSIVE_ONE_FOCUS_PER_REQUEST"
    assert focused["product_call_count_per_request"] == 1
    assert focused["runtime_role"] == "PRODUCT_FOCUSED_READING"
    assert focused["openai_api_required"] is False
    assert focused["production_dependencies"] == [
        "DETERMINISTIC_LOCAL_SYSTEM",
        "LOCAL_QWEN",
    ]
    assert focused["publication_allowed"] is False
    assert payload["speech_runtime"]["generation_mode"] == (
        "LAZY_FROM_PERSISTED_FOCUSED_PASS"
    )
    assert payload["speech_runtime"]["timeline_version"] == (
        "v60.mingli-focused-speech-timeline.001"
    )
    assert payload["speech_runtime"]["clock_source"] == "HTML_AUDIO_CURRENT_TIME"
    assert payload["speech_runtime"]["subtitle_granularity"] == "SENTENCE_OR_CLAUSE"
    assert payload["speech_runtime"]["particle_focus"] == "EXPLICIT_COORDINATE_TERMS_ONLY"

    assert "mingli_agent_runtime" not in payload
    assert "mingli_synthetic_distillation_runtime" not in payload
    assert "episode_catalog" not in payload
    assert "episode_source_packages" not in payload


def test_health_binds_database_to_runtime_foundation() -> None:
    response = asyncio.run(_get("/api/v60/health"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["database"] == {
        "status": "ready",
        "foundation_version": "v60.foundation.045",
        "expected_foundation_version": "v60.foundation.045",
    }


def test_database_manifest_binds_current_mingli_agent_contracts() -> None:
    with engine.connect() as connection:
        manifest = connection.execute(
            text("SELECT manifest_json FROM platform.schema_manifest WHERE singleton_id = 1")
        ).scalar_one()
    assert manifest["schema_revision"].startswith("0053_")
    assert manifest["mingli_agent_packet_version"] == ("v60.mingli-agent-case-packet.003")
    assert manifest["mingli_agent_packet_compiler_version"] == (
        "v60.mingli-agent-packet-compiler.003"
    )
    assert manifest["mingli_agent_prompt_view_version"] == ("v60.mingli-agent-prompt-view.019")
    assert manifest["mingli_agent_reading_version"] == ("v60.mingli-agent-reading.006")
    assert manifest["mingli_agent_normalization_receipt_version"] == (
        "v60.mingli-agent-normalization-receipt.001"
    )
    assert manifest["mingli_agent_adjudication_version"] == ("v60.mingli-agent-adjudication.013")
    assert manifest["mingli_agent_output_repair_version"] == ("v60.mingli-agent-output-repair.004")
    assert manifest["mingli_agent_method_distillation_version"] == (
        "v60.mingli-agent-method-distillation.006"
    )
    assert manifest["mingli_agent_regime_contract_version"] == (
        "v60.mingli-agent-regime-decision.002"
    )
    assert manifest["mingli_agent_runtime_version"] == "v60.mingli-agent-runtime.035"
    assert manifest["mingli_effective_root_method_version"] == (
        "v60.mingli-effective-root-method.001"
    )
    assert manifest["mingli_stage_projection_version"] == ("v60.mingli-stage-projection.004")
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
        "v60.mingli-synthetic-experiment-snapshot.004"
    )
    assert manifest["mingli_synthetic_experiment_catalog_version"] == (
        "v60.mingli-synthetic-experiment-catalog.007"
    )
    assert manifest["mingli_synthetic_experiment_evaluator_version"] == (
        "v60.mingli-synthetic-experiment-evaluator.010"
    )
    assert manifest["mingli_synthetic_experiment_dev_gold_version"] == (
        "v60.mingli-synthetic-experiment-dev-gold.006"
    )
    assert manifest["mingli_synthetic_suite_catalog_version"] == (
        "v60.mingli-synthetic-suite-catalog.005"
    )
    assert manifest["mingli_month_coordinate_discipline_version"] == (
        "v60.mingli-month-coordinate-discipline.001"
    )
    assert manifest["mingli_raw_judgment_coherence_version"] == (
        "v60.mingli-raw-judgment-coherence.001"
    )
    assert manifest["mingli_synthetic_distillation_runtime_version"] == (
        "v60.mingli-synthetic-distillation-runtime.001"
    )
    assert manifest["mingli_synthetic_distillation_prompt_version"] == (
        "v60.prompt.mingli-synthetic-distillation.001"
    )
    assert manifest["mingli_synthetic_distillation_pass_version"] == (
        "v60.mingli-synthetic-distillation-pass.001"
    )
    assert manifest["mingli_synthetic_distillation_evaluator_version"] == (
        "v60.mingli-synthetic-distillation-evaluator.001"
    )
    assert manifest["mingli_synthetic_distillation_run_version"] == (
        "v60.mingli-synthetic-distillation-run.001"
    )
    assert manifest["mingli_synthetic_distillation_provider_profile_ref"] == (
        "v60.model-serving.qwen38-27b-mingli-distillation.001"
    )
    assert manifest["mingli_synthetic_suite_run_request_version"] == (
        "v60.mingli-synthetic-suite-run-request.001"
    )
    assert manifest["mingli_synthetic_training_status_version"] == (
        "v60.mingli-synthetic-training-status.001"
    )
    assert manifest["mingli_synthetic_suite_runner_version"] == (
        "v60.mingli-synthetic-suite-runner.002"
    )
    assert manifest["mingli_synthetic_suite_run_version"] == ("v60.mingli-synthetic-suite-run.002")
    assert manifest["mingli_reading_claim_graph_version"] == ("v60.mingli-reading-claim-graph.010")
    assert manifest["mingli_focused_runtime_version"] == ("v60.mingli-focused-runtime.001")
    assert manifest["mingli_focused_reading_version"] == ("v60.mingli-focused-reading.001")
    assert manifest["mingli_focused_pass_version"] == ("v60.mingli-focused-pass.001")
    assert manifest["mingli_focused_request_version"] == ("v60.mingli-focused-request.001")
    assert manifest["mingli_focused_pass_record_version"] == ("v60.mingli-focused-pass-record.001")
    assert manifest["mingli_focused_pass_request_version"] == (
        "v60.mingli-focused-pass-request.001"
    )
    assert manifest["mingli_focused_prompt_version"] == ("v60.prompt.mingli-focused-reading.001")
    assert manifest["mingli_reading_summary_version"] == ("v60.mingli-reading-summary.008")


def test_case_workspace_requires_authentication() -> None:
    response = asyncio.run(_get("/api/v60/cases"))
    assert response.status_code == 401


def test_runtime_status_exposes_only_public_runtime_readiness() -> None:
    response = asyncio.run(_get("/api/v60/system/runtime-status"))
    assert response.status_code == 200
    payload = response.json()

    assert set(payload) == {
        "status",
        "foundation_version",
        "entry_experience",
        "public_product_exposure",
        "mingli_focused_runtime",
        "speech_runtime",
    }
    assert payload["status"] == "READY"
    assert payload["entry_experience"] == "MINGLI_HOME"
    assert payload["public_product_exposure"]["public_units"] == [
        "MINGLI_READING",
        "ABU_SAYS",
    ]
    assert "case_ref" not in payload
    assert "integrity" not in payload
    assert "episode_catalog" not in payload


def test_bootstrap_exposes_only_public_release_media_bindings() -> None:
    response = asyncio.run(_get("/api/v60/bootstrap"))
    assert response.status_code == 200
    payload = response.json()
    media = payload["media"]

    assert payload["experience"] == {
        "state": "MINGLI_READY",
        "entry": "MINGLI_HOME",
        "unavailable_reason": None,
    }
    assert set(media["assets"]) == {
        "brand_logo",
        "login_life_tree_background",
        "home_day_background",
        "home_night_background",
        "home_day_logo",
        "home_night_logo",
        "home_profile_leaf",
        "mingli_growth_day_video",
        "mingli_growth_day_start",
        "mingli_growth_day_poster",
        "mingli_growth_night_video",
        "mingli_growth_night_start",
        "mingli_growth_night_poster",
        "mingli_lab_day_background",
        "mingli_lab_night_background",
    }
    assert set(media["cues"]) == {"abu_idle", "dodo_idle"}
    assert media["cues"]["abu_idle"]["cue_ref"] == "cue.mingli.abu-idle.v1"
    assert media["cues"]["abu_idle"]["trigger"] == "ABU_VISIBLE_IN_MINGLI_READING"


def test_internal_lab_and_legacy_internal_home_are_not_registered_publicly() -> None:
    async def request() -> tuple[int, int]:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://v60.test",
        ) as client:
            lab = await client.get("/api/v60/mingli/lab/synthetic-experiments")
            internal_home = await client.get("/api/v60/experience/home/internal")
            return lab.status_code, internal_home.status_code

    assert asyncio.run(request()) == (404, 404)
