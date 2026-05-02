from __future__ import annotations

from v20.core.elements import element_distribution
from v20.core.schemas import ChartFacts, CoreInference, TimeContext
from v20.features.discovery_trace import DOMAIN_MECHANISM_TYPES, TOPIC_PROJECTIONS
from v20.features.schema import BaziFeature


WEALTH_LABELS = {"正财", "偏财"}
AUTHORITY_LABELS = {"正官", "七杀"}
OUTPUT_LABELS = {"食神", "伤官"}
RESOURCE_LABELS = {"正印", "偏印"}
PEER_LABELS = {"比肩", "劫财"}


def build_feature_discovery_model(
    facts: ChartFacts,
    inference: CoreInference,
    time_context: TimeContext,
    features: tuple[BaziFeature, ...] | list[BaziFeature],
) -> dict[str, object]:
    feature_rows = tuple(features)
    evidence_atoms = _evidence_atoms_from_facts(facts, inference, time_context)
    rule_paths = _rule_paths_from_evidence(evidence_atoms, feature_rows)
    mechanism_paths = _mechanism_paths_from_rules(rule_paths, feature_rows)
    decision_states = _decision_states_from_evidence(feature_rows, evidence_atoms, time_context)
    topic_projections = _topic_projections_from_decisions(decision_states)
    feature_bindings = _feature_bindings(feature_rows, rule_paths, decision_states)
    counter_evidence = _counter_evidence_from_rules(rule_paths)
    trace_nodes = _trace_nodes(evidence_atoms, rule_paths, mechanism_paths, decision_states, topic_projections)
    layer_coverage = _model_layer_coverage(evidence_atoms)
    completeness = _algorithm_completeness(layer_coverage, counter_evidence, trace_nodes)
    return {
        "version": "v20.feature_discovery_model.v1",
        "status": "ready",
        "algorithm": "evidence_first_feature_discovery_phase1",
        "source": "ChartFacts+CoreInference+TimeContext",
        "feature_count": len(feature_rows),
        "evidence_atom_count": len(evidence_atoms),
        "rule_path_count": len(rule_paths),
        "mechanism_path_count": len(mechanism_paths),
        "decision_state_count": len(decision_states),
        "topic_projection_count": len(topic_projections),
        "feature_binding_count": len(feature_bindings),
        "counter_evidence_count": len(counter_evidence),
        "trace_node_count": len(trace_nodes),
        "model_layer_coverage": layer_coverage,
        "model_layer_coverage_count": len(layer_coverage),
        "algorithm_completeness": completeness,
        "evidence_atoms": evidence_atoms,
        "rule_paths": rule_paths,
        "mechanism_paths": mechanism_paths,
        "counter_evidence": counter_evidence,
        "decision_states": decision_states,
        "topic_projections": topic_projections,
        "feature_bindings": feature_bindings,
        "trace_nodes": trace_nodes,
        "runtime_mutation": False,
        "guardrails": (
            "EVIDENCE_FIRST_FEATURE_DISCOVERY",
            "TRACE_IS_INTERNAL_REASONING_CONTEXT",
            "TRACE_IS_NOT_USER_FACING_VERDICT",
            "BaziFeature_REMAINS_PRODUCT_CONTRACT",
            "TOPIC_PROJECTION_REQUIRED_BEFORE_APPLICATION_OUTPUT",
            "NO_LLM_ARBITRATION",
        ),
    }


