from __future__ import annotations

import re

from abu_v60.mingli.agent_contracts import (
    MingliAgentCasePacket,
    MingliAgentReadingEnvelope,
)
from abu_v60.mingli.agent_fact_language import manifestation_claim_conflicts
from abu_v60.mingli.agent_method_cards import FALLBACK_METHOD_CARD_REF
from abu_v60.mingli.agent_reasoning_modes import BLIND_READING_CONTRACT
from abu_v60.mingli.reading_claim_admission import (
    domain_method_assessment_codes,
    exact_role_path_assessment_codes,
)
from abu_v60.mingli.reading_claim_graph_contracts import (
    MingliReadingClaim,
    MingliReadingClaimEdge,
    MingliReadingClaimGraph,
)
from abu_v60.mingli.reading_claim_language import (
    method_bound_timing_chain,
    method_bound_timing_statement,
    method_bound_working_thesis,
    primary_limit,
)

DOMAIN_KEYS = (
    ("personality", "DOMAIN_PERSONALITY", "性情"),
    ("career", "DOMAIN_CAREER", "事业"),
    ("wealth", "DOMAIN_WEALTH", "财富"),
    ("relationship", "DOMAIN_RELATIONSHIP", "关系"),
    ("family", "DOMAIN_FAMILY", "家庭"),
)


