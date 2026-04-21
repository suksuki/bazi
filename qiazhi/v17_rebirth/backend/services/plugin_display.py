from __future__ import annotations

import re
from typing import Any, Dict


_DISPLAY_OVERRIDES: Dict[str, Dict[str, str]] = {
    "l1.physics.op_branch_sanhe": {
        "display_name": "三合成局",
        "definition": "地支三合/半合带来的聚势与协同做功。",
    },
    "l1.physics.op_branch_liuhe": {
        "display_name": "六合协同",
        "definition": "地支六合形成的稳定绑定与局部增益。",
    },
    "l1.physics.op_branch_liuchong": {
        "display_name": "六冲对抗",
        "definition": "地支六冲触发的对抗、破局与位移压力。",
    },
    "l1.physics.op_branch_liupo": {
        "display_name": "六破关系",
        "definition": "地支六破触发的关系裂解与资源耗散。",
    },
    "l1.physics.op_branch_liuhai": {
        "display_name": "六害关系",
        "definition": "地支六害形成的隐性牵制与迟滞。",
    },
    "l1.physics.op_branch_sanxing": {
        "display_name": "三刑压力",
        "definition": "地支三刑引发的约束、应激与结构摩擦。",
    },
    "l1.physics.op_branch_muku": {
        "display_name": "墓库门态",
        "definition": "墓库地支对能量的收纳、锁定与开库释放。",
    },
    "l1.physics.op_stem_fusion": {
        "display_name": "天干五合",
        "definition": "天干五合产生的牵引、羁绊与转化倾向。",
    },
    "l1.physics.full_bandwidth": {
        "display_name": "地支场烈度",
        "definition": "地支整体能场的带宽、烈度与通道负载。",
    },
    "l1.physics.op_status": {
        "display_name": "状态机节律",
        "definition": "对当前运行节奏、边界和相位的观察性校准。",
    },
    "chang_sheng_12": {
        "display_name": "长生状态",
        "definition": "日主在十二长生序列中的阶段与抗性提示。",
    },
    "l2.risk.risk_matrix": {
        "display_name": "官伤风险矩阵",
        "definition": "围绕羊刃、枭神、官伤等高阶风险结构的检测与提示。",
    },
    "narrative_clip": {
        "display_name": "叙事剪辑",
        "definition": "将物理事实翻译为现代执行建议的叙事插件。",
    },
    "l1.physics.op_geography": {
        "display_name": "地理势场",
        "definition": "识别地支空间位势与分布结构对当前命局的势场影响。",
    },
    "l1.physics.op_vertical_crush": {
        "display_name": "上下压制",
        "definition": "审计干支上下呼应中的压制、穿透与结构挤压。",
    },
    "l1.physics.op_branch_banhe": {
        "display_name": "半合聚势",
        "definition": "识别地支半合带来的局部聚势与偏向性放大。",
    },
    "l1.physics.op_branch_anhe": {
        "display_name": "暗合牵引",
        "definition": "识别地支暗合造成的隐性牵引、绑定与转向。",
    },
    "l1.physics.op_stem_fusion_stuck": {
        "display_name": "合而不化",
        "definition": "审计天干相合但未成化时的牵制、黏滞与悬置状态。",
    },
    "l1.physics.op_stem_fusion_transform": {
        "display_name": "天干化象",
        "definition": "审计天干合化成象后的方向偏移与元素转化倾向。",
    },
    "l1.physics.op_blade_clash": {
        "display_name": "刃杀冲突",
        "definition": "审计羊刃、七杀等刚性结构之间的冲撞与爆发压力。",
    },
    "l1.physics.op_owl_food": {
        "display_name": "枭神夺食",
        "definition": "识别偏印与食神之间的夺食关系，但只作为结构观察。",
    },
    "l1.physics.op_robber_wealth": {
        "display_name": "比劫夺财",
        "definition": "识别比劫争财、分流资源与争夺控制权的结构张力。",
    },
    "l1.physics.op_gov_kill_mix": {
        "display_name": "官杀混杂",
        "definition": "识别正官与七杀并立时的混杂、竞权与结构失清。",
    },
    "l1.physics.op_wealth_seal": {
        "display_name": "财印相战",
        "definition": "识别财星与印星之间的相战、破印与资源背离。",
    },
    "l1.physics.op_connection": {
        "display_name": "生扶连线",
        "definition": "审计五行生扶链路是否形成稳定的支持通道。",
    },
    "l1.physics.op_production": {
        "display_name": "泄秀通道",
        "definition": "审计生出关系形成的输出通道与能量泄放方向。",
    },
    "l1.physics.op_destruction": {
        "display_name": "克制回路",
        "definition": "审计克制关系形成的约束回路与阻尼压力。",
    },
    "l0.foundation.hidden_stems.v1": {
        "display_name": "藏干基线",
        "definition": "把四柱地支的藏干结构投影为可审计的 L0 基础事实。",
    },
    "l0.foundation.rooted_stems.v1": {
        "display_name": "通根基线",
        "definition": "把天干在四柱、运流中的通根条件显影为 L0 基础事实。",
    },
    "l0.foundation.exposed_hidden_stems.v1": {
        "display_name": "透干显影",
        "definition": "识别藏干是否透出为明干，并作为 L0 基础事实输出。",
    },
    "l0.foundation.month_command.v1": {
        "display_name": "月令主气",
        "definition": "将月令主气显影为 L0 旺衰和专题判断的起点。",
    },
    "classical.blind.work_axis.v1": {
        "display_name": "盲派做功主轴",
        "definition": "以冲、刑、合等结构先定盲派做功的主观察轴。",
    },
    "classical.blind.response_chain.v1": {
        "display_name": "盲派应链",
        "definition": "围绕主轴与触发结构，输出盲派的一事一应链提示。",
    },
    "classical.blind.symbol_trigger.v1": {
        "display_name": "盲派触发象",
        "definition": "把当前最强结构和主神转换为盲派断事入口之象。",
    },
    "classical.blind.timing_window.v1": {
        "display_name": "盲派应期窗",
        "definition": "把冲、刑、合等结构映射为盲派的近应、迟应与联应窗口。",
    },
    "classical.blind.summary.v1": {
        "display_name": "盲派断口收束",
        "definition": "把做功、应期与象法汇总为一个可直接断事的盲派断口。",
    },
    "classical.ziping.month_command.v1": {
        "display_name": "子平月令法",
        "definition": "以月令主气为第一判断基准的子平专题插件。",
    },
    "classical.ziping.balance.v1": {
        "display_name": "子平旺衰平衡",
        "definition": "围绕主轴与次轴比例，对命局旺衰与偏枯做结构判断。",
    },
    "classical.ziping.yongshen.v1": {
        "display_name": "子平用神建议",
        "definition": "按当前强弱结构给出用神观察方向的专题插件。",
    },
    "classical.pattern.axis.v1": {
        "display_name": "格局轴线",
        "definition": "先给出当前命局最强主轴，作为格局专题第一候选。",
    },
    "classical.pattern.jianlu_yuejie.v1": {
        "display_name": "建禄月劫候选",
        "definition": "从月令主气切入，检测建禄与月劫方向的格局候选。",
    },
    "classical.pattern.congshi.v1": {
        "display_name": "从势候选",
        "definition": "识别一枝独强、具备从势倾向的格局候选。",
    },
    "classical.pattern.finance_officer.v1": {
        "display_name": "财官协同",
        "definition": "识别财官双线并举的格局候选。",
    },
    "classical.pattern.resolver.v1": {
        "display_name": "格局裁决器",
        "definition": "对多个格局候选并存时的冲突做专题审计与裁决提示。",
    },
    "classical.pattern.formation_gate.v1": {
        "display_name": "成格条件",
        "definition": "对格局候选是否具备成格条件做专题审计。",
    },
    "classical.pattern.break_guard.v1": {
        "display_name": "破格预警",
        "definition": "对格局候选是否受到冲刑害等结构干扰做专题预警。",
    },
    "classical.pattern.dynamic_scope.v1": {
        "display_name": "动态格局来源",
        "definition": "按原局、运、流来源权重标注当前格局候选的动态生效来源。",
    },
    "classical.pattern.wealth_star.v1": {
        "display_name": "财格候选",
        "definition": "围绕正财格与偏财格的月令、透干与结构条件做候选审计。",
    },
    "classical.pattern.seal_star.v1": {
        "display_name": "印格候选",
        "definition": "围绕正印格与偏印格的月令与护格条件做候选审计。",
    },
    "classical.pattern.yangren.v1": {
        "display_name": "羊刃候选",
        "definition": "审计月令羊刃是否成势，以及是否具备制刃、驾杀等后续路径。",
    },
    "classical.pattern.guanyin.v1": {
        "display_name": "官印相生",
        "definition": "审计官印相生路线是否成立，以及能否形成清贵结构。",
    },
    "classical.pattern.shayin.v1": {
        "display_name": "杀印相生",
        "definition": "审计七杀与印星的化杀成权路线是否成立。",
    },
    "classical.pattern.shishen_zhisha.v1": {
        "display_name": "食神制杀",
        "definition": "审计食神是否足以制服七杀并维持格局清纯。",
    },
    "classical.pattern.shangguan_peiyin.v1": {
        "display_name": "伤官配印",
        "definition": "审计伤官旺而得印护的高阶成格路线。",
    },
    "classical.pattern.caipoyin.v1": {
        "display_name": "财破印",
        "definition": "审计财星过强反伤印绶的结构压力与体用逆转风险。",
    },
    "classical.pattern.shishen_shengcai.v1": {
        "display_name": "食神生财",
        "definition": "审计食神吐秀顺泄到财星的流通路线。",
    },
    "classical.pattern.shangguan_shengcai.v1": {
        "display_name": "伤官生财",
        "definition": "审计伤官输出转财的结构路径与成格条件。",
    },
    "classical.pattern.yangren_jiasha.v1": {
        "display_name": "阳刃驾杀",
        "definition": "审计羊刃与七杀并行时是否形成可用权格路线。",
    },
    "classical.pattern.zaqi_caiguan.v1": {
        "display_name": "杂气财官格",
        "definition": "针对辰戌丑未杂气月的财官透势做专题候选审计。",
    },
    "classical.pattern.zaqi_yin.v1": {
        "display_name": "杂气印绶格",
        "definition": "针对杂气月中印绶透势与护格条件做专题候选审计。",
    },
    "classical.pattern.zaqi_qisha.v1": {
        "display_name": "杂气七杀格",
        "definition": "针对杂气月中七杀透势与制化条件做专题候选审计。",
    },
    "classical.pattern.congcai.v1": {
        "display_name": "从财格",
        "definition": "审计财势独旺、身党不敌时的从财路线。",
    },
    "classical.pattern.congsha.v1": {
        "display_name": "从杀格",
        "definition": "审计七杀成势、日主难起时的从杀路线。",
    },
    "classical.pattern.conger.v1": {
        "display_name": "从儿格",
        "definition": "审计食伤成党、印比不足回身时的从儿路线。",
    },
    "classical.pattern.congwang.v1": {
        "display_name": "从旺格",
        "definition": "审计印比成势、一边独旺时的从旺路线。",
    },
    "classical.pattern.congqiang.v1": {
        "display_name": "从强格",
        "definition": "审计身党绝对主导、异党难敌时的从强路线。",
    },
    "classical.pattern.congruo.v1": {
        "display_name": "从弱格",
        "definition": "审计身党极弱、异党集中成势时的从弱路线。",
    },
    "classical.pattern.huaqi.v1": {
        "display_name": "化气格",
        "definition": "审计天干五合与化神得令条件，确认是否具备化气胚象。",
    },
    "classical.pattern.quzhi.v1": {
        "display_name": "曲直格",
        "definition": "审计木气专旺是否达到曲直外格的候选条件。",
    },
    "classical.pattern.yanshang.v1": {
        "display_name": "炎上格",
        "definition": "审计火气专旺是否达到炎上外格的候选条件。",
    },
    "classical.pattern.jiase.v1": {
        "display_name": "稼穑格",
        "definition": "审计土气专旺是否达到稼穑外格的候选条件。",
    },
    "classical.pattern.congge.v1": {
        "display_name": "从革格",
        "definition": "审计金气专旺是否达到从革外格的候选条件。",
    },
    "classical.pattern.runxia.v1": {
        "display_name": "润下格",
        "definition": "审计水气专旺是否达到润下外格的候选条件。",
    },
    "classical.pattern.liangshen.v1": {
        "display_name": "两神成象",
        "definition": "审计双主轴并峙是否形成稳定的两神成象结构。",
    },
    "classical.pattern.tianyuan.v1": {
        "display_name": "天元一气",
        "definition": "审计天干同气重复与一元化结构是否达到天元一气候选条件。",
    },
    "ten_god_pattern": {
        "display_name": "十神主轴观察",
        "definition": "只负责十神主轴与家族混合摘要，不再定义古典格局 headline。",
    },
    "kong_wang": {
        "display_name": "空亡观察",
        "definition": "识别四柱与运流中的空亡位置，并作为结构观察层提示。",
    },
    "shensha": {
        "display_name": "神煞观察",
        "definition": "识别神煞命中，但不直接定义主格局或物理强弱。",
    },
}


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _trim_sentence(text: str) -> str:
    text = _clean_text(text)
    if not text:
        return ""
    text = re.sub(r"[。；;:：]+$", "", text)
    return text


