
"""
Phase D: Life-Path Simulation Engine (Single-Body Excellence)
============================================================
Performs high-resolution temporal sampling across a human lifespan.
- Samples energy metrics (SAI, IC, Entropy, DM Strength) at solar term resolution.
- Identifies 'Risk Nodes' (Extreme stress/entropy peaks).
- Generates a time-continuous orbital dataset for UI visualization.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from core.bazi_profile import BaziProfile
from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.engines.quantum_dispersion import QuantumDispersionEngine

class LifePathEngine:
    def __init__(self, oracle: Optional[TrinityOracle] = None):
        self.oracle = oracle or TrinityOracle()
        self.dispersion_engine = QuantumDispersionEngine()

    def simulate_lifespan(self, profile: BaziProfile, 
                          start_year: Optional[int] = None, 
                          end_year: Optional[int] = None,
                          resolution: str = 'term') -> Dict[str, Any]:
        """
        Samples the personal quantum orbit from start_year to end_year.
        
        Args:
            profile: The BaziProfile instance (Single Source of Truth).
            start_year: Start of simulation (defaults to birth year).
            end_year: End of simulation (defaults to birth + 80).
            resolution: 'year' (1 point/year, fast), 'term' (24 points/year), or 'month' (12 points/year).
        """
        birth_year = profile.birth_date.year
        s_year = start_year or birth_year
        e_year = end_year or (birth_year + 80)
        
        birth_pillars_dict = profile.pillars
        birth_pillars_list = [birth_pillars_dict['year'], birth_pillars_dict['month'], 
                              birth_pillars_dict['day'], birth_pillars_dict['hour']]
        dm = profile.day_master
        
        timeline = []
        risk_nodes = []
        
        print(f"DEBUG: Starting Life-Path Simulation for {dm} DM from {s_year} to {e_year} (resolution={resolution})")
        
        for year in range(s_year, e_year + 1):
            luck_p = profile.get_luck_pillar_at(year)
            annual_p = profile.get_year_pillar(year)
            
            # 根据 resolution 决定采样点
            if resolution == 'year':
                # 年度采样：每年只采样一次（使用年中时间点）
                sample_points = [(f"Year_{year}", datetime(year, 6, 15, 12))]
            else:
                # 节气采样：每年24个节气点
                term_times = self.dispersion_engine.get_solar_term_times_for_year(year)
                sample_points = sorted(term_times.items(), key=lambda x: x[1])
            
            for term_name, t_time in sample_points:
                # Compute analysis
                res = self.oracle.analyze(
                    pillars=birth_pillars_list,
                    day_master=dm,
                    luck_pillar=luck_p,
                    annual_pillar=annual_p,
                    birth_date=t_time,
                    dispersion_mode=True
                )
                
                # Extract key metrics
                emergence = res.get('emergence', {})
                stress = res.get('structural_stress', {})
                wealth_res = res.get('wealth_fluid', {})
                rel_res = res.get('relationship_gravity', {})
                
                metrics = {
                    'timestamp': t_time.isoformat(),
                    'year': year,
                    'term': term_name,
                    'entropy': emergence.get('causal_entropy', 0),
                    'sai': stress.get('SAI', 0),
                    'ic': stress.get('IC', 0),
                    'dm_strength': res.get('verdict', {}).get('score', 0),
                    'sync_state': res.get('resonance', {}).sync_state if res.get('resonance') else None,
                    'wealth': wealth_res,
                    'relationship': rel_res
                }
                
                timeline.append(metrics)
                
                # Identify structure risks
                if metrics['sai'] > 0.6 or metrics['entropy'] > 1.5 or metrics['ic'] > 0.6:
                    risk_nodes.append({
                        'timestamp': t_time.isoformat(),
                        'reason': self._identify_risk_reason(metrics),
                        'metrics': metrics,
                        'topic': 'structure',
                        'risk_score': metrics['entropy'] * 0.6 + metrics['sai'] * 0.3 + metrics['ic'] * 0.1
                    })
                
                # Wealth risk scoring
                if wealth_res:
                    re_v = wealth_res.get('Reynolds', 0)
                    visc_v = wealth_res.get('Viscosity', 0)
                    state_w = wealth_res.get('State', '')
                    w_score = (re_v / 4000.0) + max(0, visc_v - 1.2) * 0.5
                    if state_w == "TURBULENT":
                        w_score += 0.5
                    elif state_w == "TRANSITION":
                        w_score += 0.2
                    if w_score >= 1.0:
                        risk_nodes.append({
                            'timestamp': t_time.isoformat(),
                            'reason': f"Wealth state: {state_w or 'UNKNOWN'}",
                            'metrics': metrics,
                            'topic': 'wealth',
                            'risk_score': w_score
                        })
                
                # Relationship risk scoring (使用完整物理指标)
                if rel_res:
                    state_r = rel_res.get('State', '')
                    bind_e = rel_res.get('Binding_Energy', 0)
                    orbital_stab = rel_res.get('Orbital_Stability', 1.0)
                    phase_coh = rel_res.get('Phase_Coherence', 0.5)
                    peach = rel_res.get('Peach_Blossom_Amplitude', 0)
                    
                    # 综合评分公式：
                    # 1. 基础分：状态权重
                    # 2. 轨道稳定性：越低越危险 (倒数)
                    # 3. 相位相干度：越低越危险 (倒数)
                    # 4. 桃花振幅：越高越危险 (正相关)
                    # 5. 绑定能：越弱（数值越高/越接近0）越危险
                    
                    # 基础分
                    if state_r == "UNBOUND":
                        base_score = 2.0
                    elif state_r == "PERTURBED":
                        base_score = 1.2
                    elif state_r == "BOUND":
                        base_score = 0.5
                    elif state_r == "ENTANGLED":
                        base_score = 0.3
                    else:
                        base_score = 0.8
                    
                    # 轨道不稳定惩罚：稳定性 < 1.0 时增加风险
                    orbit_penalty = max(0, (1.0 - orbital_stab) * 0.5)
                    
                    # 相位失相干惩罚：相干度 < 0.5 时增加风险
                    phase_penalty = max(0, (0.5 - phase_coh) * 0.8)
                    
                    # 桃花干扰加分
                    peach_boost = peach / 100.0  # 归一化
                    
                    # 绑定能惩罚：能量 > -100 表示弱绑定
                    # 典型范围 -900 到 -50，越接近0越弱
                    bind_penalty = max(0, (bind_e + 100) / 200.0) if bind_e > -100 else 0
                    
                    r_score = base_score + orbit_penalty + phase_penalty + peach_boost + bind_penalty
                    
                    # 只记录有意义的风险 (>= 0.8)
                    if r_score >= 0.8:
                        risk_nodes.append({
                            'timestamp': t_time.isoformat(),
                            'reason': f"Relationship: {state_r} (σ={orbital_stab:.1f}, η={phase_coh:.2f}, 桃花={peach:.0f})",
                            'metrics': metrics,
                            'topic': 'relationship',
                            'risk_score': round(r_score, 2)
                        })
                    
        return {
            'metadata': {
                'start_year': s_year,
                'end_year': e_year,
                'dm': dm,
                'resolution': resolution
            },
            'timeline': timeline,
            'risk_nodes': risk_nodes
        }

    def _identify_risk_reason(self, metrics: Dict[str, Any]) -> str:
        reasons = []
        if metrics['sai'] > 0.6: reasons.append("CRITICAL_STRESS (SAI)")
        if metrics['entropy'] > 1.5: reasons.append("HIGH_ENTROPY (S)")
        if metrics['ic'] > 0.6: reasons.append("PHASE_JITTER (IC)")
        return " | ".join(reasons)