class MingliReadingClaimGraphProjector:
    """Pure projection: no model call, summary, evidence invention or write."""

    def project(
        self,
        reading: MingliAgentReadingEnvelope,
        *,
        packet: MingliAgentCasePacket,
    ) -> MingliReadingClaimGraph:
        if (reading.packet_ref, reading.packet_hash) != (
            packet.packet_ref,
            packet.packet_hash,
        ):
            raise ValueError("mingli_reading_claim_graph_packet_lineage_conflict")
        output = reading.output
        server_issue_keys = set(output.server_issue_keys)
        primary = next(item for item in output.hypotheses if item.role == "PRIMARY")
        primary_chart_evidence = _unique(
            (
                *primary.evidence_ids,
                *primary.mechanism_evidence_ids,
                *(
                    evidence_id
                    for ruling in primary.method_rulings
                    for evidence_id in ruling.evidence_ids
                ),
            )
        )
        primary_working_thesis = method_bound_working_thesis(primary)
        timing_coordinates = {item.layer: item for item in packet.timing_coordinates}
        mechanism_catalog = {item.evidence_id for item in packet.mechanism_observations}
        claims: list[MingliReadingClaim] = []

        def add(**values: object) -> MingliReadingClaim:
            evidence_ids = _unique(tuple(values.get("evidence_ids", ())))
            values["evidence_ids"] = evidence_ids
            values.setdefault(
                "mechanism_evidence_ids",
                tuple(item for item in evidence_ids if item in mechanism_catalog),
            )
            values.setdefault("coordinate_evidence_id", None)
            values.setdefault("relation_evidence_ids", ())
            if values.get("semantic_key") in server_issue_keys:
                values["assessment_codes"] = ("MODEL_FIELD_INVALID",)
            assessed = _assess_claim(
                values=values,
                packet=packet,
                primary_method_ref=primary.method_card_ref,
            )
            claim = MingliReadingClaim.issue(
                source_agent_reading_ref=reading.agent_reading_ref,
                **assessed,
            )
            claims.append(claim)
            return claim

        whole_chart = add(
            semantic_key="WHOLE_CHART",
            layer="PRINCIPLE",
            kind="WHOLE_CHART_THESIS",
            role="SYNTHESIS",
            status="PROVISIONAL",
            headline=_complete_heading(
                primary.name,
                fallback=output.first_look,
            ),
            statement=primary_working_thesis,
            causal_chain=(),
            condition=None,
            evidence_ids=primary_chart_evidence,
            mechanism_evidence_ids=_unique(primary.mechanism_evidence_ids),
            confidence="MEDIUM",
            codes=(),
            assessment_codes=(),
        )
        add(
            semantic_key="DAY_MASTER",
            layer="PRINCIPLE",
            kind="DAY_MASTER_STATE",
            role="PROJECTION",
            status="PROVISIONAL",
            headline=output.day_master_state,
            statement=output.day_master_rationale,
            causal_chain=(),
            condition=None,
            evidence_ids=_unique(output.day_master_evidence_ids),
            confidence="MEDIUM",
            codes=(output.day_master_state,),
            assessment_codes=(),
        )
        hypothesis_claims: dict[str, MingliReadingClaim] = {}
        for hypothesis in output.hypotheses:
            hypothesis_claims[hypothesis.hypothesis_id] = add(
                semantic_key=f"HYPOTHESIS_{hypothesis.hypothesis_id}",
                layer="PRINCIPLE",
                kind="COMPETING_HYPOTHESIS",
                role=hypothesis.role,
                status=("PROVISIONAL" if hypothesis.role == "PRIMARY" else "NEEDS_RECONCILIATION"),
                headline=_complete_heading(
                    hypothesis.name,
                    fallback=hypothesis.thesis,
                ),
                statement=(
                    primary_working_thesis
                    if hypothesis.role == "PRIMARY"
                    else hypothesis.thesis
                ),
                causal_chain=(),
                condition=hypothesis.failure_condition,
                evidence_ids=_unique(
                    (
                        *hypothesis.evidence_ids,
                        *hypothesis.mechanism_evidence_ids,
                        *(
                            evidence_id
                            for ruling in hypothesis.method_rulings
                            for evidence_id in ruling.evidence_ids
                        ),
                    )
                ),
                mechanism_evidence_ids=_unique(hypothesis.mechanism_evidence_ids),
                confidence=hypothesis.confidence,
                codes=(hypothesis.judgment, hypothesis.adjudication),
                assessment_codes=exact_role_path_assessment_codes(
                    hypothesis=hypothesis,
                    packet=packet,
                ),
            )
        work_path = add(
            semantic_key="WORK_PATH",
            layer="PRINCIPLE",
            kind="WORK_PATH",
            role="PRIMARY",
            status="PROVISIONAL",
            headline=output.work_path.closure,
            statement=output.work_path.path_statement,
            causal_chain=(),
            condition=output.work_path.condition,
            evidence_ids=_unique(output.work_path.evidence_ids),
            confidence="MEDIUM",
            codes=(
                *output.work_path.transformation_codes,
                f"CLOSURE_{output.work_path.closure}",
            ),
            assessment_codes=(),
        )
        life_image = add(
            semantic_key="LIFE_IMAGE",
            layer="IMAGE",
            kind="LIFE_IMAGE",
            role="PROJECTION",
            status="PROVISIONAL",
            headline=output.life_image.title,
            statement=output.life_image.explanation,
            causal_chain=(output.life_image.image,),
            condition=None,
            evidence_ids=_unique(output.life_image.evidence_ids),
            confidence="MEDIUM",
            codes=(),
            assessment_codes=(),
        )
        domain_claims: list[MingliReadingClaim] = []
        for domain, semantic_key, label in DOMAIN_KEYS:
            domain_reading = getattr(output.domains, domain)
            domain_claims.append(
                add(
                    semantic_key=semantic_key,
                    layer="THEMES",
                    kind="LIFE_DOMAIN",
                    role="PROJECTION",
                    status="NEEDS_RECONCILIATION",
                    headline=domain_reading.headline,
                    statement=domain_reading.conclusion,
                    causal_chain=domain_reading.causal_chain,
                    condition=domain_reading.condition,
                    evidence_ids=_unique(domain_reading.evidence_ids),
                    confidence=domain_reading.confidence,
                    codes=(domain.upper(), label),
                    assessment_codes=(),
                )
            )
        natal_timing = add(
            semantic_key="TIMING_NATAL",
            layer="TIMING",
            kind="TIMING_BASELINE",
            role="SYNTHESIS",
            status="PROVISIONAL",
            headline="原局基线",
            statement=primary_working_thesis,
            causal_chain=(),
            condition=None,
            evidence_ids=primary_chart_evidence,
            confidence="MEDIUM",
            codes=("NATAL",),
            assessment_codes=(),
        )
        dayun_timing = add(
            semantic_key="TIMING_DAYUN",
            layer="TIMING",
            kind="TIMING_LAYER",
            role="PROJECTION",
            status="PROVISIONAL",
            headline="当前大运",
            statement=method_bound_timing_statement(
                primary=primary,
                coordinate=timing_coordinates["DAYUN"],
                period_label="大运",
                period_scope="这十年",
            ),
            causal_chain=method_bound_timing_chain(
                primary=primary,
                coordinate=timing_coordinates["DAYUN"],
                period_label="大运",
            ),
            condition=primary_limit(primary),
            evidence_ids=_unique(
                (
                    *output.timing.dayun.evidence_ids,
                    output.timing.dayun.coordinate_evidence_id,
                    *output.timing.dayun.relation_evidence_ids,
                )
            ),
            coordinate_evidence_id=output.timing.dayun.coordinate_evidence_id,
            relation_evidence_ids=_unique(output.timing.dayun.relation_evidence_ids),
            confidence=output.timing.dayun.confidence,
            codes=("DAYUN",),
            assessment_codes=(),
        )
        annual_timing = add(
            semantic_key="TIMING_ANNUAL",
            layer="TIMING",
            kind="TIMING_LAYER",
            role="PROJECTION",
            status="PROVISIONAL",
            headline="所选流年",
            statement=method_bound_timing_statement(
                primary=primary,
                coordinate=timing_coordinates["ANNUAL"],
                period_label="流年",
                period_scope="这一年",
            ),
            causal_chain=method_bound_timing_chain(
                primary=primary,
                coordinate=timing_coordinates["ANNUAL"],
                period_label="流年",
            ),
            condition=primary_limit(primary),
            evidence_ids=_unique(
                (
                    *output.timing.annual.evidence_ids,
                    output.timing.annual.coordinate_evidence_id,
                    *output.timing.annual.relation_evidence_ids,
                )
            ),
            coordinate_evidence_id=output.timing.annual.coordinate_evidence_id,
            relation_evidence_ids=_unique(output.timing.annual.relation_evidence_ids),
            confidence=output.timing.annual.confidence,
            codes=("ANNUAL",),
            assessment_codes=(),
        )
        question = add(
            semantic_key="DISCRIMINATING_QUESTION",
            layer="QUESTION",
            kind="DISCRIMINATING_QUESTION",
            role="QUESTION",
            status="OPEN_QUESTION",
            headline="用来区分两种解释的问题",
            statement=output.hypothesis_decision.reversal.question,
            causal_chain=(
                output.hypothesis_decision.reversal.winner_signal,
                output.hypothesis_decision.reversal.loser_signal,
            ),
            condition=None,
            evidence_ids=(),
            confidence=None,
            codes=(),
            assessment_codes=(),
        )

        primary_claim = next(item for item in hypothesis_claims.values() if item.role == "PRIMARY")
        alternative_claim = next(
            item for item in hypothesis_claims.values() if item.role == "ALTERNATIVE"
        )
        unavailable_dependencies = tuple(
            item for item in (primary_claim, work_path) if item.status == "WITHHELD"
        )
        if unavailable_dependencies and whole_chart.status != "WITHHELD":
            whole_chart = _with_dependency_withheld(whole_chart)
            claims[0] = whole_chart
        edge_values = [
            ("COMPETES_WITH", primary_claim, alternative_claim),
            ("SUPPORTS", primary_claim, whole_chart),
            ("SUPPORTS", work_path, whole_chart),
            ("PROJECTS_TO", work_path, life_image),
            *(("PROJECTS_TO", work_path, item) for item in domain_claims),
            ("TEMPORALLY_EXTENDS", natal_timing, dayun_timing),
            ("TEMPORALLY_EXTENDS", natal_timing, annual_timing),
            ("DISCRIMINATES", question, primary_claim),
            ("DISCRIMINATES", question, alternative_claim),
        ]
        edges = tuple(
            MingliReadingClaimEdge.issue(
                relation=relation,
                source_claim_ref=source.claim_ref,
                target_claim_ref=target.claim_ref,
            )
            for relation, source, target in edge_values
            if source.status != "WITHHELD" and target.status != "WITHHELD"
        )
        return MingliReadingClaimGraph.issue(
            case_ref=reading.case_ref,
            chart_version_ref=reading.chart_version_ref,
            life_case_revision_ref=reading.life_case_revision_ref,
            reading_ref=reading.reading_ref,
            reading_hash=reading.reading_hash,
            agent_reading_ref=reading.agent_reading_ref,
            agent_reading_hash=reading.agent_reading_hash,
            packet_ref=reading.packet_ref,
            packet_hash=reading.packet_hash,
            agent_profile_ref=reading.agent_profile_ref,
            agent_profile_hash=reading.agent_profile_hash,
            model_ref=reading.model_ref,
            model_digest=reading.model_digest,
            reasoning_mode_contract_ref=BLIND_READING_CONTRACT.contract_ref,
            reasoning_mode_contract_hash=BLIND_READING_CONTRACT.contract_hash,
            claims=tuple(claims),
            edges=edges,
        )


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _complete_heading(value: str, *, fallback: str) -> str:
    """Project a complete short heading from immutable model prose."""

    for candidate in (value, fallback):
        first = re.split(r"[。！？；;\n]", candidate, maxsplit=1)[0].strip()
        first = re.split(r"[:：]", first, maxsplit=1)[0].strip()
        if len(first) >= 4:
            return first[:120]
    return fallback[:120]


