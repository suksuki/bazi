from __future__ import annotations

import json
from pathlib import Path

from product.database_schema import SCHEMA_PATH, product_schema_hash
from scripts.v50_export_experience_schemas import (
    CONTRACTS,
    SCHEMA_OUTPUT,
    TYPESCRIPT_OUTPUT,
    render_typescript_contracts,
)


ROOT = Path(__file__).resolve().parents[1]


def test_one_authority_registry_replaces_split_owners() -> None:
    manifest = json.loads(
        (ROOT / "config/production_authority_manifest_v1.json").read_text(encoding="utf-8")
    )

    assert manifest["registry_status"] == "canonical_module_and_schema_owner"
    assert manifest["classification"]["new_transitional_layers_allowed"] is False
    assert manifest["module_ownership"]["database_schema"] == "deploy/postgres_v50_schema.sql"
    assert manifest["schema_ownership"]["typescript_handwritten_contract_owner"] is False
    for retired in manifest["supersedes"]:
        assert not (ROOT / "config" / retired).exists()


def test_postgres_schema_has_one_ddl_owner_and_all_stores_delegate_to_it() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    required_tables = {
        "v50_user_accounts",
        "v50_user_sessions",
        "v50_bazi_profiles",
        "v50_mingli_agent_cases",
        "v50_mingli_cognitive_jobs",
        "v50_voice_validation_sessions",
        "v50_theater_sessions",
        "v50_theater_events",
        "v50_legacy_runtime_usage",
    }
    assert all(f"CREATE TABLE IF NOT EXISTS {name}" in schema for name in required_tables)
    assert len(product_schema_hash()) == 64

    store_paths = [
        "product_store.py",
        "agent_case_store.py",
        "agent_job_store.py",
        "theater_store.py",
        "voice_validation_store.py",
        "legacy_usage.py",
    ]
    for name in store_paths:
        source = (ROOT / "apps/product" / name).read_text(encoding="utf-8")
        assert "ensure_product_database_schema(database_url)" in source
        assert "CREATE TABLE" not in source
        assert "ALTER TABLE" not in source


def test_python_contracts_generate_json_schema_and_typescript_without_drift() -> None:
    generated_typescript = TYPESCRIPT_OUTPUT.read_text(encoding="utf-8")
    assert generated_typescript == render_typescript_contracts()
    assert "approved_claims?:" not in generated_typescript
    assert "hidden_stems?:" not in generated_typescript
    assert (ROOT / "apps/product/experience_shell/src/contracts.ts").read_text(
        encoding="utf-8"
    ) == 'export * from "./contracts.generated";\n'
    for filename, contract in CONTRACTS.items():
        checked_in = json.loads((SCHEMA_OUTPUT / filename).read_text(encoding="utf-8"))
        assert checked_in == contract.model_json_schema()


def test_sync_and_progressive_baselines_share_one_command_owner() -> None:
    api_source = (ROOT / "apps/product/agent_api.py").read_text(encoding="utf-8")
    service_source = (ROOT / "apps/product/agent_command_service.py").read_text(
        encoding="utf-8"
    )

    assert api_source.count("baseline_commands.execute(") == 2
    assert "compile_chart_world(" not in api_source
    assert "commit_baseline_life_case(" not in api_source
    assert "class BaselineCaseCommandService" in service_source
    assert service_source.count("self._case_store.save(") == 1
