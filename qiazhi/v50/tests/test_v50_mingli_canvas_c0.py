from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from experience.canvas import (
    CanvasAction,
    CanvasCompileRequest,
    apply_canvas_action,
    compile_canvas_context,
    compile_canvas_diff,
    compile_canvas_spec,
    create_temporal_sandbox,
    load_canvas_compile_input,
    project_canvas_spec_for_role,
)
from scripts.v50_audit_mingli_canvas_c0 import audit


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "packages" / "experience" / "fixtures"


def _temporal_source():
    return load_canvas_compile_input(FIXTURES / "temporal_sandbox_c0_v1.json")


def _compile_temporal_stages():
    source = _temporal_source()
    natal = compile_canvas_spec(CanvasCompileRequest(source=source, stage="natal"))
    luck = compile_canvas_spec(CanvasCompileRequest(
        source=source,
        stage="luck",
        luck_layer_id="luck-gengzi-official",
    ))
    year = compile_canvas_spec(CanvasCompileRequest(
        source=source,
        stage="year",
        luck_layer_id="luck-gengzi-official",
        year_layer_id="year-bingwu-official",
    ))
    return source, natal, luck, year


def _all_traces(spec):
    return [
        *(item.trace for item in spec.semantic_slots),
        *(item.trace for item in spec.nodes),
        *(item.trace for item in spec.relations),
        *(item.state_trace for item in spec.relations),
        *(item.trace for item in spec.clusters),
        *(item.trace for item in spec.paths),
        *(item.state_trace for item in spec.paths),
    ]


def test_c0_baseline_compile_is_deterministic_traceable_and_has_no_sandbox_objects() -> None:
    source = _temporal_source()
    request = CanvasCompileRequest(source=source, stage="natal")

    first = compile_canvas_spec(request)
    second = compile_canvas_spec(request)

    assert first == second
    assert first.identity.canvas_spec_id == second.identity.canvas_spec_id
    assert first.identity.content_hash == second.identity.content_hash
    assert [item.slot_type for item in first.semantic_slots] == [
        "natal_year", "natal_month", "natal_day", "natal_hour"
    ]
    assert all(item.immutable for item in first.semantic_slots)
    assert first.identity.sandbox_session_id == ""
    assert all(item.source_mode != "hypothetical" for item in _all_traces(first))
    assert all(item.source_refs for item in _all_traces(first))

    paths = {item.path_ref: item for item in first.paths}
    assert paths["path-committed-output-pressure"].trace.epistemic_status == "committed"
    assert paths["path-candidate-direct-earth"].trace.epistemic_status == "candidate"
    assert paths["path-blocked-template-reading"].trace.epistemic_status == "blocked"


def test_c0_temporal_stages_compile_independent_reproducible_diffs_without_mutating_natal_slots() -> None:
    _, natal, luck, year = _compile_temporal_stages()
    natal_to_luck = compile_canvas_diff(natal, luck, source_action_ref="action:add-luck-gengzi")
    luck_to_year = compile_canvas_diff(luck, year, source_action_ref="action:add-year-bingwu")
    natal_to_year = compile_canvas_diff(natal, year, source_action_ref="action:direct-comparison-only")

    assert natal_to_luck == compile_canvas_diff(natal, luck, source_action_ref="action:add-luck-gengzi")
    assert luck_to_year == compile_canvas_diff(luck, year, source_action_ref="action:add-year-bingwu")
    assert natal_to_luck.from_spec_id == natal.identity.canvas_spec_id
    assert natal_to_luck.to_spec_id == luck.identity.canvas_spec_id
    assert luck_to_year.from_spec_id == luck.identity.canvas_spec_id
    assert luck_to_year.to_spec_id == year.identity.canvas_spec_id
    assert natal_to_year.content_hash not in {natal_to_luck.content_hash, luck_to_year.content_hash}

    natal_slots = [(item.slot_ref, item.stem, item.branch, item.immutable) for item in natal.semantic_slots]
    assert [(item.slot_ref, item.stem, item.branch, item.immutable) for item in luck.semantic_slots[:4]] == natal_slots
    assert [(item.slot_ref, item.stem, item.branch, item.immutable) for item in year.semantic_slots[:4]] == natal_slots
    assert [item.slot_type for item in year.semantic_slots] == [
        "natal_year", "natal_month", "natal_day", "natal_hour", "luck", "year"
    ]

    assert [item.target_ref for item in natal_to_luck.added_relations] == ["relation-luck-geng-controls-yi"]
    assert [item.target_ref for item in natal_to_luck.weakened_paths] == ["path-committed-output-pressure"]
    assert [item.target_ref for item in luck_to_year.added_relations] == ["relation-year-bing-supports-ding"]
    assert [item.target_ref for item in luck_to_year.reinforced_paths] == ["path-committed-output-pressure"]