_RELATION_EFFECT_TERMS = (
    "合动",
    "冲动",
    "引动",
    "激活",
    "化解",
    "解冲",
    "冲开",
    "冲去",
    "提升",
    "削弱",
    "增强",
    "破坏",
    "改变",
    "牵动",
    "触发",
    "兑现",
    "落地",
    "成局",
    "成化",
    "放大",
    "导致",
    "带来",
    "决定",
    "主导",
    "指向",
)
_RELATION_LABELS = ("六合", "六冲", "同支", "三合", "相合", "相冲")
_CONDITIONAL_TERMS = (
    "若",
    "如果",
    "只有",
    "取决于",
    "是否",
    "能否",
    "仍需",
    "尚需",
    "未足以",
    "不足以",
    "不代表",
    "不等于",
    "尚不能",
    "尚未",
    "未确定",
    "仅是",
    "候选",
    "可能",
)
_SOFT_ASSESSMENT_CODES = {
    "PRIMARY_HYPOTHESIS_CHART_BASIS_INCOMPLETE",
    "MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION",
    "CONFIDENCE_EXCEEDS_PACKET",
    "DEPENDENCY_WITHHELD",
    "TIMING_NATAL_BASIS_MISSING",
    "DOMAIN_PRIMARY_PATH_MISSING",
}


