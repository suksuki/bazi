"""
FDS AI Engine - 流形语义生成 (Manifold-to-Text)
===============================================
对接本地 Ollama/vLLM，将 5D 物理偏移转化为「物理逻辑一致」的深度判词。

- 输入：命例在 5D 空间的 point、相对质心的 offset、十神分布、矩阵版本
- 输出：Qwen-32B 生成的语义解读（性格/倾向微调，非二元结论）

Compliance: 公理三（量子概率性）、零硬编码（参数从 config 读取）
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from core.balance_engine import run_balance_audit
from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# 5D 轴语义（与 hkb_params 一致，仅作 Prompt 说明用，不写死阈值）
AXIS_SEMANTICS = {
    "E": "能量轴 (Energy)：身强/身弱、生命力能级",
    "O": "秩序轴 (Order)：社会地位、克制力、法律边界",
    "M": "财富轴 (Material)：资源拥有度、物质丰盈度",
    "S": "压力轴 (Stress)：环境应力、危机感",
    "R": "关系轴 (Relation)：逻辑深度、精神高度",
}

SYSTEM_PROMPT_5D = """你是一位精通命理学与物理建模的「流形解读师」。你的任务是根据命例在 5D 命运流形上的**物理坐标与偏移向量**，给出简洁、有逻辑的语义解读。

## 五轴含义（必须严格按此理解）
- **E (能量轴)**：身强/身弱、生命力能级。正值越大表示日主根基越稳、抗压能力越强。
- **O (秩序轴)**：社会地位、克制力、法律边界。与官星、纪律、管理能力相关。
- **M (财富轴)**：资源拥有度、物质丰盈度。与财星、资产、执行力相关。
- **S (压力轴)**：环境应力、危机感。压力大时需看是否有印比化解。
- **R (关系轴)**：逻辑深度、精神高度、人际与悟性。

## 输入说明
你会收到：
1. **5D 坐标** (point)：命例在当前矩阵下的 E/O/M/S/R 取值。
2. **偏移向量** (offset)：命例相对「最近质心」在各轴上的偏移（正=向该轴正向偏，负=向负向偏）。
3. **最近质心** (best_subpattern)：如 A-01-S1（身强任官）或 A-01-S2（财官双美）。
4. **矩阵版本**：物理校准矩阵版本号。

