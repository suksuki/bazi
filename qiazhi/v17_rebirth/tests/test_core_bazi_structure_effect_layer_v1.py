from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v17_rebirth.backend.api import v18_1_predictive as api_module
from v17_rebirth.backend.api.app import app
from v17_rebirth.backend.services import core_bazi_feature_layer as feature_layer
from v17_rebirth.backend.services import core_bazi_strength_model as strength_model
from v17_rebirth.backend.services import core_bazi_structure_effect_layer as structure_layer


def _chart(year: str, month: str, day: str, hour: str, *, luck: str | None = None, flow: str | None = None) -> dict:
    chart = {
        "chart_id": f"chart-structure-{year}-{month}-{day}-{hour}",
        "four_pillars": {
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
        },
    }
    if luck:
        chart["luck_pillar"] = luck
    if flow:
        chart["flow_pillar"] = flow
    return {"chart_snapshot": chart}


def _pipeline(chart: dict) -> tuple[dict, dict]:
    core = feature_layer.extract_core_bazi_features(chart)
    strength = strength_model.evaluate_core_strength({"core_feature_bundle": core})
    return core, strength


def test_structure_effect_clash_activates_and_destabilizes_vault() -> None:
    core, strength = _pipeline(_chart("丁巳", "乙酉", "乙丑", "乙卯", luck="壬子", flow="己未"))
    structure = structure_layer.evaluate_core_structure_effect({"core_feature_bundle": core, "core_strength_bundle": strength})

    clash = next(item for item in structure["relation_effects"] if item["source_relation"]["relation_type"] == "clash")
    assert clash["activation_effect"] > 0
    assert clash["stability_effect"] < 0
    assert clash["risk_effect"] > 0

    vault = next(item for item in structure["vault_effects"] if item["vault_branch"] == "丑")
    assert vault["vault_state"] == "opened_by_clash"
    assert vault["activation_effect"] > 0
    assert vault["liquidity_effect"] > 0
    assert vault["risk_effect"] > 0


def test_structure_effect_harmony_stabilizes_and_locks() -> None:
    core, strength = _pipeline(_chart("丁巳", "乙酉", "乙丑", "乙卯", luck="壬子"))
    structure = structure_layer.evaluate_core_structure_effect({"core_feature_bundle": core, "core_strength_bundle": strength})

    harmony = [item for item in structure["relation_effects"] if item["source_relation"]["relation_type"] in {"six_harmony", "three_harmony"}]
    assert harmony
    assert all(item["stability_effect"] > 0 for item in harmony)
    assert any(item["suppression_effect"] > 0 for item in harmony)

    vault = next(item for item in structure["vault_effects"] if item["vault_branch"] == "丑")
    assert vault["vault_state"] == "locked_by_combination"
    assert vault["stability_effect"] > 0
    assert vault["activation_effect"] < 0


def test_structure_effect_three_harmony_amplifies_target_structure() -> None:
    core, strength = _pipeline(_chart("丁巳", "乙酉", "乙丑", "乙卯"))
    structure = structure_layer.evaluate_core_structure_effect({"core_feature_bundle": core, "core_strength_bundle": strength})

    three_harmony = next(item for item in structure["relation_effects"] if item["source_relation"]["relation_type"] == "three_harmony")
    assert three_harmony["source_relation"]["branches"] == ["巳", "酉", "丑"]
    assert three_harmony["target"]["target_element"] == "metal"
    assert three_harmony["amplification_effect"] > 0
    assert three_harmony["effect_type"] == "structure_combination"


def test_structure_effect_vault_closed_and_blocked_states() -> None:
    closed_core, closed_strength = _pipeline(_chart("丁卯", "甲寅", "乙丑", "乙亥"))
    closed = structure_layer.evaluate_core_structure_effect({"core_feature_bundle": closed_core, "core_strength_bundle": closed_strength})
    closed_vault = next(item for item in closed["vault_effects"] if item["vault_branch"] == "丑")
    assert closed_vault["vault_state"] == "closed"
    assert closed_vault["activation_effect"] == 0.0

    blocked_core, blocked_strength = _pipeline(_chart("丁卯", "乙酉", "乙丑", "甲戌"))
    blocked = structure_layer.evaluate_core_structure_effect({"core_feature_bundle": blocked_core, "core_strength_bundle": blocked_strength})
    blocked_vault = next(item for item in blocked["vault_effects"] if item["vault_branch"] == "丑")
    assert blocked_vault["vault_state"] == "blocked_by_disruptive_relation"
    assert blocked_vault["suppression_effect"] > 0
    assert blocked_vault["risk_effect"] > 0


def test_structure_store_has_no_prediction_or_domain_conclusion_side_effects(tmp_path: Path) -> None:
    core, strength = _pipeline(_chart("丁巳", "乙酉", "乙丑", "乙卯", luck="壬子", flow="己未"))
    store = structure_layer.CoreBaziStructureEffectStore(tmp_path / "structure.json")
    structure = store.evaluate_and_store({"core_feature_bundle": core, "core_strength_bundle": strength})
    loaded = store.get_bundle(structure["structure_bundle_id"])

    forbidden = {
        "prediction_id",
        "ledger",
        "conclusion",
        "conclusions",
        "narrative",
        "pattern_verdict",
        "use_god_verdict",
        "domain_conclusion",
    }
    found: list[str] = []

    def walk(value, path: str = "") -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if key in forbidden:
                    found.append(f"{path}/{key}")
                walk(nested, f"{path}/{key}")
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                walk(nested, f"{path}[{index}]")

    walk(loaded)

    assert loaded["guardrails"]["structure_effect_evidence_only"] is True
    assert loaded["guardrails"]["no_prediction_id"] is True
    assert loaded["guardrails"]["no_ledger_write"] is True
    assert found == []


def test_structure_api_evaluate_and_get_round_trip(tmp_path: Path, monkeypatch) -> None:
    store = structure_layer.CoreBaziStructureEffectStore(tmp_path / "api_structure.json")
    monkeypatch.setattr(api_module, "core_bazi_structure_effect_service", store)

    client = TestClient(app)
    core, strength = _pipeline(_chart("丁巳", "乙酉", "乙丑", "乙卯", luck="壬子", flow="己未"))
    evaluate_resp = client.post(
        "/api/v18.1/core-bazi/structure/evaluate",
        json={"core_feature_bundle": core, "core_strength_bundle": strength},
    )

    assert evaluate_resp.status_code == 200
    payload = evaluate_resp.json()
    assert payload["ok"] is True
    structure_bundle_id = payload["data"]["structure_bundle_id"]

    get_resp = client.get(f"/api/v18.1/core-bazi/structure/{structure_bundle_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["structure_bundle_id"] == structure_bundle_id
