from __future__ import annotations

from v30.presentation import build_presentation_model
from v30.presentation.leakage_guard import scan_product_payload
from v30.runtime import create_smoke_runtime


FORBIDDEN_VISIBLE_TOKENS = {
    "keep_both_branches_until_decision_engine_or_practitioner_calibration_separates_weight",
    "ask_only_if_value_of_information_exceeds_user_cost",
    "downgrade_assertion_level_unless_counter_evidence_is_resolved",
    "value_of_information",
    "training_target",
    "claim_key",
    "conflict_group_id",
    "model_probe_failed",
}


def test_output_runtime_product_projection_is_clean_for_user() -> None:
    runtime = create_smoke_runtime("pytest-output-runtime-user")
    payload = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    workbench = payload["reading_surface"]["decision_workbench"]

    assert payload["projection_contract"]["output_runtime_product_projection_contract"]["version"] == (
        "v30.output_runtime_product_projection_contract.v1"
    )
    assert workbench["product_projection"]["version"] == "v30.product_projection_bundle.v1"
    assert workbench["product_projection"]["leakage_scan"]["passed"] is True
    assert workbench["leakage_scan"]["passed"] is True
    assert "output_runtime_contract" not in workbench

    rendered = str(workbench)
    for token in FORBIDDEN_VISIBLE_TOKENS:
        assert token not in rendered


def test_output_runtime_branch_cards_are_deduped_and_human_readable() -> None:
    runtime = create_smoke_runtime("pytest-output-runtime-branches")
    payload = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    cards = payload["reading_surface"]["decision_workbench"]["product_projection"]["branch_cards"]

    assert cards
    keys = {(row.get("domain"), row.get("key_question")) for row in cards}
    assert len(keys) == len(cards)
    assert all(row["title"] for row in cards)
    assert all(row["user_summary"] for row in cards)
    assert all("keep_both" not in row["user_summary"] for row in cards)
    assert all("ask_only_if_value" not in row["user_summary"] for row in cards)


def test_output_runtime_practitioner_branch_actions_are_semantic() -> None:
    runtime = create_smoke_runtime("pytest-output-runtime-practitioner")
    payload = build_presentation_model(runtime, role_key="practitioner", locale="zh", client="web").model_dump(mode="json")
    workbench = payload["reading_surface"]["decision_workbench"]
    cards = workbench["product_projection"]["branch_cards"]
    labels = {
        action["label"]
        for card in cards
        for action in card.get("practitioner_actions", [])
    }

    assert workbench["visible_detail_level"] == "practitioner_calibration"
    assert workbench["leakage_scan"]["passed"] is True
    assert "更像这个表现" in labels
    assert "作为辅助参考" in labels
    assert "暂不采用" in labels
    assert "需要追问确认" in labels
    assert "降权" not in workbench["calibration"]["practitioner_policy"]


def test_product_leakage_guard_rejects_raw_runtime_language() -> None:
    dirty = {
        "visible_text": (
            "keep_both_branches_until_decision_engine_or_practitioner_calibration_separates_weight "
            "value_of_information"
        )
    }
    clean = {"visible_text": "健康这里先保留两条判断，补充作息和身体反馈后再收束。"}

    assert scan_product_payload(dirty, role_key="user")["passed"] is False
    assert scan_product_payload(clean, role_key="user")["passed"] is True