## 输出要求
1. **物理逻辑优先**：先根据偏移方向与幅度，说明「相对标准质心」在哪些轴上发生了何种方向的微调（例如：向 E 轴正向偏移 0.5 单位 → 能量略强于该子格局典型值）。
2. **性格/倾向**：用 1～3 句中文，概括这种偏移在现实中可能体现的性格或命运倾向微调，避免绝对化结论（如「一定」「必然」）。
3. **禁止**：不输出纯表格、不输出 JSON、不输出「仅供参考」等免责句。直接给出一段连贯的解读段落，控制在 150 字以内。
"""

# 默认 HKB 路径（A-01 语义核心从该文件注入）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_HKB_PATH = _PROJECT_ROOT / "config" / "hkb" / "hkb_params.json"
_COMBINED_PATTERN_YAML = _PROJECT_ROOT / "config" / "ai" / "prompts" / "combined_pattern_analysis.yaml"
_QGA_MANIFEST_PATH = _PROJECT_ROOT / "registry" / "qga_manifest.json"

# 格局语义兜底（仅当 manifest/HKB 均无时使用，新格局审计后应写入 manifest）
_PATTERN_SEMANTIC_FALLBACK: Dict[str, str] = {
    "A-01": "正官约束、秩序优先、贵气",
    "A-02": "应力转化、秩序重构、爆发动能",
    "A-03": "资源扩张、投机动能、财富留存",
    "A-04": "稳健积累、务实管理、风险厌恶",
    "A-05": "枭神夺食、偏门学术、孤傲与夺食之危机感（枭神格）",
    "A-06": "食神生财、口福表达、温和输出",
    "A-07": "才华外泄、挑战秩序、应力扰动（伤官见官须手术刀式识别）",
    "A-08": "贵气、包容、秩序加持",
    "A-09": "建禄、禄劫用财官、自力更生（禁止称比肩格）",
    "A-10": "阳刃、极端应力、羊刃架杀（禁止称劫财格）",
    "A-11": "从财格、弃命从财、M极值E/O坍缩（第046号审计师签发）",
    "A-12": "从杀格、日主无依、S峰值E消失（第046号审计师签发）",
    "A-13": "专旺格、一气专旺、E爆表S/M排斥（第046号审计师签发）",
}


def _load_combined_pattern_yaml() -> Tuple[str, str]:
    """加载混合格局 Prompt 模板，返回 (system, user_template) 两段文本。"""
    if not _COMBINED_PATTERN_YAML.exists():
        logger.warning("混合格局模板不存在: %s", _COMBINED_PATTERN_YAML)
        return "", ""
    raw = _COMBINED_PATTERN_YAML.read_text(encoding="utf-8")
    system, user_template = "", ""
    # 简单解析：定位 system: | 与 user_template: | 块（块内行首为两空格）
    in_system = False
    in_user = False
    for line in raw.splitlines():
        if line.strip().startswith("system:") and "|" in line:
            in_system = True
            in_user = False
            continue
        if line.strip().startswith("user_template:") and "|" in line:
            in_system = False
            in_user = True
            continue
        if in_system and (line.startswith("  ") or line.strip() == ""):
            system += line[2:] if len(line) >= 2 else line
            system += "\n"
            continue
        if in_user and (line.startswith("  ") or line.strip() == ""):
            user_template += line[2:] if len(line) >= 2 else line
            user_template += "\n"
            continue
        if line.strip() and not line.startswith(" ") and ":" in line:
            in_system = in_user = False
    return system.strip(), user_template.strip()


def _manifest_path_for_pattern(pattern_id: str) -> Optional[Path]:
    """解析格局 manifest 路径：优先 registry/holographic_pattern/{id}/{id}_manifest.json，其次 config/patterns/manifest_{id}.json。"""
    pid = (pattern_id or "").strip().upper()
    if not pid:
        return None
    reg_path = _PROJECT_ROOT / "registry" / "holographic_pattern" / pid / f"{pid}_manifest.json"
    if reg_path.exists():
        return reg_path
    cfg_name = pid.replace("-", "")
    cfg_path = _PROJECT_ROOT / "config" / "patterns" / f"manifest_{cfg_name}.json"
    if cfg_path.exists():
        return cfg_path
    return None


def _load_manifest_for_pattern(pattern_id: str) -> Optional[Dict[str, Any]]:
    """按 pattern_id 加载 manifest（先按路径解析，再可兜底从 QGA manifest_ref 取）。"""
    path = _manifest_path_for_pattern(pattern_id)
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.debug("加载 manifest %s 失败: %s", pattern_id, e)
    if _QGA_MANIFEST_PATH.exists():
        try:
            with open(_QGA_MANIFEST_PATH, "r", encoding="utf-8") as f:
                qga = json.load(f)
            entries = (qga.get("topics") or {}).get("holographic_pattern") or []
            for ent in entries:
                if (ent.get("pattern_id") or "").strip().upper() == (pattern_id or "").strip().upper():
                    ref = ent.get("manifest_ref")
                    if ref:
                        full = _PROJECT_ROOT / ref
                        if full.exists():
                            with open(full, "r", encoding="utf-8") as f:
                                return json.load(f)
                    break
        except Exception as e:
            logger.debug("从 QGA 解析 manifest 失败: %s", e)
    return None


def _get_pattern_display_name(pattern_id: str) -> str:
    """返回格局展示名（如「正财格」），优先 manifest meta_info.chinese_name。"""
    manifest = _load_manifest_for_pattern(pattern_id)
    if manifest:
        meta = (manifest.get("meta_info") or {}).get("chinese_name")
        if meta:
            return meta
    pid = (pattern_id or "").strip().upper()
    names = {"A-01": "正官格", "A-02": "七杀格", "A-03": "偏财格", "A-04": "正财格", "A-05": "枭神格", "A-06": "食神格", "A-07": "伤官格", "A-08": "正印格", "A-09": "建禄格", "A-10": "阳刃格", "A-11": "从财格", "A-12": "从杀格", "A-13": "专旺格"}
    return names.get(pid, pid)


def _get_semantic_text_for_pattern(pattern_id: str) -> str:
    """
    通用格局语义加载（SOP V5.1 三级降级协议）：任一审计注册格局均可获语义原文。
    1) Manifest 动态提取：manifest.semantic_core_dimensions（最新审计立法，唯一真理源）；
    2) HKB 静态映射：hkb_params.json 内 {pid}_semantic_core（历史法理沉淀）；
    3) System Default：_PATTERN_SEMANTIC_FALLBACK 或「语义待立法」（系统安全性兜底）。
    """
    pid = (pattern_id or "").strip().upper()
    if not pid:
        return ""

    # 1) manifest 内 semantic_core_dimensions
    manifest = _load_manifest_for_pattern(pid)
    if manifest:
        core = manifest.get("semantic_core_dimensions") or {}
        if isinstance(core, dict) and core:
            lines = []
            for key, d in sorted(core.items()):
                if not isinstance(d, dict):
                    continue
                name = d.get("name", key)
                classical = d.get("classical_by_gemini", d.get("definition", ""))
                if classical:
                    lines.append(f"{name}：{classical}")
            if lines:
                return "；".join(lines)

    # 2) HKB 中 {a01_semantic_core, a02_*, ...}
    if _DEFAULT_HKB_PATH.exists():
        try:
            with open(_DEFAULT_HKB_PATH, "r", encoding="utf-8") as f:
                hkb = json.load(f)
            key = f"{pid.lower().replace('-', '')}_semantic_core"
            core = (hkb.get("hkb") or {}).get(key)
            if isinstance(core, dict) and core:
                lines = []
                for k, d in core.items():
                    if not isinstance(d, dict):
                        continue
                    name = d.get("name", k)
                    definition = d.get("definition", d.get("classical_by_gemini", ""))
                    if definition:
                        lines.append(f"{name}：{definition}")
                if lines:
                    return "；".join(lines)
        except Exception as e:
            logger.debug("加载 %s HKB 语义失败: %s", pid, e)

    # 3) 兜底
    return _PATTERN_SEMANTIC_FALLBACK.get(pid, f"{pid} 语义待立法")


def _build_hkb_semantic_block(probabilistic_patterns: List[Dict[str, Any]], max_patterns: int = 5) -> str:
    """
    按对撞结果动态组装「各格局语义核心」块，仅包含本命命中的格局，供 LLM 判词使用。
    新格局审计并注册后无需改代码即可自动纳入。
    """
    seen: set = set()
    parts = []
    for p in (probabilistic_patterns or [])[:max_patterns]:
        pid = (p.get("pattern_id") or "").strip().upper()
        if not pid or pid in seen:
            continue
        seen.add(pid)
        name = _get_pattern_display_name(pid)
        semantic = _get_semantic_text_for_pattern(pid)
        parts.append(f"  {pid} {name}：{semantic}")
    return "\n".join(parts) if parts else "  （无命中格局时此处为空，请据 mixed_ratio 与 5D 坐标综合判断）"


def _format_balance_audit_for_prompt(audit: Dict[str, Any]) -> str:
    """将喜忌神审计结果格式化为 Prompt 内嵌文案。"""
    if not audit or not audit.get("useful_god") and not audit.get("harmful_god"):
        return "本次未做喜忌神模拟，五行调理宜根据流年再细论。"
    parts = [
        f"用神：{audit.get('useful_god', '')}。理由：{audit.get('reason_useful', '')}",
        f"忌神：{audit.get('harmful_god', '')}。理由：{audit.get('reason_harmful', '')}",
    ]
    if audit.get("bridge_god"):
        parts.append(f"通关神：{audit.get('bridge_god')}。{audit.get('reason_bridge') or ''}")
    else:
        parts.append("通关神：无。")
    return "\n".join(parts)


def _fill_combined_user_prompt(
    user_template: str,
    mixed_ratio: str,
    hkb_semantic_block: str,
    point_5d: Dict[str, float],
    delta_v_repair: str,
    balance_audit_text: str = "",
) -> str:
    """将占位符填入 user_template。hkb_semantic_block 由 _build_hkb_semantic_block 按对撞结果动态生成。"""
    if not balance_audit_text:
        balance_audit_text = "本次未做喜忌神模拟，五行调理宜根据流年再细论。"
    repl = {
        "{{ mixed_ratio }}": mixed_ratio,
        "{{ hkb_semantic_block }}": hkb_semantic_block,
        "{{ balance_audit }}": balance_audit_text,
        "{{ point_5d_E }}": str(point_5d.get("E", 0.0)),
        "{{ point_5d_O }}": str(point_5d.get("O", 0.0)),
        "{{ point_5d_M }}": str(point_5d.get("M", 0.0)),
        "{{ point_5d_S }}": str(point_5d.get("S", 0.0)),
        "{{ point_5d_R }}": str(point_5d.get("R", 0.0)),
        "{{ delta_v_repair }}": delta_v_repair,
    }
    # 兼容旧模板中可能残留的单项占位符
    for pid in ("a02", "a03", "a04", "a05"):
        key = f"{{{{ hkb_semantic_{pid} }}}}"
        if key in user_template:
            repl[key] = "（已并入上方各格局语义核心块）"
    out = user_template
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def _get_semantic_section_from_manifest(pattern_id: str) -> str:
    """
    SOP V5.1 元驱动：从格局 manifest 提取语义核心块（仅 section 文本，不含 base）。
    任一审计注册格局均走此路径，无 pattern_id 分支；manifest 为唯一真理源。
    """
    manifest = _load_manifest_for_pattern(pattern_id)
    if not manifest:
        return ""
    core = manifest.get("semantic_core_dimensions") or {}
    if not isinstance(core, dict) or not core:
        return ""
    name = _get_pattern_display_name(pattern_id)
    lines = ["", f"## {pattern_id} {name} 语义核心（审计师立法，必须遵循）"]
    for key, d in sorted(core.items()):
        if not isinstance(d, dict):
            continue
        dim_name = d.get("name", key)
        mapping = d.get("physical_mapping", "")
        classical = d.get("classical_by_gemini", d.get("definition", ""))
        lines.append(f"- **{dim_name}**（{mapping}）：{classical}")
    if len(lines) <= 2:
        return ""
    return "\n".join(lines)


def _get_system_prompt_with_a01_semantic() -> str:
    """在基础 Prompt 后追加 A-01 正官格语义核心（立法），从 hkb_params 读取。"""
    base = SYSTEM_PROMPT_5D
    try:
        with open(_DEFAULT_HKB_PATH, "r", encoding="utf-8") as f:
            hkb = json.load(f)
        core = (hkb.get("hkb") or {}).get("a01_semantic_core")
        if not isinstance(core, dict):
            return base
        lines = [
            "",
            "## A-01 正官格语义核心（立法，必须遵循）",
        ]
        for key in ("dimension_a_order_rigidity", "dimension_b_energy_carrier", "dimension_c_wealth_coupling"):
            d = core.get(key)
            if not isinstance(d, dict):
                continue
            name = d.get("name", key)
            definition = d.get("definition", "")
            mapping = d.get("physical_mapping", "")
            axis = d.get("axis") or ", ".join(d.get("axes") or [])
            lines.append(f"- **{name}**（轴：{axis}）定义：{definition} 物理映射：{mapping}")
        if len(lines) > 2:
            base = base + "\n".join(lines)
        base += "\n\n## 动态演化（若输入中提供）\n若输入中包含【动态 5D 坐标】与【时间增量】，请对比原局与动态点的位移，给出**动态趋势分析**与**风险提示**（例如：S 轴突增、O 轴坍缩时，建议收缩扩张、稳固秩序）；结合古典「伤官见官」「财能生官」等法理，用 1～3 句概括该时段格局健康度与趋吉避凶要点。"
    except Exception as e:
        logger.debug("加载 A-01 语义核心失败，使用基础 Prompt: %s", e)
    return base


def _get_system_prompt_for_pattern_from_hkb(pattern_id: str) -> str:
    """SOP V4.1：从 HKB 读取格局语义核心（sync_pattern_hkb 同步后的 a02_semantic_core / a03_semantic_core）。"""
    base = SYSTEM_PROMPT_5D
    try:
        with open(_DEFAULT_HKB_PATH, "r", encoding="utf-8") as f:
            hkb = json.load(f)
        core = (hkb.get("hkb") or {}).get(f"{pattern_id.lower().replace('-', '')}_semantic_core")
        if not isinstance(core, dict):
            return base
        lines = ["", f"## {pattern_id} 语义核心（HKB 立法，必须遵循）"]
        for key, d in core.items():
            if not isinstance(d, dict):
                continue
            name = d.get("name", key)
            mapping = d.get("physical_mapping", "")
            definition = d.get("definition", d.get("classical_by_gemini", ""))
            ref = d.get("classical_ref", "")
            if ref:
                definition = f"{definition} 古籍印证：{ref}"
            lines.append(f"- **{name}**（{mapping}）：{definition}")
        if len(lines) > 2:
            base = base + "\n".join(lines)
    except Exception as e:
        logger.debug("加载 %s HKB 语义失败: %s", pattern_id, e)
    return base


def _get_classical_verdict_block(pattern_id: str) -> str:
    """第 044 号审计师签发：从 HKB pattern_classical_verdict 读取古典真意语义块与判词指令，供 32B 判词不走样。"""
    try:
        with open(_DEFAULT_HKB_PATH, "r", encoding="utf-8") as f:
            hkb = json.load(f)
        blocks = (hkb.get("hkb") or {}).get("pattern_classical_verdict") or {}
        block = blocks.get(pattern_id.strip().upper()) if isinstance(blocks, dict) else None
        if not block or not isinstance(block, dict):
            return ""
        literal = block.get("hkb_literal", "")
        instruction = block.get("verdict_instruction", "")
        if not literal and not instruction:
            return ""
        lines = ["", "## 古典真意与判词指令（必须遵循）", f"核心语义：{literal}"]
        if instruction:
            lines.append(f"判词指令：{instruction}")
        return "\n".join(lines)
    except Exception as e:
        logger.debug("加载古典判词块失败: %s", e)
        return ""


def _get_system_prompt_for_pattern(pattern_id: Optional[str]) -> str:
    """
    Clause 0.3 / SOP V5.1 元驱动：按格局 ID 返回带语义立法的 System Prompt。
    无 pattern_id 分支；优先级：Manifest 动态提取 → HKB 静态映射 → System Default（A-01 兜底）。
    第 044 号：A-05/A-08/A-09/A-10 追加 pattern_classical_verdict 古典真意与判词指令。
    """
    if not pattern_id:
        return _get_system_prompt_with_a01_semantic()
    pid = str(pattern_id).strip().upper()
    section = _get_semantic_section_from_manifest(pid)
    base = (SYSTEM_PROMPT_5D + section) if section else _get_system_prompt_for_pattern_from_hkb(pid)
    verdict = _get_classical_verdict_block(pid)
    if verdict:
        base = base + "\n" + verdict
    return base


def _get_ollama_client():
    """从配置读取 ollama_host 并返回 Ollama 客户端（懒加载）。"""
    try:
        import ollama
    except ImportError:
        logger.warning("ollama 未安装，AI 判词不可用")
        return None
    cm = ConfigManager()
    host = cm.get("ollama_host") or "http://localhost:11434"
    if host and host != "http://localhost:11434":
        return ollama.Client(host=host)
    return ollama.Client()


def _build_user_prompt(
    point: Dict[str, float],
    offset: Dict[str, float],
    best_subpattern: str,
    matrix_version: str,
    ten_gods_summary: Optional[str] = None,
    dynamic_context: Optional[str] = None,
) -> str:
    """构建发给大模型的用户 Prompt（含物理数据、十神摘要与可选动态演化）。"""
    lines = [
        "请根据以下物理数据给出流形语义解读：",
        "",
        "【5D 坐标 point】",
        json.dumps(point, ensure_ascii=False, indent=2),
        "",
        "【相对质心的偏移向量 offset】",
        json.dumps(offset, ensure_ascii=False, indent=2),
        "",
        f"【最近质心子格局】{best_subpattern}",
        f"【矩阵版本】{matrix_version}",
    ]
    if ten_gods_summary:
        lines.append("")
        lines.append("【十神分布摘要】")
        lines.append(ten_gods_summary)
    if dynamic_context:
        lines.append("")
        lines.append("【动态演化】")
        lines.append(dynamic_context)
    return "\n".join(lines)


def generate_manifold_interpretation(
    point: Dict[str, float],
    offset: Dict[str, float],
    best_subpattern: str,
    matrix_version: str,
    ten_gods: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
    timeout_sec: int = 60,
    dynamic_context: Optional[str] = None,
    pattern_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    根据 5D 坐标与偏移向量，调用本地大模型生成「物理偏移感应式」判词。

    Args:
        point: 5D 坐标 {"E": float, "O": float, ...}
        offset: 相对质心偏移 {"E": float, ...}
        best_subpattern: 最近质心 ID，如 A-01-S1
        matrix_version: 矩阵版本号
        ten_gods: 十神向量（可选），用于生成摘要
        model: 模型名，默认从配置读取或 qwen2.5:32b
        timeout_sec: 请求超时秒数
        pattern_id: 格局 ID（如 A-01、A-02），用于加载该格局的语义立法作为 System Prompt；Clause 0.3

    Returns:
        {
            "success": bool,
            "text": str,           # 生成的判词正文
            "model": str,
            "error": str | None,
        }
    """
    result = {"success": False, "text": "", "model": "", "error": None}
    client = _get_ollama_client()
    if not client:
        result["error"] = "Ollama 未安装或不可用"
        return result

    cm = ConfigManager()
    ai_cfg = cm.get("ai_engine")
    model_name = model or (ai_cfg.get("chat_model") if isinstance(ai_cfg, dict) else None)
    if not model_name:
        model_name = "qwen2.5:32b"

    ten_gods_summary = None
    if ten_gods:
        # 只取非零或主要几项，避免 prompt 过长
        parts = [f"{k}={v}" for k, v in sorted(ten_gods.items(), key=lambda x: -abs(x[1] if isinstance(x[1], (int, float)) else 0))[:6]]
        ten_gods_summary = ", ".join(parts)

    user_prompt = _build_user_prompt(
        point=point,
        offset=offset,
        best_subpattern=best_subpattern,
        matrix_version=matrix_version,
        ten_gods_summary=ten_gods_summary,
        dynamic_context=dynamic_context,
    )

    system_prompt = _get_system_prompt_for_pattern(pattern_id)
    # 第 045 号：判词链路 DB→RAG→LLM — 注入古典原话引证，判词须含引证
    if pattern_id:
        try:
            from core.rag_canon import query_citations, format_citations_for_prompt
            citations = query_citations(pattern_id, query_text="格局判词 古典引证", top_k=3)
            if citations:
                system_prompt = system_prompt + "\n" + format_citations_for_prompt(citations)
        except Exception as e:
            logger.debug("RAG 古典引证注入失败: %s", e)
    try:
        response = client.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"num_predict": 400},
        )
        # Ollama 返回格式: { "message": { "content": "..." } }
        content = (
            response.get("message", {}).get("content")
            if isinstance(response, dict)
            else (getattr(response, "message", None) and getattr(response.message, "content", None))
        )
        if content and isinstance(content, str):
            result["success"] = True
            result["text"] = content.strip()
            result["model"] = model_name
        else:
            result["error"] = "模型返回内容为空"
    except Exception as e:
        logger.exception("AI 判词调用失败")
        result["error"] = str(e)
    return result


