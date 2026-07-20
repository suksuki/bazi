from __future__ import annotations

import pytest
import sys
from pathlib import Path

from core.contracts import BirthInputCanonical
from core.engines import normalize_birth_input
from core.engines.bazi import build_bazi_material_store
from core.graph import analyze_mingli_graph, build_mingli_graph_from_material_store, classify_node_roles, explore_mingli_paths
from core.graph.contracts import GraphAnalysisResult
from core.mechanism import MechanismCompleteness, MechanismComponentRole, MechanismRepresentation, StateDeltaStatus, build_mechanism_representation_from_flow_state
from core.simulation import build_mingli_state_from_graph_analysis, run_ablation_simulation
from core.state import FlowState, build_bazi_flow_states


V50_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = V50_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from v50_run_mechanism_representation_batch import run_batch


def _birth() -> BirthInputCanonical:
    return BirthInputCanonical(
        birth_input_id="birth.mechanism_representation.001",
        name="mechanism_representation_case",
        gender="male",
        calendar_type="solar",
        birth_date="1977-05-20",
        birth_time="18:00",
        birth_location="Guangzhou",
        timezone="Asia/Shanghai",
        input_quality="complete",
        year_pillar="丁巳",
        month_pillar="乙巳",
        day_pillar="乙丑",
        hour_pillar="乙酉",
    )


def _representation(mechanism: str = "output_controls_pressure"):
    reading_id = "reading.mechanism_representation.001"
    calendar = normalize_birth_input(_birth())
    store = build_bazi_material_store(reading_id=reading_id, birth_input=_birth(), calendar=calendar)
    graph = build_mingli_graph_from_material_store(store)
    paths = explore_mingli_paths(graph)
    roles = classify_node_roles(graph, paths)
    analysis = analyze_mingli_graph(graph, path_result=paths, role_result=roles)
    state = build_mingli_state_from_graph_analysis(analysis)
    simulation_report = run_ablation_simulation(state)
    flow_states = build_bazi_flow_states(
        analysis=analysis,
        path_result=paths,
        state=state,
        simulation_report=simulation_report,
        include_secondary_mechanisms=True,
    )
    flow_state = next(item for item in flow_states if item.mechanism == mechanism)
    return build_mechanism_representation_from_flow_state(
        flow_state=flow_state,
        analysis=analysis,
        simulation_report=simulation_report,
    )


def _minimal_representation(mechanism: str = "output_controls_pressure"):
    reading_id = f"reading.mechanism_representation.minimal.{mechanism}"
    flow_state = FlowState(
        state_id=f"flow_state.{mechanism}",
        reading_id=reading_id,
        mechanism=mechanism,
        path_refs=[f"path.{mechanism}.minimal"],
        node_refs=["node.source", "node.target"],
        mechanism_refs=[f"mechanism.{mechanism}"],
        output_strength=0.42,
        path_score=0.51,
        ablation_sensitivity=0.0,
        evidence_refs=[f"evidence.{mechanism}.minimal"],
        confidence=0.42,
    )
    analysis = GraphAnalysisResult(
        analysis_id=f"graph_analysis.{mechanism}.minimal",
        reading_id=reading_id,
        graph_id=f"graph.{mechanism}.minimal",
        node_metrics=[],
        ranked_node_ids=[],
    )
    return build_mechanism_representation_from_flow_state(
        flow_state=flow_state,
        analysis=analysis,
        simulation_report=None,
    )


