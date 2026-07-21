from __future__ import annotations

import json
import re

from core.mingli_agent.context import MingliContextCompiler, ReasoningContextPack
from core.mingli_agent.contracts import (
    ChartWorldInstance,
    DualLensCognitionDraft,
    HypothesisComparisonReceipt,
    PatternHypothesisDraft,
    PatternPreviewDraft,
    PredictionProbeDraft,
    WholeChartCognitionDraft,
    WorkPathPortraitDraft,
)
from core.mingli_agent.fact_review import (
    assertive_claim_text,
    deterministic_fact_conflicts,
    is_parallel_predicate_fragment,
)
from core.mingli_agent.reasoning_facts import _reasoning_world_payload
from core.mingli_agent.reasoning_utils import _hypothesis_signature, _unique


def _citation_allowed(*, ref: str, allowed: set[str]) -> bool:
    if ref in allowed:
        return True
    match = re.fullmatch(r"([FOK])(\d{3})\s*[-–—]\s*\1?(\d{3})", ref)
    if not match:
        return False
    prefix, start_text, end_text = match.groups()
    start, end = int(start_text), int(end_text)
    if end < start or end - start > 120:
        return False
    return f"{prefix}{start:03d}" in allowed and f"{prefix}{end:03d}" in allowed

def _pattern_stage_errors(
    *,
    pattern: PatternHypothesisDraft,
    world: ChartWorldInstance,
    context: ReasoningContextPack | None = None,
) -> list[str]:
    return _unique([
        *_pattern_hard_errors(pattern=pattern, world=world, context=context),
        *_pattern_soft_issues(pattern=pattern, world=world, context=context),
    ])

def _pattern_preview_errors(
    *,
    preview: PatternPreviewDraft,
    world: ChartWorldInstance,
    context: ReasoningContextPack,
) -> list[str]:
    errors = _semantic_text_errors(text=preview.preview_line, world=world)
    if not preview.preview_line.strip():
        errors.append("第一眼预览为空")
    if not preview.focus_refs:
        errors.append("第一眼预览缺少事实引用")
    allowed = set(context.fact_refs)
    missing = [ref for ref in preview.focus_refs if ref not in allowed]
    if missing:
        errors.append(f"第一眼预览引用不存在:{','.join(missing)}")
    return _unique(errors)

def _pattern_hard_errors(
    *,
    pattern: PatternHypothesisDraft,
    world: ChartWorldInstance,
    context: ReasoningContextPack | None = None,
) -> list[str]:
    errors: list[str] = []
    selected = next((item for item in pattern.hypotheses if item.hypothesis_id == pattern.selected_hypothesis_id), None)
    if selected is None:
        errors.append("selected_hypothesis_id 不存在")
    elif "从" in selected.name and ("制杀" in selected.name or "食伤" in selected.name):
        errors.append("从格与主动食伤做功不能混入同一主假设")
    text = json.dumps(pattern.model_dump(mode="json"), ensure_ascii=False)
    errors.extend(_semantic_text_errors(text=text, world=world, include_deterministic=False))
    errors.extend(deterministic_fact_conflicts(text=assertive_claim_text(pattern.model_dump(mode="json")), world=world))
    comparison = _review_hypothesis_space(
        pattern=pattern,
        context=context or MingliContextCompiler().compile(world=world, stage="pattern"),
    )
    hard_prefixes = (
        "竞争假设 id 重复",
        "竞争假设 rank 重复",
        "竞争假设必须且只能有一个 primary",
        "selected_hypothesis_id 必须指向唯一 primary",
    )
    errors.extend(issue for issue in comparison.issues if issue.startswith(hard_prefixes))
    return _unique(errors)

def _pattern_soft_issues(
    *,
    pattern: PatternHypothesisDraft,
    world: ChartWorldInstance,
    context: ReasoningContextPack | None = None,
) -> list[str]:
    issues: list[str] = []
    if not 2 <= len(pattern.hypotheses) <= 3:
        issues.append("竞争假设必须为2到3个")
    if len(pattern.salient_phenomena) > 3:
        issues.append("盘面重心最多3个")
    for hypothesis in pattern.hypotheses:
        if not hypothesis.failure_conditions:
            issues.append(f"假设缺少失败条件:{hypothesis.hypothesis_id}")
        if hypothesis.status == "alternative" and not hypothesis.rejection_reason:
            issues.append(f"替代假设缺少放弃理由:{hypothesis.hypothesis_id}")
    comparison = _review_hypothesis_space(
        pattern=pattern,
        context=context or MingliContextCompiler().compile(world=world, stage="pattern"),
    )
    hard_prefixes = (
        "竞争假设 id 重复",
        "竞争假设 rank 重复",
        "竞争假设必须且只能有一个 primary",
        "selected_hypothesis_id 必须指向唯一 primary",
    )
    issues.extend(issue for issue in comparison.issues if not issue.startswith(hard_prefixes))
    return _unique(issues)