def _first_phrase(text: str) -> str:
    text = _trim_sentence(text)
    if not text:
        return ""
    parts = re.split(r"[。；;:：,，]", text, maxsplit=1)
    return parts[0].strip()


def _derive_name_from_text(text: str) -> str:
    phrase = _first_phrase(text)
    if not phrase:
        return ""
    phrase = re.sub(r"^(检测到|高阶|现代|基于|用于|围绕)", "", phrase).strip()
    phrase = re.sub(r"(通用)?(协同)?(性)?算法$", "", phrase).strip()
    phrase = re.sub(r"(结构)?检测矩阵$", "风险矩阵", phrase).strip()
    phrase = re.sub(r"插件$", "", phrase).strip()
    return phrase[:24].strip()


def plugin_display_profile(
    *,
    plugin_id: Any,
    manifest: Dict[str, Any] | None = None,
    summary: Any = "",
    rationale: Any = "",
    module_doc: Any = "",
    spec_doc: Any = "",
) -> Dict[str, str]:
    pid = str(plugin_id or "").strip()
    manifest = manifest if isinstance(manifest, dict) else {}
    summary_text = _trim_sentence(
        manifest.get("Description")
        or manifest.get("summary")
        or manifest.get("display_definition")
        or summary
    )
    rationale_text = _trim_sentence(
        manifest.get("Rationale")
        or manifest.get("rationale")
        or manifest.get("display_description")
        or rationale
    )
    module_text = _trim_sentence(module_doc)
    spec_text = _trim_sentence(spec_doc)
    override = _DISPLAY_OVERRIDES.get(pid, {})

    display_name = _trim_sentence(
        override.get("display_name")
        or manifest.get("DisplayName")
        or manifest.get("display_name")
        or manifest.get("Name")
        or manifest.get("name")
        or _derive_name_from_text(summary_text)
        or _derive_name_from_text(module_text)
        or pid
    )
    display_definition = _trim_sentence(
        override.get("definition")
        or summary_text
        or module_text
        or spec_text
        or "该插件已接入 V17 推理链路，但尚未补齐定义说明"
    )
    display_description = _trim_sentence(
        rationale_text
        or summary_text
        or module_text
        or spec_text
        or "暂无补充说明"
    )
    technical_label = pid or "unknown_plugin"
    family = technical_label.split(".")[-1] if technical_label else ""
    return {
        "display_name": display_name,
        "display_definition": display_definition,
        "display_description": display_description,
        "technical_label": technical_label,
        "family_label": family,
    }


def plugin_source_label(source: Any, *, fallback: Any = "") -> str:
    raw = str(source or "").strip()
    if not raw:
        return _trim_sentence(fallback) or "未知规则"
    override = _DISPLAY_OVERRIDES.get(raw, {})
    if override.get("display_name"):
        return str(override["display_name"]).strip()
    text_fallback = _trim_sentence(fallback)
    if text_fallback:
        derived = _derive_name_from_text(text_fallback)
        if derived:
            return derived
    if raw.startswith("l2."):
        tail = raw.split(".")[-1]
        return _derive_name_from_text(tail.replace("_", " ")) or raw.replace("l2.", "L2:", 1)
    if raw.startswith("l1."):
        tail = raw.split(".")[-1]
        return _derive_name_from_text(tail.replace("_", " ")) or raw.replace("l1.", "L1:", 1)
    return raw
