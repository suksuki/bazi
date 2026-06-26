from __future__ import annotations

from typing import Any

from v20.knowledge.directory_seeds import build_full_directory_seed_library
from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.structure_mechanisms import structure_mechanism_units
from v20.rules.catalog import build_bazi_rule_catalog
from v20.validation.structure_dynamics_path_distribution import build_structure_dynamics_path_distribution


STRUCTURE_DYNAMICS_KNOWLEDGE_COVERAGE_VERSION = "v20.structure_dynamics_knowledge_coverage.v1"
_NON_STRUCTURAL_LABELS = frozenset({"", "暂未形成清晰结构主链"})


_LABEL_SUPPORT_TERMS: dict[str, tuple[str, ...]] = {
    "食神制杀": ("食神制杀",),
    "伤官制杀": ("伤官制杀", "伤官见官", "输出制官杀"),
    "输出制官杀": ("食伤输出路径", "官杀作用路径", "五行生克泄耗助", "五行制化通关", "食神制杀", "伤官见官"),
    "食伤生财": ("食伤生财",),
    "财生官/财滋杀": ("财生官财官相生", "财生官", "财滋杀"),
    "官印/杀印相生": ("官印相生", "杀印相生", "官印杀印规则"),
    "印星承身": ("印星", "印比", "印星转化路径"),
    "比劫承身": ("比劫", "比肩", "劫财", "印比"),
    "印制食伤": ("印星转化路径", "枭神夺食", "印制食伤"),
    "比劫夺财": ("比劫夺财分财", "比劫分财规则", "比劫夺财"),
    "财破印": ("财破印财多坏印", "财破印", "财多坏印"),
}