def _assess_claim(
    *,
    values: dict[str, object],
    packet: MingliAgentCasePacket,
    primary_method_ref: str,
) -> dict[str, object]:
    """Admit the whole reading while quarantining only an unsafe claim."""

    assessed: dict[str, object] = dict(values)
    prose = _claim_prose(assessed)
    assertion_prose = _claim_assertion_prose(assessed)
    evidence_ids = set(assessed.get("evidence_ids", ()))
    mechanism_evidence_ids = set(assessed.get("mechanism_evidence_ids", ()))
    coordinate_evidence_id = assessed.get("coordinate_evidence_id")
    relation_evidence_ids = set(assessed.get("relation_evidence_ids", ()))
    layer = str(assessed["layer"])
    kind = str(assessed["kind"])
    role = str(assessed["role"])
    codes: list[str] = list(assessed.get("assessment_codes", ()))

    if kind != "DISCRIMINATING_QUESTION" and not evidence_ids:
        codes.append("CLAIM_EVIDENCE_MISSING")

    mechanism_ids = {item.evidence_id for item in packet.mechanism_observations}
    if kind == "COMPETING_HYPOTHESIS" and role == "PRIMARY" and not (evidence_ids - mechanism_ids):
        codes.append("PRIMARY_HYPOTHESIS_CHART_BASIS_INCOMPLETE")
    if mechanism_evidence_ids and assessed.get("confidence") == "HIGH":
        codes.append("CONFIDENCE_EXCEEDS_PACKET")
        assessed["confidence"] = "MEDIUM"

    timing_ids = {
        *(item.evidence_id for item in packet.timing_coordinates),
        *(item.evidence_id for item in packet.timing_relations),
    }
    natal_ids = {
        item.evidence_id for item in packet.evidence_catalog if item.evidence_id not in timing_ids
    }
    natal_interpretation = layer in {"PRINCIPLE", "IMAGE", "THEMES"} or kind == "TIMING_BASELINE"
    if natal_interpretation and evidence_ids & timing_ids:
        codes.append("NATAL_CLAIM_CITES_TIMING_EVIDENCE")
    if natal_interpretation and _uses_selected_timing(
        prose=assertion_prose,
        packet=packet,
    ):
        codes.append("NATAL_CLAIM_USES_SELECTED_TIMING")

    relation_ids = {
        *(item.evidence_id for item in packet.natal_relations),
        *(item.evidence_id for item in packet.timing_relations),
    }
    cites_relation = bool(evidence_ids & relation_ids)
    names_relation = any(term in assertion_prose for term in _RELATION_LABELS)
    if kind == "TIMING_LAYER" and coordinate_evidence_id not in evidence_ids:
        codes.append("TIMING_COORDINATE_EVIDENCE_MISSING")
    if kind == "TIMING_LAYER" and not evidence_ids & natal_ids:
        codes.append("TIMING_NATAL_BASIS_MISSING")
    if kind == "TIMING_LAYER" and names_relation and not relation_evidence_ids:
        codes.append("TIMING_RELATION_EVIDENCE_MISSING")
    if kind == "TIMING_LAYER" and _uses_other_timing_layer(
        prose=assertion_prose,
        semantic_key=str(assessed["semantic_key"]),
        packet=packet,
    ):
        codes.append("TIMING_LAYER_PROSE_CONFLICT")
    if _has_unconditioned_relation_effect(
        values=assessed,
        cites_relation=cites_relation,
    ):
        codes.append("RELATION_MEMBERSHIP_PROMOTED_TO_EFFECT")
    claim_codes = set(assessed.get("codes", ()))
    if kind == "WORK_PATH" and "CLOSURE_CLOSED" in claim_codes:
        codes.append("WORK_PATH_CLOSURE_EXCEEDS_PACKET")
    if any(
        term in prose
        for term in (
            "手术",
            "外伤",
            "重病",
            "车祸",
            "自杀",
            "抑郁症",
            "第三者",
            "第三人",
            "外遇",
            "婚外",
            "外情",
            "背叛",
            "离婚",
            "分手",
            "感情破裂",
            "疾病",
            "灾祸",
            "必然破财",
        )
    ):
        codes.append("HIGH_RISK_EVENT_ASSERTION")
    if not packet.day_master_support.same_element_hidden_support and _uses_positive_root_claim(
        prose
    ):
        codes.append("ROOT_ASSERTION_CONFLICTS_WITH_PACKET")
    if _has_named_coordinate_conflict(prose=prose, packet=packet):
        codes.append("NAMED_COORDINATE_CONFLICTS_WITH_PACKET")
    additional_visible = _timing_visible_context(
        semantic_key=str(assessed["semantic_key"]),
        packet=packet,
    )
    if manifestation_claim_conflicts(
        prose,
        pillars=packet.pillars,
        additional_visible=additional_visible,
    ):
        codes.append("TEN_GOD_MANIFESTATION_CONFLICTS_WITH_PACKET")
    if _has_peer_count_conflict(prose=prose, packet=packet):
        codes.append("PEER_COUNT_CONFLICTS_WITH_PACKET")
    if "流月" in prose:
        codes.append("UNSELECTED_TIMING_LAYER_ASSERTION")
    if _has_unlisted_relation_assertion(prose=prose, packet=packet):
        codes.append("UNLISTED_RELATION_COORDINATE_ASSERTION")
    if any(term in prose for term in ("财库", "官库", "印库", "食伤库")):
        codes.append("UNADMITTED_CLASSICAL_ASSERTION")
    if any(
        term in prose for term in ("Case", "Hash", "canonical", "尚未接线", "证据缺口", "候选准入")
    ):
        codes.append("NON_READING_LANGUAGE")
    if any(
        term in prose for term in ("有机会也有挑战", "保持平衡", "值得继续观察", "当前证据适合观察")
    ):
        codes.append("LOW_INFORMATION_LANGUAGE")
    if kind == "LIFE_DOMAIN" and any(
        term in prose
        for term in (
            "人脉",
            "朋友资源",
            "团队支持",
            "社交资源",
            "贵人",
            "人际合作",
            "合作伙伴支持",
            "同伴支持",
        )
    ):
        codes.append("UNSUPPORTED_SOCIAL_RESOURCE_INFERENCE")
    if (
        kind == "LIFE_DOMAIN"
        and primary_method_ref != FALLBACK_METHOD_CARD_REF
        and primary_method_ref not in mechanism_evidence_ids
    ):
        codes.append("DOMAIN_PRIMARY_PATH_MISSING")
    if kind == "LIFE_DOMAIN":
        codes.extend(
            domain_method_assessment_codes(
                semantic_key=str(assessed["semantic_key"]),
                prose=assertion_prose,
            )
        )

    assessed["assessment_codes"] = tuple(dict.fromkeys(codes))
    hard_quarantine_codes = set(codes) - _SOFT_ASSESSMENT_CODES
    if hard_quarantine_codes:
        assessed["status"] = "WITHHELD"
    elif codes:
        assessed["status"] = "NEEDS_RECONCILIATION"
    return assessed


