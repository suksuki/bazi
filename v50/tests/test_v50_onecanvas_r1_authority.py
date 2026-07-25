from __future__ import annotations

import json
import subprocess
from functools import lru_cache
from pathlib import Path

from product.onecanvas_structural import selection_catalog_payload


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "apps/product/static/experience/active/onecanvas-r1"
FIXTURE = PROTOTYPE / "fixture.json"
RUNTIME = PROTOTYPE / "onecanvas-runtime.js"
COMPONENTS = PROTOTYPE / "onecanvas-components.js"
CONTROLLER = PROTOTYPE / "prototype.js"
REVIEW_TARGETS = PROTOTYPE / "review-targets.json"
R1_DESIGN = ROOT / "docs/product/V50_ONECANVAS_R1_IMPLEMENTATION_DESIGN.md"
VISUAL_CONTRACT = ROOT / "docs/product/V50_ONECANVAS_VISUAL_COMPONENT_CONTRACT_V1.md"


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _runtime_probe() -> dict:
    catalog = selection_catalog_payload()
    script = f"""
import fs from "node:fs/promises";
import {{ cloneSnapshot, compileOneCanvasCues, createOneCanvasModel, recomputeViewModel }} from {json.dumps(RUNTIME.as_uri())};
import {{ ONECANVAS_LAYER_ORDER, renderRecomputeIndicator, renderTargetResolution }} from {json.dumps(COMPONENTS.as_uri())};
const fixture = JSON.parse(await fs.readFile({json.dumps(str(FIXTURE))}, "utf8"));
const model = createOneCanvasModel(fixture);
model.setSelectionCatalog({json.dumps(catalog, ensure_ascii=False)});
const formal = {{
  mode: "formal",
  axis: "day",
  index: fixture.baseline_candidate_index.day,
  yearIndex: model.officialYearIndex,
  luckIndex: null,
  gender: fixture.structural_context.gender,
  draftNodes: [],
}};
const experiment = {{...formal, mode: "experiment", analysisYear: fixture.formal.analysis_year, birthYearHint: null}};
const stemSession = model.beginPillarEditSession(experiment, "day_stem", 1);
const stemAnchorStep = model.stepPillarEditSession(stemSession, "day_stem", 1);
const stemCounterpartStepOne = model.stepPillarEditSession(stemAnchorStep, "day_branch", 1);
const stemCounterpartStepTwo = model.stepPillarEditSession(stemCounterpartStepOne, "day_branch", 1);
const branchSession = model.beginPillarEditSession(experiment, "day_branch", 1);
const branchAnchorStep = model.stepPillarEditSession(branchSession, "day_branch", 1);
const branchCounterpartStep = model.stepPillarEditSession(branchAnchorStep, "day_stem", 1);
const monthCandidates = model.dependentPillarOptions("month", experiment);
const hourCandidates = model.dependentPillarOptions("hour", experiment);
const targetRequest = model.targetCompileRequest(
  ["丁巳", "乙巳", "乙丑", "乙酉"],
  experiment,
  {{gender: "male", cycleYearAnchor: 1977, analysisYear: 2026, targetDraftId: "runtime-probe"}},
);
const unresolvedVariant = {{
  ...fixture.formal,
  timing_recalculation: {{
    ...fixture.formal.timing_recalculation,
    status: "recalculated_changed",
    calculation_mode: "structural_sequence_only",
    exact_timing_status: "unavailable",
    current_luck_status: "unresolved",
    luck_pillar: "",
    luck_year_range: [],
    luck_sequence: [{{pillar: "甲辰", sequence_index: 1, nodes: []}}, {{pillar: "庚子", sequence_index: 5, nodes: []}}],
  }},
}};
const unresolvedSnapshot = {{...formal, mode: "experiment", variant: unresolvedVariant, gender: "male"}};
console.log(JSON.stringify({{
  stemSession,
  stemAnchorStep,
  stemCounterpartStepOne,
  stemCounterpartStepTwo,
  branchSession,
  branchAnchorStep,
  branchCounterpartStep,
  monthCandidateCount: monthCandidates.length,
  hourCandidateCount: hourCandidates.length,
  targetRequest,
  changed: recomputeViewModel({{status: "recalculated_changed"}}),
  unchanged: recomputeViewModel({{status: "recalculated_unchanged"}}),
  unavailable: recomputeViewModel({{status: "recalculation_unavailable", missing_inputs: ["birth_time"]}}),
  pendingMarkup: renderRecomputeIndicator({{status: "recalculating"}}),
  multipleResolutionMarkup: renderTargetResolution({{
    resolution: {{
      status: "multiple_solutions",
      candidate_count: 2,
      ranking_is_presentation_only: true,
      legal_variants: [
        {{variant_ref: "variant-a", pillars: ["丁巳", "乙巳", "乙丑", "乙酉"]}},
        {{variant_ref: "variant-b", pillars: ["丁巳", "乙巳", "乙未", "乙酉"]}},
      ],
    }},
  }}),
  noSolutionMarkup: renderTargetResolution({{
    resolution: {{
      status: "no_solution",
      conflict_reasons: [{{reason: "month_pillar_not_legal_for_year", detail: "month conflict"}}],
      releasable_constraints: ["month.pillar", "year.pillar"],
    }},
  }}),
  layerOrder: ONECANVAS_LAYER_ORDER,
  luckCapability: fixture.r1_contract.slot_capabilities.luck,
  annualCapability: fixture.r1_contract.slot_capabilities.annual,
  luckObservation: model.luckObservationFor(formal),
  unresolvedLuckIndex: model.currentLuckIndex(unresolvedSnapshot),
  unresolvedLuckObservation: model.luckObservationFor(unresolvedSnapshot),
  explicitLuckObservation: model.luckObservationFor({{...unresolvedSnapshot, luckIndex: 1}})?.pillar,
  dingSiBirthYearChoices: model.cycleYearChoicesForPillar("丁巳", 2026),
  annualObservationCount: model.annualObservations().length,
  noLuckCueActions: compileOneCanvasCues({{node_keys: [], segments: []}}, {{luckAvailable: false}}).map((item) => item.action),
  clonedGender: cloneSnapshot({{...formal, gender: "female"}}).gender,
}}));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_r1_fixture_freezes_authority_and_six_semantic_slots() -> None:
    payload = _fixture()
    contract = payload["r1_contract"]

    assert contract["selection_mode"] == "sexagenary_cycle_structural"
    assert contract["candidate_authority"] == "server_side_pillar_target_solver"
    assert payload["interaction_contract"]["semantic_slots"] == [
        "year",
        "month",
        "day",
        "hour",
        "luck",
        "annual",
    ]
    assert contract["slot_capabilities"]["luck"] == {
        "editable_in_experiment": False,
        "switchable": True,
        "derived": True,
    }
    assert contract["slot_capabilities"]["annual"] == {
        "editable_in_experiment": False,
        "switchable": True,
        "derived": True,
        "independent_observation": True,
    }
    assert contract["slot_capabilities"]["year"]["option_count"] == 60
    assert contract["slot_capabilities"]["year"]["independent_cycle_choice"] is True
    assert contract["slot_capabilities"]["day"]["option_count"] == 60
    assert contract["slot_capabilities"]["month"]["depends_on"] == "year"
    assert contract["slot_capabilities"]["month"]["option_count"] == 12
    assert contract["slot_capabilities"]["hour"]["depends_on"] == "day"
    assert contract["slot_capabilities"]["hour"]["option_count"] == 12
    assert contract["gender_authority"] == "explicit_birth_fact_or_explicit_sandbox_choice"
    assert contract["unknown_gender_luck_policy"] == "unavailable_never_inferred"
    assert payload["structural_context"]["gender"] == "unknown"
    assert payload["structural_context"]["gender_required_for_luck"] is True
    assert not any(node["node_key"].startswith("luck_") for node in payload["formal"]["nodes"])


def test_r1_solver_output_is_complete_traceable_and_privacy_safe() -> None:
    payload = _fixture()
    forbidden_keys = {"birth_date", "birth_time", "solar_datetime", "email", "display_name"}

    for axis, candidates in payload["candidate_families"].items():
        assert candidates, axis
        for candidate in candidates:
            assert len(candidate["pillars"]) == 4
            assert candidate["structural_candidate_ref"].startswith("cycle-candidate:c2a:")
            assert candidate["selection_context"]["raw_birth_datetime_in_fixture"] is False
            assert candidate["selection_context"]["maps_to_real_birth_datetime"] is False
            assert candidate["selection_context"]["disclosure_mode"] == "sexagenary_cycle_structural"
            assert candidate["timing_recalculation"]["status"] in {
                "recalculated_changed",
                "recalculated_unchanged",
                "recalculation_unavailable",
            }
            assert not (set(candidate) & forbidden_keys)

    assert payload["source"]["contains_raw_birth_datetime"] is False


def test_r1_first_operation_anchor_persists_while_both_components_step() -> None:
    probe = _runtime_probe()

    assert probe["stemSession"]["slot"] == "day"
    assert probe["stemSession"]["anchorComponent"] == "stem"
    assert len(probe["stemSession"]["legalCounterparts"]) == 6
    assert probe["stemSession"]["complete"] is True
    assert probe["stemAnchorStep"]["anchorComponent"] == "stem"
    assert probe["stemAnchorStep"]["anchorValue"] != probe["stemSession"]["anchorValue"]
    assert probe["stemCounterpartStepOne"]["anchorValue"] == probe["stemCounterpartStepTwo"]["anchorValue"]
    assert probe["stemCounterpartStepOne"]["counterpartValue"] != probe["stemCounterpartStepTwo"]["counterpartValue"]
    assert len(probe["stemCounterpartStepTwo"]["previewPillar"]) == 2
    assert probe["branchSession"]["anchorComponent"] == "branch"
    assert len(probe["branchSession"]["legalCounterparts"]) == 5
    assert probe["branchAnchorStep"]["anchorComponent"] == "branch"
    assert probe["branchCounterpartStep"]["anchorValue"] == probe["branchAnchorStep"]["anchorValue"]
    assert probe["branchCounterpartStep"]["complete"] is True
    catalog = _fixture()["selection_catalogs"]["year"]
    for key in (
        "stemSession",
        "stemAnchorStep",
        "stemCounterpartStepOne",
        "stemCounterpartStepTwo",
        "branchSession",
        "branchAnchorStep",
        "branchCounterpartStep",
    ):
        assert probe[key]["previewPillar"] in catalog
    assert probe["monthCandidateCount"] == 12
    assert probe["hourCandidateCount"] == 12
    assert probe["targetRequest"]["desired"] == {
        "year": "丁巳",
        "month": "乙巳",
        "day": "乙丑",
        "hour": "乙酉",
    }


def test_r1_recompute_language_covers_changed_unchanged_unavailable_and_pending() -> None:
    probe = _runtime_probe()

    assert probe["changed"]["status"] == "recalculated_changed"
    assert probe["unchanged"]["status"] == "recalculated_unchanged"
    assert probe["unavailable"]["status"] == "recalculation_unavailable"
    assert "无法可靠重算" in probe["unavailable"]["title"]
    assert 'data-recompute-status="recalculating"' in probe["pendingMarkup"]


def test_r1_luck_is_derived_switchable_and_precompiled() -> None:
    probe = _runtime_probe()

    assert probe["luckCapability"] == {
        "editable_in_experiment": False,
        "switchable": True,
        "derived": True,
    }
    assert probe["luckObservation"] is None
    assert probe["unresolvedLuckIndex"] == -1
    assert probe["unresolvedLuckObservation"] is None
    assert probe["explicitLuckObservation"] == "庚子"
    assert "enter_luck" not in probe["noLuckCueActions"]
    assert "enter_annual" in probe["noLuckCueActions"]
    assert probe["clonedGender"] == "female"
    assert probe["annualCapability"]["switchable"] is True


def test_r1_birth_year_anchor_is_calendar_constrained_and_separate_from_structure() -> None:
    probe = _runtime_probe()
    controller = CONTROLLER.read_text(encoding="utf-8")
    stylesheet = (PROTOTYPE / "styles.css").read_text(encoding="utf-8")

    assert probe["dingSiBirthYearChoices"] == [1977, 1917]
    assert 'data-action="birth-year-anchor"' in controller
    assert 'data-intent="temporal:anchor"' in controller
    assert "function selectBirthYearAnchor(year)" in controller
    assert "model.cycleYearChoicesForPillar" in controller
    assert "allowedYears.includes(year)" in controller
    assert 'workingSnapshot.gender === "unknown"' in controller
    assert "确认乾造或坤造后定位大运" in controller
    assert "cycleYearAnchor: year" in controller
    assert 'type="number"' not in controller
    assert ".birth-year-anchor select" in stylesheet


def test_r1_components_have_fixed_layers_emit_intents_and_do_not_import_reasoner() -> None:
    probe = _runtime_probe()
    components = COMPONENTS.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")
    combined = components + runtime + controller

    assert probe["layerOrder"] == [
        "background",
        "structural-nodes",
        "root-and-reveal",
        "relations",
        "temporal-activation",
        "system-path",
        "user-path",
        "diff",
        "interaction-hints",
        "selection",
    ]
    for intent in (
        "node:select",
        "candidate:cancel",
        "temporal:observe",
        "history:undo",
        "history:redo",
        "canvas:reset",
        "gender:select",
    ):
        assert f'data-intent="{intent}"' in combined
    assert 'intent: "pillar:edit-independent"' in controller
    assert 'intent: "pillar:select-dependent"' in controller
    for forbidden in (
        "Reasoner",
        "resolve_ten_god",
        "STEM_ELEMENTS",
        "BRANCH_ELEMENTS",
        "inferRelation",
        "calculateLuck",
        "LifeCase.write",
        "ChartVersion.write",
    ):
        assert forbidden not in combined


def test_r1_automatic_edit_session_and_dependent_steppers_are_solver_backed() -> None:
    components = COMPONENTS.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")
    stylesheet = (PROTOTYPE / "styles.css").read_text(encoding="utf-8")

    assert 'class="node-step node-step-previous"' in components
    assert 'class="node-step node-step-next"' in components
    assert 'data-direction="-1"' in components
    assert 'data-direction="1"' in components
    assert 'action === "step-independent-pillar"' in controller
    assert "function stepIndependentPillar(key, direction)" in controller
    assert "model.beginPillarEditSession(workingSnapshot, key, direction)" in controller
    assert "model.stepPillarEditSession(activeSession, key, direction)" in controller
    assert "function endPillarEditSession()" in controller
    assert "function schedulePillarEditExit(clientX, clientY)" in controller
    assert 'root.addEventListener("focusin"' in controller
    assert 'root.addEventListener("focusout"' not in controller
    assert "schedulePillarEditExit(event.clientX, event.clientY)" in controller
    assert "schedulePillarEditExit(Number.NaN, Number.NaN)" in controller
    assert 'data-action="finish-pillar-edit"' not in components
    assert 'data-action="switch-composition-lock"' not in components
    assert "pillar-edit-button" not in components
    assert "composition-lock-button" not in components
    assert "function stepDependentPillar(nodeKey, direction)" in controller
    assert 'action: "step-dependent-pillar"' in controller
    assert "function selectDependentPillar(axis, pillar," in controller
    assert 'data-action="dependent-pillar-select"' not in components
    assert 'workingSnapshot.mode = "experiment"' in controller
    assert "candidate-select-dropdown" not in controller
    assert "candidate-apply" not in controller
    assert 'data-gender="male"' in controller
    assert 'data-gender="female"' in controller
    assert "/api/v50/experience/onecanvas/target-compile" in controller
    assert "model.targetCompileRequest(selectedPillars, snapshot, overrides)" in controller
    assert "workingSnapshot.birthYearHint" in controller
    assert "workingSnapshot.variant = payload.variant" in controller
    assert "workingSnapshot.constraintResolution = payload.resolution" in controller
    assert ".node-control:hover .node-step" in stylesheet
    assert '.pillar-column:not([data-slot="year"]):not([data-slot="day"]):hover .whole-pillar-stepper .node-step' in stylesheet
    assert ".pillar-column.edit-session .node-step" in stylesheet
    assert ".edit-anchor-badge" in stylesheet
    assert 'node.node_type !== "stem"' in controller
    assert '"whole-pillar-stepper"' in components
    assert ".node-control > .node { width: 72px; height: 82px; }" in stylesheet
    assert ".node-step-previous { left: 4px; }" in stylesheet
    assert ".node-step-next { right: 4px; }" in stylesheet
    assert "border-radius: 50% 50% 46% 46%" not in stylesheet
    assert ".node.polarity-yang::before" in stylesheet
    assert ".node.polarity-yin::before" in stylesheet
    assert "repeating-linear-gradient(90deg, currentColor" in stylesheet
    assert "color-mix(in srgb, currentColor 58%, var(--ink-soft))" in stylesheet
    assert ".node.edit-anchor, .node.edit-counterpart { background: rgba(199, 82, 52, .045); }" in stylesheet
    assert ".node.edit-anchor, .node.edit-counterpart { background: rgba(199, 82, 52, .045); color: var(--ink); }" not in stylesheet
    assert "@media (hover: none)" in stylesheet
    assert ".pillar-column:not(.edit-session) .node-control:not(.selected) .node-step" in stylesheet
    for forbidden in (
        "beginPillarComposition",
        "stepPillarComposition",
        "switchPillarCompositionLock",
        "compose-pillar",
        "finish-pillar-edit",
        "switch-composition-lock",
    ):
        assert forbidden not in controller + components + RUNTIME.read_text(encoding="utf-8")


def test_r1_product_projects_multiple_and_no_solution_without_auto_selection() -> None:
    probe = _runtime_probe()
    controller = CONTROLLER.read_text(encoding="utf-8")
    components = COMPONENTS.read_text(encoding="utf-8")
    review_targets = json.loads(REVIEW_TARGETS.read_text(encoding="utf-8"))

    multiple = probe["multipleResolutionMarkup"]
    assert "有 2 个完整命盘符合条件" in multiple
    assert 'data-action="select-target-variant"' in multiple
    assert "候选顺序只便于查看，不代表专业排序" in multiple
    assert "丁巳" in multiple and "乙未" in multiple

    no_solution = probe["noSolutionMarkup"]
    assert "年柱与月柱不能同时成立" in no_solution
    assert 'data-action="release-target-constraint"' in no_solution
    assert 'data-constraint-path="month.pillar"' in no_solution
    assert "取消，保留当前命盘" in no_solution

    assert 'action === "select-target-variant"' in controller
    assert 'action === "release-target-constraint"' in controller
    assert "selectedVariantId: variantRef" in controller
    assert 'targetDraft[slot][field] = ""' in controller
    assert "if (!payload.variant)" in controller
    assert "legal_variants[0]" not in controller + components
    assert ".candidates[0]" not in controller + components

    assert review_targets["contains_personal_identity"] is False
    assert set(review_targets["targets"]) == {"4", "5"}
    serialized = json.dumps(review_targets, ensure_ascii=False).lower()
    for forbidden in ("email", "display_name", "profile_id", "case_id"):
        assert forbidden not in serialized


def test_onecanvas_does_not_overclaim_graph_candidate_as_system_best_path() -> None:
    controller = CONTROLLER.read_text(encoding="utf-8")

    assert ">正式</button>" in controller
    assert "播放 LifeCase 已提交的正式主路径" in controller
    assert "正式路径 ${systemPath.node_keys.length} 节点" in controller
    assert "路径待形成" in controller
    assert ">系统</button>" not in controller
    assert "系统最佳路径" not in controller
    assert "系统推荐路径" not in controller


def test_r1_pillar_dependency_catalog_has_sixty_by_twelve_by_sixty_by_twelve() -> None:
    payload = _fixture()
    catalogs = payload["selection_catalogs"]

    assert len(catalogs["year"]) == 60
    assert len(catalogs["day"]) == 60
    assert len(catalogs["stems"]) == 10
    assert len(catalogs["branches"]) == 12
    assert {len(items) for items in catalogs["branches_by_stem"].values()} == {6}
    assert {len(items) for items in catalogs["stems_by_branch"].values()} == {5}
    assert {len(items) for items in catalogs["month_by_year"].values()} == {12}
    assert {len(items) for items in catalogs["hour_by_day"].values()} == {12}
    assert catalogs["cycle_year_anchor_by_year_pillar"]["丁巳"][:2] == [1917, 1977]
    assert len(catalogs["annual_observations"]) == 201
    assert catalogs["month_by_year"]["甲子"][0] == "丙寅"
    assert catalogs["hour_by_day"]["甲子"][0] == "甲子"

    stem_order = "甲乙丙丁戊己庚辛壬癸"
    branch_order = "子丑寅卯辰巳午未申酉戌亥"
    all_pillars = [
        *catalogs["year"],
        *catalogs["day"],
        *(pillar for family in catalogs["month_by_year"].values() for pillar in family),
        *(pillar for family in catalogs["hour_by_day"].values() for pillar in family),
    ]
    assert all(stem_order.index(pillar[0]) % 2 == branch_order.index(pillar[1]) % 2 for pillar in all_pillars)

    frontend = RUNTIME.read_text(encoding="utf-8") + CONTROLLER.read_text(encoding="utf-8")
    for forbidden in ("FIVE_TIGERS", "FIVE_RATS", "五虎遁", "五鼠遁", "JIAZI", "甲乙丙丁戊己庚辛壬癸"):
        assert forbidden not in frontend


def test_r1_month_and_hour_are_editable_dependent_axes() -> None:
    controller = CONTROLLER.read_text(encoding="utf-8")
    payload = _fixture()

    assert payload["r1_contract"]["slot_capabilities"]["month"]["editable_in_experiment"] is True
    assert payload["r1_contract"]["slot_capabilities"]["hour"]["editable_in_experiment"] is True
    assert 'axis === "month" || axis === "hour"' not in controller
    assert "month_by_year" in RUNTIME.read_text(encoding="utf-8")
    assert "hour_by_day" in RUNTIME.read_text(encoding="utf-8")


def test_existing_path_draft_has_clear_continuous_finish_controls_without_new_reasoning() -> None:
    components = COMPONENTS.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")
    stylesheet = (PROTOTYPE / "styles.css").read_text(encoding="utf-8")

    assert "function finishDraftPath()" in controller
    assert "state.snapshot.draftNodes.at(-1) === key" in controller
    assert 'data-action="finish-path"' in controller
    assert 'data-intent="path:complete"' in controller
    assert 'data-intent="path:start"' in controller
    assert 'event.key === "Enter" || event.key === "Escape"' in controller
    assert "再点当前终点完成" in controller
    assert "继续画线" in controller
    assert "draftEndpoint" in components
    assert ".node.draft-endpoint" in stylesheet
    assert "inferRelation" not in controller


def test_r1_annual_selection_uses_gregorian_year_with_derived_ganzhi() -> None:
    payload = _fixture()
    controller = CONTROLLER.read_text(encoding="utf-8")

    assert all(isinstance(item["year"], int) for item in payload["year_dial"])
    assert all(len(item["pillar"]) == 2 for item in payload["year_dial"])
    assert all(item["calendar_context"]["disclosure_mode"] == "gregorian_year" for item in payload["year_dial"])
    components = COMPONENTS.read_text(encoding="utf-8")
    assert 'data-action="annual-year-select"' in components
    assert 'data-intent="temporal:observe"' in components
    assert "function selectAnnualYear(year)" in controller
    assert "model.annualObservations()" in controller
    assert "analysisYear: year" in controller
    for forbidden in ("annual-search", "year-preview", "year-apply", "step-annual"):
        assert forbidden not in controller + components


def test_r1_luck_stepper_changes_observation_not_derived_sequence() -> None:
    controller = CONTROLLER.read_text(encoding="utf-8")

    assert 'action === "step-luck"' in controller
    assert "function stepLuck(direction)" in controller
    assert "state.snapshot.luckIndex = index" in controller
    assert "timing_recalculation.luck_sequence" in controller
    assert "selected_pillars" not in controller.split("function stepLuck", 1)[1].split("function observeLuck", 1)[0]


def test_r1_gallery_and_tokens_cover_required_visual_states() -> None:
    html = (PROTOTYPE / "gallery.html").read_text(encoding="utf-8")
    script = (PROTOTYPE / "gallery.js").read_text(encoding="utf-8")
    stylesheet = (PROTOTYPE / "gallery.css").read_text(encoding="utf-8")
    main_styles = (PROTOTYPE / "styles.css").read_text(encoding="utf-8")
    combined = html + script + stylesheet

    assert 'id="galleryRoot"' in html
    for state in (
        "正式",
        "实验",
        "选中",
        "派生锁定",
        "候选",
        "受阻",
        "recalculating",
        "recalculated_changed",
        "recalculated_unchanged",
        "recalculation_unavailable",
    ):
        assert state in combined
    for token in (
        "foundation.css",
        "element.css",
        "epistemic.css",
        "motion.css",
        "geometry.css",
        "typography.css",
    ):
        assert f'@import url("./tokens/{token}")' in main_styles
    assert "@media (max-width: 420px)" in stylesheet
    assert "prefers-reduced-motion: reduce" in main_styles
    assert ":focus-visible" in main_styles


def test_r1_documents_keep_later_slices_and_release_blocked() -> None:
    design = R1_DESIGN.read_text(encoding="utf-8")
    contract = VISUAL_CONTRACT.read_text(encoding="utf-8")

    assert "authorized_scope: R1_only" in design
    assert "r2_to_r6_authorized: false" in design
    assert "production_deployment: false" in design
    assert "machine success does not pass the product gate" in design
    assert "No React migration" in contract
    assert "R2-R6 functionality is not" in contract
    assert "Components never" in contract