def stream_manifold_interpretation(
    point: Dict[str, float],
    offset: Dict[str, float],
    best_subpattern: str,
    matrix_version: str,
    ten_gods: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
    dynamic_context: Optional[str] = None,
    pattern_id: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    流式生成判词，逐 chunk 产出，供 UI 打字机展示。
    成功时 yield 内容片段；失败时抛出异常。
    """
    client = _get_ollama_client()
    if not client:
        raise RuntimeError("Ollama 未安装或不可用")
    cm = ConfigManager()
    ai_cfg = cm.get("ai_engine")
    model_name = model or (ai_cfg.get("chat_model") if isinstance(ai_cfg, dict) else None) or "qwen2.5:32b"
    ten_gods_summary = None
    if ten_gods:
        parts = [f"{k}={v}" for k, v in sorted(ten_gods.items(), key=lambda x: -abs(x[1] if isinstance(x[1], (int, float)) else 0))[:6]]
        ten_gods_summary = ", ".join(parts)
    user_prompt = _build_user_prompt(point=point, offset=offset, best_subpattern=best_subpattern, matrix_version=matrix_version, ten_gods_summary=ten_gods_summary, dynamic_context=dynamic_context)
    system_prompt = _get_system_prompt_for_pattern(pattern_id)
    stream = client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
        options={"num_predict": 400},
    )
    for chunk in stream:
        content = ""
        if isinstance(chunk, dict):
            content = (chunk.get("message") or {}).get("content", "") or ""
        elif hasattr(chunk, "message"):
            content = getattr(getattr(chunk, "message", None), "content", "") or ""
        if isinstance(content, str) and content:
            yield content


def is_ai_engine_available() -> bool:
    """检测本地 AI 引擎（Ollama）是否可用。"""
    client = _get_ollama_client()
    if not client:
        return False
    try:
        client.list()  # 简单列出模型即可验证连通
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 动态推演引擎 (026: 位移矢量 → 32B 微分诊断)
# ---------------------------------------------------------------------------

CONTEXT_TYPE_LABELS = {
    "liunian": "流年",
    "dayun": "大运",
    "geo": "地理方位",
}

SYSTEM_PROMPT_DYNAMIC_IMPACT = """你是「生命流形分析」的推演师。根据**原局 5D 坐标**与**位移矢量（delta_vector）**，给出该位移在现实中的物理含义与趋吉避凶建议。

## A-01 语义核心三维度（必须遵循）
- **O 轴（秩序）**：社会地位、克制力、法律边界。O 升=权柄巩固；O 降=秩序松动、易有是非。
- **E 轴（能量）**：身强/身弱、生命力。E 升=抗压增强；E 降=易疲惫、需借印比。
- **M 轴（财富）**：资源、物质。M 升=得财契机；M 降=宜守不宜攻。

## 位移解读规则
1. **S 轴（压力）**正向位移较大（如 +1.0 以上）：环境应力超过阈值 → 提示「结构性压力」或「逆境突围」可能，避免盲目扩张。
2. **S 轴**负向或 O 轴坍缩：秩序受损 → 提示收缩战线、稳固根基。
3. **M 轴**正向且 O 稳：财官相生 → 可简要提示机遇窗口。
4. 结合古典法理（伤官见官、财能生官等）用 1～3 句概括该时段格局健康度与建议。禁止绝对化结论，控制在 120 字以内。"""


def _build_dynamic_impact_prompt(
    base_point: Dict[str, float],
    delta_vector: Dict[str, float],
    context_type: str,
) -> str:
    """构建动态推演的用户 Prompt。"""
    # 推演后坐标 = 原局 + 位移
    dims = ["E", "O", "M", "S", "R"]
    projected = {
        k: base_point.get(k, 0.0) + delta_vector.get(k, 0.0)
        for k in dims
    }
    ctx_label = CONTEXT_TYPE_LABELS.get(context_type, context_type)
    return "\n".join([
        "请根据以下【原局坐标】与【位移矢量】给出推演解读：",
        "",
        "【原局 5D 坐标】",
        json.dumps(base_point, ensure_ascii=False, indent=2),
        "",
        "【位移矢量 delta】（正=该轴增强，负=减弱）",
        json.dumps(delta_vector, ensure_ascii=False, indent=2),
        "",
        "【推演后坐标】",
        json.dumps(projected, ensure_ascii=False, indent=2),
        "",
        f"【推演类型】{ctx_label}",
        "",
        "请直接给出 1～3 句专业判定与建议，不要前言与免责句。",
    ])


def simulate_dynamic_impact(
    base_point: Dict[str, float],
    delta_vector: Dict[str, float],
    context_type: str = "liunian",
    model: Optional[str] = None,
    timeout_sec: int = 45,
) -> Dict[str, Any]:
    """
    动态推演：根据原局 5D 点与位移矢量，让 32B 解释「位移」的现实含义。

    Args:
        base_point: 原局 5D 坐标 {"E", "O", "M", "S", "R"}
        delta_vector: 各轴位移量（如流年/大运/地理带来的增量）
        context_type: "liunian" | "dayun" | "geo"
        model: 模型名，默认从配置读取
        timeout_sec: 超时

    Returns:
        { "success", "text", "model", "error" }
    """
    result = {"success": False, "text": "", "model": "", "error": None}
    client = _get_ollama_client()
    if not client:
        result["error"] = "Ollama 未安装或不可用"
        return result

    cm = ConfigManager()
    ai_cfg = cm.get("ai_engine")
    model_name = model or (ai_cfg.get("chat_model") if isinstance(ai_cfg, dict) else None) or "qwen2.5:32b"

    user_prompt = _build_dynamic_impact_prompt(base_point, delta_vector, context_type)
    try:
        response = client.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_DYNAMIC_IMPACT},
                {"role": "user", "content": user_prompt},
            ],
            options={"num_predict": 300},
        )
        content = (
            response.get("message", {}).get("content")
            if isinstance(response, dict)
            else (getattr(response, "message", None) and getattr(response.message, "content", None))
        )
        if content and isinstance(content, str):
            result["success"] = True
            result["text"] = content.strip()
            result["model"] = model_name
        else:
            result["error"] = "模型返回内容为空"
    except Exception as e:
        logger.exception("动态推演 AI 调用失败")
        result["error"] = str(e)
    return result


def explain_classical_logic(
    classical_text: str,
    source: str = "古籍",
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    古籍逻辑溯源：用 32B 解释「为什么古人这么说」的物理逻辑。
    供 HKB 交互：点击古籍判词后弹出解析。

    Returns:
        { "success", "text", "model", "error" }
    """
    result = {"success": False, "text": "", "model": "", "error": None}
    client = _get_ollama_client()
    if not client:
        result["error"] = "Ollama 未安装或不可用"
        return result
    cm = ConfigManager()
    ai_cfg = cm.get("ai_engine")
    model_name = model or (ai_cfg.get("chat_model") if isinstance(ai_cfg, dict) else None) or "qwen2.5:32b"

    sys = "你是命理学与物理建模专家。用户会给出一段古籍中的判词。请用现代「物理/因果」语言解释：古人为何会得出这样的结论？背后的五行、十神、格局逻辑是什么？控制在 150 字以内，不要复读原文。"
    user = f"【出处】{source}\n【原文】\n{classical_text}\n\n请写出「物理逻辑解析」："
    try:
        response = client.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
            options={"num_predict": 280},
        )
        content = (
            response.get("message", {}).get("content")
            if isinstance(response, dict)
            else (getattr(response, "message", None) and getattr(response.message, "content", None))
        )
        if content and isinstance(content, str):
            result["success"] = True
            result["text"] = content.strip()
            result["model"] = model_name
        else:
            result["error"] = "模型返回内容为空"
    except Exception as e:
        logger.exception("古籍逻辑解析调用失败")
        result["error"] = str(e)
    return result


