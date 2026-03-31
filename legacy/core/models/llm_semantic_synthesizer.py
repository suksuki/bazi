"""
LLM语义合成器 (LLM Semantic Synthesizer)
基于格局语义池，使用LLM生成全息命运画像
支持Qwen2.5:2.5b及未来70B模型
[QGA V24.3] 从系统配置读取LLM模型名称
[QGA V24.7] 集成LLM逻辑网关中间件和格局引擎注册机制
"""

import logging
from typing import Dict, List, Optional, Any
import json

from core.models.pattern_semantic_pool import get_multiple_pattern_semantics
from core.config_manager import ConfigManager
from utils.llm_parser import LLMParser  # [QGA V24.7] LLM逻辑网关
from core.models.pattern_engine import get_pattern_registry  # [QGA V24.7] 格局引擎注册表

logger = logging.getLogger(__name__)


class LLMSemanticSynthesizer:
    """
    LLM语义合成器
    基于格局语义池，使用LLM生成全息命运画像
    [QGA V24.3] 从系统配置读取LLM模型名称
    """
    
    def __init__(self, model_name: Optional[str] = None, use_llm: bool = True):
        """
        初始化LLM合成器
        
        Args:
            model_name: LLM模型名称（如果为None，则从系统配置读取）
            use_llm: 是否使用LLM（如果False，则使用规则生成）
        """
        # [QGA V24.3] 从系统配置读取LLM模型名称
        if model_name is None:
            config_manager = ConfigManager()
            model_name = config_manager.get("selected_model_name")
            if not model_name:
                # 如果配置中没有，使用默认值（注意：实际应该使用配置中的值）
                model_name = "qwen2.5:2.5b"
                logger.warning(f"系统配置中未找到LLM模型名称，使用默认值: {model_name}。请在系统配置页面设置selected_model_name")
            else:
                logger.info(f"✅ 从系统配置读取LLM模型名称: {model_name}")
        
        self.model_name = model_name
        self.use_llm = use_llm
        self._llm_client = None
        self._ollama_host = None
        
        if use_llm:
            self._init_llm_client()
    
    def _init_llm_client(self):
        """初始化LLM客户端（支持ollama）"""
        try:
            import ollama
            
            # [QGA V24.3] 从系统配置读取ollama_host
            config_manager = ConfigManager()
            ollama_host = config_manager.get("ollama_host", "http://localhost:11434")
            self._ollama_host = ollama_host
            
            # 创建ollama客户端
            if ollama_host and ollama_host != "http://localhost:11434":
                self._llm_client = ollama.Client(host=ollama_host)
            else:
                # 使用默认host
                self._llm_client = ollama.Client()
            
            # [QGA V24.3] 动态测试LLM连接（不阻塞，即使失败也继续）
            try:
                self._test_llm_connection()
            except Exception as e:
                logger.warning(f"LLM连接测试失败: {e}，但继续使用LLM")
                self._connection_status = f"连接测试失败: {str(e)}"
            
            logger.info(f"LLM客户端初始化成功: {self.model_name} (host: {ollama_host})")
        except ImportError:
            logger.warning("ollama未安装，将使用规则生成")
            self.use_llm = False
            self._llm_client = None
            self._connection_status = "未安装ollama"
        except Exception as e:
            logger.warning(f"LLM客户端初始化失败: {e}，将使用规则生成")
            self.use_llm = False
            self._llm_client = None
            self._connection_status = f"连接失败: {str(e)}"
    
    def _test_llm_connection(self):
        """
        测试LLM连接
        返回连接状态信息
        """
        self._connection_status = "未知"
        self._connection_error = None
        
        # 检查ollama是否可用
        try:
            import ollama
        except ImportError:
            self._connection_status = "未安装ollama"
            return
        
        try:
            # 使用已创建的客户端
            client = self._llm_client
            
            # 测试：发送一个简单的请求（使用stream=False快速测试）
            response = client.generate(
                model=self.model_name,
                prompt="测试",
                stream=False,
                options={'num_predict': 5}  # 只生成5个token，快速测试
            )
            
            # 如果成功，检查响应
            if response and (hasattr(response, 'response') or isinstance(response, dict)):
                self._connection_status = "连接正常"
                logger.info(f"✅ LLM连接测试成功: {self.model_name}")
            else:
                self._connection_status = "连接异常（无响应）"
                self.use_llm = False
                
        except Exception as e:
            self._connection_status = f"连接失败"
            self._connection_error = str(e)
            self.use_llm = False
            logger.warning(f"❌ LLM连接测试失败: {e}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        获取LLM连接信息
        
        Returns:
            包含模型名称、host、连接状态的字典
        """
        return {
            'model_name': self.model_name,
            'ollama_host': self._ollama_host,
            'connection_status': getattr(self, '_connection_status', '未初始化'),
            'connection_error': getattr(self, '_connection_error', None),
            'use_llm': self.use_llm
        }
    
    def synthesize_persona(self, active_patterns: List[Dict], 
                           synthesized_field: Dict,
                           profile_name: str = "此人",
                           day_master: str = None,
                           force_vectors: Dict = None,
                           year: int = None,
                           luck_pillar: str = None,
                           year_pillar: str = None,
                           geo_info: str = None) -> Dict[str, Any]:
        """
        合成全息命运画像
        [QGA V24.4] 使用结构化JSON数据协议
        
        Args:
            active_patterns: 激活的格局列表
            synthesized_field: 合成场强信息
            profile_name: 档案名称
            day_master: 日主（如"丁火"）
            force_vectors: 五行能量分布
            year: 流年
            luck_pillar: 大运
            year_pillar: 流年柱
            geo_info: 地理信息
            
        Returns:
            包含persona和element_calibration的字典
        """
        if not active_patterns:
            return {
                'persona': f"{profile_name}的命局相对平稳，无明显特殊格局。",
                'element_calibration': None,
                'debug_data': None
            }
        
        # [QGA V24.7] 处理active_patterns（可能是包装字典）
        patterns_list = active_patterns
        base_vector_bias = None
        geo_context_from_patterns = None
        
        if isinstance(active_patterns, dict) and 'patterns_list' in active_patterns:
            # 提取patterns列表和元数据
            patterns_list = active_patterns.get('patterns_list', [])
            base_vector_bias = active_patterns.get('base_vector_bias')
            geo_context_from_patterns = active_patterns.get('geo_context', '')
            logger.debug(f"✅ 提取patterns列表: {len(patterns_list)}个格局, base_vector_bias={base_vector_bias is not None}")
        elif isinstance(active_patterns, list):
            # 如果是列表，直接使用
            patterns_list = active_patterns
            logger.debug(f"✅ 直接使用patterns列表: {len(patterns_list)}个格局")
        
        # [QGA V24.4] 构建结构化JSON数据
        structured_data = self._build_structured_data(
            patterns_list, synthesized_field, profile_name,
            day_master, force_vectors, year, luck_pillar, year_pillar, geo_info
        )
        
        # [QGA V24.7] 如果有base_vector_bias，添加到structured_data中作为"底色"
        if base_vector_bias:
            structured_data['BaseVectorBias'] = base_vector_bias
            logger.debug(f"✅ 添加BaseVectorBias到structured_data: {base_vector_bias}")
        
        # [QGA V24.4] 始终构建结构化数据，无论是否使用LLM
        # 这样即使LLM失败，也能看到发送的数据
        
        # 检查LLM客户端是否可用
        llm_available = self.use_llm and self._llm_client is not None
        if not llm_available and self.use_llm:
            logger.warning(f"LLM开关已启用，但客户端不可用: use_llm={self.use_llm}, _llm_client={self._llm_client}")
        
        if llm_available:
            # 使用LLM生成（结构化协议）
            try:
                result = self._llm_synthesize_structured(structured_data, profile_name)
                # 确保debug_data存在
                if 'debug_data' not in result:
                    result['debug_data'] = structured_data
                return result
            except Exception as e:
                logger.error(f"LLM结构化合成失败: {e}，回退到规则生成")
                # 即使失败，也返回debug_data
                pattern_names = [p.get('name', '') for p in active_patterns[:5]]
                pattern_semantics = get_multiple_pattern_semantics(pattern_names)
                result = self._rule_based_synthesize(pattern_semantics, synthesized_field, profile_name)
                result['debug_data'] = structured_data
                result['debug_error'] = str(e)
                # 尝试生成prompt用于调试
                try:
                    result['debug_prompt'] = self._construct_structured_prompt(structured_data)
                except:
                    result['debug_prompt'] = "Prompt生成失败"
                result['debug_response'] = ''
                return result
        else:
            # 使用规则生成（回退方案）
            pattern_names = [p.get('name', '') for p in active_patterns[:5]]
            pattern_semantics = get_multiple_pattern_semantics(pattern_names)
            result = self._rule_based_synthesize(pattern_semantics, synthesized_field, profile_name)
            result['debug_data'] = structured_data  # 即使不使用LLM，也保存结构化数据用于调试
            result['debug_prompt'] = "未使用LLM（规则生成）"
            result['debug_response'] = ''
            return result
    
    def _llm_synthesize_structured(self, structured_data: Dict,
                                   profile_name: str) -> Dict[str, Any]:
        """
        [QGA V24.4] 使用结构化JSON数据协议调用LLM
        
        Args:
            structured_data: 结构化的JSON数据
            profile_name: 档案名称
            
        Returns:
            包含persona和element_calibration的字典
        """
        try:
            # 构造结构化Prompt
            prompt = self._construct_structured_prompt(structured_data)
            
            # 调用LLM
            import ollama
            if isinstance(self._llm_client, ollama.Client):
                client = self._llm_client
            elif hasattr(ollama, 'Client'):
                if self._ollama_host and self._ollama_host != "http://localhost:11434":
                    client = ollama.Client(host=self._ollama_host)
                else:
                    client = ollama.Client()
            else:
                raise ValueError("无法创建ollama客户端")
            
            # 发送请求
            response = client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 500
                }
            )
            
            # 解析响应
            if isinstance(response, dict):
                response_text = response.get('response', '')
            elif hasattr(response, 'response'):
                response_text = response.response
            else:
                response_text = str(response)
            
            # [QGA V24.7] 使用LLM逻辑网关解析响应
            original_elements = structured_data.get('RawElements', {})
            # 转换为英文key用于LLMParser
            element_map = {'金': 'metal', '木': 'wood', '水': 'water', '火': 'fire', '土': 'earth'}
            original_elements_en = {}
            for cn_name, val in original_elements.items():
                if cn_name in element_map:
                    original_elements_en[element_map[cn_name]] = val
            
            # 转换为LLMParser需要的格式（中文key）
            original_elements_for_parser = original_elements.copy()
            
            # 调用LLM逻辑网关
            persona, calibration_en, debug_info = LLMParser.parse_llm_response(
                response_text=response_text,
                original_elements=original_elements_for_parser
            )
            
            # 转换为内部格式
            result = {
                'persona': persona,
                'element_calibration': calibration_en,  # 已经是英文key
                'debug_data': structured_data,
                'debug_prompt': prompt,
                'debug_response': response_text,
                'debug_parser_info': debug_info  # 新增：解析器调试信息
            }

            return result
            
        except Exception as e:
            logger.error(f"LLM结构化合成失败: {e}，回退到规则生成")
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"错误堆栈: {error_trace}")
            
            # 即使失败，也返回debug_data
            # 尝试生成prompt用于调试
            try:
                if structured_data and isinstance(structured_data, dict):
                    prompt = self._construct_structured_prompt(structured_data)
                else:
                    prompt = f"Prompt生成失败: structured_data无效 ({type(structured_data)})"
            except Exception as prompt_error:
                logger.error(f"Prompt生成也失败: {prompt_error}")
                prompt = f"Prompt生成失败: {str(prompt_error)}"
            
            return {
                'persona': f"LLM生成失败: {str(e)}",
                'element_calibration': None,
                'debug_data': structured_data if structured_data else {},
                'debug_error': str(e),
                'debug_prompt': prompt,
                'debug_response': ''
            }
    
    def _construct_structured_prompt(self, structured_data: Dict) -> str:
        """
        [QGA V24.4] 构造结构化Prompt（Few-shot示例）
        """
        import json
        
        # 格式化JSON数据
        json_str = json.dumps(structured_data, ensure_ascii=False, indent=2)
        
        # [QGA V24.6] Few-shot示例 - 严格的纯JSON格式
        example_input = """{
  "Context": {
    "Name": "测试案例",
    "TimeSpace": "1993年 | 大运甲子 | 流年癸酉 | 城市北京",
    "DayMaster": "丁火"
  },
  "ActivePatterns": [
    {
      "Name": "伤官见官",
      "Type": "Conflict",
      "PriorityRank": 1,
      "Logic": "流年支酉金生旺伤官，直冲官星",
      "Strength": 0.92
    }
  ],
  "RawElements": { "金": 40, "木": 10, "水": 20, "火": 20, "土": 10 }
}"""
        
        example_output = """{"persona": "伤官见官格局在1993年北京（水地）环境下激化，权威与自由的冲突达到峰值，系统稳定性极低，需要财星通关化解。", "corrected_elements": {"金": 25, "木": 15, "水": 30, "火": 20, "土": 10}}"""
        
        example2_input = """{
  "Context": {
    "Name": "案例二",
    "TimeSpace": "2025年 | 城市上海",
    "DayMaster": "丙火"
  },
  "ActivePatterns": [
    {
      "Name": "从儿格",
      "Type": "Special",
      "PriorityRank": 1,
      "Logic": "火土格局",
      "Strength": 0.85
    }
  ],
  "RawElements": { "金": 5, "木": 10, "水": 15, "火": 60, "土": 10 }
}"""
        
        example2_output = """{"persona": "从儿格（火土）在2025年上海（火地）环境下得到充分激活，才华如等离子喷泉般喷发，但需注意过度消耗导致能量不稳定。", "corrected_elements": {"金": 5, "木": 8, "水": 12, "火": 65, "土": 10}}"""
        
        # [QGA V24.5] 提取最高优先级格局用于因果映射
        top_pattern = None
        if structured_data.get('ActivePatterns'):
            sorted_patterns = sorted(
                structured_data['ActivePatterns'],
                key=lambda x: x.get('Strength', 0.0),
                reverse=True
            )
            if sorted_patterns:
                top_pattern = sorted_patterns[0]
        
        geo_info = structured_data.get('Context', {}).get('TimeSpace', '')
        geo_context = ""
        if '近水' in geo_info or 'water' in geo_info.lower():
            geo_context = "近水环境"
        elif '北京' in geo_info or '北方' in geo_info:
            geo_context = "北方/北京"
        elif '南方' in geo_info or 'fire' in geo_info.lower():
            geo_context = "南方/火地"
        
        # [QGA V24.7] 针对特定格局+地理环境的因果映射修正
        prompt_suffix = ""
        if geo_context:
            active_patterns_str = json.dumps(structured_data.get('ActivePatterns', []), ensure_ascii=False)
            if "从儿格" in active_patterns_str or "CONG_ER_GE" in str(structured_data):
                if "近水" in geo_context or "北方" in geo_context or "北京" in geo_context:
                    prompt_suffix = f"""
【特别因果映射规则 - 从儿格 + 近水/北方环境】
- 物理逻辑：从儿格（等离子喷泉）在近水环境下遭遇极寒冷却，导致才华输出受阻。
- 画像要求：必须体现"才华无法跨越地域寒气，导致产出受阻"这一物理过程。
- 五行修正：火元素应该显著降低，水元素可能增强（但需要平衡）。
"""
            elif "食神制杀" in active_patterns_str or "SHI_SHEN_ZHI_SHA" in str(structured_data):
                if "近水" in geo_context or "低层" in geo_context:
                    prompt_suffix = f"""
【特别因果映射规则 - 食神制杀 + 近水/低层环境】
- 物理逻辑：近水环境增强了土元素的稳定性，但可能抑制食神的活力。
- 画像要求：必须体现"过度的理智(水)淹没了表现力(火)"这一物理过程。
"""
            elif "枭神夺食" in active_patterns_str or "XIAO_SHEN_DUO_SHI" in str(structured_data):
                if "近水" in geo_context or "北方" in geo_context or "北京" in geo_context:
                    prompt_suffix = f"""
【特别因果映射规则 - 枭神夺食 + 近水/北方环境】
- 物理逻辑：水势作为燃料供给拦截器（木/枭），使得拦截力持续增强，导致生物能供给截断加剧。
- 能量传导链：当前环境（水）正在作为燃料供给拦截器（木），请在画像中体现这种"助纣为虐"的逻辑。
- 画像要求：必须包含"水势助长了印星的拦截力，使得原本枯竭的供给系统雪上加霜"这一物理过程。
- 五行修正：火元素应该显著降低（食神被夺），水元素应该增强（拦截能量注入），土元素可能增强（财星通关）。
"""

        prompt = f"""你是一个逻辑转换器。严禁输出任何分析过程、标题或解释性文字。仅允许输出纯JSON格式。

【严格响应模版 (Template)】
仅允许输出符合以下格式的JSON，不要带markdown代码块标记，不要带任何其他文字：
{{"persona": "...", "corrected_elements": {{"金": XX, "木": XX, "水": XX, "火": XX, "土": XX}}}}

【Few-Shot示例1】
输入：
{example_input}

输出：
{example_output}

【Few-Shot示例2】
输入：
{example2_input}

输出：
{example2_output}

---

【实际数据】
{json_str}

---

【强制约束规则】

1. **主导格局识别**: 
   - 优先使用PriorityRank=1的格局，如无则选择Strength最高的格局
   - 仅根据主导格局生成persona，忽略其他格局

2. **因果映射规则**:
   - [从儿格（火土）] + [北方/北京/近水] -> "等离子喷泉遭遇极寒冷却，才华产出虽高但无法变现/受阻"
   - [从儿格（火土）] + [南方/火地] -> "才华在火环境中得到充分激活，但需注意过度消耗"
   - [食神制杀] + [近水环境] -> "过度的理智(水)淹没了表现力(火)，导致才华无法释放"
   - [建禄月劫] + [近水] -> "水克火，导致热失控格局被抑制，但可能产生内部压力"
   - [枭神夺食] + [北方/北京/近水] -> "水势助长了印星的拦截力，使得原本枯竭的供给系统雪上加霜"

{prompt_suffix}

3. **五行修正规则**:
   - 所有五行值必须 >= 0（负数自动设为0）
   - 五行总和应接近原始总和（允许小幅波动）
   - 仅在JSON的corrected_elements中输出纯数字，不要写算式或代码
   - 如果提供了BaseVectorBias（初始物理偏差），你只需要在此基础上进行微调（±10%以内）

4. **输出格式**: 
   - 仅输出JSON，不要markdown代码块
   - persona为一句完整的描述
   - corrected_elements中的值必须是数字

{f"[提示：系统已计算初始物理偏差 {structured_data.get('BaseVectorBias', {})}，你只需在此基础上微调]" if structured_data.get('BaseVectorBias') else ""}

【请根据实际数据输出JSON】
"""
        return prompt
    
    # [QGA V24.7] _parse_structured_response已被LLMParser替代
    # 保留此方法作为向后兼容的回退方案
    def _parse_structured_response(self, response_text: str, structured_data: Dict) -> Dict[str, Any]:
        """
        [DEPRECATED] 此方法已被LLMParser替代
        保留作为向后兼容的回退方案
        """
        original_elements = structured_data.get('RawElements', {})
        persona, calibration, _ = LLMParser.parse_llm_response(response_text, original_elements)
        
        return {
            'persona': persona,
            'element_calibration': calibration
        }
    
    def _llm_synthesize(self, pattern_semantics: List[Dict],
                       synthesized_field: Dict, profile_name: str) -> Dict[str, Any]:
        """
        使用LLM合成画像
        
        Args:
            pattern_semantics: 格局语义列表
            synthesized_field: 合成场强信息
            profile_name: 档案名称
            
        Returns:
            包含persona和element_calibration的字典
        """
        try:
            # 构造Prompt
            prompt = self._construct_prompt(pattern_semantics, synthesized_field, profile_name)
            
            # 调用LLM（ollama API）
            # 如果使用了自定义host，需要使用Client对象
            if isinstance(self._llm_client, type) and hasattr(self._llm_client, 'Client'):
                # 使用ollama模块的默认方式
                client = self._llm_client.Client(host=self._ollama_host) if self._ollama_host else self._llm_client.Client()
            else:
                # 已经是Client实例
                client = self._llm_client
            
            # ollama的generate方法返回一个生成器，需要获取完整响应
            stream = client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': 500  # ollama使用num_predict而非max_tokens
                }
            )
            
            # 收集完整响应
            full_response = ""
            for chunk in stream:
                if hasattr(chunk, 'response'):
                    full_response += chunk.response
                elif isinstance(chunk, dict) and 'response' in chunk:
                    full_response += chunk['response']
                elif isinstance(chunk, str):
                    full_response += chunk
            
            # 解析响应
            result = self._parse_llm_response(full_response)
            
            return result
            
        except Exception as e:
            logger.error(f"LLM合成失败: {e}，回退到规则生成")
            return self._rule_based_synthesize(pattern_semantics, synthesized_field, profile_name)
    
    def _build_structured_data(self, active_patterns: List[Dict],
                              synthesized_field: Dict, profile_name: str,
                              day_master: str = None, force_vectors: Dict = None,
                              year: int = None, luck_pillar: str = None,
                              year_pillar: str = None, geo_info: str = None) -> Dict[str, Any]:
        """
        [QGA V24.4] 构建结构化JSON数据协议
        [QGA V24.7] 集成格局引擎，提取semantic_definition
        
        Returns:
            结构化的JSON数据字典
        """
        # 构建时空信息
        timespace_parts = []
        if year:
            timespace_parts.append(f"{year}年")
        if luck_pillar:
            timespace_parts.append(f"大运{luck_pillar}")
        if year_pillar:
            timespace_parts.append(f"流年{year_pillar}")
        if geo_info:
            timespace_parts.append(geo_info)
        timespace = " | ".join(timespace_parts) if timespace_parts else "原局"
        
        # [QGA V24.7] 识别地理环境
        geo_context = ""
        if '近水' in geo_info or 'water' in (geo_info or '').lower():
            geo_context = "近水环境"
        elif '北京' in geo_info or '北方' in geo_info:
            geo_context = "北方/北京"
        elif '南方' in geo_info or 'fire' in (geo_info or '').lower():
            geo_context = "南方/火地"
        
        # [QGA V24.7] 从格局引擎注册表获取semantic_definition
        pattern_registry = get_pattern_registry()
        
        # 构建激活格局列表（[QGA V24.5] 添加PriorityRank，按Strength降序排列）
        active_patterns_list = []
        for pattern in active_patterns[:5]:  # 最多5个格局
            pattern_type = "Special" if pattern.get('is_special', False) else "Conflict" if pattern.get('is_conflict', False) else "Normal"
            
            # 提取Strength（sai字段），如果为0或不存在，根据格局类型设置默认值
            sai = pattern.get('sai', None)
            if sai is None or (isinstance(sai, (int, float)) and float(sai) == 0.0):
                # 根据格局类型设置默认强度
                if pattern_type == "Special":
                    default_strength = 0.9  # 特殊格局默认高强度
                elif pattern_type == "Conflict":
                    default_strength = 0.7  # 冲突格局默认中等强度
                else:
                    default_strength = 0.5  # 普通格局默认中等强度
            else:
                try:
                    default_strength = float(sai)
                except (ValueError, TypeError):
                    default_strength = 0.5
            
            pattern_name = pattern.get('name', '')
            
            # [QGA V24.7] 尝试从格局引擎获取semantic_definition
            semantic_definition = pattern.get('matching_logic', '')[:100]  # 默认使用matching_logic
            engine = pattern_registry.get_by_name(pattern_name)
            if engine:
                try:
                    # 构造简化的match_result（实际应该使用真实的match_result）
                    from core.models.pattern_engine import PatternMatchResult
                    match_result = PatternMatchResult(
                        matched=True,
                        confidence=default_strength,
                        match_data={},
                        sai=pattern.get('sai', 0.0),
                        stress=pattern.get('stress', 0.0)
                    )
                    semantic_definition = engine.semantic_definition(match_result, geo_context)
                    logger.debug(f"✅ 从格局引擎获取semantic_definition: {pattern_name}")
                except Exception as e:
                    logger.warning(f"⚠️ 获取格局引擎semantic_definition失败 ({pattern_name}): {e}")
            
            active_patterns_list.append({
                "Name": pattern_name,
                "Type": pattern_type,
                "Logic": semantic_definition,  # [QGA V24.7] 使用格局引擎的semantic_definition
                "Strength": default_strength
            })
        
        # [QGA V24.5] 按Strength降序排列，添加PriorityRank
        active_patterns_list.sort(key=lambda x: x.get('Strength', 0.0), reverse=True)
        for idx, pattern in enumerate(active_patterns_list, start=1):
            pattern['PriorityRank'] = idx  # 1=最高优先级
        
        # 构建五行分布
        raw_elements = {}
        if force_vectors:
            element_map = {
                'metal': '金', 'wood': '木', 'water': '水',
                'fire': '火', 'earth': '土'
            }
            for key, value in force_vectors.items():
                if key in element_map:
                    raw_elements[element_map[key]] = round(float(value), 1)
        else:
            raw_elements = {"金": 20, "木": 20, "水": 20, "火": 20, "土": 20}
        
        return {
            "Context": {
                "Name": profile_name,
                "TimeSpace": timespace,
                "DayMaster": day_master or "未知"
            },
            "ActivePatterns": active_patterns_list,
            "RawElements": raw_elements
        }
    
    def _construct_prompt(self, pattern_semantics: List[Dict],
                         synthesized_field: Dict, profile_name: str) -> str:
        """
        构造LLM Prompt
        
        Args:
            pattern_semantics: 格局语义列表
            synthesized_field: 合成场强信息
            profile_name: 档案名称
            
        Returns:
            Prompt字符串
        """
        # 提取格局判词
        pattern_texts = []
        for semantic in pattern_semantics:
            pattern_name = semantic.get('pattern_name', '')
            physical = semantic.get('physical_logic', '')
            energy = semantic.get('energy_flow', '')
            destiny = semantic.get('destiny_traits', '')
            
            pattern_texts.append(f"""
【格局：{pattern_name}】
物理逻辑：{physical}
能量流动：{energy}
命运特征：{destiny}
""")
        
        # 提取时空耦合信息
        coupling_info = []
        if synthesized_field.get('has_luck'):
            coupling_info.append("大运已注入")
        if synthesized_field.get('has_year'):
            coupling_info.append("流年已注入")
        if synthesized_field.get('geo_element'):
            coupling_info.append(f"地理因子：{synthesized_field['geo_element']}")
        
        prompt = f"""作为QGA物理命理专家，请综合以下{len(pattern_semantics)}段格局逻辑，执行逻辑合并，输出一段300字的【全息命运画像】。

{''.join(pattern_texts)}

【时空耦合状态】
{', '.join(coupling_info) if coupling_info else '原局状态'}

【要求】
1. 忽略数值统计，专注于逻辑推理
2. 执行逻辑合并，找出格局之间的主旋律
3. 输出300字左右的【全息命运画像】，描述{profile_name}在当前时空耦合状态下的性格特质、人生主题和命运走向
4. 反向推导出该状态下最核心的五行矢量偏移（例如：水火交战导致火气被压制，水箭矢变长）

【输出格式】
画像：[300字全息命运画像]
五行偏移：[例如：火-15%，水+10%，土+5%]
"""
        return prompt
    
    def _parse_llm_response(self, response: Any) -> Dict[str, Any]:
        """
        解析LLM响应
        
        Args:
            response: LLM响应对象
            
        Returns:
            包含persona和element_calibration的字典
        """
        try:
            # 提取文本
            if hasattr(response, 'response'):
                text = response.response
            elif isinstance(response, str):
                text = response
            elif isinstance(response, dict):
                text = response.get('response', '')
            else:
                text = str(response)
            
            # 解析画像和五行偏移
            persona = ""
            element_calibration = None
            
            # 提取画像部分
            if "画像：" in text:
                persona = text.split("画像：")[1].split("五行偏移：")[0].strip()
            elif "【全息命运画像】" in text:
                persona = text.split("【全息命运画像】")[1].split("五行偏移")[0].strip()
            else:
                # 如果没有明确标记，取前300字作为画像
                persona = text[:300].strip()
            
            # 提取五行偏移
            if "五行偏移：" in text:
                offset_text = text.split("五行偏移：")[1].strip()
                element_calibration = self._parse_element_calibration(offset_text)
            
            return {
                'persona': persona,
                'element_calibration': element_calibration
            }
            
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            return {
                'persona': "LLM生成失败，使用规则生成。",
                'element_calibration': None
            }
    
    def _parse_element_calibration(self, offset_text: str) -> Optional[Dict[str, float]]:
        """
        解析五行偏移文本
        
        Args:
            offset_text: 五行偏移文本（例如：火-15%，水+10%，土+5%）
            
        Returns:
            五行偏移字典
        """
        calibration = {'metal': 0.0, 'wood': 0.0, 'water': 0.0, 'fire': 0.0, 'earth': 0.0}
        
        element_map = {
            '金': 'metal', '木': 'wood', '水': 'water',
            '火': 'fire', '土': 'earth'
        }
        
        try:
            # 解析格式：火-15%，水+10%，土+5%
            import re
            pattern = r'([金木水火土])([+-]?\d+(?:\.\d+)?)%'
            matches = re.findall(pattern, offset_text)
            
            for element_cn, offset_str in matches:
                if element_cn in element_map:
                    element = element_map[element_cn]
                    offset = float(offset_str)
                    calibration[element] = offset
        except Exception as e:
            logger.debug(f"解析五行偏移失败: {e}")
        
        return calibration
    
    def _rule_based_synthesize(self, pattern_semantics: List[Dict],
                               synthesized_field: Dict, profile_name: str) -> Dict[str, Any]:
        """
        基于规则的合成（回退方案）
        
        Args:
            pattern_semantics: 格局语义列表
            synthesized_field: 合成场强信息
            profile_name: 档案名称
            
        Returns:
            包含persona和element_calibration的字典
        """
        if not pattern_semantics:
            return {
                'persona': f"{profile_name}的命局相对平稳，无明显特殊格局。",
                'element_calibration': None
            }
        
        # 合并格局语义
        parts = [f"{profile_name}的命局呈现以下格局特征："]
        
        for semantic in pattern_semantics:
            pattern_name = semantic.get('pattern_name', '')
            destiny = semantic.get('destiny_traits', '')
            parts.append(f"【{pattern_name}】：{destiny}")
        
        # 添加时空耦合信息
        if synthesized_field.get('has_luck') or synthesized_field.get('has_year'):
            parts.append("在当前时空耦合状态下，这些格局特征被进一步激活或转化。")
        
        persona = " ".join(parts)
        
        return {
            'persona': persona,
            'element_calibration': None
        }

