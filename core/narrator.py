"""
命运叙事生成器 (Fate Narrator)
将5维张量数据翻译为人类可读的洞察报告

基于LLM生成《经济学人》风格的评语
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.models.llm_semantic_synthesizer import LLMSemanticSynthesizer
from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# 全局LLM合成器实例（延迟初始化）
_llm_synthesizer: Optional[LLMSemanticSynthesizer] = None


def _get_llm_synthesizer() -> Optional[LLMSemanticSynthesizer]:
    """获取或创建LLM合成器（延迟初始化）"""
    global _llm_synthesizer
    if _llm_synthesizer is None:
        try:
            _llm_synthesizer = LLMSemanticSynthesizer()
            # 测试连接
            if _llm_synthesizer.use_llm:
                logger.info("✅ LLM叙事生成器已初始化")
            else:
                logger.warning("⚠️ LLM不可用，将使用规则生成")
        except Exception as e:
            logger.warning(f"⚠️ LLM初始化失败: {e}，将使用规则生成")
            _llm_synthesizer = None
    return _llm_synthesizer


def generate_holographic_report(
    tensor_data: Dict[str, Any],
    pattern_name: str = "A-03",
    pattern_state: str = "STABLE",
    use_llm: bool = True
) -> str:
    """
    生成全息格局报告（基于5维张量数据）
    
    Args:
        tensor_data: 包含投影数据的字典，应包含：
            - projection: {'E': float, 'O': float, 'M': float, 'S': float, 'R': float}
            - alpha: float (可选)
            - pattern_state: dict (可选)
        pattern_name: 格局名称（如'A-03'）
        pattern_state: 格局状态（'STABLE', 'CRYSTALLIZED', 'COLLAPSED', 'MUTATED'）
        
    Returns:
        生成的叙事文本
    """
    # 尝试使用LLM生成
    if use_llm:
        llm_synthesizer = _get_llm_synthesizer()
        if llm_synthesizer and llm_synthesizer.use_llm:
            logger.info("🔮 尝试使用LLM生成叙事报告...")
            try:
                result = _generate_with_llm(tensor_data, pattern_name, pattern_state, llm_synthesizer)
                if result:
                    return result
                else:
                    logger.warning("⚠️ LLM返回空结果，回退到规则生成")
            except Exception as e:
                logger.warning(f"⚠️ LLM生成失败，回退到规则生成: {e}", exc_info=True)
        else:
            logger.warning(f"⚠️ LLM不可用: synthesizer={llm_synthesizer is not None}, use_llm={llm_synthesizer.use_llm if llm_synthesizer else 'N/A'}")
    
    # 回退到规则生成
    logger.info("📝 使用规则生成叙事报告")
    return _generate_with_rules(tensor_data, pattern_name, pattern_state)


def _generate_with_llm(
    tensor_data: Dict[str, Any],
    pattern_name: str,
    pattern_state: str,
    llm_synthesizer: LLMSemanticSynthesizer
) -> str:
    """使用LLM生成叙事报告"""
    projection = tensor_data.get('projection', {})
    E = projection.get('E', 0.0)
    O = projection.get('O', 0.0)
    M = projection.get('M', 0.0)
    S = projection.get('S', 0.0)
    R = projection.get('R', 0.0)
    alpha = tensor_data.get('alpha', 1.0)
    
    # 构建LLM Prompt
    prompt = f"""作为量子命运物理学家，分析以下5维命运张量数据。

[物理遥测数据]
- 能级轴 (E): {E:.4f} (生命力和抗压底气)
- 秩序轴 (O): {O:.4f} (社会地位和权力)
- 物质轴 (M): {M:.4f} (财富和资产)
- 应力轴 (S): {S:.4f} (系统摩擦和风险)
- 关联轴 (R): {R:.4f} (人际关系网络)
- 结构完整性 (Alpha): {alpha:.4f}
- 当前状态: {pattern_state}
- 格局: {pattern_name}

[分析指南]
1. 如果状态是'CRYSTALLIZED'：描述这是一个高度凝聚的瞬间，混沌转化为秩序。
2. 如果状态是'COLLAPSED'：描述结构崩塌，权柄（O）被应力（S）吞噬。
3. 如果O高但M低（典型{pattern_name}特征）：解释为什么有权力但财富有限（重名轻利）。
4. 如果S为负：解释这是"负压吸积"的奇迹，高压被完美转化。
5. 语调：专业、深刻，略带科幻感（如《经济学人》遇见《星际穿越》）。
6. 长度：简洁（150字以内）。