def generate_case_comparison_blurb(
    user_point: Dict[str, float],
    nearest_cases: List[Dict[str, Any]],
    model: Optional[str] = None,
    timeout_sec: int = 30,
) -> Dict[str, Any]:
    """
    全息相似案例对比：用 32B 生成一句「您与案例库中某类命例的物理流形相似度与共同点」。
    供 A-01 案例对撞机 UI 展示。

    Args:
        user_point: 当前用户 5D 坐标
        nearest_cases: find_nearest_cases 返回的列表，每项含 ref, subpattern, similarity_pct, point 等

    Returns:
        { "success", "text", "model", "error" }
    """
    result = {"success": False, "text": "", "model": "", "error": None}
    client = _get_ollama_client()
    if not client:
        result["error"] = "Ollama 未安装或不可用"
        return result
    if not nearest_cases:
        result["error"] = "无相似案例"
        return result

    cm = ConfigManager()
    ai_cfg = cm.get("ai_engine")
    model_name = model or (ai_cfg.get("chat_model") if isinstance(ai_cfg, dict) else None) or "qwen2.5:32b"

    sys = (
        "你是命理学与物理建模专家。用户会给出自己的 5D 命运流形坐标，以及案例库中与之最相似的若干案例（含相似度、子格局、案例编号）。"
        "请用 1～3 句话写出：用户与这些案例的「物理流形相似度」概括，以及主要共同点（例如 O 轴稳定、E 轴偏强等）。"
        "不要输出 JSON 或列表，直接给出一段连贯的中文段落，控制在 120 字以内。"
    )
    cases_desc = []
    for i, c in enumerate(nearest_cases[:3], 1):
        sim = c.get("similarity_pct", 0)
        sp = c.get("subpattern", "")
        ref = c.get("ref", "")
        pt = c.get("point", {})
        if isinstance(pt, dict):
            pt_str = json.dumps(pt, ensure_ascii=False)
        else:
            pt_str = str(pt)
        cases_desc.append(f"案例{i}：{ref}，子格局 {sp}，相似度 {sim}%，5D 坐标 {pt_str}")
    user = (
        "【当前用户 5D 坐标】\n"
        + json.dumps(user_point, ensure_ascii=False, indent=2)
        + "\n\n【最相似案例】\n"
        + "\n".join(cases_desc)
        + "\n\n请写出「同类项」对比文案："
    )
    try:
        response = client.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": user},
            ],
            options={"num_predict": 200},
        )
        content = (
            response.get("message", {}).get("content")
            if isinstance(response, dict)
            else (getattr(response, "message", None) and getattr(response.message, "content", None))
        )
        if content and isinstance(content, str):
            result["success"] = True
            result["text"] = content.strip()
            result["model"] = model_name
        else:
            result["error"] = "模型返回内容为空"
    except Exception as e:
        logger.exception("案例对比文案调用失败")
        result["error"] = str(e)
    return result


