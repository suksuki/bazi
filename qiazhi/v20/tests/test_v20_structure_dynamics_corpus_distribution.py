from __future__ import annotations

from v20.validation import structure_dynamics_corpus_distribution as corpus_distribution


def test_v20_structure_dynamics_corpus_distribution_writes_latest_artifact(tmp_path, monkeypatch) -> None:
    def fake_runtime(*pillars, **kwargs):
        return {
            "chart_facts": {"day_master": pillars[2][0]},
            "structure_dynamics": {
                "dominant_chain_v2": {
                    "pattern_label": "食伤生财",
                    "pattern_key": "knowledge.semantic.output_generate_wealth",
                    "chain_key": "resource->output->wealth",
                    "state": "leaking",
                    "confidence": 0.9,
                    "path_score": 0.88,
                    "node_labels": ["癸正印", "甲比肩", "丙食神", "戊偏财"],
                },
                "dominant_path": {
                    "family_chain": ["resource", "self", "output", "wealth"],
                    "node_labels": ["癸正印", "甲比肩", "丙食神", "戊偏财"],
                    "score": 0.88,
                },
                "semantic_candidates": [
                    {"label": "食伤生财"},
                    {"label": "比劫夺财"},
                    {"label": "印制食伤"},
                ],
            },
        }

    monkeypatch.setattr(corpus_distribution, "run_runtime_from_pillars", fake_runtime)

    report = corpus_distribution.build_structure_dynamics_corpus_distribution(
        limit=4,
        run_id="test_sde_corpus",
        write=True,
        runtime_dir=tmp_path,
    )
    latest = corpus_distribution.read_latest_structure_dynamics_corpus_distribution(runtime_dir=tmp_path)

    assert report["version"] == "v20.structure_dynamics_corpus_distribution.v1"
    assert report["status"] == "completed"
    assert report["limit"] == 4
    assert report["unsupported_label_count"] == 0
    assert report["knowledge_coverage"]["status"] == "covered_current_scope"
    assert report["label_distribution"][0]["key"] == "食伤生财"
    assert latest["run_id"] == "test_sde_corpus"
    assert latest["runtime_mutation"] is False
    assert "NO_CORPUS_REPLAY_ON_ADMIN_READ" in latest["guardrails"]
