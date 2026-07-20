from __future__ import annotations

from scripts.v50_run_model_context_baseline import build_model_context_baseline


def test_model_context_baseline_keeps_one_non_downgraded_cognitive_authority(monkeypatch) -> None:
    monkeypatch.setenv("V50_MINGLI_AGENT_MODEL", "qwen3.5:35b")
    monkeypatch.setenv("V50_MINGLI_PATTERN_MODEL", "qwen3.5:35b")
    monkeypatch.setenv("V50_MINGLI_WORK_MODEL", "qwen3.5:35b")
    monkeypatch.setenv("V50_MINGLI_DOMAIN_MODEL", "qwen3.5:35b")
    report = build_model_context_baseline(
        endpoint="http://example.invalid",
        available_models=[{"name": "qwen3.5:35b"}, {"name": "qwen3:8b"}],
        running_models=[{"name": "qwen3.5:35b", "size_vram": 23_000_000_000}],
    )

    assert report["status"] == "passed"
    assert report["observed_data"]["cognitive_models"] == ["qwen3.5:35b"]
    assert report["observed_data"]["cognitive_role_drift"] is False
    assert report["observed_data"]["critical_attention_omissions"] == 0
    assert report["boundary_status"]["model_downgraded"] is False
