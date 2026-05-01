from __future__ import annotations


def shadow_delta_report(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    changed_keys = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
    return {
        "version": "v20.shadow_delta.v1",
        "changed_keys": changed_keys,
        "runtime_mutation": False,
        "guardrails": ["SHADOW_REPORT_ONLY", "NO_PROMOTION_WITHOUT_DECISION"],
    }
