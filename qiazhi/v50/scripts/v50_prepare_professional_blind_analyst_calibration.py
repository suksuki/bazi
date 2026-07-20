from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "professional-blind-test" / "analyst-calibration-v1"


@dataclass(frozen=True)
class CalibrationCase:
    review_code: str
    profile_id: str
    selection_family: str
    expected_pillars: tuple[str, str, str, str]


CALIBRATION_CASES = (
    CalibrationCase(
        "AC-01",
        "v50-v40-profile-26fdb0cfa3d9bded843d",
        "结构相对清晰：三合局与输出/制化路径",
        ("丁巳", "乙巳", "乙丑", "乙酉"),
    ),
    CalibrationCase(
        "AC-02",
        "v50-v40-profile-461c9565c09112e4beed",
        "结构相对清晰：同柱复现与强金环境",
        ("癸未", "庚申", "庚申", "丙戌"),
    ),
    CalibrationCase(
        "AC-03",
        "v50-v40-profile-f755a8f581e7d94f589f",
        "偏极命盘：火势集中与寒暖燥湿",
        ("丁亥", "乙巳", "丙午", "甲午"),
    ),
    CalibrationCase(
        "AC-04",
        "v50-v40-profile-da38c06e5629325b5d59",
        "多路径命盘：土势、财星与制化并存",
        ("己未", "辛未", "丁丑", "己酉"),
    ),
    CalibrationCase(
        "AC-05",
        "v50-v40-profile-29974fcc5472d64e3760",
        "多路径命盘：火、土、金关系混杂",
        ("丁巳", "庚戌", "丙辰", "丁酉"),
    ),
    CalibrationCase(
        "AC-06",
        "v50-v40-profile-b769f83ff15fb5d00c5e",
        "争议命盘：旺衰与做功方向可能冲突",
        ("壬戌", "丙午", "乙丑", "丙戌"),
    ),
    CalibrationCase(
        "AC-07",
        "v50-v40-profile-f86f12e131284a2e7daf",
        "维度分歧：调候需求与制化方向可能不同",
        ("丁酉", "辛亥", "庚戌", "甲申"),
    ),
    CalibrationCase(
        "AC-08",
        "v50-v40-profile-c3474d4152dcdb85626d",
        "竞争解释：依据不足时应保留分歧或暂不判断",
        ("庚寅", "丁亥", "庚戌", "壬午"),
    ),
)


class ProductClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if data is not None else {},
        )
        try:
            with self.opener.open(request, timeout=300) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} {path} failed: {exc.code} {detail}") from exc

    def get(self, path: str, query: dict[str, str] | None = None) -> dict[str, Any]:
        suffix = f"?{urlencode(query)}" if query else ""
        return self.request("GET", f"{path}{suffix}")

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", path, payload)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value) + "\n", encoding="utf-8")


def _profile_map(profiles_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["profile_id"]): item for item in profiles_payload.get("profiles", [])}


def _reading(response: dict[str, Any]) -> dict[str, Any]:
    value = response.get("reading")
    return value if isinstance(value, dict) else {}


def _case_status(raw: dict[str, Any]) -> str:
    start = raw.get("start_response") or {}
    practitioner = raw.get("practitioner_response") or {}
    reading = _reading(practitioner)
    if reading.get("life_case"):
        return "committed"
    outcome = practitioner.get("outcome") or start.get("outcome") or {}
    return str(outcome.get("state") or start.get("status") or "unknown")


def _birth_line(profile: dict[str, Any]) -> str:
    calendar = "农历" if profile.get("calendar_type") == "lunar" else "公历"
    gender = "乾造" if profile.get("gender") == "male" else "坤造" if profile.get("gender") == "female" else "命造"
    birth = " ".join(part for part in (profile.get("birth_date"), profile.get("birth_time")) if part)
    location = profile.get("birth_location") or "出生地未记录"
    return f"{gender} · {calendar} {birth} · {location}"


