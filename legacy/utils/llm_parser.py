"""
[QGA V24.7] LLM逻辑网关中间件
专门负责对LLM的输入进行预处理，并对输出进行"正则强制清洗"
核心目标：从"黑盒计算"转变为"确定性逻辑链路"
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class LLMParser:
    """
    LLM输出解析器 - 逻辑网关中间件
    
    功能：
    1. 正则强制提取JSON（无论LLM带多少废话）
    2. 清洗脏数据（算式、代码逻辑、markdown标记）
    3. 应用非负约束和归一化
    4. 验证数据结构完整性
    """
    
    @staticmethod
    def extract_json(response_text: str) -> Optional[str]:
        """
        [步骤1] 正则强制提取JSON
        
        无论LLM输出多少废话，只抓取 {...} 中的JSON
        
        Args:
            response_text: LLM原始响应文本
            
        Returns:
            提取出的JSON字符串（如果没有找到则返回None）
        """
        if not response_text:
            return None
        
        cleaned_text = response_text.strip()
        
        # 1. 移除markdown代码块标记
        cleaned_text = re.sub(r'```json\s*', '', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'```\s*', '', cleaned_text)
        
        # 2. 提取JSON对象（匹配第一个{到最后一个}）
        json_start = cleaned_text.find('{')
        json_end = cleaned_text.rfind('}')
        
        if json_start != -1:
            if json_end != -1 and json_end > json_start:
                extracted = cleaned_text[json_start:json_end + 1]
                logger.debug(f"✅ JSON提取成功: 起始位置={json_start}, 结束位置={json_end}")
                return extracted
            else:
                # [QGA V24.7] 如果找不到闭合括号，尝试自动补全
                # 检查是否缺少最后的}
                extracted = cleaned_text[json_start:]
                # 计算大括号平衡
                open_count = extracted.count('{')
                close_count = extracted.count('}')
                if open_count > close_count:
                    # 缺少闭合括号，自动补全
                    extracted = extracted + '}' * (open_count - close_count)
                    logger.debug(f"✅ JSON自动补全闭合括号: 补全了{open_count - close_count}个}}")
                    return extracted
        else:
            # 3. 如果找不到完整的JSON，尝试更宽松的匹配
            json_match = re.search(r'\{.*"persona".*"corrected_elements".*?\}', cleaned_text, re.DOTALL)
            if json_match:
                logger.debug("✅ 使用宽松模式提取JSON")
                return json_match.group(0)
        
        logger.warning("⚠️ 未找到有效的JSON对象")
        return None
    
    @staticmethod
    def clean_numeric_expressions(json_str: str) -> str:
        """
        [步骤2] 清洗JSON内的算式和代码逻辑
        
        处理如 "14.3 + 5" -> "19.3"
        移除 Math.max() 等函数调用
        
        Args:
            json_str: JSON字符串
            
        Returns:
            清洗后的JSON字符串
        """
        def eval_simple_math(match):
            """计算简单算式"""
            try:
                expr = match.group(1)
                # 移除可能的Math.max等函数调用
                expr = re.sub(r'Math\.max\([^)]+\)', '', expr)
                expr = re.sub(r'Math\.min\([^)]+\)', '', expr)
                # 只保留数字和运算符
                expr = re.sub(r'[^0-9+\-*/.()]', '', expr)
                if expr:
                    result = eval(expr)
                    return str(result)
            except Exception as e:
                logger.debug(f"算式计算失败: {e}")
            return match.group(0)
        
        # 处理值中的算式（格式如 "金": 14.3 + 5）
        pattern = r':\s*([0-9.+\-*/()]+)\s*([,\}])'
        cleaned = re.sub(pattern, 
                        lambda m: f': {eval_simple_math(m) if any(op in m.group(1) for op in ["+", "-", "*", "/"]) else m.group(1)}{m.group(2)}', 
                        json_str)
        
        return cleaned
    
    @staticmethod
    def parse_and_validate(json_str: str, original_elements: Dict[str, float]) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """
        [步骤3] 解析JSON并应用约束验证
        
        Args:
            json_str: JSON字符串
            original_elements: 原始五行值（用于计算偏移量）
            
        Returns:
            (parsed_dict, element_calibration) 元组
            parsed_dict: 解析后的字典（包含persona和corrected_elements）
            element_calibration: 五行校准偏移量
        """
        try:
            parsed = json.loads(json_str)
            
            persona = parsed.get('persona', '')
            corrected_elements = parsed.get('corrected_elements', {})
            
            # 应用非负约束和类型转换
            element_map = {'金': 'metal', '木': 'wood', '水': 'water', '火': 'fire', '土': 'earth'}
            cleaned_corrected = {}
            
            for cn_name in element_map.keys():
                raw_val = corrected_elements.get(cn_name)
                if raw_val is None:
                    cleaned_corrected[cn_name] = original_elements.get(cn_name, 20.0)
                else:
                    try:
                        # 如果是字符串且包含算式，尝试计算
                        if isinstance(raw_val, str):
                            # 移除可能的Math.max等函数
                            raw_val = re.sub(r'Math\.max\([^)]+\)', '', raw_val)
                            raw_val = re.sub(r'Math\.min\([^)]+\)', '', raw_val)
                            raw_val = re.sub(r'[^0-9+\-*/.()]', '', raw_val)
                            if raw_val and any(op in raw_val for op in ['+', '-', '*', '/']):
                                raw_val = eval(raw_val)
                        val = max(0.0, float(raw_val))  # 非负约束
                        cleaned_corrected[cn_name] = val
                    except (ValueError, TypeError) as e:
                        logger.warning(f"数值转换失败 ({cn_name}): {e}, 使用原始值")
                        cleaned_corrected[cn_name] = original_elements.get(cn_name, 20.0)
            
            # 应用能量守恒（归一化到原始总和）
            original_sum = sum(original_elements.values())
            if original_sum > 0:
                corrected_sum = sum(cleaned_corrected.values())
                if corrected_sum > 0:
                    # 按比例缩放，保持总和一致
                    scale_factor = original_sum / corrected_sum
                    for key in cleaned_corrected:
                        cleaned_corrected[key] *= scale_factor
            
            # 计算校准偏移量
            calibration = {}
            for cn_name, en_name in element_map.items():
                original_val = original_elements.get(cn_name, 20.0)
                corrected_val = cleaned_corrected.get(cn_name, original_val)
                calibration[en_name] = corrected_val - original_val
            
            # 限制校准幅度（防止数值崩溃，最大±30%）
            max_offset = original_sum * 0.3 if original_sum > 0 else 30.0
            for key in calibration:
                calibration[key] = max(-max_offset, min(max_offset, calibration[key]))
            
            return {
                'persona': persona,
                'corrected_elements': cleaned_corrected
            }, calibration
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise ValueError(f"无效的JSON格式: {e}")
        except Exception as e:
            logger.error(f"解析验证失败: {e}")
            raise
    
    @staticmethod
    def parse_llm_response(response_text: str, original_elements: Dict[str, float]) -> Tuple[str, Dict[str, float], Dict[str, Any]]:
        """
        [主入口] 完整的LLM响应解析流程
        
        Args:
            response_text: LLM原始响应文本
            original_elements: 原始五行值字典（如 {"金": 5.2, "木": 74.8, ...}）
            
        Returns:
            (persona, element_calibration, debug_info) 元组
            persona: 生成的画像文本
            element_calibration: 五行校准偏移量（英文key: metal, wood, water, fire, earth）
            debug_info: 调试信息（提取的JSON、清洗步骤等）
        """
        debug_info = {
            'original_response_length': len(response_text),
            'extraction_method': None,
            'cleaned_json': None,
            'validation_errors': []
        }
        
        try:
            # 步骤1: 提取JSON
            json_str = LLMParser.extract_json(response_text)
            if not json_str:
                raise ValueError("未找到有效的JSON对象")
            
            debug_info['extraction_method'] = 'regex_extraction'
            debug_info['cleaned_json'] = json_str
            
            # 步骤2: 清洗算式
            cleaned_json = LLMParser.clean_numeric_expressions(json_str)
            
            # 步骤3: 解析和验证
            parsed_dict, calibration = LLMParser.parse_and_validate(cleaned_json, original_elements)
            
            persona = parsed_dict.get('persona', '')
            
            logger.info(f"✅ LLM响应解析成功: persona长度={len(persona)}, 校准={calibration}")
            
            return persona, calibration, debug_info
            
        except Exception as e:
            logger.error(f"❌ LLM响应解析失败: {e}")
            debug_info['validation_errors'].append(str(e))
            # 返回空结果
            return "", {'metal': 0.0, 'wood': 0.0, 'water': 0.0, 'fire': 0.0, 'earth': 0.0}, debug_info

