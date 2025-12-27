"""
LLM语义合成器 (LLM Semantic Synthesizer)
基于格局语义池，使用LLM生成全息命运画像
支持Qwen2.5:2.5b及未来70B模型
[QGA V24.3] 从系统配置读取LLM模型名称
"""

import logging
from typing import Dict, List, Optional, Any
import json

from core.models.pattern_semantic_pool import get_multiple_pattern_semantics
from core.config_manager import ConfigManager

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
        
        # [QGA V24.4] 构建结构化JSON数据
        structured_data = self._build_structured_data(
            active_patterns, synthesized_field, profile_name,
            day_master, force_vectors, year, luck_pillar, year_pillar, geo_info
        )
        
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
            
            # 解析LLM返回
            result = self._parse_structured_response(response_text, structured_data)
            result['debug_data'] = structured_data
            result['debug_prompt'] = prompt
            result['debug_response'] = response_text
            
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
        
        # Few-shot示例
        example = """
【案例参考】
输入：
{
  "Context": {
    "Name": "测试案例",
    "TimeSpace": "1993年 | 大运甲子 | 流年癸酉",
    "DayMaster": "丁火"
  },
  "ActivePatterns": [
    {
      "Name": "伤官见官",
      "Type": "Conflict",
      "Logic": "流年支酉金生旺伤官，直冲官星",
      "Strength": 0.92
    }
  ],
  "RawElements": { "金": 40, "木": 10, "水": 20, "火": 20, "土": 10 }
}

输出：
核心矛盾：规则冲突。伤官见官格局导致权威与自由的撕裂，系统稳定性极低。
五行修正：减金（官星受冲）-15%，加水（财通关）+10%，加木（印星制伤）+5%。
修正后：{ "金": 25, "木": 15, "水": 30, "火": 20, "土": 10 }
"""
        
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
        
        prompt = f"""你是一个QGA审计专家。请阅读提供的JSON数据，执行以下两步分析：

{example}

---

【实际数据】
{json_str}

---

【强制约束规则 (Constraint Rules)】

1. **强制排序 (Strict Sorting)**: 
   - 必须按照PriorityRank字段识别主导格局（PriorityRank=1为最高优先级）
   - 如果PriorityRank不存在，则按Strength降序排列，取Strength最高的格局为主导
   - 主导格局（Top 1）必须作为核心矛盾的主要来源
   - 其他格局（Top 2-3）仅作为扰动因素

2. **非负约束 (Positive Only)**: 
   - 五行修正后的结果严禁出现负数
   - 若需扣减，最低限度为0（使用Math.max(0, value)逻辑）
   - 所有五行值必须 >= 0

3. **因果映射表 (Hard-Mapping)**:
   - 若 [食神制杀] + [近水环境] -> "过度的理智(水)淹没了表现力(火)，导致才华无法释放"
   - 若 [从儿格] + [北方/北京] -> "才华无法跨越地域寒气，导致产出受阻，需要火元素激活"
   - 若 [从儿格] + [南方/火地] -> "才华在火环境中得到激活，但需注意过度消耗"
   - 若 [建禄月劫] + [近水] -> "水克火，导致热失控格局被抑制，但可能产生内部压力"

4. **输出规范**: 
   - 必须返回纯JSON格式，严禁带"任务A/B"、"核心矛盾："等标题
   - 格式：{{"persona": "...", "corrected_elements": {{"金": XX, "木": XX, "水": XX, "火": XX, "土": XX}}}}

---

【任务A：逻辑归纳】
第一步：找出PriorityRank=1的格局（或Strength最高的格局）作为主导格局。
第二步：结合地理环境（{geo_context if geo_context else '当前环境'}），用一句话解释这个格局如何导致了命主在{structured_data.get('Context', {}).get('TimeSpace', '当前时空')}的不顺。

【任务B：五行修正】
基于主导格局和地理环境，请给出RawElements的修正百分比。
规则：
- 受克格局对应的五行必须扣减（但最低为0）
- 救应格局对应的五行必须增加
- 通关格局对应的五行必须增加
- 所有修正后的值必须 >= 0

【输出格式（纯JSON）】
{{"persona": "[一句话描述，结合格局和地理环境]", "corrected_elements": {{"金": XX, "木": XX, "水": XX, "火": XX, "土": XX}}}}
"""
        return prompt
    
    def _parse_structured_response(self, response_text: str, structured_data: Dict) -> Dict[str, Any]:
        """
        [QGA V24.4] 解析结构化响应
        [QGA V24.5] 增强解析：支持纯JSON格式，添加非负约束验证
        """
        import json
        import re
        
        persona = ""
        element_calibration = None
        
        # [QGA V24.5] 优先尝试解析纯JSON格式
        try:
            # 尝试提取JSON对象
            json_match = re.search(r'\{[^{}]*"persona"[^{}]*"corrected_elements"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                persona = parsed.get('persona', '')
                corrected_elements = parsed.get('corrected_elements', {})
                
                # [QGA V24.5] 应用非负约束
                original = structured_data.get('RawElements', {})
                element_map = {'金': 'metal', '木': 'wood', '水': 'water', '火': 'fire', '土': 'earth'}
                calibration = {'metal': 0.0, 'wood': 0.0, 'water': 0.0, 'fire': 0.0, 'earth': 0.0}
                
                for cn_name, en_name in element_map.items():
                    original_val = original.get(cn_name, 20.0)
                    corrected_val = max(0.0, float(corrected_elements.get(cn_name, original_val)))  # 非负约束
                    calibration[en_name] = corrected_val - original_val
                
                element_calibration = calibration
        except Exception as e:
            logger.debug(f"JSON格式解析失败，尝试旧格式: {e}")
        
        # 回退到旧格式解析
        if not persona:
            if "核心矛盾：" in response_text:
                persona = response_text.split("核心矛盾：")[1].split("五行修正")[0].strip()
            elif "核心矛盾" in response_text:
                parts = response_text.split("核心矛盾")
                if len(parts) > 1:
                    persona = parts[1].split("五行修正")[0].strip().lstrip("：").lstrip(":")
            
            # 提取五行修正
            if "修正后：" in response_text:
                json_match = re.search(r'修正后：\s*(\{[^}]+\})', response_text)
                if json_match:
                    try:
                        corrected = json.loads(json_match.group(1))
                        # 计算偏移量
                        original = structured_data.get('RawElements', {})
                        element_map = {'金': 'metal', '木': 'wood', '水': 'water', '火': 'fire', '土': 'earth'}
                        calibration = {'metal': 0.0, 'wood': 0.0, 'water': 0.0, 'fire': 0.0, 'earth': 0.0}
                        
                        for cn_name, en_name in element_map.items():
                            original_val = original.get(cn_name, 20.0)
                            corrected_val = max(0.0, float(corrected.get(cn_name, original_val)))  # [QGA V24.5] 非负约束
                            calibration[en_name] = corrected_val - original_val
                        
                        element_calibration = calibration
                    except Exception as e:
                        logger.debug(f"解析五行修正失败: {e}")
        
        # 如果没有提取到，使用默认
        if not persona:
            persona = response_text[:300].strip()
        
        # [QGA V24.5] 最终验证：确保所有校准值都是合理的
        if element_calibration:
            for key, value in element_calibration.items():
                if not isinstance(value, (int, float)) or value != value:  # 检查NaN
                    element_calibration[key] = 0.0
        
        return {
            'persona': persona,
            'element_calibration': element_calibration
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
            
            active_patterns_list.append({
                "Name": pattern.get('name', ''),
                "Type": pattern_type,
                "Logic": pattern.get('matching_logic', '')[:100],  # 限制长度
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

