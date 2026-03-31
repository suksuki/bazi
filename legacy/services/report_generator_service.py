import logging
import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class ReportGeneratorService:
    """
    Service responsible for generating semantic reports, personas, and prescriptions.
    Extracts logic previously in ProfileAuditController.
    """

    def __init__(self):
        # Placeholder for LLM service if needed
        pass

    def generate_semantic_report(self, profile_data: Dict, pfa_result, soa_result,
                                 mca_result, force_vectors: Dict, year: int,
                                 pattern_audit: Dict = None, use_llm: bool = False,
                                 bazi_profile=None, city: str = None,
                                 micro_env: List[str] = None,
                                 llm_debug_data_saver=None,
                                 active_patterns_fallback: List = None) -> Dict[str, str]:
        """
        Generate semantic report.
        Args:
            llm_debug_data_saver: Callable to save debug data (e.g. controller instance)
            active_patterns_fallback: Fallback patterns if pattern_audit is None (from engine state)
        """
        
        # 1. Core Conflict
        core_conflict = self._generate_core_conflict(pfa_result, soa_result)
        
        # 2. Persona (300 words)
        persona = self._generate_persona_with_llm(
            profile_data, pfa_result, soa_result, force_vectors, mca_result, year, pattern_audit, use_llm,
            city=city, micro_env=micro_env, debug_saver=llm_debug_data_saver, 
            bazi_profile=bazi_profile, active_patterns_fallback=active_patterns_fallback
        )
        
        # 3. Wealth Prediction
        wealth_prediction = self._generate_wealth_prediction(soa_result, force_vectors, year, mca_result)
        
        # 4. Prescription
        prescription = self._generate_prescription(soa_result, mca_result, pfa_result)
        
        result = {
            'core_conflict': core_conflict,
            'persona': persona,
            'wealth_prediction': wealth_prediction,
            'prescription': prescription
        }
        
        return result
    
    def _generate_core_conflict(self, pfa_result, soa_result) -> str:
        """Generate core conflict description."""
        friction = pfa_result.friction_index
        stability = soa_result.stability_score
        
        if friction > 60 and stability < 0.5:
            return "命局中存在严重的格局冲突，系统稳定性极低，导致理想与现实的强烈撕裂，需要外部干预来调和矛盾。"
        elif friction > 40:
            return f"命局中存在格局冲突（{', '.join(pfa_result.conflicting_patterns[:2]) if pfa_result.conflicting_patterns else '内在矛盾'}），导致性格中的自我拆台，需要寻找平衡点。"
        elif stability < 0.5:
            return "系统能量分布不稳定，存在内耗，需要通过优化来提升稳定性。"
        else:
            return "命局基本协调，但存在微妙的平衡点需要维护。"

    def _generate_persona_with_llm(self, profile_data: Dict, pfa_result, soa_result,
                                   force_vectors: Dict, mca_result=None, year: int = None,
                                   pattern_audit: Dict = None, use_llm: bool = False,
                                   city: str = None, micro_env: List[str] = None,
                                   debug_saver=None, bazi_profile=None,
                                   active_patterns_fallback: List = None) -> str:
        """Generate persona using LLM or fallback."""
        if not use_llm:
            return self._generate_persona(
                profile_data, pfa_result, soa_result, force_vectors, mca_result, year, pattern_audit
            )
        
        try:
            from core.models.llm_semantic_synthesizer import LLMSemanticSynthesizer
            
            synthesizer = LLMSemanticSynthesizer(use_llm=True)
            
            # Get active patterns
            if pattern_audit:
                active_patterns_list = pattern_audit.get('patterns', [])
                active_patterns = {
                    'patterns_list': active_patterns_list,
                    'base_vector_bias': pattern_audit.get('base_vector_bias'),
                    'geo_context': pattern_audit.get('geo_context', '')
                }
                
                synthesized_field = {
                    'has_luck': bool(pattern_audit.get('luck_pillar')),
                    'has_year': bool(pattern_audit.get('year_pillar')),
                    'geo_element': None
                }
            else:
                # Fallback
                active_patterns = {
                    'patterns_list': active_patterns_fallback or [],
                    'base_vector_bias': None,
                    'geo_context': ''
                }
                synthesized_field = {}
            
            # Construct geo info
            geo_info_parts = []
            if city:
                geo_info_parts.append(f"城市{city}")
            if micro_env:
                geo_info_parts.extend(micro_env)
            geo_info = " | ".join(geo_info_parts) if geo_info_parts else None
            
            # Get day master
            day_master = None
            if bazi_profile:
                day_master_stem = bazi_profile.pillars['day'][0]
                day_master_element = self._get_element_from_stem(day_master_stem)
                day_master_yinyang = "阴" if day_master_stem in ['乙', '丁', '己', '辛', '癸'] else "阳"
                day_master = f"{day_master_stem}{day_master_element} ({day_master_yinyang}{day_master_element})"
            
            # Luck/Year string
            luck_pillar_str = None
            year_pillar_str = None
            if bazi_profile and year:
                try:
                    luck_pillar = bazi_profile.get_luck_pillar_at(year)
                    if luck_pillar:
                        luck_pillar_str = f"{luck_pillar[0]}{luck_pillar[1]}"
                    year_pillar = bazi_profile.get_year_pillar(year)
                    if year_pillar:
                        year_pillar_str = f"{year_pillar[0]}{year_pillar[1]}"
                except:
                    pass
            
            # Synthesis
            result = synthesizer.synthesize_persona(
                active_patterns,
                synthesized_field,
                profile_data.get('name', '此人'),
                day_master=day_master,
                force_vectors=force_vectors,
                year=year,
                luck_pillar=luck_pillar_str,
                year_pillar=year_pillar_str,
                geo_info=geo_info
            )
            
            persona = result.get('persona', '')
            element_calibration = result.get('element_calibration')
            
            # Debug data callback
            if debug_saver:
                debug_data = {
                    'debug_data': result.get('debug_data'),
                    'debug_prompt': result.get('debug_prompt', ''),
                    'debug_response': result.get('debug_response', ''),
                    'debug_error': result.get('debug_error')
                }
                debug_saver.set_llm_debug_data(debug_data)
                
                if element_calibration:
                    debug_saver.set_llm_element_calibration(element_calibration)
            
            if not persona or persona.startswith("LLM生成失败"):
                logger.warning("LLM generation failed, fallback to rules.")
                return self._generate_persona(
                    profile_data, pfa_result, soa_result, force_vectors, mca_result, year, pattern_audit
                )
                
            return persona

        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}", exc_info=True)
            return self._generate_persona(
                profile_data, pfa_result, soa_result, force_vectors, mca_result, year, pattern_audit
            )

    def _generate_persona(self, profile_data: Dict, pfa_result, soa_result,
                          force_vectors: Dict, mca_result=None, year: int = None,
                          pattern_audit: Dict = None) -> str:
        """Generate persona using rules."""
        name = profile_data.get('name', '此人')
        
        parts = []
        
        if pattern_audit:
            state_changes = pattern_audit.get('state_changes', [])
            if state_changes:
                change = state_changes[0]
                parts.append(f"{name}的命局在{year}年发生了**格局状态变化**。")
                parts.append(f"原局格局【{change.get('original', '')}】")
                parts.append(f"在时空耦合（大运+流年+地理）作用下，")
                parts.append(f"已退化为【{change.get('current', '')}】。")
                parts.append(f"{change.get('impact', '')}")
                parts.append(f"因此，你的用神和应对策略必须立即调整。")
                return " ".join(parts)
        
        # Simple logical fallback since we don't have access to engine state easily here
        # unless passed in.
        
        if pfa_result.friction_index < 30:
             parts.append(f"{name}具有较为流畅的能量结构。")
        else:
             parts.append(f"{name}的能量结构存在一定内耗。")
             
        if soa_result.stability_score > 0.7:
             parts.append("整体运势稳健，抗风险能力强。")
        else:
             parts.append("运势波动较大，需要注意求稳。")
        
        return "".join(parts)

    def _generate_wealth_prediction(self, soa_result, force_vectors: Dict, year: int, mca_result) -> str:
        """Generate wealth prediction."""
        wealth_energy = force_vectors.get('wealth', 0) + force_vectors.get('water', 0) * 0.5 # Example
        if wealth_energy > 40:
            return "财星高照，利于投资和积累。"
        elif wealth_energy > 20:
             return "财运平稳，不仅求财，更重守成。"
        else:
             return "财运较弱，避免高风险投资。"

    def _generate_prescription(self, soa_result, mca_result, pfa_result) -> str:
        """Generate prescription."""
        optimal = soa_result.optimal_elements
        if not optimal:
            return "保持现状，顺势而为。"
        
        elements = [k for k,v in optimal.items() if v > 0]
        return f"建议补充{'、'.join(elements)}元素能量，可以通过方位、颜色或行业选择来调整。"

    def _get_element_from_stem(self, stem: str) -> str:
        """Helper to get element from stem."""
        element_map = {
            '甲': '木', '乙': '木',
            '丙': '火', '丁': '火',
            '戊': '土', '己': '土',
            '庚': '金', '辛': '金',
            '壬': '水', '癸': '水'
        }
        return element_map.get(stem, '土')
