from pathlib import Path

from app.core.config.physics_settings import resolve_physics_settings
from app.core.evolution.dna_registry import (
    RuleGene,
    append_routing_audit_item,
    apply_dna_overlay,
    save_rule_genes,
    set_evolution_admission,
)


def test_apply_dna_overlay_with_admission_and_parameters(tmp_path: Path, monkeypatch) -> None:
    dna_p = tmp_path / "dna_registry.json"
    adm_p = tmp_path / "evolution_admission.json"
    save_rule_genes(
        [
            RuleGene(
                skill_id="l1_prod_01",
                evolved_parameters={"L1_OP_PROD_ETA": 1.11},
                fitness_score=0.9,
                generation_id=3,
            )
        ],
        path=dna_p,
    )
    monkeypatch.setenv("QIAZHI_DNA_REGISTRY_PATH", str(dna_p))
    monkeypatch.setenv("QIAZHI_EVOLUTION_ADMISSION_PATH", str(adm_p))
    monkeypatch.delenv("QIAZHI_EVOLUTION_ADMIT", raising=False)
    set_evolution_admission(True, path=adm_p)
    base = resolve_physics_settings({})
    assert abs(float(base["L1_OP_PROD_ETA"]) - 1.11) < 1e-6


def test_dna_overlay_blocked_when_not_admitted(tmp_path: Path, monkeypatch) -> None:
    dna_p = tmp_path / "dna_registry.json"
    adm_p = tmp_path / "evolution_admission.json"
    save_rule_genes(
        [
            RuleGene(
                skill_id="l1_prod_01",
                evolved_parameters={"L1_OP_PROD_ETA": 2.0},
                fitness_score=0.99,
                generation_id=1,
            )
        ],
        path=dna_p,
    )
    monkeypatch.setenv("QIAZHI_DNA_REGISTRY_PATH", str(dna_p))
    monkeypatch.setenv("QIAZHI_EVOLUTION_ADMISSION_PATH", str(adm_p))
    monkeypatch.delenv("QIAZHI_EVOLUTION_ADMIT", raising=False)
    set_evolution_admission(False, path=adm_p)
    base = resolve_physics_settings({})
    assert abs(float(base["L1_OP_PROD_ETA"]) - 1.0) < 1e-6


def test_legacy_gene_json_evolved_weight(tmp_path: Path, monkeypatch) -> None:
    dna_p = tmp_path / "dna_registry.json"
    adm_p = tmp_path / "evolution_admission.json"
    dna_p.write_text(
        '{"version":1,"genes":[{"skill_id":"l1_prod_01","evolved_weight":1.07,"confidence_score":0.8}]}',
        encoding="utf-8",
    )
    monkeypatch.setenv("QIAZHI_DNA_REGISTRY_PATH", str(dna_p))
    monkeypatch.setenv("QIAZHI_EVOLUTION_ADMISSION_PATH", str(adm_p))
    monkeypatch.delenv("QIAZHI_EVOLUTION_ADMIT", raising=False)
    set_evolution_admission(True, path=adm_p)
    base = resolve_physics_settings({})
    assert abs(float(base["L1_OP_PROD_ETA"]) - 1.07) < 1e-6


def test_resolve_without_dna_file_respects_overrides(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("QIAZHI_DNA_REGISTRY_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setenv("QIAZHI_EVOLUTION_ADMISSION_PATH", str(tmp_path / "adm.json"))
    set_evolution_admission(False, path=tmp_path / "adm.json")
    s = resolve_physics_settings({"L1_OP_PROD_ETA": 0.88})
    assert abs(float(s["L1_OP_PROD_ETA"]) - 0.88) < 1e-6


def test_apply_dna_overlay_direct_low_fitness_skipped(tmp_path: Path, monkeypatch) -> None:
    dna_p = tmp_path / "dna_registry.json"
    adm_p = tmp_path / "evolution_admission.json"
    save_rule_genes(
        [
            RuleGene(
                skill_id="l1_prod_01",
                evolved_parameters={"L1_OP_PROD_ETA": 9.0},
                fitness_score=0.01,
                generation_id=0,
            )
        ],
        path=dna_p,
    )
    monkeypatch.setenv("QIAZHI_DNA_REGISTRY_PATH", str(dna_p))
    monkeypatch.setenv("QIAZHI_EVOLUTION_ADMISSION_PATH", str(adm_p))
    set_evolution_admission(True, path=adm_p)
    out = apply_dna_overlay({"L1_OP_PROD_ETA": 1.0})
    assert abs(float(out["L1_OP_PROD_ETA"]) - 1.0) < 1e-6


def test_append_routing_audit_item_appends_and_writes_meta() -> None:
    pkg = {
        "routing_decision": "优先盲派",
        "strategy_applied": "conservative",
        "conflict_events": [{"x": 1}],
        "merged_impact": {"a": 1, "b": 2},
    }
    tensor: dict = {"audit_log": {}, "meta": {}}
    append_routing_audit_item(tensor, pkg)
    items = tensor["audit_log"]["causal_routing_audit_items"]
    assert len(items) == 1
    assert items[0]["role"] == "CausalRouter"
    assert items[0]["routing_decision"] == "优先盲派"
    assert items[0]["conflict_event_count"] == 1
    assert tensor["meta"]["causal_routing"] is pkg

    append_routing_audit_item(tensor, {**pkg, "routing_decision": "第二轮"})
    assert len(tensor["audit_log"]["causal_routing_audit_items"]) == 2
    assert tensor["meta"]["causal_routing"]["routing_decision"] == "第二轮"
