from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


STRUCTURE_MECHANISM_UNITS_VERSION = "v20.structure_mechanism_units.v1"


@dataclass(frozen=True)
class StructureMechanismUnit:
    semantic_key: str
    label: str
    domain: str
    required_pairs: tuple[tuple[str, str], ...]
    required_terms: tuple[str, ...] = ()
    exact_family_chain: tuple[str, ...] = ()
    priority: int = 0
    boundary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


STRUCTURE_MECHANISM_UNITS: tuple[StructureMechanismUnit, ...] = (
    StructureMechanismUnit(
        semantic_key="knowledge.semantic.shishen_controls_killing",
        label="食神制杀",
        domain="career",
        required_pairs=(("output", "authority"),),
        required_terms=("食神", "七杀"),
        priority=90,
        boundary="食神制杀只说明输出星对七杀形成制化通路，必须继续看日主承载、印星承接和财星是否改写路径。",
    ),
    StructureMechanismUnit(
        semantic_key="knowledge.semantic.shangguan_controls_killing",
        label="伤官制杀",
        domain="career",
        required_pairs=(("output", "authority"),),
        required_terms=("伤官", "七杀"),
        priority=88,
        boundary="伤官制杀强调强输出对七杀的制约，不能直接等同于吉凶结果，需看印星、财星和日主承载。",
    ),
    StructureMechanismUnit(
        semantic_key="knowledge.semantic.output_controls_authority",
        label="输出制官杀",
        domain="career",
        required_pairs=(("output", "authority"),),
        priority=70,
        boundary="输出制官杀是制化路径候选，需继续区分食神、伤官、正官、七杀及承接节点。",
    ),
    StructureMechanismUnit(
        semantic_key="knowledge.semantic.output_generate_wealth",
        label="食伤生财",
        domain="wealth",
        required_pairs=(("output", "wealth"),),
        priority=65,
        boundary="食伤生财说明输出进入财星路径，不直接等于收入结果，需看财星承载、比劫分夺和岁运引动。",
    ),
    StructureMechanismUnit(
        semantic_key="knowledge.semantic.wealth_generate_authority",
        label="财生官/财滋杀",
        domain="career",
        required_pairs=(("wealth", "authority"),),
        priority=60,
        boundary="财星进入官杀压力或秩序路径，需要区分正官、七杀和日主是否承载。",
    ),
    StructureMechanismUnit(
        semantic_key="knowledge.semantic.authority_generate_resource",
        label="官印/杀印相生",
        domain="career",
        required_pairs=(("authority", "resource"),),
        priority=55,
        boundary="官杀压力进入印星承接路径，不直接推出职位、学历或结果。",
    ),
    StructureMechanismUnit(
        semantic_key="knowledge.semantic.resource_supports_self",
        label="印星承身",
        domain="strength",
        required_pairs=(("resource", "self"),),
        priority=42,
        boundary="印星承身说明资源星进入日主或比劫承接路径，只能作为承载与支持线索，不能直接推出吉凶结果。",
    ),
    StructureMechanismUnit(
        semantic_key="knowledge.semantic.peer_supports_day_master",
        label="比劫承身",
        domain="strength",
        required_pairs=(),
        exact_family_chain=("self", "day_master"),
        priority=36,
        boundary="比劫承身说明同气力量直接承接日主，只能作为自我承载和同类助力线索，不能直接推出竞争、破财或吉凶结果。",
    ),
    StructureMechanismUnit(
        semantic_key="knowledge.semantic.resource_constrains_output",
        label="印制食伤",
        domain="ten_god",
        required_pairs=(("resource", "output"),),
        priority=45,
        boundary="印星牵制输出路径，需要看财星是否制印、输出是否被阻断，以及是否形成通关。",
    ),
    StructureMechanismUnit(
        semantic_key="knowledge.semantic.peer_competes_wealth",
        label="比劫夺财",
        domain="wealth",
        required_pairs=(("self", "wealth"),),
        priority=50,
        boundary="比劫夺财说明同类力量进入财星分夺或竞争路径，不等同于破财结论，必须看财星根气、官杀制比劫和岁运触发。",
    ),
    StructureMechanismUnit(
        semantic_key="knowledge.semantic.wealth_breaks_resource",
        label="财破印",
        domain="ten_god",
        required_pairs=(("wealth", "resource"),),
        priority=48,
        boundary="财破印说明财星对印星形成制约路径，需要看印星是否为关键承接、官杀是否转入印星，以及输出是否被保护或阻断。",
    ),
)


def structure_mechanism_units() -> tuple[StructureMechanismUnit, ...]:
    return STRUCTURE_MECHANISM_UNITS


def match_structure_path_mechanisms(
    *,
    family_chain: tuple[str, ...],
    node_labels: tuple[str, ...],
    path_score: float,
) -> list[dict[str, Any]]:
    label_text = "".join(node_labels)
    rows: list[dict[str, Any]] = []
    for unit in STRUCTURE_MECHANISM_UNITS:
        if unit.exact_family_chain and tuple(family_chain) != unit.exact_family_chain:
            continue
        if not _required_pairs_match(unit.required_pairs, family_chain):
            continue
        if unit.required_terms and not all(term in label_text for term in unit.required_terms):
            continue
        rows.append(_mechanism_row(unit=unit, family_chain=family_chain, path_score=path_score))
    rows.sort(key=lambda row: (int(row.get("priority", 0)), float(row.get("confidence", 0.0))), reverse=True)
    return rows


def _required_pairs_match(required_pairs: tuple[tuple[str, str], ...], family_chain: tuple[str, ...]) -> bool:
    for left, right in required_pairs:
        left_positions = [index for index, family in enumerate(family_chain) if family == left]
        right_positions = [index for index, family in enumerate(family_chain) if family == right]
        if not any(left_index < right_index for left_index in left_positions for right_index in right_positions):
            return False
    return True


def _mechanism_row(*, unit: StructureMechanismUnit, family_chain: tuple[str, ...], path_score: float) -> dict[str, Any]:
    return {
        "semantic_key": unit.semantic_key,
        "label": unit.label,
        "domain": unit.domain,
        "confidence": round(min(0.96, 0.42 + path_score * 0.5 + min(unit.priority, 100) * 0.0005), 4),
        "matched_path": list(family_chain),
        "boundary": unit.boundary,
        "mechanism_source": "knowledge.structure_mechanisms",
        "mechanism_units_version": STRUCTURE_MECHANISM_UNITS_VERSION,
        "priority": unit.priority,
    }