def _evidence_atoms_from_facts(
    facts: ChartFacts,
    inference: CoreInference,
    time_context: TimeContext,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = [
        _atom("evidence.l0.day_master", "chart_fact", "day_master", f"日主={facts.day_master}", "foundation", ("feature.strength", "feature.ten_god")),
        _atom("evidence.l0.calendar_assumption", "chart_fact", "calendar", facts.calendar_assumption, "foundation", ("feature.chart_fact",)),
        _atom("evidence.l2.support_score", "strength", "support_pressure", f"support={inference.support_score}", "core", ("feature.strength",)),
        _atom("evidence.l2.pressure_score", "strength", "support_pressure", f"pressure={inference.pressure_score}", "core", ("feature.strength",)),
        _atom("evidence.l2.capacity_state", "strength", "capacity_state", inference.day_master_capacity, "core", ("feature.strength", "feature.useful_god")),
    ]
    for position, pillar in sorted(facts.pillars.items()):
        rows.append(
            _atom(
                f"evidence.l0.pillar.{position}",
                "chart_fact",
                "pillar",
                f"{position}:{pillar.display}",
                "foundation",
                ("feature.chart_fact", "feature.branch", "feature.ten_god"),
            )
        )
    for index, row in enumerate(facts.visible_ten_gods):
        rows.append(_ten_god_atom("visible", index, row.label, row.pillar, row.weight, row.element))
    for index, row in enumerate(facts.hidden_ten_gods):
        rows.append(_ten_god_atom("hidden", index, row.label, row.pillar, row.weight, row.element))
    for index, hit in enumerate(facts.relation_hits):
        rows.append(
            _atom(
                f"evidence.l4.branch_relation.{index}",
                "branch",
                hit.relation_type,
                f"{'/'.join(hit.positions)}:{'/'.join(hit.branches)}",
                hit.layer,
                ("feature.branch", "feature.relationship", "feature.romance"),
            )
        )
    for position in facts.vault_branches:
        rows.append(_atom(f"evidence.l4.vault.{position}", "branch", "vault", position, "core", ("feature.pattern", "feature.branch")))
    for element, value in sorted(element_distribution(facts).items()):
        rows.append(_atom(f"evidence.l1.element.{element}", "element", "element_distribution", f"{element}={value}", "core", ("feature.element", "feature.useful_god")))
    rows.extend(_wealth_atoms(facts))
    rows.extend(_combination_atoms(facts))
    rows.extend(_pattern_atoms(facts))
    rows.extend(_useful_god_atoms(inference))
    rows.extend(_palace_atoms(facts))
    rows.extend(_blind_lifa_atoms(facts))
    rows.extend(_time_atoms(time_context))
    rows.extend(_archive_atoms())
    rows.extend(_governance_atoms())
    return tuple(rows)


def _rule_paths_from_evidence(
    evidence_atoms: tuple[dict[str, object], ...],
    features: tuple[BaziFeature, ...],
) -> tuple[dict[str, object], ...]:
    by_domain: dict[str, list[dict[str, object]]] = {}
    for atom in evidence_atoms:
        by_domain.setdefault(str(atom["domain"]), []).append(atom)
    rows: list[dict[str, object]] = []
    for domain, atoms in sorted(by_domain.items()):
        target_features = tuple(feature.feature_id for feature in features if feature.domain == domain or domain in feature.feature_id)
        if not target_features and domain == "chart_fact":
            target_features = tuple(feature.feature_id for feature in features if feature.domain in {"strength", "ten_god", "branch"})
        rows.append(
            {
                "path_id": f"rule_path.{domain}.evidence_gate",
                "title": f"{domain} evidence gate",
                "domain": domain,
                "evidence_atom_ids": tuple(str(atom["atom_id"]) for atom in atoms),
                "target_feature_ids": target_features,
                "decision_state_policy": _domain_decision_policy(domain),
                "counter_evidence_ids": _counter_evidence_ids(domain, atoms),
            }
        )
    return tuple(rows)


def _mechanism_paths_from_rules(
    rule_paths: tuple[dict[str, object], ...],
    features: tuple[BaziFeature, ...],
) -> tuple[dict[str, object], ...]:
    feature_domains = {feature.domain for feature in features}
    rows = []
    for path in rule_paths:
        domain = str(path["domain"])
        if domain == "chart_fact":
            continue
        rows.append(
            {
                "mechanism_id": f"mechanism.{domain}",
                "title": f"{domain} mechanism path",
                "mechanism_type": DOMAIN_MECHANISM_TYPES.get(domain, f"{domain}_mechanism"),
                "source_rule_path_ids": (path["path_id"],),
                "source_feature_ids": tuple(feature.feature_id for feature in features if feature.domain == domain),
                "target_domains": _target_domains(domain, feature_domains),
                "boundary": "结构机制只输出证据状态，不输出命运结论。",
            }
        )
    return tuple(rows)


def _decision_states_from_evidence(
    features: tuple[BaziFeature, ...],
    evidence_atoms: tuple[dict[str, object], ...],
    time_context: TimeContext,
) -> tuple[dict[str, object], ...]:
    evidence_domains = {str(atom["domain"]) for atom in evidence_atoms}
    rows = []
    for feature in features:
        state = _state_for_feature(feature, evidence_domains, time_context)
        rows.append(
            {
                "state_id": f"decision_state.{feature.feature_id}",
                "state": state,
                "title": feature.title,
                "source_feature_id": feature.feature_id,
                "domain": feature.domain,
                "confidence": feature.confidence,
                "readiness": feature.readiness,
                "evidence_domain_present": feature.domain in evidence_domains or _projection_evidence_present(feature.domain, evidence_domains),
            }
        )
    return tuple(rows)


def _topic_projections_from_decisions(decision_states: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    decision_domains = {str(row["domain"]) for row in decision_states if str(row["state"]) not in {"blocked", "countered", "out_of_scope"}}
    rows = []
    for projection in TOPIC_PROJECTIONS:
        source_domains = set(projection.get("source_domains", ()))
        matched = tuple(sorted(decision_domains & source_domains))
        if matched:
            rows.append(
                {
                    "projection_id": projection.get("projection_id", ""),
                    "topic_domain": projection.get("topic_domain", ""),
                    "title": projection.get("title", ""),
                    "matched_source_domains": matched,
                    "output_focus": projection.get("output_focus", ()),
                    "boundary": projection.get("boundary", ""),
                    "state": "candidate_projection",
                }
            )
    return tuple(rows)


def _feature_bindings(
    features: tuple[BaziFeature, ...],
    rule_paths: tuple[dict[str, object], ...],
    decision_states: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    paths_by_domain = {str(path["domain"]): path for path in rule_paths}
    states_by_feature = {str(row["source_feature_id"]): row for row in decision_states}
    rows = []
    for feature in features:
        path = paths_by_domain.get(feature.domain) or paths_by_domain.get("chart_fact", {})
        state = states_by_feature.get(feature.feature_id, {})
        rows.append(
            {
                "feature_id": feature.feature_id,
                "domain": feature.domain,
                "rule_path_id": path.get("path_id", ""),
                "decision_state": state.get("state", ""),
                "evidence_atom_ids": tuple(path.get("evidence_atom_ids", ()))[:8],
            }
        )
    return tuple(rows)


def _counter_evidence_from_rules(rule_paths: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    rows = []
    for path in rule_paths:
        for counter_id in path.get("counter_evidence_ids", ()):
            rows.append(
                {
                    "counter_id": counter_id,
                    "source_rule_path_id": path.get("path_id", ""),
                    "domain": path.get("domain", ""),
                    "title": _counter_title(str(counter_id)),
                    "resulting_state": _counter_resulting_state(str(counter_id)),
                    "runtime_mutation": False,
                }
            )
    rows.extend(
        (
            {
                "counter_id": "counter.l11.archive_not_runtime_authority",
                "source_rule_path_id": "rule_path.archive.evidence_gate",
                "domain": "archive",
                "title": "辅助体系归档内容不能直接作为运行时裁决依据",
                "resulting_state": "requires_review",
                "runtime_mutation": False,
            },
            {
                "counter_id": "counter.l12.llm_no_arbitration",
                "source_rule_path_id": "rule_path.governance.evidence_gate",
                "domain": "governance",
                "title": "LLM 不能绕过 EvidencePack 或覆盖裁决",
                "resulting_state": "blocked",
                "runtime_mutation": False,
            },
        )
    )
    deduped: dict[str, dict[str, object]] = {}
    for row in rows:
        deduped[str(row["counter_id"])] = row
    return tuple(deduped[key] for key in sorted(deduped))


def _trace_nodes(
    evidence_atoms: tuple[dict[str, object], ...],
    rule_paths: tuple[dict[str, object], ...],
    mechanism_paths: tuple[dict[str, object], ...],
    decision_states: tuple[dict[str, object], ...],
    topic_projections: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return (
        {
            "trace_id": "trace.fact_to_evidence",
            "trace_type": "FactNode->EvidenceAtom",
            "title": "ChartFacts/CoreInference/TimeContext 进入证据原子",
            "source_ids": tuple(str(row["atom_id"]) for row in evidence_atoms[:12]),
        },
        {
            "trace_id": "trace.evidence_to_rule_path",
            "trace_type": "EvidenceAtom->RulePath",
            "title": "证据原子按领域汇入规则路径",
            "source_ids": tuple(str(row["path_id"]) for row in rule_paths[:12]),
        },
        {
            "trace_id": "trace.rule_to_mechanism",
            "trace_type": "RulePath->MechanismPath",
            "title": "规则路径汇入命理机制链",
            "source_ids": tuple(str(row["mechanism_id"]) for row in mechanism_paths[:12]),
        },
        {
            "trace_id": "trace.mechanism_to_decision",
            "trace_type": "MechanismPath->DecisionState",
            "title": "机制链形成结构裁决状态",
            "source_ids": tuple(str(row["state_id"]) for row in decision_states[:12]),
        },
        {
            "trace_id": "trace.decision_to_projection",
            "trace_type": "DecisionState->TopicProjection",
            "title": "结构裁决投射到用户主题",
            "source_ids": tuple(str(row["projection_id"]) for row in topic_projections),
        },
    )


def _ten_god_atom(layer: str, index: int, label: str, pillar: str, weight: float, element: str) -> dict[str, object]:
    targets = ["feature.ten_god"]
    if label in WEALTH_LABELS:
        targets.append("feature.wealth")
    if label in AUTHORITY_LABELS:
        targets.append("feature.career")
    if label in OUTPUT_LABELS:
        targets.extend(("feature.wealth", "feature.career"))
    if label in RESOURCE_LABELS:
        targets.extend(("feature.strength", "feature.career"))
    if label in PEER_LABELS:
        targets.extend(("feature.wealth", "feature.relationship"))
    return _atom(
        f"evidence.l3.ten_god.{layer}.{index}",
        "ten_god",
        layer,
        f"{label}@{pillar};weight={weight};element={element}",
        layer,
        tuple(dict.fromkeys(targets)),
    )


def _wealth_atoms(facts: ChartFacts) -> tuple[dict[str, object], ...]:
    rows = []
    wealth_rows = [row for row in [*facts.visible_ten_gods, *facts.hidden_ten_gods] if row.label in WEALTH_LABELS]
    if wealth_rows:
        rows.append(_atom("evidence.l10.wealth.material", "wealth", "wealth_material", f"count={len(wealth_rows)}", "ten_god", ("feature.wealth",)))
    output_rows = [row for row in [*facts.visible_ten_gods, *facts.hidden_ten_gods] if row.label in OUTPUT_LABELS]
    if wealth_rows and output_rows:
        rows.append(_atom("evidence.l10.wealth.output_channel", "wealth", "output_to_wealth", "食伤生财候选", "ten_god", ("feature.wealth", "feature.ten_god")))
    peer_rows = [row for row in [*facts.visible_ten_gods, *facts.hidden_ten_gods] if row.label in PEER_LABELS]
    if wealth_rows and peer_rows:
        rows.append(_atom("evidence.l10.wealth.peer_competition", "wealth", "peer_wealth", "比劫分夺候选", "ten_god", ("feature.wealth",)))
    return tuple(rows)


def _pattern_atoms(facts: ChartFacts) -> tuple[dict[str, object], ...]:
    rows = [
        _atom(
            "evidence.l5.pattern.month_command_review",
            "pattern",
            "month_command_review",
            f"月令={facts.pillars['month'].branch}",
            "core",
            ("feature.pattern",),
        )
    ]
    if facts.vault_branches:
        rows.append(
            _atom(
                "evidence.l5.pattern.vault_review",
                "pattern",
                "vault_pattern_review",
                f"墓库={','.join(facts.vault_branches)}",
                "core",
                ("feature.pattern", "feature.branch"),
            )
        )
    return tuple(rows)


def _useful_god_atoms(inference: CoreInference) -> tuple[dict[str, object], ...]:
    return (
        _atom(
            "evidence.l6.useful_god.capacity_path",
            "useful_god",
            "capacity_path",
            inference.day_master_capacity,
            "core",
            ("feature.useful_god", "feature.strength"),
        ),
        _atom(
            "evidence.l6.useful_god.support_pressure_gap",
            "useful_god",
            "support_pressure_gap",
            f"support={inference.support_score};pressure={inference.pressure_score}",
            "core",
            ("feature.useful_god",),
        ),
    )


def _palace_atoms(facts: ChartFacts) -> tuple[dict[str, object], ...]:
    rows = []
    for position, pillar in sorted(facts.pillars.items()):
        role = {
            "year": "年柱外部背景",
            "month": "月柱平台月令",
            "day": "日柱主体夫妻宫",
            "hour": "时柱输出后续",
        }.get(position, position)
        rows.append(
            _atom(
                f"evidence.l7.palace.{position}",
                "palace",
                "pillar_palace",
                f"{role}:{pillar.display}",
                "palace",
                ("feature.branch", "feature.ten_god"),
            )
        )
    return tuple(rows)


def _blind_lifa_atoms(facts: ChartFacts) -> tuple[dict[str, object], ...]:
    rows = []
    labels = {row.label for row in [*facts.visible_ten_gods, *facts.hidden_ten_gods]}
    if labels & WEALTH_LABELS:
        rows.append(
            _atom(
                "evidence.l8.blind_lifa.wealth_action",
                "blind_lifa",
                "zuogong",
                "财的做功候选：看财来就我、我去取财、承接与分夺",
                "blind_lifa",
                ("feature.wealth", "feature.ten_god", "feature.branch"),
            )
        )
    if labels & AUTHORITY_LABELS:
        rows.append(
            _atom(
                "evidence.l8.blind_lifa.authority_action",
                "blind_lifa",
                "zuogong",
                "官杀做功候选：看规则压力、印化、食伤冲击和承接",
                "blind_lifa",
                ("feature.ten_god", "feature.pattern"),
            )
        )
    if facts.relation_hits:
        rows.append(
            _atom(
                "evidence.l8.blind_lifa.branch_action",
                "blind_lifa",
                "position_image",
                "地支互动可进入位置象与做功路径复核",
                "blind_lifa",
                ("feature.branch",),
            )
        )
    return tuple(rows)


def _governance_atoms() -> tuple[dict[str, object], ...]:
    return (
        _atom(
            "evidence.l12.governance.no_verdict",
            "governance",
            "answer_boundary",
            "禁止把结构状态表达为命运断语",
            "governance",
            ("answer.boundary",),
        ),
        _atom(
            "evidence.l12.governance.evidence_pack_required",
            "governance",
            "evidence_pack_required",
            "用户输出必须经过 EvidencePack 与 AnswerPlan",
            "governance",
            ("answer.evidence",),
        ),
    )


def _archive_atoms() -> tuple[dict[str, object], ...]:
    return (
        _atom(
            "evidence.l11.archive.shensha",
            "archive",
            "auxiliary_symbol",
            "神煞只能作为归档辅助内容，不能单独裁决",
            "archive",
            ("feature.auxiliary_archive",),
        ),
        _atom(
            "evidence.l11.archive.nayin",
            "archive",
            "auxiliary_symbol",
            "纳音不能覆盖五行十神主线",
            "archive",
            ("feature.auxiliary_archive",),
        ),
        _atom(
            "evidence.l11.archive.school_variant",
            "archive",
            "school_variant",
            "门派口诀和异文必须经来源与反证审核",
            "archive",
            ("feature.auxiliary_archive",),
        ),
    )


def _combination_atoms(facts: ChartFacts) -> tuple[dict[str, object], ...]:
    labels = {row.label for row in [*facts.visible_ten_gods, *facts.hidden_ten_gods]}
    rows = []
    if labels & AUTHORITY_LABELS and labels & OUTPUT_LABELS:
        rows.append(_atom("evidence.l3.combo.output_authority", "career", "output_authority", "伤官见官/官伤合参候选", "ten_god", ("feature.ten_god", "feature.pattern")))
    if labels & AUTHORITY_LABELS and labels & RESOURCE_LABELS:
        rows.append(_atom("evidence.l3.combo.authority_resource", "career", "authority_resource", "官印/杀印候选", "ten_god", ("feature.ten_god", "feature.pattern")))
    return tuple(rows)


def _time_atoms(time_context: TimeContext) -> tuple[dict[str, object], ...]:
    if time_context.status != "ready":
        return ()
    rows = []
    for layer in time_context.layers:
        rows.append(_atom(f"evidence.l9.time_layer.{layer.layer_key}", "time", "time_layer", f"{layer.layer_key}:{layer.pillar.display}", "time", ("feature.time",)))
    for index, hit in enumerate(time_context.relation_hits):
        rows.append(_atom(f"evidence.l9.time_relation.{index}", "time", hit.relation_type, f"{'/'.join(hit.positions)}:{'/'.join(hit.branches)}", "time", ("feature.time", "feature.branch")))
    return tuple(rows)


def _atom(
    atom_id: str,
    domain: str,
    evidence_type: str,
    title: str,
    source_layer: str,
    supports: tuple[str, ...],
) -> dict[str, object]:
    return {
        "atom_id": atom_id,
        "domain": domain,
        "evidence_type": evidence_type,
        "title": title,
        "required_fact_types": (source_layer,),
        "supports": supports,
        "boundary": "证据原子只作为结构材料，不直接输出结论。",
    }


def _domain_decision_policy(domain: str) -> str:
    if domain == "time":
        return "volatile"
    if domain in {"useful_god", "pattern", "blind_lifa", "archive"}:
        return "requires_review"
    if domain in {"palace", "governance"}:
        return "candidate"
    if domain in {"wealth", "career", "relationship", "health"}:
        return "candidate"
    if domain == "branch":
        return "mixed"
    return "candidate"


def _counter_evidence_ids(domain: str, atoms: list[dict[str, object]]) -> tuple[str, ...]:
    if domain == "wealth" and not atoms:
        return ("counter.wealth.no_material",)
    if domain == "time" and not atoms:
        return ("counter.time.not_provided",)
    if domain in {"useful_god", "pattern", "blind_lifa", "archive"}:
        return (f"counter.{domain}.needs_practitioner_review",)
    if domain == "palace":
        return ("counter.palace.no_private_fact_inference",)
    if domain == "governance":
        return ("counter.governance.blocks_fortune_verdict",)
    return ()


def _counter_title(counter_id: str) -> str:
    titles = {
        "counter.useful_god.needs_practitioner_review": "用神路径需要命理师复核",
        "counter.pattern.needs_practitioner_review": "格局候选需要命理师复核",
        "counter.blind_lifa.needs_practitioner_review": "盲派做功需要证据链复核",
        "counter.archive.needs_practitioner_review": "辅助归档内容需要额外审核",
        "counter.palace.no_private_fact_inference": "宫位象不能推断隐私事实",
        "counter.governance.blocks_fortune_verdict": "治理层阻断命运断语",
    }
    return titles.get(counter_id, counter_id)


def _counter_resulting_state(counter_id: str) -> str:
    if "governance" in counter_id:
        return "blocked"
    if "archive" in counter_id or "needs_practitioner_review" in counter_id:
        return "requires_review"
    if "palace" in counter_id:
        return "countered"
    return "mixed"


def _state_for_feature(feature: BaziFeature, evidence_domains: set[str], time_context: TimeContext) -> str:
    if feature.domain == "time" and time_context.status == "ready":
        return "volatile"
    if "hidden_material" in feature.feature_id:
        return "mixed"
    if "not_visible" in feature.feature_id:
        return "out_of_scope"
    if feature.domain in {"useful_god", "pattern"} or feature.readiness == "review_ready":
        return "requires_review"
    if feature.domain not in evidence_domains and not _projection_evidence_present(feature.domain, evidence_domains):
        return "weak_candidate"
    if feature.readiness == "ready" and feature.confidence >= 0.48:
        return "confirmed"
    if feature.readiness == "boundary_ready":
        return "weak_candidate"
    return "candidate"


def _projection_evidence_present(domain: str, evidence_domains: set[str]) -> bool:
    projection_sources = {
        "wealth": {"wealth", "ten_god", "strength"},
        "career": {"career", "ten_god", "pattern", "strength"},
        "relationship": {"relationship", "branch", "ten_god"},
        "romance": {"relationship", "branch", "ten_god", "palace"},
        "health": {"health", "element", "strength"},
    }
    return bool(projection_sources.get(domain, set()) & evidence_domains)


def _target_domains(domain: str, feature_domains: set[str]) -> tuple[str, ...]:
    if domain in {"strength", "ten_god", "branch", "time", "pattern", "element", "palace", "blind_lifa", "archive"}:
        return tuple(row for row in ("wealth", "career", "relationship", "romance", "health") if row in feature_domains or row in {"wealth", "career", "relationship", "romance", "health"})
    if domain == "wealth":
        return ("wealth",)
    if domain == "career":
        return ("career",)
    if domain == "relationship":
        return ("relationship", "romance")
    if domain == "health":
        return ("health",)
    return (domain,)


def _model_layer_coverage(evidence_atoms: tuple[dict[str, object], ...]) -> tuple[str, ...]:
    layers = set()
    for atom in evidence_atoms:
        atom_id = str(atom.get("atom_id", ""))
        parts = atom_id.split(".")
        if len(parts) >= 2 and parts[1].startswith("l"):
            layers.add(parts[1].upper())
    return tuple(sorted(layers, key=lambda row: int(row[1:]) if row[1:].isdigit() else 99))


def _algorithm_completeness(
    layer_coverage: tuple[str, ...],
    counter_evidence: tuple[dict[str, object], ...],
    trace_nodes: tuple[dict[str, object], ...],
) -> dict[str, object]:
    required_layers = tuple(f"L{index}" for index in range(13))
    missing_layers = tuple(layer for layer in required_layers if layer not in set(layer_coverage))
    return {
        "version": "v20.feature_discovery_algorithm_completeness.v1",
        "status": "complete_phase1_model" if not missing_layers else "needs_layer_coverage",
        "required_layers": required_layers,
        "covered_layers": layer_coverage,
        "missing_layers": missing_layers,
        "has_counter_evidence": bool(counter_evidence),
        "has_trace_nodes": len(trace_nodes) >= 5,
        "next_phase": "promote_directory_batches_to_exact_rule_paths_and_counterexamples",
    }