def _md_json(title: str, value: Any) -> list[str]:
    return [f"#### {title}", "", "```json", _json(value), "```", ""]


def _member_review_payload(response: dict[str, Any]) -> dict[str, Any]:
    reading = _reading(response)
    if not reading:
        return {"product_status": response.get("status"), "outcome": response.get("outcome")}
    return {
        "first_look": reading.get("first_look"),
        "whole_chart_thesis": reading.get("whole_chart_thesis"),
        "public_evidence": reading.get("public_evidence"),
        "life_case": reading.get("life_case"),
        "reliability": reading.get("reliability"),
    }


def _professional_review_payload(response: dict[str, Any]) -> dict[str, Any]:
    reading = _reading(response)
    if not reading:
        return {"product_status": response.get("status"), "outcome": response.get("outcome")}
    return {
        "first_look": reading.get("first_look"),
        "whole_chart_thesis": reading.get("whole_chart_thesis"),
        "salient_phenomena": reading.get("salient_phenomena"),
        "hypotheses": reading.get("hypotheses"),
        "selected_hypothesis_id": reading.get("selected_hypothesis_id"),
        "work_path": reading.get("work_path"),
        "useful_god_reasoning": reading.get("useful_god_reasoning"),
        "dual_lens": reading.get("dual_lens"),
        "unresolved_questions": reading.get("unresolved_questions"),
        "deliberation": reading.get("deliberation"),
        "life_case": reading.get("life_case"),
        "reliability": reading.get("reliability"),
    }


def _review_table() -> list[str]:
    rows = [
        ("整盘重心", "准确 / 部分准确 / 失焦 / 错误"),
        ("主要路径", "成立 / 有条件成立 / 不成立"),
        ("关键命理依据", "充分 / 部分 / 不足"),
        ("条件性用忌", "清楚 / 混淆 / 错误"),
        ("调候、扶抑、制化、做功是否分开", "是 / 部分 / 否"),
        ("竞争假设", "完整 / 缺失 / 不需要"),
        ("不确定性", "合理 / 过度确定 / 过度保守"),
        ("命盘特异性", "强 / 一般 / 通用套话"),
        ("普通用户表达", "准确 / 有损失 / 误导"),
        ("是否可作为 LifeCase 基线", "可以 / 修改后可以 / 不可以"),
    ]
    lines = ["| 审阅项目 | 分析师判断 |", "| --- | --- |"]
    lines.extend(f"| {name} | {options} |" for name, options in rows)
    lines.extend(["", "**分析师备注：**", "", "", ""])
    return lines


_BLIND_REDACTED_KEYS = frozenset(
    {
        "case_belief_direction",
        "case_id",
        "commit_eligible",
        "confidence",
        "confidence_band",
        "deliberation",
        "display_name",
        "formal_insight_committed",
        "gate_version",
        "hard_failure_codes",
        "life_case",
        "professionally_selected",
        "product_status",
        "profile_id",
        "rank",
        "reliability",
        "research_forked",
        "review",
        "review_code",
        "selection_family",
        "semantic_signature",
        "state",
        "status",
        "support_percent",
        "system_preferred",
        "version",
        "world_id",
    }
)


def _sanitize_blind_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _sanitize_blind_value(item)
            for key, item in value.items()
            if key not in _BLIND_REDACTED_KEYS
        }
    if isinstance(value, list):
        return [_sanitize_blind_value(item) for item in value]
    return value