def _with_dependency_withheld(
    claim: MingliReadingClaim,
) -> MingliReadingClaim:
    values = claim.model_dump(mode="python", exclude={"claim_ref"})
    values["status"] = "NEEDS_RECONCILIATION"
    values["assessment_codes"] = tuple(
        dict.fromkeys((*claim.assessment_codes, "DEPENDENCY_WITHHELD"))
    )
    return MingliReadingClaim.issue(**values)


def _claim_prose(values: dict[str, object]) -> str:
    parts: list[str] = []
    for key in ("headline", "statement", "condition"):
        value = values.get(key)
        if isinstance(value, str):
            parts.append(value)
    causal_chain = values.get("causal_chain")
    if isinstance(causal_chain, (tuple, list)):
        parts.extend(str(item) for item in causal_chain)
    return "\n".join(parts)


def _claim_assertion_prose(values: dict[str, object]) -> str:
    """Return asserted copy only; a separate condition cannot launder it."""

    parts: list[str] = []
    for key in ("headline", "statement"):
        value = values.get(key)
        if isinstance(value, str):
            parts.append(value)
    causal_chain = values.get("causal_chain")
    if isinstance(causal_chain, (tuple, list)):
        parts.extend(str(item) for item in causal_chain)
    return "\n".join(parts)


