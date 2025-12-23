
"""
Quantum Trinity V2.0: Logic Arbitrator
======================================
High-precision Bazi rule matching and geometric interaction arbitration.
"""

from typing import List, Dict, Optional, Any, Set
import numpy as np
from ..nexus.definitions import BaziParticleNexus, ArbitrationNexus, PhysicsConstants
from ..physics.wave_laws import WaveState, WaveLaws

class LogicArbitrator:
    """The 'Brain' that identifies structural locks and geometric overlaps."""

    @staticmethod
    def match_interactions(pillars: List[str], day_master: str) -> List[Dict[str, Any]]:
        """
        Identify active combinations, clashes, and structural locks.
        """
        stems = [p[0] for p in pillars if p]
        branches = [p[1] for p in pillars if len(p) > 1]
        branch_set = set(branches)
        interactions = []

        # Find DM relations
        dm_elem, _, _ = BaziParticleNexus.STEMS.get(day_master, ("Earth", "", 0))
        output_elem = PhysicsConstants.GENERATION[dm_elem]
        control_elem = None
        for k, v in PhysicsConstants.CONTROL.items():
            if v == dm_elem: control_elem = k
            
        # Detect Oppose (Phase 28)
        # Check if output and control elements both have representatives in stems or pillars
        has_output = any(BaziParticleNexus.STEMS[s][0] == output_elem for s in stems if s in BaziParticleNexus.STEMS)
        has_control = any(BaziParticleNexus.STEMS[s][0] == control_elem for s in stems if s in BaziParticleNexus.STEMS)
        
        # --- Phase 29: Dynamic Intervention Logic (Polarity Sensitive) ---
        dm_elem, dm_pol, _ = BaziParticleNexus.STEMS.get(day_master, ("Earth", "Yang", 0))
        resource_elem = None
        wealth_elem = None
        for k, v in PhysicsConstants.GENERATION.items():
            if v == dm_elem: resource_elem = k
        for k, v in PhysicsConstants.CONTROL.items():
            if k == dm_elem: wealth_elem = v
            
        stems_info = [BaziParticleNexus.STEMS.get(s) for s in stems if s in BaziParticleNexus.STEMS]
        
        # Capture: Same Polarity Output (Eating God) vs Same Polarity Control (7-Killings)
        has_shishen = any(info[0] == output_elem and info[1] == dm_pol for info in stems_info)
        has_qisha = any(info[0] == control_elem and info[1] == dm_pol for info in stems_info)
        
        # Cutting: Same Polarity Resource (Owl God) vs Eating God
        has_owl = any(info[0] == resource_elem and info[1] == dm_pol for info in stems_info)
        
        # Contamination: Wealth (Cai) vs Resource (Yin)
        has_wealth = any(info[0] == wealth_elem for info in stems_info)
        has_resource = any(info[0] == resource_elem for info in stems_info)

        # 1. OPPOSE (Shang Guan vs Zheng Guan) - Traditional Element Check
        if any(info[0] == output_elem for info in stems_info) and any(info[0] == control_elem for info in stems_info):
             dyn = ArbitrationNexus.DYNAMICS["OPPOSE"]
             interactions.append({
                 "id": "PH28_01", "type": "OPPOSE", "name": f"Shang Guan vs Zheng Guan ({output_elem}-{control_elem})",
                 "target_element": control_elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                 "priority": ArbitrationNexus.PRIORITY["OPPOSE"], "branches": set()
             })

        # 2. CAPTURE (Eating God vs Seven Killings)
        if has_shishen and has_qisha:
             dyn = ArbitrationNexus.DYNAMICS["CAPTURE"]
             interactions.append({
                 "id": "PH29_01", "type": "CAPTURE", "name": "Eating God Captures Killings",
                 "target_element": control_elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                 "priority": ArbitrationNexus.PRIORITY["CAPTURE"], "branches": set()
             })
             
        # 3. CUTTING (Owl God Cuts Food)
        if has_owl and has_shishen:
             dyn = ArbitrationNexus.DYNAMICS["CUTTING"]
             interactions.append({
                 "id": "PH29_02", "type": "CUTTING", "name": "Owl God Cuts Food (Interruption)",
                 "target_element": output_elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                 "priority": ArbitrationNexus.PRIORITY["CUTTING"], "branches": set()
             })

        # 4. CONTAMINATION (Wealth Breaks Seal)
        if has_wealth and has_resource:
             dyn = ArbitrationNexus.DYNAMICS["CONTAMINATION"]
             interactions.append({
                 "id": "PH29_03", "type": "CONTAMINATION", "name": "Wealth Contaminates Resource",
                 "target_element": resource_elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                 "priority": ArbitrationNexus.PRIORITY["CONTAMINATION"], "branches": set()
             })

        # 1. San Hui (Three Seasonal Meeting) - Priority 1
        for trio, elem in ArbitrationNexus.SAN_HUI.items():
            if trio.issubset(branch_set):
                dyn = ArbitrationNexus.DYNAMICS["SAN_HUI"]
                interactions.append({
                    "id": "A1", "type": "SAN_HUI", "name": f"Seasonal Meeting ({elem})",
                    "target_element": elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                    "priority": ArbitrationNexus.PRIORITY["SAN_HUI"], "branches": set(trio)
                })

        # 2. San He (Three Harmony) - Priority 2
        for trio, elem in ArbitrationNexus.SAN_HE.items():
            if trio.issubset(branch_set):
                dyn = ArbitrationNexus.DYNAMICS["SAN_HE"]
                interactions.append({
                    "id": "A2", "type": "SAN_HE", "name": f"Three Harmony ({elem})",
                    "target_element": elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                    "priority": ArbitrationNexus.PRIORITY["SAN_HE"], "branches": set(trio)
                })

        # 3. Liu He (Six Combinations) - Priority 3
        for pair, elem in ArbitrationNexus.LIU_HE.items():
            if pair.issubset(branch_set):
                dyn = ArbitrationNexus.DYNAMICS["LIU_HE"]
                interactions.append({
                    "id": "A3", "type": "LIU_HE", "name": f"Six Combination ({elem})",
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
                        "id": "B1", "type": "CLASH", "name": f"Clash ({b1}-{b2})",
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
                        "id": "R1", "type": "RESONANCE", "name": f"Resonance ({b})",
                        "target_element": elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                        "priority": ArbitrationNexus.PRIORITY["RESONANCE"], "branches": {b}
                    })

        # 6. Punishment (刑) - Priority 7
        # 6.1 Three-pillar Punishments
        for trio in ArbitrationNexus.PUNISHMENT_THREE:
            if trio.issubset(branch_set):
                dyn = ArbitrationNexus.DYNAMICS["PUNISHMENT"]
                interactions.append({
                    "id": "P1", "type": "PUNISHMENT", "name": f"Three-fold Punishment ({'-'.join(trio)})",
                    "target_element": "Chaos", "q": dyn['q'], "phi": dyn['phi'], "lock": False,
                    "priority": ArbitrationNexus.PRIORITY["PUNISHMENT"], "branches": set(trio)
                })
        
        # 6.2 Self-punishment
        for b in branches:
            if b in ArbitrationNexus.SELF_PUNISHMENT and branches.count(b) >= 2:
                # Avoid duplicates: only add once
                if not any(i['name'] == f"Self-Punishment ({b})" for i in interactions):
                    dyn = ArbitrationNexus.DYNAMICS["PUNISHMENT"]
                    interactions.append({
                        "id": "P2", "type": "PUNISHMENT", "name": f"Self-Punishment ({b})",
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
                        "id": "H1", "type": "HARM", "name": f"Harm ({b1}-{b2})",
                        "target_element": "Conflict", "q": dyn['q'], "phi": dyn['phi'], "lock": False,
                        "priority": ArbitrationNexus.PRIORITY["HARM"], "branches": {b1, b2}
                    })

        # 6. Arbitration: Sort and dedup
        # In V2, we keep all but tag priority
        interactions.sort(key=lambda x: x['priority'])
        
        return interactions

    @staticmethod
    def initialize_field(pillars: List[str], day_master: str) -> Dict[str, WaveState]:
        """
        Transforms Bazi characters into their initial physics WaveStates.
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
                b_elem, _, hidden = BaziParticleNexus.BRANCHES[b_char]
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