def _blind_case_pairs(run: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    cases = list(run.get("cases", []))
    cases.sort(
        key=lambda item: hashlib.sha256(
            f"analyst-calibration-v1:{item.get('review_code', '')}".encode("utf-8")
        ).hexdigest()
    )
    return [(f"Case {chr(65 + index)}", item) for index, item in enumerate(cases)]


def _blind_chart(profile: dict[str, Any]) -> dict[str, Any]:
    birth_location = str(profile.get("birth_location") or "出生地未记录")
    if "V40 导入" in birth_location:
        birth_location = "未记录"
    return {
        "gender": profile.get("gender"),
        "calendar_type": profile.get("calendar_type"),
        "birth_date": profile.get("birth_date"),
        "birth_time": profile.get("birth_time"),
        "birth_location": birth_location,
        "pillars": profile.get("pillars"),
    }


def _blind_birth_line(profile: dict[str, Any]) -> str:
    return _birth_line(_blind_chart(profile))


def _blind_professional_candidate(item: dict[str, Any]) -> dict[str, Any]:
    payload = item.get("professional_review_payload") or {}
    if isinstance(payload.get("outcome"), dict):
        payload = payload["outcome"]
    return _sanitize_blind_value(payload)


def _source_digest(run: dict[str, Any]) -> str:
    serialized = json.dumps(run, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _analyst_adjudication_template(case_id: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "primary_decision": None,
        "decision_confidence": None,
        "hard_fact_integrity": None,
        "five_element_relation_integrity": None,
        "ten_god_integrity": None,
        "natal_timing_modality_integrity": None,
        "whole_chart_coherence": None,
        "primary_hypothesis_quality": None,
        "alternative_hypothesis_quality": None,
        "work_path_quality": None,
        "conditional_useful_harmful_logic": None,
        "portrait_specificity": None,
        "domain_reasoning_quality": None,
        "template_risk": None,
        "epistemic_discipline": None,
        "blocking_reasons": [],
        "non_blocking_issues": [],
        "professional_rationale": "",
    }


def _round_one_adjudication_yaml(case_id: str) -> list[str]:
    return [
        "```yaml",
        "analyst_blind_adjudication:",
        f"  case_id: {case_id}",
        "  primary_decision: # ACCEPT_FOR_PROFESSIONAL_SUBMISSION | BLOCK_FROM_PROFESSIONAL_SUBMISSION",
        "  decision_confidence: # high | medium | low",
        "  hard_fact_integrity: # pass | fail",
        "  five_element_relation_integrity: # pass | fail",
        "  ten_god_integrity: # pass | fail | not_applicable",
        "  natal_timing_modality_integrity: # pass | fail",
        "  whole_chart_coherence: # pass | fail",
        "  primary_hypothesis_quality: # strong | acceptable | weak | invalid",
        "  alternative_hypothesis_quality: # strong | acceptable | weak | missing",
        "  work_path_quality: # complete | partial | incoherent | missing",
        "  conditional_useful_harmful_logic: # strong | acceptable | weak | invalid | missing",
        "  portrait_specificity: # high | medium | low",
        "  domain_reasoning_quality: # strong | acceptable | generic | unsupported",
        "  template_risk: # low | medium | high",
        "  epistemic_discipline: # pass | fail",
        "  blocking_reasons: []",
        "  non_blocking_issues: []",
        "  professional_rationale: |",
        "    ",
        "```",
    ]


def _minimal_correction_fields() -> list[str]:
    return [
        "- 必须删除的错误判断：",
        "- 必须修正的核心路径：",
        "- 遗漏的关键盘面关系：",
        "- 应降级为竞争假设的内容：",
        "- 需要增加的成立条件：",
        "- 其他个案争议（如有）：",
    ]


def _round_one_json(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": "deepbazi.analyst_calibration.round1_blinded.v1",
        "source_digest": _source_digest(run),
        "machine_status_hidden": True,
        "machine_scores_hidden": True,
        "case_identity_hidden": True,
        "cases": [
            {
                "anonymous_case_id": label,
                "chart": _blind_chart(item.get("profile") or {}),
                "professional_candidate": _blind_professional_candidate(item),
                "analyst_blind_adjudication": _analyst_adjudication_template(label),
            }
            for label, item in _blind_case_pairs(run)
        ],
    }


def render_round_one_blinded(run: dict[str, Any]) -> str:
    lines = [
        "# Professional Blind Test v1 — Round 1 Blinded Mingli Review",
        "",
        "> 第一轮只裁决命理内容。完成并锁定本文件前，不得打开 Round 2 揭盲包。",
        "",
        "## 本轮不可见信息",
        "",
        "- 系统是否提交或拦截；",
        "- Reliability Gate 与 Validator 结果；",
        "- 系统支持度、置信度和内部排序分数；",
        "- 原始案例编号、Case ID、用户姓名与选择目的；",
        "- 产品截图及其他可能暴露机器状态的界面信息。",
        "",
        "## 裁决顺序",
        "",
        "1. 只根据命盘事实和候选认知判断专业内容。",
        "2. 每盘只写最小修正，不重写理想答案。",
        "3. 八盘全部完成后，才归纳跨盘系统性问题。",
        "4. 本轮裁决锁定后，才能进入 Round 2 门禁复核与普通用户表达审阅。",
        "",
        "## 必须阻止专业提交的情形",
        "",
        "以下任一项成立，原则上应选择 `BLOCK_FROM_PROFESSIONAL_SUBMISSION`：",
        "",
        "1. 硬命盘事实错误；",
        "2. 五行生克方向错误；",
        "3. 十神身份错误；",
        "4. 把流年、反事实或假设写成原局既成事实；",
        "5. 主假设与自身证据明显矛盾；",
        "6. 做功路径缺少来源、作用过程或目标，却下了确定结论；",
        "7. 用神、忌神仅凭固定口诀，没有条件和作用对象；",
        "8. 严重忽略核心反证；",
        "9. 主要专业断言不可追溯；",
        "10. 主体内容属于可跨盘复用的套话。",
        "",
        "表达略显啰嗦、术语不够友好、次要假设展开不足、职业候选略宽或合理流派分歧，",
        "不自动构成 Block，但必须记录在 `non_blocking_issues`。",
        "",
        "## 匿名样本",
        "",
        "| 匿名编号 | 出生资料 | 四柱 |",
        "| --- | --- | --- |",
    ]
    for label, item in _blind_case_pairs(run):
        profile = item.get("profile") or {}
        lines.append(
            f"| {label} | {_blind_birth_line(profile)} | {' · '.join(profile.get('pillars') or [])} |"
        )
    lines.extend(["", "---", ""])
    for label, item in _blind_case_pairs(run):
        profile = item.get("profile") or {}
        lines.extend(
            [
                f"## {label}",
                "",
                f"- 出生资料：{_blind_birth_line(profile)}",
                f"- 四柱：`{' · '.join(profile.get('pillars') or [])}`",
                "",
                "### 原始专业候选认知",
                "",
                "> 仅移除了机器状态、自评分、用户身份与门禁元数据；命理判断文字未润色、未补写。",
                "",
                "```json",
                _json(_blind_professional_candidate(item)),
                "```",
                "",
                "### 第一轮独立裁决",
                "",
            ]
        )
        lines.extend(_round_one_adjudication_yaml(label))
        lines.extend(["", "### 最小修正", ""])
        lines.extend(_minimal_correction_fields())
        lines.extend(["", "---", ""])
    lines.extend(
        [
            "## 跨盘系统性问题（八盘裁决后填写）",
            "",
            "| 级别 | 问题 | 涉及匿名案例 | 重复次数 | 建议处理层 |",
            "| --- | --- | --- | --- | --- |",
            "| A 硬错误 |  |  |  | Chart Facts / Reasoner |",
            "| B 系统性专业缺陷 |  |  |  | Reasoner / Prompt / Theory |",
            "| C 个案争议 |  |  |  | 保留竞争解释与条件 |",
            "",
            "## 第一轮锁定",
            "",
            "- 分析师：",
            "- 完成时间：",
            "- Round 1 内容已锁定：是 / 否",
            "- 锁定后文件哈希：",
            "",
        ]
    )
    return "\n".join(lines)


def _gate_payload(item: dict[str, Any]) -> Any:
    professional = item.get("professional_review_payload") or {}
    outcome = professional.get("outcome") if isinstance(professional, dict) else None
    if isinstance(outcome, dict):
        return outcome.get("review") or {}
    return professional.get("reliability") or {}


def _round_two_json(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": "deepbazi.analyst_calibration.round2_reveal.v1",
        "source_digest": _source_digest(run),
        "cases": [
            {
                "anonymous_case_id": label,
                "review_code": item.get("review_code"),
                "case_id": item.get("case_id"),
                "selection_family": item.get("selection_family"),
                "product_status": item.get("product_status"),
                "gate_result": _gate_payload(item),
                "member_output": item.get("member_review_payload"),
            }
            for label, item in _blind_case_pairs(run)
        ],
    }


def render_round_two_reveal(output_dir: Path, run: dict[str, Any]) -> str:
    lines = [
        "# Professional Blind Test v1 — Round 2 Machine Reveal",
        "",
        "> 只有 Round 1 八盘命理裁决全部完成并锁定后，才能打开本文件。",
        "",
        "## 揭盲矩阵",
        "",
        "| 匿名编号 | 原始编号 | 系统行为 | 第一轮分析师裁决 | 最终分类 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for label, item in _blind_case_pairs(run):
        lines.append(
            f"| {label} | {item.get('review_code')} | `{item.get('product_status')}` |  | "
            "正确提交 / 错误放行 / 过度拦截 / 正确拦截 |"
        )
    lines.extend(
        [
            "",
            "## 四类结果",
            "",
            "- 正确提交：专业内容可成为基线，系统也已提交。",
            "- 错误放行：专业内容不应成为基线，但系统已提交。此项最高风险。",
            "- 过度拦截：专业候选可接受，但系统阻断。",
            "- 正确拦截：内容存在实质错误、冲突或依据不足，系统阻断合理。",
            "",
            "---",
            "",
        ]
    )
    for label, item in _blind_case_pairs(run):
        code = str(item.get("review_code") or "").lower()
        lines.extend(
            [
                f"## {label} · {item.get('review_code')}",
                "",
                f"- 选择目的：{item.get('selection_family')}",
                f"- 系统行为：`{item.get('product_status')}`",
                f"- Case ID：`{item.get('case_id')}`",
                f"- 普通用户截图：[查看](screenshots/{code}-member.png)",
                f"- 专业视图截图：[查看](screenshots/{code}-professional.png)",
                "",
                "### Gate / Validator 结果",
                "",
                "```json",
                _json(_gate_payload(item)),
                "```",
                "",
                "### 普通用户实际输出",
                "",
                "```json",
                _json(item.get("member_review_payload")),
                "```",
                "",
                "### 第二轮门禁裁决",
                "",
                "- 最终分类：正确提交 / 错误放行 / 过度拦截 / 正确拦截",
                "- Gate 是否抓住真正问题：是 / 部分 / 否",
                "- Gate 是否遗漏高风险问题：",
                "- Gate 是否误把可修表达问题当成专业硬错误：",
                "",
                "### 普通用户表达裁决",
                "",
                "- 成立条件是否保留：是 / 部分 / 否",
                "- 不确定性是否保留：是 / 部分 / 否",
                "- 是否把局部倾向写成人生定论：是 / 否",
                "- 是否存在可能误导的绝对表达：",
                "- 只需修改表达还是需要回到专业内核：表达 / 内核 / 两者",
                "",
                "### 最小修正",
                "",
                "- 必须删除的错误判断：",
                "- 必须修正的核心路径：",
                "- 遗漏的关键盘面关系：",
                "- 需要降级为竞争假设的内容：",
                "- 需要增加的成立条件：",
                "- 普通用户表达中可能误导的部分：",
                "",
                "---",
                "",
            ]
        )
    lines.extend(
        [
            "## 最终指标",
            "",
            "- 已提交结果的专业有效率：",
            "- 错误放行率：",
            "- 正确拒绝率：",
            "- 过度拦截率：",
            "- 整体专业处理正确率：",
            "",
            "## 下一步裁决",
            "",
            "- [ ] 进入正式 24 盘盲测",
            "- [ ] 暂停并修 Reliability Gate",
            "- [ ] 暂停并修 Baseline Reasoner",
            "- [ ] 只修 Expression Projection",
            "",
            "**理由：**",
            "",
        ]
    )
    return "\n".join(lines)


def write_split_review_packets(output_dir: Path, run: dict[str, Any]) -> None:
    _write_json(output_dir / "analyst_calibration_round1_blinded_v1.json", _round_one_json(run))
    _write_json(output_dir / "analyst_calibration_round2_reveal_v1.json", _round_two_json(run))
    (output_dir / "ANALYST_CALIBRATION_ROUND1_BLINDED.md").write_text(
        render_round_one_blinded(run),
        encoding="utf-8",
    )
    (output_dir / "ANALYST_CALIBRATION_ROUND2_REVEAL.md").write_text(
        render_round_two_reveal(output_dir, run),
        encoding="utf-8",
    )


def render_report(output_dir: Path, run: dict[str, Any]) -> str:
    status_counts: dict[str, int] = {}
    for item in run.get("cases", []):
        status = str(item.get("product_status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    status_summary = " · ".join(
        f"`{status}` {count} 盘" for status, count in sorted(status_counts.items())
    )
    lines = [
        "# Professional Blind Test v1 — Analyst Calibration Review Packet",
        "",
        "> **内部未盲化档案：不得用于第一轮命理裁决。第一轮只使用 `ANALYST_CALIBRATION_ROUND1_BLINDED.md`。**",
        "",
        "> 本包只呈现当前真实产品输出，不代表专业命理能力已经通过。所有文字均来自产品响应，未由 Codex 润色或补写。",
        "",
        "## 审阅边界",
        "",
        "- 每盘只使用出生资料、四柱与当前产品正式计算事实。",
        "- 未向 Baseline Reasoner 提供职业、性格、家庭、健康经历、历史聊天、现实反馈或已知人生事件。",
        "- 同一盘只执行一次整盘认知；普通、命理师与研究视图均从同一份认知记录投影。",
        "- `blocked`、`competing` 与 `committed` 仅是当前产品状态，不是分析师的专业裁决。",
        "- 本轮不得据此自动修改 Prompt、Reasoner、理论权重、模型参数或 Formal Insight 含义。",
        "",
        "## 机器侧观察",
        "",
        f"- 样本数：{len(run.get('cases', []))} 盘。",
        f"- 当前产品状态：{status_summary or '`unknown`'}。",
        "- 上述状态只用于帮助定位审阅材料，不构成通过率或专业结论。",
        "",
        "## 当前冻结环境",
        "",
        "```json",
        _json(run.get("environment", {})),
        "```",
        "",
        "## 样本概览",
        "",
        "| 代码 | 选择目的 | 四柱 | 产品状态 | 截图 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in run.get("cases", []):
        member_screenshot = output_dir / "screenshots" / f"{item['review_code'].lower()}-member.png"
        professional_screenshot = output_dir / "screenshots" / f"{item['review_code'].lower()}-professional.png"
        screenshot_links = []
        if member_screenshot.exists():
            screenshot_links.append(f"[普通](screenshots/{member_screenshot.name})")
        if professional_screenshot.exists():
            screenshot_links.append(f"[专业](screenshots/{professional_screenshot.name})")
        screenshot_cell = " / ".join(screenshot_links) or "待生成"
        lines.append(
            f"| {item['review_code']} | {item['selection_family']} | {' · '.join(item['profile']['pillars'])} | "
            f"`{item['product_status']}` | {screenshot_cell} |"
        )
    lines.extend(["", "---", ""])

    for item in run.get("cases", []):
        code = item["review_code"]
        profile = item["profile"]
        member_screenshot = output_dir / "screenshots" / f"{code.lower()}-member.png"
        professional_screenshot = output_dir / "screenshots" / f"{code.lower()}-professional.png"
        lines.extend(
            [
                f"## {code} · {item['selection_family']}",
                "",
                f"- 出生资料：{_birth_line(profile)}",
                f"- 四柱：`{' · '.join(profile['pillars'])}`",
                f"- 当前产品状态：`{item['product_status']}`",
                f"- Case ID：`{item['case_id']}`",
                "",
            ]
        )
        if member_screenshot.exists():
            lines.extend(["#### 普通用户实际页面", "", f"![{code} 当前产品普通用户视图](screenshots/{member_screenshot.name})", ""])
        if professional_screenshot.exists():
            lines.extend(["#### 专业视图实际页面", "", f"![{code} 当前产品专业视图](screenshots/{professional_screenshot.name})", ""])
        if not member_screenshot.exists() and not professional_screenshot.exists():
            lines.extend(["> 页面截图待生成。", ""])
        lines.extend(_md_json("普通用户实际内容（原文摘录，未改写）", item["member_review_payload"]))
        lines.extend(_md_json("专业视图实际内容（原文摘录，未改写）", item["professional_review_payload"]))
        lines.extend(
            [
                "#### 完整原始响应",
                "",
                f"- [查看本盘原始 JSON](cases/{code.lower()}.json)",
                "",
                "#### 分析师裁决",
                "",
            ]
        )
        lines.extend(_review_table())
        lines.extend(["---", ""])

    lines.extend(
        [
            "## 跨盘系统性问题归纳（分析师填写）",
            "",
            "只有多个命盘重复出现的缺陷才进入这里；不得因单盘问题增加特殊规则。",
            "",
            "| 问题类别 | 重复出现的案例 | 观察 | 是否系统性 |",
            "| --- | --- | --- | --- |",
            "| 命盘事实使用问题 |  |  |  |",
            "| 整盘认知问题 |  |  |  |",
            "| 做功路径问题 |  |  |  |",
            "| 条件性用忌问题 |  |  |  |",
            "| 理论维度混淆问题 |  |  |  |",
            "| 竞争假设问题 |  |  |  |",
            "| 不确定性问题 |  |  |  |",
            "| 普通用户表达损失 |  |  |  |",
            "",
            "## 本轮状态边界",
            "",
            "```yaml",
            "training_performed: false",
            "weights_modified: false",
            "runtime_rules_modified: false",
            "brain_logic_modified: false",
            "mingli_algorithm_modified: false",
            "theory_modified: false",
            "prompt_modified: false",
            "model_parameters_modified: false",
            "life_case_contract_modified: false",
            "product_ui_modified: false",
            "professional_logic_repaired: false",
            "analyst_calibration_only: true",
            "```",
            "",
            "## 有意复现",
            "",
            "本命令会调用冻结中的真实产品链并创建新的 LifeCase；只在需要重新采样时运行：",
            "",
            "```bash",
            "V50_CALIBRATION_ADMIN_PASSWORD=<admin-password> \\",
            "  ../.venv312/bin/python scripts/v50_prepare_professional_blind_analyst_calibration.py",
            "```",
            "",
            "仅在已有原始结果和截图上重新生成审阅文档：",
            "",
            "```bash",
            "../.venv312/bin/python scripts/v50_prepare_professional_blind_analyst_calibration.py --report-only",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def execute(args: argparse.Namespace) -> dict[str, Any]:
    password = os.environ.get(args.password_env, "")
    if not password:
        raise SystemExit(f"missing password environment variable: {args.password_env}")

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    client = ProductClient(args.base_url)
    client.post(
        "/api/v50/product/auth/login",
        {"email": args.email, "password": password},
    )
    profiles_payload = client.get("/api/v50/product/profiles")
    profiles = _profile_map(profiles_payload)
    environment = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "product_health": client.get("/health"),
        "product_manifest": client.get("/api/v50/product/manifest"),
        "agent_manifest": client.get("/api/v50/agent/manifest"),
        "application_baseline": "Life OS Application Foundation v1",
    }
    run: dict[str, Any] = {
        "version": "deepbazi.professional_blind_test.analyst_calibration.v1",
        "status": "running",
        "environment": environment,
        "cases": [],
        "boundaries": {
            "reality_feedback_in_reasoner_input": False,
            "historical_chat_in_reasoner_input": False,
            "known_life_events_in_reasoner_input": False,
            "professional_logic_modified": False,
            "analyst_judgment_fabricated": False,
        },
    }
    _write_json(output_dir / "run_state.json", run)

    for selected in CALIBRATION_CASES:
        profile = profiles.get(selected.profile_id)
        if profile is None:
            raise RuntimeError(f"missing selected profile: {selected.profile_id}")
        if tuple(profile.get("pillars") or ()) != selected.expected_pillars:
            raise RuntimeError(f"pillar mismatch for {selected.review_code}")

        print(f"{selected.review_code}: running current product baseline", flush=True)
        start_response = client.post(
            "/api/v50/agent/cases",
            {
                "profile_id": selected.profile_id,
                "active_mode": "practitioner",
                "progressive": False,
            },
        )
        case_id = str(start_response.get("case_id") or "")
        if not case_id:
            raise RuntimeError(f"case creation returned no case_id for {selected.review_code}")
        member_response = client.get(f"/api/v50/agent/cases/{case_id}", {"active_mode": "member"})
        practitioner_response = client.get(
            f"/api/v50/agent/cases/{case_id}",
            {"active_mode": "practitioner"},
        )
        research_response = client.get(f"/api/v50/agent/cases/{case_id}", {"active_mode": "research"})
        raw = {
            "version": "deepbazi.analyst_calibration_case.v1",
            "review_code": selected.review_code,
            "selection_family": selected.selection_family,
            "profile": profile,
            "start_response": start_response,
            "member_response": member_response,
            "practitioner_response": practitioner_response,
            "research_response": research_response,
        }
        raw_path = output_dir / "cases" / f"{selected.review_code.lower()}.json"
        _write_json(raw_path, raw)
        item = {
            "review_code": selected.review_code,
            "selection_family": selected.selection_family,
            "case_id": case_id,
            "profile": {
                key: profile.get(key)
                for key in (
                    "profile_id",
                    "display_name",
                    "gender",
                    "calendar_type",
                    "birth_date",
                    "birth_time",
                    "birth_location",
                    "pillars",
                )
            },
            "product_status": _case_status(raw),
            "member_review_payload": _member_review_payload(member_response),
            "professional_review_payload": _professional_review_payload(practitioner_response),
            "raw_path": str(raw_path.relative_to(output_dir)),
        }
        run["cases"].append(item)
        _write_json(output_dir / "run_state.json", run)
        print(f"{selected.review_code}: {item['product_status']}", flush=True)

    run["status"] = "awaiting_analyst_review"
    run["completed_at"] = datetime.now(timezone.utc).isoformat()
    _write_json(output_dir / "analyst_calibration_v1.json", run)
    _write_json(output_dir / "run_state.json", run)
    (output_dir / "ANALYST_CALIBRATION_REVIEW_PACKET.md").write_text(
        render_report(output_dir, run),
        encoding="utf-8",
    )
    write_split_review_packets(output_dir, run)
    return run


def rerender(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir).resolve()
    run = json.loads((output_dir / "analyst_calibration_v1.json").read_text(encoding="utf-8"))
    (output_dir / "ANALYST_CALIBRATION_REVIEW_PACKET.md").write_text(
        render_report(output_dir, run),
        encoding="utf-8",
    )
    write_split_review_packets(output_dir, run)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the eight-chart analyst calibration packet from the live product.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8053")
    parser.add_argument("--email", default="jerrydidi@gmail.com")
    parser.add_argument("--password-env", default="V50_CALIBRATION_ADMIN_PASSWORD")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    if args.report_only:
        rerender(args)
    else:
        execute(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