def test_v50_mechanism_representation_is_ast_not_label() -> None:
    representation = _representation()
    roles = {component.role for component in representation.components}

    assert representation.mechanism_code == "output_controls_pressure"
    assert representation.mechanism_label_code == "mechanism.label.output_controls_pressure"
    assert representation.label_is_presentation_only is True
    assert representation.creates_judgment is False
    assert representation.calls_brain is False
    assert representation.calls_llm is False
    assert MechanismComponentRole.SOURCE in roles
    assert MechanismComponentRole.PATH in roles
    assert MechanismComponentRole.CONVERTER in roles
    assert MechanismComponentRole.BRIDGE in roles
    assert MechanismComponentRole.TARGET in roles
    assert MechanismComponentRole.STATE_DELTA in roles
    assert representation.path_refs
    assert representation.state_delta_refs
    assert representation.evidence_refs
    assert representation.completeness == MechanismCompleteness.COMPLETE
    assert representation.state_delta_status == StateDeltaStatus.REAL
    assert representation.ast_shape
    assert representation.synthetic_filled_fields == []
    assert representation.hard_filled_fields == []


def test_v50_mechanism_ast_non_empty_fields_have_evidence_refs() -> None:
    representation = _representation()

    for component in representation.components:
        assert component.ref
        assert component.evidence_refs
        assert component.reason_codes
    assert representation.evidence_refs
    assert representation.state_delta_refs
    assert representation.missing_fields == []


def test_v50_mechanism_ast_allows_missing_fields_without_hard_fill() -> None:
    representation = _minimal_representation()
    roles = {component.role for component in representation.components}

    assert representation.completeness == MechanismCompleteness.PARTIAL
    assert representation.state_delta_status == StateDeltaStatus.MISSING
    assert MechanismComponentRole.SOURCE in roles
    assert MechanismComponentRole.PATH in roles
    assert MechanismComponentRole.TARGET in roles
    assert MechanismComponentRole.BRIDGE not in roles
    assert MechanismComponentRole.CONVERTER not in roles
    assert MechanismComponentRole.ANCHOR not in roles
    assert "key_role" in representation.missing_fields
    assert "state_delta" in representation.missing_fields
    assert representation.synthetic_filled_fields == []
    assert representation.hard_filled_fields == []


def test_v50_same_label_can_have_different_ast_shapes() -> None:
    complete = _representation("output_controls_pressure")
    partial = _minimal_representation("output_controls_pressure")

    assert complete.mechanism_code == partial.mechanism_code
    assert complete.ast_shape != partial.ast_shape
    assert complete.completeness == MechanismCompleteness.COMPLETE
    assert partial.completeness == MechanismCompleteness.PARTIAL


def test_v50_mechanism_label_is_not_ast_shape() -> None:
    first = _minimal_representation("output_controls_pressure")
    second = _minimal_representation("officer_pressure")

    assert first.mechanism_code != second.mechanism_code
    assert first.ast_shape == second.ast_shape


def test_v50_mechanism_representation_allows_non_classic_label_with_same_grammar() -> None:
    representation = _representation("officer_pressure")
    roles = {component.role for component in representation.components}

    assert representation.mechanism_code == "officer_pressure"
    assert MechanismComponentRole.SOURCE in roles
    assert MechanismComponentRole.PATH in roles
    assert MechanismComponentRole.TARGET in roles
    assert representation.components


def test_v50_mechanism_representation_rejects_label_as_authority() -> None:
    representation = _representation()

    with pytest.raises(ValueError, match="presentation-only"):
        MechanismRepresentation(
            representation_id="mechanism_representation.invalid",
            reading_id=representation.reading_id,
            mechanism_code=representation.mechanism_code,
            mechanism_label_code=representation.mechanism_label_code,
            components=representation.components,
            path_refs=representation.path_refs,
            evidence_refs=representation.evidence_refs,
            confidence=representation.confidence,
            label_is_presentation_only=False,
        )


def test_v50_mechanism_representation_batch_reports_ast_role_coverage() -> None:
    summary = run_batch(limit=4)
    metrics = summary["metrics"]

    assert summary["case_count"] == 4
    assert summary["total_representations"] > 0
    assert summary["llm_used"] is False
    assert summary["brain_used"] is False
    assert summary["training_performed"] is False
    assert metrics["label_authority_violations"] == 0
    assert metrics["mechanism_count"] >= 3
    for role in ("source", "path", "target"):
        assert role in metrics["role_distribution"]
    assert metrics["avg_component_count"] >= 3
