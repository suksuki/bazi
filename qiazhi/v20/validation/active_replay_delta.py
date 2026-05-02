from __future__ import annotations


def active_replay_delta_report(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    changed_keys = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
    return {
        "version": "v20.active_replay_delta.v1",
        "changed_keys": changed_keys,
        "runtime_mutation": False,
        "guardrails": ["ACTIVE_REPLAY_REPORT_ONLY", "NO_UNTRACED_RUNTIME_OVERRIDE"],
    }
