from __future__ import annotations

from typing import Any

from experience.canvas import (
    CanvasCompileRequest,
    CanvasContextPack,
    CanvasDiffSpec,
    MingliCanvasSpec,
    compile_canvas_context,
    compile_canvas_diff,
    compile_canvas_spec,
    project_canvas_spec_for_role,
)
from experience.compiler import canonical_hash
from experience.product_projection import ReadOnlySixPillarCanvas
from product.agent_case_store import AgentCaseStore
from product.canonical_scene import CanonicalSceneOwner, CanonicalSceneUnavailable
from product.canvas_projection_graph import (
    active_projection_assertions,
    candidate_paths,
    canvas_node,
    canvas_relation,
    chart_source,
    committed_paths,
    graph_clusters,
)
from product.canvas_projection_input import compile_input_from_case_row
from product.canvas_projection_presentation import (
    change_groups,
    layer_catalog,
    object_refs,
    previous_stage,
    stage_summary,
    stage_title,
)
from product.canvas_projection_shared import (
    LAYER_DEFINITIONS,
    TEMPORAL_PATH_UPDATE_POLICY_VERSION,
    CanvasRole,
    ReadOnlyCanvasUnavailable,
    canvas_role,
)
from product.canvas_projection_temporal import (
    apply_temporal_path_updates,
    core_relation_type,
    relation_endpoints,
    relation_participant_refs,
    temporal_layer,
    temporal_layers,
    temporal_path_updates,
    temporal_relations,
)


class ReadOnlySixPillarCanvasService:
    """Project formal case state into C0 Canvas contracts without writes or LLM use."""

    def __init__(self, *, case_store: AgentCaseStore) -> None:
        self.case_store = case_store
        self.scene_owner = CanonicalSceneOwner(case_store=case_store)
        self._compiled_cache: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}

    def issue(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
    ) -> dict[str, Any]:
        role = canvas_role(account_role)
        compiled = self._compile(case_id=case_id, participant_id=participant_id, role=role)
        source = compiled["source"]
        specs: dict[str, MingliCanvasSpec] = compiled["specs"]
        diffs: dict[str, CanvasDiffSpec | None] = compiled["diffs"]

        stages: dict[str, Any] = {}
        for stage in ("natal", "luck", "year"):
            spec = specs[stage]
            diff = diffs[stage]
            layers = layer_catalog(spec)
            default_layer = (
                "work_path"
                if any(item["layer_id"] == "work_path" and item["available"] for item in layers)
                else "generation_control"
            )
            default_selected = spec.semantic_slots[0].slot_ref
            context = compile_canvas_context(
                spec=spec,
                diff=diff,
                role=role,
                selected_object_refs=[default_selected],
                visible_layers=[default_layer],
            )
            stages[stage] = {
                "stage": stage,
                "title": stage_title(stage, source),
                "summary": stage_summary(stage, source),
                "spec": spec.model_dump(mode="json"),
                "diff": diff.model_dump(mode="json") if diff else None,
                "context": context.model_dump(mode="json"),
                "layers": layers,
                "default_layer_id": default_layer,
                "change_groups": change_groups(
                    diff=diff,
                    before_spec=specs[previous_stage(stage)],
                    after_spec=spec,
                ),
            }

        payload = {
            "schema_version": "deepbazi.read_only_six_pillar_canvas.v1",
            "status": "read_only_canvas_ready",
            "case_id": case_id,
            "role": role,
            "stage_order": ["natal", "luck", "year"],
            "default_stage": "natal",
            "source": source,
            "canonical_scene": compiled["canonical_scene"],
            "projection_envelope": compiled["projection_envelope"],
            "path_availability": compiled["path_availability"],
            "stages": stages,
            "renderer_policy": {
                "read_only": True,
                "allowed_interactions": ["set_stage", "toggle_layer", "select_object", "inspect_context"],
                "forbidden_interactions": [
                    "mutate_natal_pillar",
                    "replace_temporal_pillar",
                    "write_life_case",
                    "promote_candidate",
                    "infer_relation",
                    "infer_diff",
                ],
            },
            "boundaries": [
                "原局四柱不可修改",
                "大运与流年只来自正式历法计算",
                "页面不补算关系、路径或阶段结论",
                "当前查看不会写入 LifeCase",
            ],
            "llm_used": False,
            "formal_state_writes": False,
            "sandbox_mutations": False,
        }
        return ReadOnlySixPillarCanvas.model_validate(payload).model_dump(mode="json")

    def issue_context(
        self,
        *,
        case_id: str,
        participant_id: str,
        account_role: str,
        stage: str,
        selected_object_ref: str,
        visible_layer: str,
    ) -> CanvasContextPack:
        if stage not in {"natal", "luck", "year"}:
            raise ReadOnlyCanvasUnavailable("canvas_stage_invalid")
        role = canvas_role(account_role)
        compiled = self._compile(case_id=case_id, participant_id=participant_id, role=role)
        spec: MingliCanvasSpec = compiled["specs"][stage]
        diff: CanvasDiffSpec | None = compiled["diffs"][stage]
        if selected_object_ref not in object_refs(spec):
            raise ReadOnlyCanvasUnavailable("canvas_object_not_disclosed")
        approved_layers = {item["layer_id"] for item in layer_catalog(spec)}
        if visible_layer not in approved_layers:
            raise ReadOnlyCanvasUnavailable("canvas_layer_invalid")
        return compile_canvas_context(
            spec=spec,
            diff=diff,
            role=role,
            selected_object_refs=[selected_object_ref],
            visible_layers=[visible_layer],
        )

    def _compile(
        self,
        *,
        case_id: str,
        participant_id: str,
        role: CanvasRole,
    ) -> dict[str, Any]:
        row = self.case_store.get(case_id=case_id, user_id=participant_id)
        if row is None:
            raise ReadOnlyCanvasUnavailable("experience_case_not_found")
        try:
            canonical_projection = self.scene_owner.issue_projection(
                case_id=case_id,
                participant_id=participant_id,
                account_role=role,
                projection_kind="onecanvas",
            )
        except CanonicalSceneUnavailable as exc:
            raise ReadOnlyCanvasUnavailable(str(exc)) from exc
        cache_key = (
            case_id,
            participant_id,
            role,
            canonical_projection.projection_hash,
            _candidate_selection_revision_token(row),
        )
        cached = self._compiled_cache.get(cache_key)
        if cached is not None:
            return cached
        source, metadata = compile_input_from_case_row(
            case_id=case_id,
            row=row,
            canonical_projection_payload=canonical_projection.payload,
        )
        identity = canonical_projection.scene_identity
        if (
            metadata["source"]["chart_version_id"] != identity.chart_version_id
            or metadata["source"]["life_case_id"] != identity.life_case_id
            or metadata["source"]["life_case_version"] != identity.life_case_version
        ):
            raise ReadOnlyCanvasUnavailable("canvas_canonical_scene_identity_mismatch")
        layer_ids = {item.layer_type: item.layer_id for item in source.temporal_layers}
        if "luck" not in layer_ids or "year" not in layer_ids:
            raise ReadOnlyCanvasUnavailable("canvas_official_timing_required")

        raw_specs = {
            "natal": compile_canvas_spec(CanvasCompileRequest(source=source, stage="natal")),
            "luck": compile_canvas_spec(CanvasCompileRequest(
                source=source,
                stage="luck",
                luck_layer_id=layer_ids["luck"],
            )),
            "year": compile_canvas_spec(CanvasCompileRequest(
                source=source,
                stage="year",
                luck_layer_id=layer_ids["luck"],
                year_layer_id=layer_ids["year"],
            )),
        }
        specs = {
            stage: project_canvas_spec_for_role(spec, role)
            for stage, spec in raw_specs.items()
        }
        diffs: dict[str, CanvasDiffSpec | None] = {
            "natal": None,
            "luck": compile_canvas_diff(
                specs["natal"],
                specs["luck"],
                source_action_ref="official:add-luck",
            ),
            "year": compile_canvas_diff(
                specs["luck"],
                specs["year"],
                source_action_ref="official:add-year",
            ),
        }
        compiled = {
            "source": metadata["source"],
            "path_availability": metadata["path_availability"],
            "specs": specs,
            "diffs": diffs,
            "canonical_scene": identity.model_dump(mode="json"),
            "projection_envelope": canonical_projection.model_dump(mode="json"),
        }
        for key in list(self._compiled_cache):
            if key[:3] == cache_key[:3] and key != cache_key:
                self._compiled_cache.pop(key, None)
        if len(self._compiled_cache) >= 128:
            self._compiled_cache.clear()
        self._compiled_cache[cache_key] = compiled
        return compiled


