from __future__ import annotations


def corpus_snapshot_diff(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    changed = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
    return {
        "version": "v20.corpus_snapshot_diff.v1",
        "changed_keys": changed,
        "guardrails": ["DIFF_REPORT_ONLY", "NO_RUNTIME_MUTATION"],
    }
