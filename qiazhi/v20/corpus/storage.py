from __future__ import annotations


def corpus_storage_policy() -> dict[str, object]:
    return {
        "version": "v20.corpus_storage_policy.v1",
        "required_hashes": ["input_hash", "core_version", "feature_compiler_version", "artifact_hash"],
        "guardrails": ["VERSIONED_ARTIFACTS_ONLY", "NO_UNREVIEWED_RUNTIME_USE"],
    }
