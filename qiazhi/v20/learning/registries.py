from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RegistrySpec:
    registry_key: str
    postgres_table: str
    owner_module: str
    purpose: str
    write_policy: str
    activation_policy: str = "requires_trace_validation_and_decision_record"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guardrails"] = [
            "REGISTRY_IS_AUDITABLE",
            "NO_DIRECT_CORE_TRUTH_MUTATION",
            "POSTGRES_IS_AUTHORITATIVE_STORE",
        ]
        return payload


REGISTRY_SPECS = (
    RegistrySpec(
        registry_key="DatasetRegistry",
        postgres_table="v20_corpus_snapshots",
        owner_module="v20.corpus",
        purpose="Tracks corpus snapshots, coverage maps, and precompute batches.",
        write_policy="dry_run_snapshot_records_only_until_reviewed",
    ),
    RegistrySpec(
        registry_key="ArtifactRegistry",
        postgres_table="v20_artifact_registry",
        owner_module="v20.learning",
        purpose="Tracks ranking, retrieval, calibration, eval, and model artifacts.",
        write_policy="artifact_hash_and_eval_reference_required",
    ),
    RegistrySpec(
        registry_key="RunRegistry",
        postgres_table="v20_run_registry",
        owner_module="v20.learning",
        purpose="Tracks local, service, validation, corpus, and learning runs.",
        write_policy="append_only_run_records",
    ),
    RegistrySpec(
        registry_key="DecisionRegistry",
        postgres_table="v20_decision_registry",
        owner_module="v20.learning",
        purpose="Tracks human or validation decisions for active runtime iteration.",
        write_policy="decision_record_required_before_runtime_use",
    ),
    RegistrySpec(
        registry_key="FeedbackLedger",
        postgres_table="v20_feedback_ledger",
        owner_module="v20.interaction",
        purpose="Tracks anonymized feedback summaries and calibration signals.",
        write_policy="anonymized_or_hashed_only_no_raw_private_text",
    ),
)


def registry_manifest() -> dict[str, object]:
    return {
        "version": "v20.learning_registry_manifest.v1",
        "registries": [row.to_dict() for row in REGISTRY_SPECS],
        "runtime_mutation": False,
        "guardrails": [
            "REGISTRY_MANIFEST_ONLY",
            "NO_DATABASE_CONNECTION_ATTEMPTED",
            "NO_RUNTIME_OVERRIDE_FROM_FEEDBACK_ALONE",
        ],
    }
