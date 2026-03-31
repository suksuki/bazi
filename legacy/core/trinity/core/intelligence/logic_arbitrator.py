
"""
Quantum Trinity V2.0: Logic Arbitrator
======================================
High-precision Bazi rule matching and geometric interaction arbitration.
"""

from typing import List, Dict, Optional, Any, Set
import numpy as np
from ..nexus.definitions import BaziParticleNexus, ArbitrationNexus, PhysicsConstants
from ..physics.wave_laws import WaveState, WaveLaws
from ..assets.pillar_gravity_engine import PillarGravityEngine
from ..assets.resonance_booster import ResonanceBooster
import math

class LogicArbitrator:
    """The 'Brain' that identifies structural locks and geometric overlaps."""

    @staticmethod
    def calculate_field_intensities(
        pillars: List[str], 
        day_master: str, 
        phase_progress: float = 0.5,
        dispersion_engine: Any = None,
        geo_factor: float = 1.0
    ) -> Dict[str, float]:
        """
        Calculates the expectation values (intensities) for all 10 Shi Shen.
        Integrates Natal + Luck + Annual + Hidden Stems with non-linear weighting.
        """
        # 1. Initialize intensities map
        intensities = {
            "比肩": 0.0, "劫财": 0.0,
            "食神": 0.0, "伤官": 0.0,
            "偏财": 0.0, "正财": 0.0,
            "七杀": 0.0, "正官": 0.0,
            "偏印": 0.0, "正印": 0.0
        }

        if not day_master or day_master not in BaziParticleNexus.STEMS:
            return intensities

        # 2. Get Dynamic Pillar Weights (PH_PILLAR_GRAVITY)
        p_weights = PillarGravityEngine.calculate_dynamic_weights(phase_progress)
        weight_map = {
            'year': p_weights['Year'],
            'month': p_weights['Month'],
            'day': p_weights['Day'],
            'hour': p_weights['Hour'],
            'luck': 1.2,   # Coupling constant for Luck
            'annual': 1.5  # Coupling constant for Annual
        }
        pillar_names = ['year', 'month', 'day', 'hour', 'luck', 'annual']

        # 3. Accumulated Shi Shen Mapping
        # We look at each pillar and its hidden stems
        for idx, p in enumerate(pillars):
            if not p: continue
            p_name = pillar_names[idx] if idx < len(pillar_names) else 'unknown'
            base_w = weight_map.get(p_name, 1.0) * geo_factor
            
            # Stem Contribution
            s_char = p[0]
            if s_char in BaziParticleNexus.STEMS:
                ss_name = BaziParticleNexus.get_shi_shen(s_char, day_master)
                if ss_name in intensities:
                    # Apply Rooting Gain (PH_ROOTING_GAIN)
                    branches = [pp[1] for pp in pillars if len(pp) > 1]
                    gain_ctx = ResonanceBooster.calculate_resonance_gain(s_char, branches)
                    intensities[ss_name] += 10.0 * base_w * gain_ctx['gain']

            # Branch Hidden Stem Contribution (PH_QUANTUM_DISPERSION)
            b_char = p[1] if len(p) > 1 else ''
            if b_char in BaziParticleNexus.BRANCHES:
                hidden = BaziParticleNexus.get_branch_weights(
                    b_char, 
                    phase_progress=phase_progress, 
                    dispersion_engine=dispersion_engine
                )
                # Branches have naturally higher energy (1.5x)
                branch_base = base_w * 1.5
                for s_hidden, weight in hidden:
                    ss_name = BaziParticleNexus.get_shi_shen(s_hidden, day_master)
                    if ss_name in intensities:
                        # weight is 0-10
                        intensities[ss_name] += branch_base * weight

        return intensities

    @staticmethod
    def match_interactions(
        pillars: List[str], 
        day_master: str,
        phase_progress: float = 0.5,
        dispersion_engine: Any = None,
        geo_factor: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Identify active combinations, clashes, and structural locks using Field Intensity.
        [V2.1] Transitioned to Expectation Value based trigger.
        """
        # Calculate Intensities
        intensities = LogicArbitrator.calculate_field_intensities(
            pillars, day_master, phase_progress, dispersion_engine, geo_factor
        )
        
        branches = [p[1] for p in pillars if len(p) > 1]
        branch_set = set(branches)
        interactions = []

        # 1. OPPOSE (Shang Guan vs Zheng Guan)
        # Threshold adjusted for normalized weights ( Natal max ~10-15 )
        overlap_sg_zg = intensities["伤官"] * intensities["正官"]
        if overlap_sg_zg > 36.0: 
             dyn = ArbitrationNexus.DYNAMICS["OPPOSE"]
             interactions.append({
                 "id": "PH28_01", "type": "OPPOSE", "name": f"伤官见官",
                 "target_element": "Control", "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                 "priority": ArbitrationNexus.PRIORITY["OPPOSE"], "intensity": overlap_sg_zg,
                 "branches": set()
             })
 
        # 2. CAPTURE (Eating God vs Seven Killings)
        overlap_ss_qs = intensities["食神"] * intensities["七杀"]
        if overlap_ss_qs > 25.0:
             dyn = ArbitrationNexus.DYNAMICS["CAPTURE"]
             interactions.append({
                 "id": "PH29_01", "type": "CAPTURE", "name": "食神制杀",
                 "target_element": "Control", "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                 "priority": ArbitrationNexus.PRIORITY["CAPTURE"], "intensity": overlap_ss_qs,
                 "branches": set()
             })
              
        # 3. CUTTING (Owl God Cuts Food)
        overlap_py_ss = intensities["偏印"] * intensities["食神"]
        if overlap_py_ss > 20.0:
             dyn = ArbitrationNexus.DYNAMICS["CUTTING"]
             interactions.append({
                 "id": "PH29_02", "type": "CUTTING", "name": "枭神夺食",
                 "target_element": "Output", "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                 "priority": ArbitrationNexus.PRIORITY["CUTTING"], "intensity": overlap_py_ss,
                 "branches": set()
             })
 
        # 4. CONTAMINATION (Wealth Breaks Seal)
        overlap_zc_zi = (intensities["正财"] + intensities["偏财"]) * (intensities["正印"] + intensities["偏印"])
        if overlap_zc_zi > 20.0:
             dyn = ArbitrationNexus.DYNAMICS["CONTAMINATION"]
             interactions.append({
                 "id": "PH29_03", "type": "CONTAMINATION", "name": "财星坏印",
                 "target_element": "Resource", "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                 "priority": ArbitrationNexus.PRIORITY["CONTAMINATION"], "intensity": overlap_zc_zi,
                 "branches": set()
             })

        # 1. San Hui (Three Seasonal Meeting) - Priority 1
        for trio, elem in ArbitrationNexus.SAN_HUI.items():
            if trio.issubset(branch_set):
                dyn = ArbitrationNexus.DYNAMICS["SAN_HUI"]
                interactions.append({
                    "id": "PH_SAN_HUI", "type": "SAN_HUI", "name": f"地支三会 ({elem})",
                    "target_element": elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                    "priority": ArbitrationNexus.PRIORITY["SAN_HUI"], "branches": set(trio)
                })

        # 2. San He (Three Harmony) - Priority 2
        for trio, elem in ArbitrationNexus.SAN_HE.items():
            if trio.issubset(branch_set):
                dyn = ArbitrationNexus.DYNAMICS["SAN_HE"]
                interactions.append({
                    "id": "PH_SAN_HE", "type": "SAN_HE", "name": f"地支三合 ({elem})",
                    "target_element": elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                    "priority": ArbitrationNexus.PRIORITY["SAN_HE"], "branches": set(trio)
                })

        # 3. Liu He (Six Combinations) - Priority 3
        for pair, elem in ArbitrationNexus.LIU_HE.items():
            if pair.issubset(branch_set):
                dyn = ArbitrationNexus.DYNAMICS["LIU_HE"]
                interactions.append({
                    "id": "PH_LIU_HE", "type": "LIU_HE", "name": f"地支六合 ({elem})",
                    "target_element": elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                    "priority": ArbitrationNexus.PRIORITY["LIU_HE"], "branches": set(pair)
                })

        # 4. Clashes (Chong) - Priority 4
        chong_map = ArbitrationNexus.CLASH_MAP
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                b1, b2 = branches[i], branches[j]
                if chong_map.get(b1) == b2:
                    dyn = ArbitrationNexus.DYNAMICS["CLASH"]
                    elem1 = BaziParticleNexus.BRANCHES[b1][0]
                    interactions.append({
                        "id": "PH_CHONG", "type": "CLASH", "name": f"地支六冲 ({b1}-{b2})",
                        "target_element": elem1, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                        "priority": ArbitrationNexus.PRIORITY["CLASH"], "branches": {b1, b2}
                    })

        # 5. Resonance (Identical Branches) - Priority 5
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                if branches[i] == branches[j]:
                    b = branches[i]
                    elem = BaziParticleNexus.BRANCHES[b][0]
                    dyn = ArbitrationNexus.DYNAMICS["RESONANCE"]
                    interactions.append({
                        "id": "PH_RESONANCE", "type": "RESONANCE", "name": f"同支伏吟 ({b})",
                        "target_element": elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                        "priority": ArbitrationNexus.PRIORITY["RESONANCE"], "branches": {b}
                    })

        # 6. Punishment (刑) - Priority 7
        # 6.1 Three-pillar Punishments
        for trio in ArbitrationNexus.PUNISHMENT_THREE:
            if trio.issubset(branch_set):
                dyn = ArbitrationNexus.DYNAMICS["PUNISHMENT"]
                interactions.append({
                    "id": "PH_PENALTY_3", "type": "PUNISHMENT", "name": f"地支三刑 ({'-'.join(trio)})",
                    "target_element": "Chaos", "q": dyn['q'], "phi": dyn['phi'], "lock": False,
                    "priority": ArbitrationNexus.PRIORITY["PUNISHMENT"], "branches": set(trio)
                })
        
        # 6.2 Self-punishment
        for b in branches:
            if b in ArbitrationNexus.SELF_PUNISHMENT and branches.count(b) >= 2:
                # Avoid duplicates: only add once
                if not any(i['name'] == f"地支自刑 ({b})" for i in interactions):
                    dyn = ArbitrationNexus.DYNAMICS["PUNISHMENT"]
                    interactions.append({
                        "id": "PH_PENALTY_3", "type": "PUNISHMENT", "name": f"地支自刑 ({b})",
                        "target_element": BaziParticleNexus.BRANCHES[b][0], "q": dyn['q'], "phi": dyn['phi'], "lock": False,
                        "priority": ArbitrationNexus.PRIORITY["PUNISHMENT"], "branches": {b}
                    })

        # 7. Harm (害) - Priority 6
        harm_map = ArbitrationNexus.HARM_MAP
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                b1, b2 = branches[i], branches[j]
                if harm_map.get(b1) == b2:
                    dyn = ArbitrationNexus.DYNAMICS["HARM"]
                    interactions.append({
                        "id": "PH_HARM_6", "type": "HARM", "name": f"地支相害 ({b1}-{b2})",
                        "target_element": "Conflict", "q": dyn['q'], "phi": dyn['phi'], "lock": False,
                        "priority": ArbitrationNexus.PRIORITY["HARM"], "branches": {b1, b2}
                    })

        # 6. Arbitration: Sort and dedup
        # In V2, we keep all but tag priority
        interactions.sort(key=lambda x: x['priority'])
        
        return interactions

    @staticmethod
    def initialize_field(pillars: List[str], day_master: str, 
                         phase_progress: Optional[float] = None,
                         dispersion_engine: Optional[Any] = None) -> Dict[str, WaveState]:
        """
        Transforms Bazi characters into their initial physics WaveStates.
        [Phase B] Now supports dynamic hidden stem energy allocation.
        """
        waves = {e: WaveState(1e-6, PhysicsConstants.ELEMENT_PHASES[e]) for e in PhysicsConstants.ELEMENT_PHASES}
        
        pillar_names = ['year', 'month', 'day', 'hour', 'luck', 'annual']
        
        # Phase 28: Clash Damping logic
        branches = [p[1] for p in pillars if len(p) > 1]
        clash_map = ArbitrationNexus.CLASH_MAP
        clashed_indices = set()
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                if clash_map.get(branches[i]) == branches[j]:
                    clashed_indices.add(i)
                    clashed_indices.add(j)

        # Phase 1: Context Detection (Season)
        month_b = pillars[1][1] if len(pillars) > 1 and len(pillars[1]) > 1 else '寅'
        seasonal_factors = PhysicsConstants.SEASONAL_MATRIX.get(month_b, {e: 1.0 for e in PhysicsConstants.ELEMENT_PHASES})

        for idx, p in enumerate(pillars):
            if not p: continue
            name = pillar_names[idx] if idx < len(pillar_names) else 'unknown'
            w_prio = PhysicsConstants.PILLAR_WEIGHTS.get(name, 1.0)
            
            # Stem Contribution
            s_char = p[0]
            if s_char in BaziParticleNexus.STEMS:
                elem, _, _ = BaziParticleNexus.STEMS[s_char]
                # Apply Season Multiplier
                s_seasonal = seasonal_factors.get(elem, 1.0)
                amp = PhysicsConstants.BASE_SCORE * w_prio * s_seasonal
                # Damping if pillar is in a clash
                if idx in clashed_indices: amp *= 0.5
                source = WaveState(amp, PhysicsConstants.ELEMENT_PHASES[elem])
                waves[elem] = WaveState.from_complex(waves[elem].to_complex() + source.to_complex())
            
            # Branch Contribution
            b_char = p[1] if len(p) > 1 else ''
            if b_char in BaziParticleNexus.BRANCHES:
                b_elem, _, _ = BaziParticleNexus.BRANCHES[b_char] # Element only
                
                # [Phase B] Get Hidden Stems - Dynamic or Static
                hidden = BaziParticleNexus.get_branch_weights(
                    b_char, 
                    phase_progress=phase_progress, 
                    dispersion_engine=dispersion_engine
                )
                
                b_seasonal = seasonal_factors.get(b_elem, 1.0)
                base_b_amp = PhysicsConstants.BASE_SCORE * w_prio * 1.5 * b_seasonal
                if idx in clashed_indices: base_b_amp *= 0.3 # Heavier damping for branches
                
                for s_hidden, weight in hidden:
                    h_elem, _, _ = BaziParticleNexus.STEMS.get(s_hidden, ("Earth", "", 0))
                    h_seasonal = seasonal_factors.get(h_elem, 1.0)
                    h_amp = base_b_amp * (weight / 10.0) * h_seasonal
                    h_source = WaveState(h_amp, PhysicsConstants.ELEMENT_PHASES[h_elem])
                    waves[h_elem] = WaveState.from_complex(waves[h_elem].to_complex() + h_source.to_complex())
                    
        return {e: WaveLaws.apply_saturation(w) for e, w in waves.items()}
