from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from typing import Any

from v20.api.runtime import run_runtime_from_pillars


STRUCTURE_DYNAMICS_SYNTHETIC_VERSION = "v20.structure_dynamics_synthetic.v1"


@dataclass(frozen=True)
class StructureDynamicsSyntheticCase:
    case_id: str
    pillar_displays: tuple[str, str, str, str]
    expected_label: str
    expected_nodes: tuple[str, ...]
    expected_path_terms: tuple[str, ...]
    forbidden_labels: tuple[str, ...] = field(default_factory=tuple)
    expected_semantic_labels: tuple[str, ...] = field(default_factory=tuple)
    expected_time_relation_types: tuple[str, ...] = field(default_factory=tuple)
    flow_year_pillar: str = ""
    luck_pillar: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


STRUCTURE_DYNAMICS_SYNTHETIC_CASES: tuple[StructureDynamicsSyntheticCase, ...] = (
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.food_controls_killing",
        pillar_displays=("辛酉", "癸巳", "乙卯", "丁丑"),
        expected_label="食神制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("丁食神", "辛七杀", "癸偏印", "乙日主"),
        forbidden_labels=("食伤生财",),
        notes="验证做功链先提取丁食神制辛七杀，再由癸偏印承接到乙日主。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.wealth_authority_resource",
        pillar_displays=("庚午", "辛巳", "丁丑", "乙巳"),
        expected_label="财生官/财滋杀",
        expected_nodes=("wealth", "authority", "resource"),
        expected_path_terms=("庚正财", "癸七杀", "乙偏印", "丁日主"),
        forbidden_labels=("食神制杀",),
        notes="验证财星进入官杀再由印承接时，不被旧食伤生财模板强行覆盖。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.authority_resource_self.jia_day",
        pillar_displays=("辛酉", "癸亥", "甲子", "壬申"),
        expected_label="官印/杀印相生",
        expected_nodes=("authority", "resource", "self"),
        expected_path_terms=("辛正官", "癸正印", "甲比肩", "甲日主"),
        forbidden_labels=("食伤生财", "财生官/财滋杀"),
        expected_semantic_labels=("印星承身",),
        notes="甲日主官印相生样本，验证官星进入印星再由比肩承接到日主。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.authority_resource_self.gui_day",
        pillar_displays=("壬子", "癸亥", "癸丑", "壬申"),
        expected_label="官印/杀印相生",
        expected_nodes=("authority", "resource", "self"),
        expected_path_terms=("己七杀", "庚正印", "壬劫财", "癸日主"),
        forbidden_labels=("食伤生财", "财生官/财滋杀"),
        expected_semantic_labels=("印星承身",),
        notes="癸日主杀印相生样本，验证七杀压力进入正印和劫财承身，不退回财富链。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.shangguan_controls_killing",
        pillar_displays=("辛酉", "癸巳", "乙卯", "壬午"),
        expected_label="伤官制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("丙伤官", "辛七杀", "癸偏印", "乙日主"),
        forbidden_labels=("食伤生财",),
        notes="验证伤官制杀与食神制杀同属输出制官杀，但语义定性必须区分食神和伤官。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.food_controls_killing.xin_day",
        pillar_displays=("甲子", "丁卯", "辛酉", "癸巳"),
        expected_label="食神制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("癸食神", "丁七杀", "戊正印", "辛日主"),
        forbidden_labels=("食伤生财",),
        notes="辛日主样本，验证食神制杀不依赖乙木原例。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.shangguan_controls_killing.ren_day",
        pillar_displays=("乙丑", "戊辰", "壬申", "甲午"),
        expected_label="伤官制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("乙伤官", "戊七杀", "辛正印", "壬日主"),
        forbidden_labels=("食神制杀", "食伤生财"),
        notes="壬日主样本，验证伤官制杀优先于泛化输出制官杀。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.food_controls_killing.gui_day",
        pillar_displays=("丙寅", "己巳", "癸酉", "乙未"),
        expected_label="食神制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("乙食神", "己七杀", "庚正印", "癸日主"),
        forbidden_labels=("伤官制杀", "食伤生财"),
        notes="癸日主样本，验证食神、七杀、正印、日主的闭合承接。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.shangguan_controls_killing.jia_day",
        pillar_displays=("丁卯", "庚午", "甲子", "丙寅"),
        expected_label="伤官制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("丁伤官", "庚七杀", "癸正印", "甲日主"),
        forbidden_labels=("食神制杀", "食伤生财"),
        notes="甲日主样本，验证伤官制杀路径能回到印星和日主承接。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.food_controls_killing.yi_day_variant",
        pillar_displays=("戊辰", "辛未", "乙丑", "丁亥"),
        expected_label="食神制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("丁食神", "辛七杀", "癸偏印", "乙日主"),
        forbidden_labels=("食伤生财",),
        notes="乙日主变体，验证不同柱位下仍以做功链而非固定模板命名。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.shangguan_controls_killing.bing_day",
        pillar_displays=("己巳", "壬申", "丙寅", "戊戌"),
        expected_label="伤官制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("己伤官", "壬七杀", "甲偏印", "丙日主"),
        forbidden_labels=("食神制杀", "食伤生财"),
        notes="丙日主样本，验证伤官制杀在偏印承接时仍稳定。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.food_controls_killing.ding_day",
        pillar_displays=("庚午", "癸酉", "丁卯", "己丑"),
        expected_label="食神制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("己食神", "癸七杀", "乙偏印", "丁日主"),
        forbidden_labels=("食伤生财",),
        notes="丁日主样本，验证偏印承接不改变食神制杀命名。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.shangguan_controls_killing.wu_day",
        pillar_displays=("辛未", "甲戌", "戊辰", "庚申"),
        expected_label="伤官制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("辛伤官", "甲七杀", "丁正印", "戊日主"),
        forbidden_labels=("食神制杀", "食伤生财"),
        notes="戊日主样本，验证伤官制杀和官印承接可同时入候选，但主标签不混淆。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.food_controls_killing.ji_day",
        pillar_displays=("壬申", "乙亥", "己巳", "辛卯"),
        expected_label="食神制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("辛食神", "乙七杀", "丙正印", "己日主"),
        forbidden_labels=("伤官制杀", "食伤生财"),
        notes="己日主样本，验证食神制杀不会被输出制官杀泛化标签覆盖。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.shangguan_controls_killing.geng_day",
        pillar_displays=("癸酉", "丙子", "庚午", "壬辰"),
        expected_label="伤官制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("癸伤官", "丙七杀", "己正印", "庚日主"),
        forbidden_labels=("食神制杀", "食伤生财"),
        notes="庚日主样本，验证伤官制杀的七杀和正印承接链。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.wealth_authority_resource.geng_day",
        pillar_displays=("甲午", "乙巳", "庚申", "戊寅"),
        expected_label="财生官/财滋杀",
        expected_nodes=("wealth", "authority", "resource"),
        expected_path_terms=("甲偏财", "丁正官", "戊偏印", "庚日主"),
        forbidden_labels=("食神制杀", "伤官制杀"),
        notes="庚日主财官印样本，验证财富星进入官星后由印承接。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.wealth_authority_resource.xin_day",
        pillar_displays=("乙未", "丙午", "辛酉", "己卯"),
        expected_label="财生官/财滋杀",
        expected_nodes=("wealth", "authority", "resource"),
        expected_path_terms=("乙偏财", "丙正官", "己偏印", "辛日主"),
        forbidden_labels=("食神制杀", "伤官制杀"),
        notes="辛日主财官印样本，验证财生官不被输出制杀路径抢占。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.wealth_authority_resource.ren_day",
        pillar_displays=("丙申", "丁未", "壬子", "庚辰"),
        expected_label="财生官/财滋杀",
        expected_nodes=("wealth", "authority", "resource"),
        expected_path_terms=("丙偏财", "戊七杀", "庚偏印", "壬日主"),
        forbidden_labels=("食神制杀", "伤官制杀"),
        notes="壬日主财滋杀样本，验证财星进入七杀压力后由偏印承接。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.wealth_authority_resource.gui_day",
        pillar_displays=("丁酉", "戊申", "癸亥", "辛巳"),
        expected_label="财生官/财滋杀",
        expected_nodes=("wealth", "authority", "resource"),
        expected_path_terms=("丁偏财", "戊正官", "辛偏印", "癸日主"),
        forbidden_labels=("食神制杀", "伤官制杀"),
        notes="癸日主财官印样本，验证正官路径和偏印承接。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.wealth_authority_resource.ding_day",
        pillar_displays=("癸卯", "甲寅", "丁巳", "乙酉"),
        expected_label="财生官/财滋杀",
        expected_nodes=("wealth", "authority", "resource"),
        expected_path_terms=("辛偏财", "癸七杀", "甲正印", "丁日主"),
        forbidden_labels=("食神制杀", "伤官制杀"),
        notes="丁日主财滋杀样本，验证偏财到七杀再到正印的路径。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.output_generate_wealth.jia_day",
        pillar_displays=("戊子", "己亥", "甲寅", "壬辰"),
        expected_label="食伤生财",
        expected_nodes=("resource", "output", "wealth"),
        expected_path_terms=("壬偏印", "甲比肩", "丙食神", "戊偏财"),
        forbidden_labels=("食神制杀", "伤官制杀"),
        expected_semantic_labels=("财破印", "比劫夺财", "印制食伤"),
        notes="甲日主食伤生财样本，验证输出进入财星路径可作为主标签。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.output_controls_authority.generic_yi_day",
        pillar_displays=("己丑", "庚子", "乙卯", "癸巳"),
        expected_label="输出制官杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("丙伤官", "庚正官", "癸偏印", "乙日主"),
        forbidden_labels=("食神制杀", "伤官制杀"),
        notes="乙日主泛化输出制官杀样本，验证非七杀组合不会误命名为食神制杀或伤官制杀。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.output_controls_authority.zhengguan_jia_day",
        pillar_displays=("丙午", "戊辰", "甲子", "辛酉"),
        expected_label="输出制官杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("丙食神", "辛正官", "癸正印", "甲日主"),
        forbidden_labels=("食神制杀", "伤官制杀", "食伤生财"),
        expected_semantic_labels=("食伤生财",),
        notes="甲日主正官样本，验证食神见正官时只归入泛化输出制官杀，不误判为食神制杀。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.resource_supports_self.gui_day",
        pillar_displays=("甲子", "癸酉", "癸酉", "辛酉"),
        expected_label="印星承身",
        expected_nodes=("resource", "self"),
        expected_path_terms=("辛偏印", "癸比肩", "癸日主"),
        forbidden_labels=("食伤生财", "财生官/财滋杀", "官印/杀印相生"),
        notes="癸日主印星承身样本，验证资源星直接承接到比劫和日主时可被知识库完整命名。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.peer_supports_day_master.xin_day",
        pillar_displays=("甲子", "癸酉", "辛卯", "辛卯"),
        expected_label="比劫承身",
        expected_nodes=("self",),
        expected_path_terms=("辛比肩", "辛日主"),
        forbidden_labels=("食伤生财", "财生官/财滋杀", "官印/杀印相生"),
        notes="辛日主比劫承身样本，验证同类承身主链不被财官印或食伤模板覆盖。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.time_clash_blocker.food_controls_killing",
        pillar_displays=("辛酉", "癸巳", "乙卯", "丁丑"),
        expected_label="食神制杀",
        expected_nodes=("output", "authority", "resource"),
        expected_path_terms=("丁食神", "辛七杀", "癸偏印", "乙日主"),
        forbidden_labels=("食伤生财",),
        expected_time_relation_types=("clash", "break", "punishment"),
        flow_year_pillar="丁酉",
        luck_pillar="甲申",
        notes="验证岁运冲破刑只作为结构波动和阻断证据，不改变原局食神制杀主链。",
    ),
    StructureDynamicsSyntheticCase(
        case_id="sde.v2.synthetic.time_clash_blocker.output_wealth",
        pillar_displays=("戊子", "己亥", "甲寅", "壬辰"),
        expected_label="食伤生财",
        expected_nodes=("resource", "output", "wealth"),
        expected_path_terms=("壬偏印", "甲比肩", "丙食神", "戊偏财"),
        expected_semantic_labels=("比劫夺财", "印制食伤"),
        expected_time_relation_types=("clash",),
        flow_year_pillar="甲午",
        luck_pillar="甲子",
        notes="验证流年子午冲进入阻断诊断，但食伤生财主路径仍保留反例边界。",
    ),
)