def test_c0_hypothetical_year_is_replayable_and_restore_returns_exact_formal_spec() -> None:
    source, _, _, formal_year = _compile_temporal_stages()
    source_before = deepcopy(source.model_dump(mode="json"))
    base = create_temporal_sandbox(
        sandbox_session_id="sandbox-c0-replay",
        base_snapshot_id="snapshot-year-bingwu-v1",
        luck_layer_id="luck-gengzi-official",
        year_layer_id="year-bingwu-official",
    )
    action = CanvasAction(
        action_id="action-replace-year-guimao",
        action_type="replace_year",
        target_layer_id="year-guimao-hypothetical",
        source_ref="user:temporal-sandbox-selection",
    )
    modified_a = apply_canvas_action(source=source, sandbox=base, action=action)
    modified_b = apply_canvas_action(source=source, sandbox=base, action=action)
    assert modified_a == modified_b

    hypothetical_a = compile_canvas_spec(CanvasCompileRequest(source=source, stage="year", sandbox=modified_a))
    hypothetical_b = compile_canvas_spec(CanvasCompileRequest(source=source, stage="year", sandbox=modified_b))
    assert hypothetical_a == hypothetical_b
    assert hypothetical_a.identity.sandbox_session_id == "sandbox-c0-replay"

    main_path = next(item for item in hypothetical_a.paths if item.path_ref == "path-committed-output-pressure")
    assert main_path.trace.source_mode == "committed"
    assert main_path.trace.epistemic_status == "committed"
    assert main_path.semantic_state == "blocked"
    assert main_path.state_trace.source_mode == "hypothetical"
    hypothetical_refs = {
        item.node_ref for item in hypothetical_a.nodes if item.trace.source_mode == "hypothetical"
    }
    assert hypothetical_refs == {"node-year-gui-hyp", "node-year-mao-hyp"}
    assert all(item.trace.source_mode == "canonical" for item in hypothetical_a.semantic_slots[:4])

    restored = apply_canvas_action(
        source=source,
        sandbox=modified_a,
        action=CanvasAction(action_id="action-restore", action_type="restore", source_ref="user:restore"),
    )
    restored_spec = compile_canvas_spec(CanvasCompileRequest(
        source=source,
        stage="year",
        luck_layer_id="luck-gengzi-official",
        year_layer_id="year-bingwu-official",
        sandbox=restored,
    ))
    assert restored_spec == formal_year
    assert source.model_dump(mode="json") == source_before
    assert restored.writes_chart is False
    assert restored.writes_life_case is False


def test_c0_epistemic_states_remain_distinct_from_semantic_presence() -> None:
    _, natal, _, _ = _compile_temporal_stages()
    paths = {item.path_ref: item for item in natal.paths}

    committed = paths["path-committed-output-pressure"]
    candidate = paths["path-candidate-direct-earth"]
    blocked = paths["path-blocked-template-reading"]
    derived_node = next(item for item in natal.nodes if item.node_ref == "node-metal-structure")

    assert committed.trace.epistemic_status == "committed"
    assert candidate.trace.epistemic_status == "candidate"
    assert blocked.trace.epistemic_status == "blocked"
    assert blocked.path_ref in paths
    assert blocked.semantic_state == "blocked"
    assert derived_node.trace.source_mode == "derived"
    assert derived_node.trace.epistemic_status == "derived"
    assert derived_node.trace.source_mode != "hypothetical"


