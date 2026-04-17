import json
from pathlib import Path

from app.core import runtime_config


def test_runtime_config_defaults_when_missing(monkeypatch, tmp_path: Path):
    cfg_file = tmp_path / "runtime_config.json"
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", cfg_file)
    cfg = runtime_config.get_runtime_config()
    assert "llm" in cfg
    assert cfg["llm"]["provider"] == "ollama"
    assert cfg["llm"]["narrative_strategy"] == "assertion_tree"


def test_runtime_config_save_and_reload(monkeypatch, tmp_path: Path):
    cfg_file = tmp_path / "runtime_config.json"
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", cfg_file)
    saved = runtime_config.set_runtime_config(
        {"llm": {"base_url": "http://x/v1", "api_key": "k", "model": "m1"}}
    )
    assert saved["llm"]["base_url"] == "http://x/v1"
    loaded = runtime_config.get_runtime_config()
    assert loaded["llm"]["model"] == "m1"
    raw = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert raw["llm"]["api_key"] == "k"


def test_runtime_config_causal_routing_merge(monkeypatch, tmp_path: Path) -> None:
    cfg_file = tmp_path / "runtime_config.json"
    monkeypatch.setattr(runtime_config, "_CONFIG_FILE", cfg_file)
    cfg_file.write_text(
        json.dumps(
            {
                "llm": {"model": "keep-me"},
                "causal_routing": {"conflict_strategy": "conservative", "school_sovereignty": False},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    runtime_config.set_runtime_config({"causal_routing": {"conflict_strategy": "school_priority"}})
    loaded = runtime_config.get_runtime_config()
    assert loaded["llm"]["model"] == "keep-me"
    assert loaded["causal_routing"]["conflict_strategy"] == "school_priority"
    assert loaded["causal_routing"]["school_sovereignty"] is False