def run_structure_dynamics_synthetic_suite(
    cases: tuple[StructureDynamicsSyntheticCase, ...] = STRUCTURE_DYNAMICS_SYNTHETIC_CASES,
) -> dict[str, Any]:
    rows = tuple(_evaluate_case(case) for case in cases)
    failures = tuple(
        failure
        for row in rows
        for failure in row.get("failures", ())
    )
    pass_count = sum(1 for row in rows if row.get("ok") is True)
    return {
        "version": STRUCTURE_DYNAMICS_SYNTHETIC_VERSION,
        "case_count": len(rows),
        "pass_count": pass_count,
        "pass_rate": round(pass_count / max(1, len(rows)), 4),
        "ok": not failures,
        "results": rows,
        "failures": failures,
        "quality_scores": {
            "dynamic_path_consistency": round(pass_count / max(1, len(rows)), 4),
            "semantic_candidate_precision": _semantic_precision(rows),
        },
        "runtime_mutation": False,
        "guardrails": [
            "STRUCTURE_DYNAMICS_SYNTHETIC_IS_DRY_RUN",
            "NO_RUNTIME_RULE_MUTATION",
            "NO_POLICY_POINTER_MUTATION",
            "SDE_V2_VALIDATES_PATH_BEFORE_LEGACY_SWITCH",
        ],
    }


