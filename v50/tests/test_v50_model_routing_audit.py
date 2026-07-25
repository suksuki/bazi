from pathlib import Path

from scripts.v50_audit_model_routing import audit_model_routing


ROOT = Path(__file__).resolve().parents[1]


def test_model_routing_audit_accepts_the_qualified_deployment_example():
    report = audit_model_routing(
        registry_path=ROOT / "config/model_registry.json",
        env_path=ROOT / "deploy/v50.env.production.example",
    )
    assert report["status"] == "passed"
    assert report["deployment_allowed"] is True
    assert report["drift"] == []


def test_model_routing_audit_blocks_an_unreviewed_cognitive_model(tmp_path):
    env_path = tmp_path / "drift.env"
    env_path.write_text("V50_MINGLI_PATTERN_MODEL=qwen3.6:27b\n", encoding="utf-8")
    report = audit_model_routing(
        registry_path=ROOT / "config/model_registry.json",
        env_path=env_path,
    )
    assert report["status"] == "blocked"
    assert report["deployment_allowed"] is False
    assert report["drift"] == [{
        "role": "cognitive_pattern",
        "model_env": "V50_MINGLI_PATTERN_MODEL",
        "qualified_model": "qwen3.5:35b",
        "actual_model": "qwen3.6:27b",
        "status": "drifted",
    }]
