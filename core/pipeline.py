# core/pipeline.py
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from service.extractor import CaseExtractor
from service.bio_miner import BioMiner
from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

@dataclass
class VerificationResult:
    case_id: str
    is_valid_birth_data: bool
    predicted_favorable_elements: List[str] # 喜用神，例如 ['Wood', 'Water']
    actual_success_years: List[int]         # 事实：发财/升职的年份
    match_score: float                      # 准确率得分 (0.0 - 1.0)
    details: str                            # 详细分析日志

class BaziVerificationPipeline:
    def __init__(self):
        # 1. 初始化三大核心组件
        self.logger = logging.getLogger("Antigravity.Pipeline")
        
        self.logger.info("Initializing Verification Pipeline Components...")
        self.extractor = CaseExtractor()   
        self.engine = QuantumEngine() # Will load default golden_parameters.json
        self.bio_miner = BioMiner()        
        
    def run_single_case(self, text_input: str) -> VerificationResult:
        """
        执行单个案例的完整闭环验证
        """
        self.logger.info("1. 启动案例提取 (Extractor)...")
        # Step 1: 从文本中提取出生信息 (LLM)
        birth_data = self.extractor.extract(text_input)
        
        # Validation checks
        if not birth_data or not birth_data.get('profile', {}).get('birth_year'):
            return VerificationResult(
                case_id="unknown", is_valid_birth_data=False, 
                predicted_favorable_elements=[], actual_success_years=[], 
                match_score=0.0, details="提取出生日期失败"
            )
            
        profile = birth_data['profile']
        case_name = profile.get('name', 'anonymous')

        self.logger.info(f"2. 启动排盘计算 (QuantumEngine) - Input: {profile}")
        # Step 2: 进行排盘和格局分析 (Python Algorithm, NOT LLM)
        # Using the monkey-patched calculate_chart method
        if not hasattr(self.engine, 'calculate_chart'):
             raise RuntimeError("QuantumEngine missing calculate_chart method. Ensure extensions are loaded.")
             
        chart_analysis = self.engine.calculate_chart(profile)
        
        if 'error' in chart_analysis:
            return VerificationResult(
                case_id=case_name, is_valid_birth_data=True,
                predicted_favorable_elements=[], actual_success_years=[],
                match_score=0.0, details=f"排盘错误: {chart_analysis['error']}"
            )

        favorable_elements = chart_analysis['favorable_elements'] # 喜用神
        self.logger.info(f"   >>> Engine Analysis: {chart_analysis['wang_shuai']}, Favorable: {favorable_elements}")

        self.logger.info("3. 启动生平挖掘 (BioMiner)...")
        # Step 3: 从文本中挖掘人生大事件 (LLM)
        # Result should contain: Year and Polarity
        life_events = self.bio_miner.mine_events(text_input)
        
        # Step 4: 核心验证逻辑 (Comparator)
        # 比较“喜用神”与“事实发生年份的五行”是否吻合
        score, verification_log = self._evaluate_accuracy(
            favorable_elements, 
            life_events
        )

        return VerificationResult(
            case_id=case_name,
            is_valid_birth_data=True,
            predicted_favorable_elements=favorable_elements,
            actual_success_years=[e['year'] for e in life_events if e['type'] == 'positive'],
            match_score=score,
            details=verification_log
        )

    def _evaluate_accuracy(self, favorable: List[str], events: List[Dict]) -> (float, str):
        """
        打分逻辑：如果某年是命主的'喜用神'年份，且发生了好事，得分。
        """
        hits = 0
        total_valid_events = 0
        log = []
        
        # Normalize favorable to capitalized
        favorable = [f.capitalize() for f in favorable]

        for event in events:
            year = event['year']
            event_type = event['type'] # 'positive' or 'negative'
            desc = event.get('description', '')
            
            # 这里调用 Engine 计算当年的五行属性
            # e.g., 2014 (甲午) -> Wood, Fire
            year_elements = self.engine.get_elements_for_year(year) 
            year_elements = [e.capitalize() for e in year_elements]
            
            # 简单的命中逻辑示例
            # 如果喜用神包含当年的属性 (Any match)
            is_favorable_year = any(e in favorable for e in year_elements)
            
            # Log Context
            yr_str = f"{year} ({'/'.join(year_elements)})"
            
            if event_type == 'positive':
                total_valid_events += 1
                if is_favorable_year:
                    hits += 1
                    log.append(f"✅ [MATCH] {yr_str} 是喜用年，命中好事: {desc}")
                else:
                    log.append(f"❌ [MISS]  {yr_str} 是忌神年? 却发生了好事: {desc}")
                    
            elif event_type == 'negative':
                total_valid_events += 1
                # Negative event should happen in Unfavorable year (Not Favorable)
                if not is_favorable_year:
                    hits += 1
                    log.append(f"✅ [MATCH] {yr_str} 是忌神年，命中坏事: {desc}")
                else:
                    log.append(f"❌ [MISS]  {yr_str} 是喜用年? 却发生了坏事: {desc}")

        score = (hits / total_valid_events) if total_valid_events > 0 else 0.0
        
        # Summary
        log.insert(0, f"=== Verification Report (Score: {score:.2f}) ===")
        log.insert(1, f"Predicted Favorable: {favorable}")
        log.insert(2, f"Total Events Evaluated: {total_valid_events}")
        
        return score, "\n".join(log)

if __name__ == "__main__":
    # Simple Test
    logging.basicConfig(level=logging.INFO)
    pipeline = BaziVerificationPipeline()
    
    # Mock Text Case
    test_case = """
    【案例】马云，1964年9月10日出生于杭州。
    1999年创办阿里巴巴，开始发财。
    2014年阿里美国上市，成为首富。
    """
    
    result = pipeline.run_single_case(test_case)
    print("\n" + result.details)