def _evaluate_case(case: StructureDynamicsSyntheticCase) -> dict[str, Any]:
    with _baseline_structure_dynamics_policy():
        runtime = run_runtime_from_pillars(
            *case.pillar_displays,
            input_id=case.case_id,
            source_role="admin",
            flow_year_pillar=case.flow_year_pillar,
            luck_pillar=case.luck_pillar,
            llm_mode="deterministic",
        )
    dynamics = runtime.get("structure_dynamics", {})
    chain = dynamics.get("dominant_chain_v2", {}) if isinstance(dynamics, dict) else {}
    legacy_chain = dynamics.get("legacy_dynamic_chain", {}) if isinstance(dynamics, dict) else {}
    brain_path = runtime.get("brain_state", {}).get("public_summary", {}).get("dynamic_work_path", {})
    failures: list[str] = []
    label = str(chain.get("pattern_label", ""))
    nodes = tuple(str(row) for row in chain.get("nodes", ()) if str(row))
    path_text = " ".join(str(row) for row in chain.get("node_labels", ()) if str(row))
    semantic_labels = tuple(
        str(row.get("label", ""))
        for row in dynamics.get("semantic_candidates", ())
        if isinstance(row, dict)
    ) if isinstance(dynamics, dict) else ()
    diagnostics = dynamics.get("sde_v2", {}).get("path_diagnostics", {}) if isinstance(dynamics, dict) else {}
    time_relation_types = tuple(
        str(row.get("relation_type", ""))
        for row in diagnostics.get("time_relation_blockers", ())
        if isinstance(row, dict)
    ) if isinstance(diagnostics, dict) else ()
    if label != case.expected_label:
        failures.append(f"label_mismatch:{case.case_id}:{label}:{case.expected_label}")
    if nodes[: len(case.expected_nodes)] != case.expected_nodes:
        failures.append(f"nodes_mismatch:{case.case_id}:{nodes}:{case.expected_nodes}")
    for term in case.expected_path_terms:
        if term not in path_text:
            failures.append(f"missing_path_term:{case.case_id}:{term}")
    for forbidden in case.forbidden_labels:
        if label == forbidden:
            failures.append(f"forbidden_label_as_dominant:{case.case_id}:{forbidden}")
    if case.expected_label not in semantic_labels:
        failures.append(f"missing_semantic_candidate:{case.case_id}:{case.expected_label}")
    for semantic_label in case.expected_semantic_labels:
        if semantic_label not in semantic_labels:
            failures.append(f"missing_expected_semantic_candidate:{case.case_id}:{semantic_label}")
    for relation_type in case.expected_time_relation_types:
        if relation_type not in time_relation_types:
            failures.append(f"missing_time_relation_blocker:{case.case_id}:{relation_type}")
    if isinstance(brain_path, dict) and str(brain_path.get("label", "")) != case.expected_label:
        failures.append(f"brain_work_path_label_mismatch:{case.case_id}:{brain_path.get('label')}")
    return {
        "case_id": case.case_id,
        "ok": not failures,
        "expected": case.to_dict(),
        "observed": {
            "label": label,
            "nodes": nodes,
            "legacy_label": str(legacy_chain.get("pattern_label", "")),
            "legacy_nodes": tuple(str(row) for row in legacy_chain.get("nodes", ()) if str(row)),
            "node_labels": tuple(chain.get("node_labels", ())),
            "edge_labels": tuple(chain.get("edge_labels", ())),
            "semantic_labels": semantic_labels,
            "time_relation_blockers": tuple(time_relation_types),
            "brain_work_path": brain_path,
        },
        "failures": tuple(failures),
        "runtime_mutation": False,
    }


def _semantic_precision(rows: tuple[dict[str, Any], ...]) -> float:
    if not rows:
        return 0.0
    matched = 0
    for row in rows:
        expected = str(row.get("expected", {}).get("expected_label", ""))
        observed = row.get("observed", {})
        labels = observed.get("semantic_labels", ()) if isinstance(observed, dict) else ()
        if expected in labels:
            matched += 1
    return round(matched / max(1, len(rows)), 4)


@contextmanager
def _baseline_structure_dynamics_policy() -> Any:
    previous = os.environ.get("V20_STRUCTURE_DYNAMICS_DISABLE_RUNTIME_POLICY")
    os.environ["V20_STRUCTURE_DYNAMICS_DISABLE_RUNTIME_POLICY"] = "1"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("V20_STRUCTURE_DYNAMICS_DISABLE_RUNTIME_POLICY", None)
        else:
            os.environ["V20_STRUCTURE_DYNAMICS_DISABLE_RUNTIME_POLICY"] = previous