def _has_unconditioned_relation_effect(
    *,
    values: dict[str, object],
    cites_relation: bool,
) -> bool:
    assertion_fields: list[str] = []
    for key in ("headline", "statement"):
        value = values.get(key)
        if isinstance(value, str):
            assertion_fields.append(value)
    causal_chain = values.get("causal_chain")
    if isinstance(causal_chain, (tuple, list)):
        assertion_fields.extend(str(item) for item in causal_chain)

    for field in assertion_fields:
        for sentence in re.split(r"[。！？；;\n]", field):
            if not sentence.strip():
                continue
            names_relation = any(term in sentence for term in _RELATION_LABELS)
            conditional_scope = False
            for clause in re.split(r"[，,]", sentence):
                stripped = clause.strip()
                if not stripped:
                    continue
                if re.match(r"^(?:但|然而|可是|不过)", stripped):
                    conditional_scope = False
                if any(term in stripped for term in _CONDITIONAL_TERMS):
                    conditional_scope = True
                uses_specific_effect = _uses_specific_relation_effect(stripped)
                uses_effect = any(term in stripped for term in _RELATION_EFFECT_TERMS)
                if (
                    uses_specific_effect or ((cites_relation or names_relation) and uses_effect)
                ) and not conditional_scope:
                    return True
    return False


def _uses_specific_relation_effect(prose: str) -> bool:
    """Do not read ordinary `化解冲突` as the technical relation verb `解冲`."""

    return bool(re.search(r"(?:合动|(?<!化)解冲|冲开|冲去|成化)", prose))


def _timing_visible_context(
    *,
    semantic_key: str,
    packet: MingliAgentCasePacket,
) -> tuple[tuple[str, str], ...]:
    layer = {
        "TIMING_DAYUN": "DAYUN",
        "TIMING_ANNUAL": "ANNUAL",
    }.get(semantic_key)
    if layer is None:
        return ()
    coordinate = next(item for item in packet.timing_coordinates if item.layer == layer)
    return ((coordinate.pillar[0], coordinate.ten_god_label),)


def _uses_selected_timing(*, prose: str, packet: MingliAgentCasePacket) -> bool:
    if any(item.pillar in prose for item in packet.timing_coordinates):
        return True
    return bool(
        re.search(
            r"(?:当前)?(?:大运|流年|岁运)[^。；\n]{0,24}"
            r"(?:决定|改变|形成|构成|重写|反写|使)[^。；\n]{0,16}"
            r"(?:原局|命局|日主|旺衰|格局|基线)",
            prose,
        )
    )