def build_structure_dynamics_knowledge_coverage_report(
    *,
    path_distribution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    distribution = path_distribution or build_structure_dynamics_path_distribution()
    observed_labels = _observed_labels(distribution)
    mechanism_labels = {unit.label for unit in structure_mechanism_units()}
    knowledge_unit_labels = _structure_knowledge_unit_labels()
    directory_text = _directory_seed_text()
    rule_text = _rule_catalog_text()
    rows = [
        _coverage_row(
            label=label,
            distribution=distribution,
            mechanism_labels=mechanism_labels,
            knowledge_unit_labels=knowledge_unit_labels,
            directory_text=directory_text,
            rule_text=rule_text,
        )
        for label in sorted(observed_labels)
    ]
    unsupported = [row["label"] for row in rows if not row["covered"]]
    partial = [row["label"] for row in rows if row["covered"] and not row["rule_catalog_supported"]]
    return {
        "version": STRUCTURE_DYNAMICS_KNOWLEDGE_COVERAGE_VERSION,
        "status": "covered_current_scope" if not unsupported else "needs_knowledge_expansion",
        "scope": "synthetic_path_distribution_current_scope",
        "observed_label_count": len(observed_labels),
        "mechanism_unit_count": len(mechanism_labels),
        "full_knowledge_unit_count": len(knowledge_unit_labels),
        "covered_count": len(rows) - len(unsupported),
        "unsupported_count": len(unsupported),
        "covered_labels": [row["label"] for row in rows if row["covered"]],
        "unsupported_labels": unsupported,
        "partial_rule_catalog_labels": partial,
        "coverage_rows": rows,
        "coverage_note": "当前合成分布内出现的结构动态标签均有机制单元和知识目录支撑；全量 518K 冷门路径仍需继续回放证明。",
        "next_gaps": [
            "run_518k_structure_path_distribution",
            "promote_structure_mechanisms_into_full_knowledge_units",
            "add_rare_path_counterexamples_when_distribution_finds_new_labels",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "COVERAGE_AUDIT_IS_READ_ONLY",
            "STRUCTURE_LABELS_MUST_MAP_TO_KNOWLEDGE_MECHANISM_UNITS",
            "OBSERVED_PATH_LABELS_MUST_NOT_BE_UNSUPPORTED_IN_ADMIN_PLAN",
            "FULL_518K_COVERAGE_REQUIRES_CORPUS_REPLAY",
        ],
    }


def _observed_labels(distribution: dict[str, Any]) -> set[str]:
    labels: set[str] = set()
    for key in ("label_distribution", "semantic_distribution"):
        for row in distribution.get(key, ()) if isinstance(distribution.get(key), list) else ():
            if isinstance(row, dict) and row.get("key"):
                label = str(row["key"])
                if label not in _NON_STRUCTURAL_LABELS:
                    labels.add(label)
    return labels


def _coverage_row(
    *,
    label: str,
    distribution: dict[str, Any],
    mechanism_labels: set[str],
    knowledge_unit_labels: set[str],
    directory_text: str,
    rule_text: str,
) -> dict[str, Any]:
    terms = _LABEL_SUPPORT_TERMS.get(label, (label,))
    mechanism_supported = label in mechanism_labels
    full_knowledge_unit_supported = label in knowledge_unit_labels
    directory_supported = any(term in directory_text for term in terms)
    rule_catalog_supported = any(term in rule_text for term in terms)
    return {
        "label": label,
        "label_count": _distribution_count(distribution, "label_distribution", label),
        "semantic_count": _distribution_count(distribution, "semantic_distribution", label),
        "mechanism_unit_supported": mechanism_supported,
        "full_knowledge_unit_supported": full_knowledge_unit_supported,
        "knowledge_directory_supported": directory_supported,
        "rule_catalog_supported": rule_catalog_supported,
        "support_terms": list(terms),
        "covered": mechanism_supported and full_knowledge_unit_supported and (directory_supported or rule_catalog_supported),
        "support_sources": _support_sources(
            mechanism_supported=mechanism_supported,
            full_knowledge_unit_supported=full_knowledge_unit_supported,
            directory_supported=directory_supported,
            rule_catalog_supported=rule_catalog_supported,
        ),
    }


def _distribution_count(distribution: dict[str, Any], key: str, label: str) -> int:
    rows = distribution.get(key, ())
    if not isinstance(rows, list):
        return 0
    for row in rows:
        if isinstance(row, dict) and row.get("key") == label:
            return int(row.get("count", 0) or 0)
    return 0


def _support_sources(
    *,
    mechanism_supported: bool,
    full_knowledge_unit_supported: bool,
    directory_supported: bool,
    rule_catalog_supported: bool,
) -> list[str]:
    sources: list[str] = []
    if mechanism_supported:
        sources.append("knowledge.structure_mechanisms")
    if full_knowledge_unit_supported:
        sources.append("knowledge.default_knowledge_units")
    if directory_supported:
        sources.append("knowledge.directory_seeds")
    if rule_catalog_supported:
        sources.append("rules.catalog")
    return sources


def _structure_knowledge_unit_labels() -> set[str]:
    labels: set[str] = set()
    for unit in default_knowledge_units():
        if not str(unit.knowledge_id).startswith("v20.structure.mechanism."):
            continue
        for tag in unit.retrieval_tags:
            if tag and not str(tag).startswith(("structure_", "dynamic_", "knowledge.")):
                labels.add(str(tag))
    return labels


def _directory_seed_text() -> str:
    library = build_full_directory_seed_library()
    seeds = library.get("seeds", ())
    pieces: list[str] = []
    if isinstance(seeds, list):
        for seed in seeds:
            if isinstance(seed, dict):
                pieces.extend(str(seed.get(key, "")) for key in ("title", "layer", "measurement_role", "rule_path_candidate"))
    return "\n".join(pieces)


def _rule_catalog_text() -> str:
    catalog = build_bazi_rule_catalog()
    rules = catalog.get("rules", ())
    pieces: list[str] = []
    if isinstance(rules, list):
        for rule in rules:
            if isinstance(rule, dict):
                pieces.extend(str(rule.get(key, "")) for key in ("rule_id", "title", "domain", "layer"))
                pieces.extend(str(item) for item in rule.get("bridges_to_runtime_rules", ()) if item)
    return "\n".join(pieces)