def generate_combined_pattern_verdict(
    probabilistic_patterns: List[Dict[str, Any]],
    point_5d: Dict[str, float],
    repair_vector: Optional[Dict[str, Any]] = None,
    ten_gods: Optional[Dict[str, float]] = None,
    dominant_pattern_id: Optional[str] = None,
    model: Optional[str] = None,
    timeout_sec: int = 90,
    debug_print_prompt: bool = False,
    prompt_only: bool = False,
) -> Dict[str, Any]:
    """
    B 计划：混合格局语义调用链闭环。根据对撞结果、5D 坐标与 ΔV 修复向量，
    调用 32B 生成混合格局下的综合判词（大白话 + 五行药方 + 物理依据）。
    若提供 ten_gods 与主格局，将自动注入喜忌神审计结果。
    prompt_only=True 时仅组装并打印 Prompt，不调用 Ollama（用于法理验证）。
    """
    result = {"success": False, "text": "", "model": "", "error": None}
    if not prompt_only:
        client = _get_ollama_client()
        if not client:
            result["error"] = "Ollama 未安装或不可用"
            return result
    system, user_template = _load_combined_pattern_yaml()
    if not system or not user_template:
        result["error"] = "混合格局模板加载失败"
        return result
    mixed_ratio = "；".join(
        f"{p.get('pattern_id', '')} {p.get('confidence_pct', 0):.0f}%"
        for p in (probabilistic_patterns or [])[:5]
    ) or "无"
    hkb_semantic_block = _build_hkb_semantic_block(probabilistic_patterns or [], max_patterns=5)
    delta_v_repair = "无"
    if repair_vector and isinstance(repair_vector.get("delta_vector"), dict):
        dv = repair_vector["delta_vector"]
        delta_v_repair = "；".join(f"Δ{k}={v}" for k, v in (dv or {}).items())
    point_5d = point_5d or {}
    dominant = dominant_pattern_id or (
        (probabilistic_patterns or [])[0].get("pattern_id") if probabilistic_patterns else None
    )
    balance_audit_text = ""
    if ten_gods and dominant and point_5d:
        try:
            audit = run_balance_audit(point_5d, ten_gods, dominant)
            balance_audit_text = _format_balance_audit_for_prompt(audit)
        except Exception as e:
            logger.debug("喜忌神审计未执行或失败: %s", e)
    user_content = _fill_combined_user_prompt(
        user_template, mixed_ratio, hkb_semantic_block, point_5d, delta_v_repair, balance_audit_text,
    )
    user_content += "\n\n【强制要求】判词须按「核心建议 → 运势细分（事业/财富/感情大白话）→ 五行调理 → 物理依据」结构输出；物理依据可放在最后并标注为学术参考，正文勿直接写 E=、R= 等数值。"
    if debug_print_prompt:
        print("=== 混合格局判词 Prompt（动态格局列表）===")
        print("--- SYSTEM ---")
        print(system)
        print("--- USER ---")
        print(user_content)
        print("=== END ===")
    if prompt_only:
        result["success"] = True
        result["text"] = "(prompt_only，未调用模型)"
        return result
    cm = ConfigManager()
    ai_cfg = cm.get("ai_engine")
    model_name = model or (ai_cfg.get("chat_model") if isinstance(ai_cfg, dict) else None) or "qwen2.5:32b"
    try:
        response = client.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            options={"num_predict": 450},
        )
        content = (
            response.get("message", {}).get("content")
            if isinstance(response, dict)
            else (getattr(response, "message", None) and getattr(response.message, "content", None))
        )
        if content and isinstance(content, str):
            result["success"] = True
            result["text"] = content.strip()
            result["model"] = model_name
        else:
            result["error"] = "模型返回内容为空"
    except Exception as e:
        logger.exception("混合格局判词调用失败")
        result["error"] = str(e)
    return result