def _review_hypothesis_space(
    *,
    pattern: PatternHypothesisDraft,
    context: ReasoningContextPack,
) -> HypothesisComparisonReceipt:
    issues: list[str] = []
    ids = [item.hypothesis_id for item in pattern.hypotheses]
    ranks = [item.rank for item in pattern.hypotheses]
    primary_ids = [item.hypothesis_id for item in pattern.hypotheses if item.status == "primary"]
    alternative_ids = [item.hypothesis_id for item in pattern.hypotheses if item.status in {"alternative", "unresolved"}]
    signatures = [_hypothesis_signature(item) for item in pattern.hypotheses]
    if len(ids) != len(set(ids)):
        issues.append("竞争假设 id 重复")
    if len(ranks) != len(set(ranks)):
        issues.append("竞争假设 rank 重复")
    if len(primary_ids) != 1:
        issues.append("竞争假设必须且只能有一个 primary")
    if primary_ids and pattern.selected_hypothesis_id != primary_ids[0]:
        issues.append("selected_hypothesis_id 必须指向唯一 primary")
    if len(signatures) != len(set(signatures)):
        issues.append("竞争假设因果签名重复")
    for hypothesis in pattern.hypotheses:
        if not hypothesis.supporting_evidence_refs:
            issues.append(f"假设缺少支持证据:{hypothesis.hypothesis_id}")

    salient_refs = _unique([
        ref
        for phenomenon in pattern.salient_phenomena
        for ref in phenomenon.evidence_refs
    ])
    explained_refs = set(
        ref
        for hypothesis in pattern.hypotheses
        for ref in [*hypothesis.supporting_evidence_refs, *hypothesis.counter_evidence_refs]
    )
    uncovered = [ref for ref in salient_refs if ref not in explained_refs]
    if uncovered:
        issues.append(f"盘面重心证据未进入假设比较:{','.join(uncovered)}")

    high_attention_refs = {
        item.fact_ref
        for item in context.attention_receipt.items
        if item.selected and item.priority in {"critical", "high"}
    }
    cited_refs = {
        *pattern.evidence_refs,
        *salient_refs,
        *explained_refs,
    }
    attention_used = sorted(high_attention_refs & cited_refs)
    if high_attention_refs and not attention_used:
        issues.append("假设空间未引用任何 critical/high 注意力事实")

    coverage = 1.0 if not salient_refs else round((len(salient_refs) - len(uncovered)) / len(salient_refs), 4)
    return HypothesisComparisonReceipt(
        passed=not issues,
        selected_hypothesis_id=pattern.selected_hypothesis_id,
        primary_hypothesis_ids=primary_ids,
        alternative_hypothesis_ids=alternative_ids,
        distinct_signature_count=len(set(signatures)),
        salient_evidence_coverage_rate=coverage,
        uncovered_salient_refs=uncovered,
        attention_evidence_used=attention_used,
        issues=_unique(issues),
    )

def _work_stage_errors(*, work: WorkPathPortraitDraft, world: ChartWorldInstance) -> list[str]:
    payload = work.model_dump(mode="json")
    errors = _semantic_text_errors(text=json.dumps(payload, ensure_ascii=False), world=world, include_deterministic=False)
    errors.extend(deterministic_fact_conflicts(text=assertive_claim_text(payload), world=world))
    return _unique(errors)

def _prediction_stage_errors(*, predictions: PredictionProbeDraft, world: ChartWorldInstance) -> list[str]:
    errors: list[str] = []
    if not predictions.prior_predictions:
        errors.append("本轮没有保留可安全展示的先验判断")
    text = json.dumps(predictions.model_dump(mode="json"), ensure_ascii=False)
    errors.extend(_semantic_text_errors(text=text, world=world, include_deterministic=False))
    errors.extend(deterministic_fact_conflicts(text=assertive_claim_text(predictions.model_dump(mode="json")), world=world))
    if len(predictions.next_probe.distinguishes_hypothesis_refs) < 2:
        errors.append("Probe 尚未区分两个假设")
    return _unique(errors)