[格式要求]
- 必须使用Markdown格式
- 使用换行符分隔段落（每个段落之间用两个换行符）
- 使用---作为水平分隔线
- 使用**加粗**标记重要概念
- 使用##作为小标题

请生成分析报告，确保使用正确的Markdown格式和换行符。"""
    
    try:
        # 调用LLM（使用ollama客户端）
        if hasattr(llm_synthesizer, '_llm_client') and llm_synthesizer._llm_client:
            client = llm_synthesizer._llm_client
            
            logger.info(f"🔮 调用LLM生成叙事报告 (模型: {llm_synthesizer.model_name})")
            
            response = client.generate(
                model=llm_synthesizer.model_name,
                prompt=prompt,
                stream=False,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 500
                }
            )
            
            logger.debug(f"LLM响应类型: {type(response)}")
            logger.debug(f"LLM响应内容: {response}")
            
            # 提取响应文本（ollama返回的是生成器或字典）
            narrative = None
            if isinstance(response, dict):
                # ollama返回字典格式
                narrative = response.get('response', '') or response.get('text', '') or response.get('content', '')
            elif hasattr(response, 'response'):
                # ollama返回对象格式
                narrative = response.response
            elif hasattr(response, '__iter__') and not isinstance(response, str):
                # ollama可能返回生成器（stream=False时也可能）
                try:
                    # 尝试获取第一个元素
                    first_chunk = next(iter(response))
                    if isinstance(first_chunk, dict):
                        narrative = first_chunk.get('response', '') or first_chunk.get('text', '')
                    else:
                        narrative = str(first_chunk)
                except StopIteration:
                    narrative = None
            else:
                narrative = str(response)
            
            if narrative and len(narrative.strip()) > 10:
                logger.info("✅ 使用LLM生成叙事报告成功")
                # 确保换行符被保留（Markdown格式需要）
                # 清理文本，但保留换行符和Markdown格式
                cleaned_narrative = narrative.strip()
                
                # 确保Markdown格式的换行被保留
                import re
                # 保留Markdown格式的换行（---、##等）
                # 将多个连续换行符合并为两个（标准Markdown段落分隔）
                cleaned_narrative = re.sub(r'\n{3,}', '\n\n', cleaned_narrative)
                
                # 确保水平线前后有换行符（Markdown要求）
                cleaned_narrative = re.sub(r'([^\n])---([^\n])', r'\1\n---\n\2', cleaned_narrative)
                cleaned_narrative = re.sub(r'^---([^\n])', r'---\n\1', cleaned_narrative)
                cleaned_narrative = re.sub(r'([^\n])---$', r'\1\n---', cleaned_narrative)
                
                logger.debug(f"清理后的文本长度: {len(cleaned_narrative)}, 换行符数量: {cleaned_narrative.count(chr(10))}")
                return cleaned_narrative
            else:
                logger.warning(f"⚠️ LLM响应为空或过短: {narrative}")
    except Exception as e:
        logger.error(f"❌ LLM调用失败: {e}", exc_info=True)
    
    # 如果LLM失败，回退到规则生成
    return _generate_with_rules(tensor_data, pattern_name, pattern_state)


def _generate_with_rules(
    tensor_data: Dict[str, Any],
    pattern_name: str,
    pattern_state: str
) -> str:
    """使用规则引擎生成叙事报告（回退方案）"""
    # 提取5维数据
    projection = tensor_data.get('projection', {})
    E = projection.get('E', 0.0)
    O = projection.get('O', 0.0)
    M = projection.get('M', 0.0)
    S = projection.get('S', 0.0)
    R = projection.get('R', 0.0)
    
    alpha = tensor_data.get('alpha', 1.0)
    
    # 构建物理定义映射
    pattern_definitions = {
        'A-03': {
            'name': '羊刃架杀',
            'description': '受控核聚变状态：高能等离子体（羊刃）被强磁场（七杀）完美约束，产生巨大的定向做功（贵气）',
            'typical_profile': 'O高M低，重名轻利，权力欲强但财富积累有限'
        }
    }
    
    pattern_info = pattern_definitions.get(pattern_name, {
        'name': pattern_name,
        'description': '格局分析',
        'typical_profile': '标准格局'
    })
    
    report_parts = []
    
    # 1. 状态描述
    if pattern_state == 'CRYSTALLIZED':
        report_parts.append(f"**💎 成格时刻**：这是一个结构高度凝聚的瞬间。{pattern_info['name']}的能量场达到了临界点，混沌转化为秩序。")
    elif pattern_state == 'COLLAPSED':
        report_parts.append(f"**⚡ 结构崩塌**：系统的完整性（Alpha={alpha:.2f}）已跌破阈值。权柄（O={O:.2f}）正在被应力（S={S:.2f}）吞噬。")
    elif pattern_state == 'MUTATED':
        report_parts.append(f"**🔮 相变发生**：格局发生了质的跃迁，原有的物理定律不再适用。")
    else:
        report_parts.append(f"**🟢 稳定态**：{pattern_info['name']}的能量场保持平衡。")
    
    report_parts.append("")
    
    # 2. 五维分析
    report_parts.append("**五维张量分析**：")
    
    # E轴（能级/寿命）
    if E > 0.7:
        e_desc = f"能级轴（E={E:.2f}）极高，代表强大的生命力和抗压底气。这是一个'巨大行星'级别的存在质量。"
    elif E > 0.4:
        e_desc = f"能级轴（E={E:.2f}）中等，系统具备基本的自愈能力。"
    else:
        e_desc = f"能级轴（E={E:.2f}）较低，系统脆弱，需要外部支撑。"
    report_parts.append(f"- {e_desc}")
    
    # O轴（秩序/权力）
    if O > 0.7:
        o_desc = f"秩序轴（O={O:.2f}）极高，你悬浮在'平流层'。这是权力的高度，但也意味着孤独。"
    elif O > 0.4:
        o_desc = f"秩序轴（O={O:.2f}）中等，处于社会结构的中层。"
    else:
        o_desc = f"秩序轴（O={O:.2f}）较低，'贴地飞行'。权力结构薄弱。"
    report_parts.append(f"- {o_desc}")
    
    # M轴（物质/财富）
    if M > 0.7:
        m_desc = f"物质轴（M={M:.2f}）极高，资产雄厚，'飞碟'般的横向展开。"
    elif M > 0.4:
        m_desc = f"物质轴（M={M:.2f}）中等，财富积累稳定。"
    elif M < 0:
        m_desc = f"物质轴（M={M:.2f}）为负，这是'重名轻利'的典型特征。能量流向了权力（O）而非财富（M）。"
    else:
        m_desc = f"物质轴（M={M:.2f}）较低，财富积累有限。"
    report_parts.append(f"- {m_desc}")
    
    # S轴（应力/灾难）
    if S > 0.7:
        s_desc = f"应力轴（S={S:.2f}）极高，系统处于'极热'状态。这是高压对抗的临界点，需要谨慎。"
    elif S > 0.4:
        s_desc = f"应力轴（S={S:.2f}）较高，存在一定的结构风险。"
    elif S < 0:
        s_desc = f"应力轴（S={S:.2f}）为负，这是'负压吸积'的奇迹。高压被完美转化，结构稳定。"
    else:
        s_desc = f"应力轴（S={S:.2f}）较低，系统'凉爽'，风险可控。"
    report_parts.append(f"- {s_desc}")
    
    # R轴（关联/人脉）
    if R > 0.7:
        r_desc = f"关联轴（R={R:.2f}）极高，人脉网络如球体般饱满。"
    elif R > 0.4:
        r_desc = f"关联轴（R={R:.2f}）中等，人际关系稳定。"
    else:
        r_desc = f"关联轴（R={R:.2f}）较低，社交网络单薄，如纸片般孤立。"
    report_parts.append(f"- {r_desc}")
    
    report_parts.append("")
    
    # 3. 形态识别
    if O > 0.7 and M < 0.3:
        shape_desc = "**形态特征**：这是一把'方尖碑/利剑'。权力（O）极高但财富（M）极低，典型的'重名轻利'格局。能量全部流向了秩序轴，而非物质轴。"
    elif M > 0.7 and O < 0.3:
        shape_desc = "**形态特征**：这是一个'飞碟/巨盘'。财富（M）雄厚但权力（O）有限，典型的'富而不贵'格局。"
    elif R > 0.7:
        shape_desc = "**形态特征**：这是一个'球体'。人脉（R）极广，社交网络饱满。"
    else:
        shape_desc = "**形态特征**：这是一个'不规则体'。五维能量分布不均衡，系统形态复杂。"
    report_parts.append(shape_desc)
    
    report_parts.append("")
    
    # 4. 物理解读
    if pattern_name == 'A-03':
        if O > 0.6 and S < 0.2:
            physics_desc = "**物理解读**：这是'羊刃架杀'的完美状态。高能等离子体（羊刃）被强磁场（七杀）完美约束，产生了巨大的定向做功（贵气）。虽然内部压力巨大，但因为结构完整（Alpha高），外部表现出的风险（S）反而低于常人。这就是'屏蔽痛苦'的数学证明。"
        elif O > 0.6 and S > 0.4:
            physics_desc = "**物理解读**：这是'羊刃架杀'的高压状态。能量转化效率高（O高），但结构风险（S高）也在累积。需要警惕'冲刃'事件，可能导致结构崩塌。"
        else:
            physics_desc = "**物理解读**：当前状态偏离了'羊刃架杀'的标准形态。可能是未入格，或正在经历相变。"
    else:
        physics_desc = f"**物理解读**：当前格局为{pattern_info['name']}。五维能量分布反映了该格局的典型特征。"
    
    report_parts.append(physics_desc)
    
    report_parts.append("")
    
    # 5. 总结
    if pattern_state == 'CRYSTALLIZED':
        conclusion = "**结论**：这是一个成格的瞬间。系统达到了高度凝聚的状态，能量被高效转化为权柄。"
    elif pattern_state == 'COLLAPSED':
        conclusion = f"**结论**：结构已崩塌。Alpha={alpha:.2f}低于阈值，系统失去了完整性。需要修复或等待重建。"
    elif O > 0.7 and M < 0:
        conclusion = "**结论**：'富豪榜上无羊刃，将军冢前多黄金'。这是权力的代价。能量流向了秩序（O），而非物质（M）。"
    else:
        conclusion = "**结论**：系统处于稳定态。五维能量分布反映了当前格局的物理特征。"
    
    report_parts.append(conclusion)
    
    return "\n".join(report_parts)


def generate_timeline_insight(
    timeline_data: List[Dict[str, Any]],
    pattern_name: str = "A-03"
) -> str:
    """
    生成时间轴洞察（基于12年轨迹）
    
    Args:
        timeline_data: 时间序列数据列表
        pattern_name: 格局名称
        
    Returns:
        生成的洞察文本
    """
    if not timeline_data:
        return "无时间序列数据。"
    
    # 分析趋势
    o_values = [d.get('projection', {}).get('O', 0.0) for d in timeline_data]
    s_values = [d.get('projection', {}).get('S', 0.0) for d in timeline_data]
    alphas = [d.get('alpha', 1.0) for d in timeline_data]
    
    o_avg = sum(o_values) / len(o_values) if o_values else 0.0
    s_avg = sum(s_values) / len(s_values) if s_values else 0.0
    alpha_avg = sum(alphas) / len(alphas) if alphas else 1.0
    
    # 检测关键事件
    critical_events = []
    for d in timeline_data:
        state = d.get('pattern_state', {}).get('state', 'STABLE')
        if state in ['COLLAPSED', 'CRYSTALLIZED', 'MUTATED']:
            critical_events.append({
                'year': d.get('year', 0),
                'state': state,
                'trigger': d.get('pattern_state', {}).get('trigger', 'N/A')
            })
    
    insight_parts = []
    insight_parts.append("**12年轨迹洞察**：")
    insight_parts.append("")
    
    # 趋势分析
    if o_avg > 0.6:
        insight_parts.append(f"- **权力高度**：平均秩序轴（O）为{o_avg:.2f}，你在这12年中始终悬浮在'平流层'。这是{pattern_name}的典型特征。")
    else:
        insight_parts.append(f"- **权力高度**：平均秩序轴（O）为{o_avg:.2f}，处于中低空。")
    
    if s_avg > 0.4:
        insight_parts.append(f"- **风险水平**：平均应力轴（S）为{s_avg:.2f}，系统持续处于高压状态。需要警惕结构风险。")
    else:
        insight_parts.append(f"- **风险水平**：平均应力轴（S）为{s_avg:.2f}，系统相对稳定。")
    
    if alpha_avg < 0.5:
        insight_parts.append(f"- **结构完整性**：平均Alpha为{alpha_avg:.2f}，系统结构脆弱，存在崩塌风险。")
    else:
        insight_parts.append(f"- **结构完整性**：平均Alpha为{alpha_avg:.2f}，系统结构稳定。")
    
    insight_parts.append("")
    
    # 关键事件
    if critical_events:
        insight_parts.append("**关键相变事件**：")
        for event in critical_events:
            year = event['year']
            state = event['state']
            trigger = event['trigger']
            
            if state == 'COLLAPSED':
                insight_parts.append(f"- {year}年：结构崩塌（触发：{trigger}）。系统完整性下降，权柄流失。")
            elif state == 'CRYSTALLIZED':
                insight_parts.append(f"- {year}年：成格瞬间（触发：{trigger}）。混沌转化为秩序，能量高效转化。")
            elif state == 'MUTATED':
                insight_parts.append(f"- {year}年：相变发生（触发：{trigger}）。格局发生质的跃迁。")
    else:
        insight_parts.append("**关键相变事件**：无重大相变，系统保持稳定。")
    
    return "\n".join(insight_parts)