def stream_combined_pattern_verdict(
    probabilistic_patterns: List[Dict[str, Any]],
    point_5d: Dict[str, float],
    repair_vector: Optional[Dict[str, Any]] = None,
    ten_gods: Optional[Dict[str, float]] = None,
    dominant_pattern_id: Optional[str] = None,
    model: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    流式生成混合格局判词，逐 chunk 产出，供 UI 打字机展示。
    若提供 ten_gods 与主格局，将自动注入喜忌神审计结果。
    """
    client = _get_ollama_client()
    if not client:
        raise RuntimeError("Ollama 未安装或不可用")
    system, user_template = _load_combined_pattern_yaml()
    if not system or not user_template:
        raise RuntimeError("混合格局模板加载失败")
    mixed_ratio = "；".join(
        f"{p.get('pattern_id', '')} {p.get('confidence_pct', 0):.0f}%"
        for p in (probabilistic_patterns or [])[:5]
    ) or "无"
    hkb_semantic_block = _build_hkb_semantic_block(probabilistic_patterns or [], max_patterns=5)
    delta_v_repair = "无"
    if repair_vector and isinstance(repair_vector.get("delta_vector"), dict):
        dv = repair_vector["delta_vector"]
        delta_v_repair = "；".join(f"Δ{k}={v}" for k, v in (dv or {}).items())
    point_5d = point_5d or {}
    dominant = dominant_pattern_id or (
        (probabilistic_patterns or [])[0].get("pattern_id") if probabilistic_patterns else None
    )
    balance_audit_text = ""
    if ten_gods and dominant and point_5d:
        try:
            audit = run_balance_audit(point_5d, ten_gods, dominant)
            balance_audit_text = _format_balance_audit_for_prompt(audit)
        except Exception as e:
            logger.debug("喜忌神审计未执行或失败: %s", e)
    user_content = _fill_combined_user_prompt(
        user_template, mixed_ratio, hkb_semantic_block, point_5d, delta_v_repair, balance_audit_text,
    )
    user_content += "\n\n【强制要求】判词须按「核心建议 → 运势细分（事业/财富/感情大白话）→ 五行调理 → 物理依据」结构输出；正文勿直接写 E=、R= 等数值。"
    cm = ConfigManager()
    ai_cfg = cm.get("ai_engine")
    model_name = model or (ai_cfg.get("chat_model") if isinstance(ai_cfg, dict) else None) or "qwen2.5:32b"
    stream = client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        stream=True,
        options={"num_predict": 450},
    )
    for chunk in stream:
        content = ""
        try:
            if isinstance(chunk, dict):
                msg = chunk.get("message") or chunk
                content = (msg.get("content") if isinstance(msg, dict) else "") or ""
            elif hasattr(chunk, "message"):
                msg = getattr(chunk, "message", None)
                content = getattr(msg, "content", "") or "" if msg else ""
        except Exception:
            content = ""
        if isinstance(content, str) and content:
            yield content


def generate_repair_strategy(
    deficit_axis: str,
    target_vector: Dict[str, float],
    user_point: Optional[Dict[str, float]] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    第 029 号：流形修复建议。将物理位移 ΔV 翻译为现实行为指引。
    例如：补齐 O 轴 → 加强职业合规、地理向西、色彩白色、心态契约导向。

    Args:
        deficit_axis: 瓶颈轴（E/O/M/S/R）
        target_vector: 建议位移矢量，如 {"E":0,"O":0.8,"M":0,"S":0,"R":0}
        user_point: 可选，当前 5D 供上下文

    Returns:
        { "success", "text", "model", "error" }
    """
    result = {"success": False, "text": "", "model": "", "error": None}
    client = _get_ollama_client()
    if not client:
        result["error"] = "Ollama 未安装或不可用"
        return result

    cm = ConfigManager()
    ai_cfg = cm.get("ai_engine")
    model_name = model or (ai_cfg.get("chat_model") if isinstance(ai_cfg, dict) else None) or "qwen2.5:32b"

    axis_names = {"E": "能量轴", "O": "秩序轴", "M": "财富轴", "S": "压力轴", "R": "关系轴"}
    axis_label = axis_names.get(deficit_axis, deficit_axis)

    sys_prompt = (
        "你是命理学与物理建模专家。用户给出了「流形修复」的物理目标：在某一 5D 轴上需要补齐的位移量。"
        "请将该物理位移翻译为**可执行的现实行为建议**，包括但不限于："
        "地理方位（如向西、北方）、色彩/五行对应、心态取向（如契约导向、合规意识）、职业或生活习惯建议。"
        "控制在 150 字以内，不要输出 JSON 或列表，直接给出一段连贯的中文导航文案。"
    )
    user_prompt = (
        f"【瓶颈轴】{axis_label} ({deficit_axis})\n"
        f"【建议位移矢量 ΔV】{json.dumps(target_vector, ensure_ascii=False)}\n"
    )
    if user_point:
        user_prompt += f"【当前 5D 坐标】{json.dumps(user_point, ensure_ascii=False)}\n"
    user_prompt += "\n请写出「流形修复」行为导航建议："

    try:
        response = client.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"num_predict": 280},
        )
        content = (
            response.get("message", {}).get("content")
            if isinstance(response, dict)
            else (getattr(response, "message", None) and getattr(response.message, "content", None))
        )
        if content and isinstance(content, str):
            result["success"] = True
            result["text"] = content.strip()
            result["model"] = model_name
        else:
            result["error"] = "模型返回内容为空"
    except Exception as e:
        logger.exception("流形修复建议调用失败")
        result["error"] = str(e)
    return result