def test_c0_diff_contract_covers_all_eight_discrete_semantics_with_reasons_and_sources() -> None:
    source = load_canvas_compile_input(FIXTURES / "canvas_diff_semantics_c0_v1.json")
    baseline = compile_canvas_spec(CanvasCompileRequest(source=source, stage="natal"))
    changed = compile_canvas_spec(CanvasCompileRequest(
        source=source,
        stage="luck",
        luck_layer_id="luck-diff-contract",
    ))
    diff = compile_canvas_diff(baseline, changed, source_action_ref="fixture:all-diff-semantics")
    expected = {
        "introduced_paths": ("introduced", "path-introduced"),
        "removed_paths": ("removed", "path-removed"),
        "activated_paths": ("activated", "path-activated"),
        "reinforced_paths": ("reinforced", "path-reinforced"),
        "weakened_paths": ("weakened", "path-weakened"),
        "blocked_paths": ("blocked", "path-blocked"),
        "reopened_paths": ("reopened", "path-reopened"),
        "unchanged_paths": ("unchanged", "path-unchanged"),
    }
    for field, (change_type, target_ref) in expected.items():
        rows = getattr(diff, field)
        assert len(rows) == 1
        assert rows[0].change_type == change_type
        assert rows[0].target_ref == target_ref
        assert rows[0].reason_refs
        assert rows[0].source_refs
        if change_type not in {"introduced", "removed"}:
            assert rows[0].before_state
            assert rows[0].after_state
    assert not any("%" in value for row in sum((getattr(diff, field) for field in expected), []) for value in [row.before_state, row.after_state])


def test_c0_abu_context_is_role_projected_and_never_sees_hidden_or_uncompiled_information() -> None:
    source, _, _, formal_year = _compile_temporal_stages()
    sandbox = create_temporal_sandbox(
        sandbox_session_id="sandbox-c0-context",
        base_snapshot_id="snapshot-year-bingwu-v1",
        luck_layer_id="luck-gengzi-official",
        year_layer_id="year-bingwu-official",
    )
    sandbox = apply_canvas_action(
        source=source,
        sandbox=sandbox,
        action=CanvasAction(
            action_id="action-context-hyp-year",
            action_type="replace_year",
            target_layer_id="year-guimao-hypothetical",
            source_ref="user:context-test",
        ),
    )
    hypothetical = compile_canvas_spec(CanvasCompileRequest(source=source, stage="year", sandbox=sandbox))
    diff = compile_canvas_diff(formal_year, hypothetical, source_action_ref="action-context-hyp-year")
    selected = [
        "path-committed-output-pressure",
        "path-candidate-direct-earth",
        "path-blocked-template-reading",
        "relation-hyp-gui-controls-ding",
        "not-compiled-free-inference",
    ]

    member = compile_canvas_context(
        spec=hypothetical,
        diff=diff,
        role="member",
        selected_object_refs=selected,
        visible_layers=["generation_control", "work_path"],
        sandbox=sandbox,
    )
    practitioner = compile_canvas_context(
        spec=hypothetical,
        diff=diff,
        role="practitioner",
        selected_object_refs=selected,
        visible_layers=["generation_control", "work_path"],
        sandbox=sandbox,
    )
    research = compile_canvas_context(
        spec=hypothetical,
        diff=diff,
        role="research",
        selected_object_refs=selected,
        visible_layers=["generation_control", "work_path"],
        sandbox=sandbox,
    )

    assert member.committed_path_refs == ["path-committed-output-pressure"]
    assert member.candidate_path_refs == []
    assert member.blocked_path_refs == []
    assert "path-candidate-direct-earth" not in member.disclosed_object_refs
    assert "path-blocked-template-reading" not in member.disclosed_object_refs
    assert "not-compiled-free-inference" not in member.selected_object_refs
    assert member.hypothetical_mutations[0].after_layer_id == "year-guimao-hypothetical"
    assert "reason:hyp-gui-controls-required-node" in member.diff_reason_refs

    assert practitioner.candidate_path_refs == ["path-candidate-direct-earth"]
    assert practitioner.blocked_path_refs == []
    assert research.candidate_path_refs == ["path-candidate-direct-earth"]
    assert research.blocked_path_refs == ["path-blocked-template-reading"]
    assert project_canvas_spec_for_role(hypothetical, "member").identity.audience_role == "member"
    assert project_canvas_spec_for_role(hypothetical, "research").identity.audience_role == "research"


def test_c0_machine_audit_gate_passes() -> None:
    result = audit()
    assert result["c0_gate_passed"], result
    assert result["boundary_status"] == {
        "runtime_modified": False,
        "reasoner_modified": False,
        "life_case_modified": False,
        "ui_modified": False,
        "mingli_algorithm_modified": False,
        "llm_used": False,
        "sandbox_writes_formal_state": False,
    }