def _dual_lens_errors(*, dual_lens: DualLensCognitionDraft, world: ChartWorldInstance) -> list[str]:
    errors: list[str] = []
    if not 2 <= len(dual_lens.palace_observations) <= 4:
        errors.append("紫微第一眼必须保留2到4个关键宫位观察")
    covered_domains = {item.domain for item in dual_lens.palace_observations}
    if len(covered_domains & {"identity", "career", "wealth"}) < 2:
        errors.append("紫微观察至少覆盖身份、事业、财富中的两个领域")
    if not dual_lens.agreements:
        errors.append("双镜头必须列出至少一个一致处")
    probe = dual_lens.cross_lens_probe
    if len(probe.distinguishes_hypothesis_refs) < 2:
        errors.append("双镜头 Probe 必须区分至少两个解释")
    if len(probe.options) < 2:
        errors.append("双镜头 Probe 至少需要两个可区分选项")
    probe_text = f"{probe.question} {probe.purpose}"
    if any(token in probe_text for token in ("星曜", "宫位", "命宫", "四化", "大限")):
        errors.append("双镜头 Probe 必须询问现实行为，不能要求用户理解紫微术语")
    dual_payload = dual_lens.model_dump(mode="json")
    text = json.dumps(dual_payload, ensure_ascii=False)
    for phrase in ("必然", "一定会", "注定"):
        for match in re.finditer(phrase, text):
            prefix = text[max(0, match.start() - 10):match.start()]
            if any(token in prefix for token in ("不", "非", "不能", "并不", "不代表", "避免", "不得")):
                continue
            errors.append("紫微时序不得写成确定事件")
            break
    allowed = set(world.allowed_evidence_refs)
    ziwei_allowed = {
        ref
        for fact in world.facts
        if fact.category.startswith("ziwei_")
        for ref in [fact.fact_id, *fact.source_refs]
    }
    cited = {
        ref
        for item in dual_lens.palace_observations
        for ref in item.evidence_refs
    }
    cited.update(dual_lens.evidence_refs)
    if not any(ref in ziwei_allowed and _citation_allowed(ref=ref, allowed=allowed) for ref in cited):
        errors.append("紫微观察缺少可追溯的紫微事实引用")
    errors.extend(deterministic_fact_conflicts(text=assertive_claim_text(dual_payload), world=world))
    return _unique(errors)

def _whole_stage_errors(*, whole: WholeChartCognitionDraft, world: ChartWorldInstance) -> list[str]:
    errors: list[str] = []
    structural_payload = whole.model_dump(mode="json")
    predictions_payload = {
        "prior_predictions": structural_payload.pop("prior_predictions", []),
        "next_probe": structural_payload.pop("next_probe", {}),
    }
    structural_text = json.dumps(structural_payload, ensure_ascii=False)
    prediction_text = json.dumps(predictions_payload, ensure_ascii=False)
    if len(whole.hypotheses) < 2:
        errors.append("结构:至少比较两个命局假设")
    if whole.selected_hypothesis_id not in {item.hypothesis_id for item in whole.hypotheses}:
        errors.append("结构:selected_hypothesis_id 不存在")
    if not whole.prior_predictions:
        errors.append("先验:本轮没有保留可安全展示的先验判断")
    selected = next((item for item in whole.hypotheses if item.hypothesis_id == whole.selected_hypothesis_id), None)
    if selected and "从" in selected.name and ("制杀" in selected.name or "食伤" in selected.name):
        errors.append("结构:主假设混合互斥解释:从格与主动食伤做功必须分开比较")
    probe_text = f"{whole.next_probe.question} {whole.next_probe.purpose}"
    if re.search(r"20\d{2}", probe_text) or any(token in probe_text for token in ("年份", "大运", "计划受阻", "决策失误", "健康", "外部因素")):
        errors.append("Probe 失焦:必须用可观察行为区分假设而非追问灾难或年份")
    errors.extend(f"结构:{item}" for item in _semantic_text_errors(text=structural_text, world=world, include_deterministic=False))
    errors.extend(f"先验:{item}" for item in _semantic_text_errors(text=prediction_text, world=world, include_deterministic=False))
    errors.extend(f"事实:{item}" for item in deterministic_fact_conflicts(text=assertive_claim_text(whole.model_dump(mode="json")), world=world))
    return _unique(errors)