def generate_pattern_overview(
    pattern_id: str,
    detail: Dict[str, Any],
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    根据格局详情调用大模型生成「格局解读」短文，用于已审计格局的语义展示。
    """
    result = {"success": False, "text": "", "model": "", "error": None}
    client = _get_ollama_client()
    if not client:
        result["error"] = "Ollama 未安装或不可用"
        return result
    cm = ConfigManager()
    ai_cfg = cm.get("ai_engine")
    model_name = model or (ai_cfg.get("chat_model") if isinstance(ai_cfg, dict) else None) or "qwen2.5:32b"
    meta = detail.get("meta_info") or {}
    rules = detail.get("classical_logic_rules") or {}
    subs = detail.get("sub_pattern_definitions") or []
    semantic = detail.get("semantic_core_dimensions") or {}
    strong = detail.get("strong_correlation") or []
    sys_prompt = (
        "你是命理学与 FDS 流形体系的解读师。请根据给出的格局结构化信息，"
        "用 200 字以内写一段「格局解读」：概括该格局的古典含义、物理映射要点、子格局关系，"
        "语言简洁、避免绝对化结论。直接输出一段连贯中文，不要 JSON 或列表。"
    )
    user_prompt = (
        f"【格局】{detail.get('pattern_id', '')} {meta.get('chinese_name') or meta.get('display_name', '')}\n"
        f"【古典逻辑描述】{rules.get('description', '')}\n"
        f"【子格局】{json.dumps([s.get('name') for s in subs], ensure_ascii=False)}\n"
        f"【语义核心维度】{json.dumps(semantic, ensure_ascii=False, indent=0)}\n"
        f"【强相关轴】{json.dumps(strong, ensure_ascii=False)}\n"
        "请写出格局解读："
    )
    try:
        response = client.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"num_predict": 400},
        )
        content = (
            response.get("message", {}).get("content")
            if isinstance(response, dict)
            else (getattr(response, "message", None) and getattr(response.message, "content", None))
        )
        if content and isinstance(content, str):
            result["success"] = True
            result["text"] = content.strip()
            result["model"] = model_name
        else:
            result["error"] = "模型返回内容为空"
    except Exception as e:
        logger.exception("格局解读生成失败")
        result["error"] = str(e)
    return result


__all__ = [
    "generate_manifold_interpretation",
    "stream_manifold_interpretation",
    "is_ai_engine_available",
    "simulate_dynamic_impact",
    "explain_classical_logic",
    "generate_case_comparison_blurb",
    "generate_repair_strategy",
    "generate_pattern_overview",
    "generate_combined_pattern_verdict",
    "stream_combined_pattern_verdict",
    "AXIS_SEMANTICS",
    "SYSTEM_PROMPT_5D",
]