def _candidate_selection_revision_token(row: dict[str, Any]) -> str:
    record = row.get("record") if isinstance(row.get("record"), dict) else {}
    cognition = record.get("cognition") if isinstance(record.get("cognition"), dict) else {}
    work_path = cognition.get("work_path") if isinstance(cognition.get("work_path"), dict) else {}
    return canonical_hash({
        "record_id": record.get("record_id"),
        "candidate_path_refs": work_path.get("candidate_path_refs"),
        "competing_path_refs": work_path.get("competing_path_refs"),
        "evidence_refs": work_path.get("evidence_refs"),
    })


# Compatibility exports for audit tools and focused fixtures. The implementation
# lives in responsibility-specific modules; this module remains the public owner.
_compile_input_from_case_row = compile_input_from_case_row
_chart_source = chart_source
_canvas_node = canvas_node
_canvas_relation = canvas_relation
_graph_clusters = graph_clusters
_committed_paths = committed_paths
_candidate_paths = candidate_paths
_active_projection_assertions = active_projection_assertions
_temporal_layers = temporal_layers
_temporal_layer = temporal_layer
_apply_temporal_path_updates = apply_temporal_path_updates
_temporal_path_updates = temporal_path_updates
_temporal_relations = temporal_relations
_relation_participant_refs = relation_participant_refs
_core_relation_type = core_relation_type
_relation_endpoints = relation_endpoints
_layer_catalog = layer_catalog
_change_groups = change_groups
_object_refs = object_refs
_previous_stage = previous_stage
_stage_title = stage_title
_stage_summary = stage_summary