def _semantic_text_errors(*, text: str, world: ChartWorldInstance, include_deterministic: bool = True) -> list[str]:
    errors: list[str] = list(deterministic_fact_conflicts(text=text, world=world)) if include_deterministic else []
    invalid_relations = (
        "木生土", "木生金", "木生水",
        "火生金", "火生水", "火生木",
        "土生木", "土生水", "土生火",
        "金生木", "金生火", "金生土",
        "水生土", "水生火", "水生金",
        "木克金", "木克水", "木克火",
        "火克木", "火克水", "火克土",
        "土克木", "土克火", "土克金",
        "金克火", "金克土", "金克水",
        "水克木", "水克金", "水克土",
    )
    for invalid in invalid_relations:
        if _contains_asserted_relation(text=text, relation=invalid):
            errors.append(f"错误五行关系:{invalid}")
    if "火化土" in text:
        errors.append("错误五行表述:火与土必须写生而不是化")
    if re.search(r"(?:食神|食伤)制杀\s*[/／]\s*化印", text):
        errors.append("机制拼接冲突:制杀与化印不能用斜线合并为同一做功")
    if re.search(r"(?:食神|食伤)生财(?:而|并|再)?化杀", text):
        errors.append("因果链压缩:食伤生财与财生杀必须逐段表达")
    for match in re.finditer(r"(?:丁火|丙火|火气|火)[^。；]{0,36}(?:(?:转化为|变成)\s*(?:酉金|金局|金气|金)|导向[^。；]{0,12}(?:酉金|金局|金气|金))", text):
        segment = match.group(0)
        if not any(token in segment for token in ("制", "克", "约束", "作用于")):
            errors.append(f"五行转化偷换:{segment[:48]}")
    for pattern in (
        r"(?:丁火|丙火)[^。；]{0,48}(?:引动|生出|化成)[^。；]{0,12}(?:酉金|金局|金气)",
        r"(?:丁火|丙火)[^。；]{0,10}(?:转化为|变成)\s*(?:食伤|食神|伤官)",
        r"(?:火气|火势|火)\s*(?:欲去生|生)\s*(?:水/金|水|金)",
    ):
        for match in re.finditer(pattern, text):
            segment = match.group(0)
            prefix = text[max(0, match.start() - 10):match.start()]
            if any(token in prefix for token in ("不", "不能", "并非", "不得", "避免", "误写")):
                continue
            if is_parallel_predicate_fragment(text=text, start=match.start(), end=match.end()):
                continue
            errors.append(f"五行转化偷换:{segment[:48]}")

    forbidden_events = (
        "失业", "疾病", "肝胆", "筋骨疼痛", "健康受损", "健康危机",
        "必然破财", "资金链断裂", "重大挫折", "重大变故", "招灾", "死亡",
    )
    for forbidden in forbidden_events:
        if forbidden in text:
            errors.append(f"越界先验:{forbidden}")
    overconfident_phrases = ("必然", "绝对阈值", "吉凶判定", "瞬间转为凶险", "立即崩塌", "结构性崩塌", "彻底改变")
    for phrase in overconfident_phrases:
        for match in re.finditer(phrase, text):
            prefix = text[max(0, match.start() - 12):match.start()]
            if any(token in prefix for token in ("不", "非", "不能", "并不", "不代表", "避免", "不得", "不等于")):
                continue
            excerpt = text[max(0, match.start() - 36):match.end() + 36]
            errors.append(f"过度确定断言:{phrase}:{excerpt}")
            break

    internal_match = re.search(r"V(?:20|30|40|50|60)|admin_profile|fixture|runtime|schema", text, flags=re.IGNORECASE)
    if internal_match:
        errors.append(f"内部工程信息泄漏:{internal_match.group(0)}")

    if re.search(r"20\d{2}\s*(?:-|—|–|至|到)\s*20\d{2}", text):
        errors.append("Timing 越权:擅自扩写连续年份区间")
    if re.search(r"(?:水|壬|癸|亥|子)[^。；]{0,28}伤官见官|伤官见官[^。；]{0,28}(?:水|壬|癸|亥|子)", text):
        errors.append("十神因果冲突:水不能被机械写成伤官见官")

    ledger = _reasoning_world_payload(world)["immutable_chart_ledger"]
    day_master = str((ledger.get("day_master") or {}).get("stem") or "")
    if day_master and f"{day_master}（比劫）" in text:
        errors.append(f"十神精度不足:{day_master}必须按账本写具体比肩/劫财")

    visible = (ledger.get("visible") or {}).get("visible_ten_gods", [])
    labels = {
        "bi_jian": "比肩", "jie_cai": "劫财", "shi_shen": "食神", "shang_guan": "伤官",
        "pian_cai": "偏财", "zheng_cai": "正财", "qi_sha": "七杀", "zheng_guan": "正官",
        "pian_yin": "偏印", "zheng_yin": "正印",
    }
    all_labels = set(labels.values())
    visible_bi_jian_count = sum(str(row.get("ten_god") or "") == "bi_jian" for row in visible)
    chinese_counts = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4}
    for chinese, count in chinese_counts.items():
        if re.search(rf"(?:透出|可见|天干[^。；]{{0,8}}|全局[^。；]{{0,8}}){chinese}(?:见|个)?比肩", text) and count != visible_bi_jian_count:
            errors.append(f"比肩数量冲突:账本可见比肩为{visible_bi_jian_count}不是{count}")

    month_branch = world.pillars[1][1] if len(world.pillars) > 1 and len(world.pillars[1]) >= 2 else ""
    for match in re.finditer(r"([子丑寅卯辰巳午未申酉戌亥])(?:木|火|土|金|水)?[^。；，]{0,8}当令", text):
        branch = match.group(1)
        if month_branch and branch != month_branch:
            errors.append(f"月令位置冲突:{branch}不在月支，不能写作当令")
    for row in visible:
        stem = str(row.get("stem") or "")
        correct = labels.get(str(row.get("ten_god") or ""), "")
        for wrong in all_labels - {correct}:
            if stem and (f"{stem}火{wrong}" in text or f"{stem}{wrong}" in text):
                errors.append(f"十神账本冲突:{stem}应为{correct}不是{wrong}")
                break

    role_ledger = _reasoning_world_payload(world)["element_role_ledger"]
    cn = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
    for element, role in role_ledger.items():
        symbol = cn.get(element, "")
        if not symbol:
            continue
        role_name = role.split("/")[0]
        for wrong in {"财星", "官杀", "印星", "食伤", "比劫"} - {role_name}:
            if (
                f"{symbol}为{wrong}" in text
                or f"{symbol}是{wrong}" in text
                or re.search(rf"{re.escape(symbol)}(?:属性|气|局|势|的)?{re.escape(wrong)}", text)
                or f"{wrong}（{symbol}）" in text
                or f"{wrong}({symbol})" in text
                or _contains_role_conflict(text=text, symbol=symbol, wrong=wrong)
            ):
                errors.append(f"元素十神冲突:{symbol}应属{role}不是{wrong}")
        if role_name != "官杀" and re.search(rf"{re.escape(symbol)}[^。；]{{0,8}}(?:直克|克制|压制|攻克)(?:日主|命主)", text):
            errors.append(f"五行作用方向冲突:{symbol}不是克制日主的官杀元素")
    return _unique(errors)

def _contains_asserted_relation(*, text: str, relation: str) -> bool:
    for match in re.finditer(re.escape(relation), text):
        prefix = text[max(0, match.start() - 10):match.start()]
        if any(token in prefix for token in ("不是", "并非", "非", "不能", "禁止", "不得", "避免", "误写为")):
            continue
        if is_parallel_predicate_fragment(text=text, start=match.start(), end=match.end()):
            continue
        return True
    return False

def _contains_role_conflict(*, text: str, symbol: str, wrong: str) -> bool:
    patterns = (
        rf"{re.escape(symbol)}[^。；]{{0,10}}(?:为|是|作为|属于|或){re.escape(wrong)}",
        rf"{re.escape(wrong)}[^。；]{{0,8}}(?:为|是|作为|属于){re.escape(symbol)}",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            segment = match.group(0)
            if any(token in segment for token in ("不是", "并非", "非财", "非官", "非印", "非食", "非比")):
                continue
            return True
    return False