def _uses_other_timing_layer(
    *,
    prose: str,
    semantic_key: str,
    packet: MingliAgentCasePacket,
) -> bool:
    coordinates = {item.layer: item.pillar for item in packet.timing_coordinates}
    if semantic_key == "TIMING_ANNUAL":
        return "大运" in prose or coordinates["DAYUN"] in prose
    if semantic_key == "TIMING_DAYUN":
        return "流年" in prose or coordinates["ANNUAL"] in prose
    return False


def _uses_positive_root_claim(prose: str) -> bool:
    without_negated = re.sub(
        r"(?:无|未|没有|并无|并非|不是|不算|不能视为|不可视为|缺乏|不足)"
        r"[^，。；;\n]{0,16}(?:得根|有根|根气|根位|根基)",
        "",
        prose,
    )
    return bool(
        re.search(
            r"(?:得根|有根|微根|坐根|通根|根气(?:受制|薄弱|微弱|尚存|存在)|"
            r"根位(?:受制|薄弱|尚存|存在)|根基(?:受制|薄弱|尚存|存在)|"
            r"(?:仍有|尚有|有|存在)[^，。；;\n]{0,6}(?:根气|根位|根基))",
            without_negated,
        )
    )


def _has_named_coordinate_conflict(*, prose: str, packet: MingliAgentCasePacket) -> bool:
    hidden_by_branch = {item.branch: set(item.hidden_stems) for item in packet.pillars}
    pattern = re.compile(
        r"([子丑寅卯辰巳午未申酉戌亥])(?:[、，,\s]{0,2}藏|中)([甲乙丙丁戊己庚辛壬癸])"
    )
    if any(
        stem not in hidden_by_branch.get(branch, set()) for branch, stem in pattern.findall(prose)
    ):
        return True
    scoped_hidden = re.compile(
        r"([子丑寅卯辰巳午未申酉戌亥])(?:木|火|土|金|水)?[^。；，,\n]{0,12}"
        r"(?:[，,]\s*)?(?:藏干中|内藏|中藏)([^。；，,\n]{0,48})"
    )
    for branch, body in scoped_hidden.findall(prose):
        stems = re.findall(r"[（(]([甲乙丙丁戊己庚辛壬癸])[）)]", body)
        if any(stem not in hidden_by_branch.get(branch, set()) for stem in stems):
            return True
    return False


def _has_unlisted_relation_assertion(*, prose: str, packet: MingliAgentCasePacket) -> bool:
    if any(
        term in prose for term in ("半合", "三会", "相刑", "自刑", "相害", "相破", "合化", "争合")
    ):
        return True
    has_three_harmony_candidate = bool(
        packet.model_prompt_view()["professional_adjudication"]["professional_structure_candidates"]
    )
    if "三合" in prose and not has_three_harmony_candidate:
        return True
    allowed_pairs = {
        frozenset((item.left_branch, item.right_branch))
        for item in (*packet.natal_relations, *packet.timing_relations)
    }
    pattern = re.compile(
        r"([子丑寅卯辰巳午未申酉戌亥])[^。；\n]{0,12}与[^。；\n]{0,12}"
        r"([子丑寅卯辰巳午未申酉戌亥])[^。；\n]{0,8}"
        r"(?:相连|相合|六合|相冲|六冲|地支关系)"
    )
    return any(
        frozenset((left, right)) not in allowed_pairs for left, right in pattern.findall(prose)
    )


_CHINESE_COUNT = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


def _has_peer_count_conflict(
    *,
    prose: str,
    packet: MingliAgentCasePacket,
) -> bool:
    expected = len(packet.day_master_support.visible_peer_support)
    pattern = re.compile(
        r"(?:天干|明干)?(?P<count>[零一二两三四五六七八九\d])"
        r"(?:个|位|处|重|透|见|株)?(?:明干|天干)?(?:比肩|比劫|同类)"
    )
    for match in pattern.finditer(prose):
        raw_count = match.group("count")
        actual = int(raw_count) if raw_count.isdigit() else _CHINESE_COUNT[raw_count]
        if actual != expected:
            return True
    return False
