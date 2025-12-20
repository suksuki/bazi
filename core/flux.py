
import numpy as np
import math
import warnings
from core.kernel import Kernel

# [DEPRECATION WARNING] V13.0
# FluxEngine is a legacy engine that does NOT use ProbValue (probability wave functions).
# For production use, please migrate to GraphNetworkEngine which fully implements
# probabilistic calculations and non-linear physics.
# See: core/engine_graph.py
warnings.warn(
    "FluxEngine is deprecated. Use GraphNetworkEngine for ProbValue-based calculations.",
    DeprecationWarning,
    stacklevel=2
)

class WaveFunction:
    """
    Quantum State of a Bazi Particle (V5.1 Protocol)
    """
    def __init__(self, distribution=None, amplitude=10.0):
        self.elements = ["Wood", "Fire", "Earth", "Metal", "Water"]
        if distribution:
            self.dist = distribution
        else:
            self.dist = {e: 0.0 for e in self.elements}
        self.amplitude = amplitude
        self.entropy = 0.0 # V5.5: Track disorder (Heat)

    def normalize(self):
        total = sum(self.dist.values())
        if total > 0:
            for k in self.dist:
                self.dist[k] /= total
        
    def collapse_to(self, target_element, strength=1.0):
        for e in self.elements:
            target_val = 1.0 if e == target_element else 0.0
            self.dist[e] = self.dist[e] * (1 - strength) + target_val * strength
        self.normalize()

    def get_energy(self, element):
        return self.amplitude * self.dist.get(element, 0.0)
    
    def copy(self):
        w = WaveFunction(self.dist.copy(), self.amplitude)
        w.entropy = self.entropy
        return w

class Particle:
    """
    Fundamental unit of the Bazi Universe.
    Follows Kernel Axiom 1: Structure.
    """
    def __init__(self, char, id_str, p_type):
        self.char = char
        self.id = id_str
        self.type = p_type # 'stem' or 'branch'
        self.angle = Kernel.get_angle(char) if p_type == 'branch' else None
        
        # Lists to track physics events
        self.interactions = [] 
        self.status = [] 
        
        # Initialize Wave Function based on Type (Axiom 1 & 3)
        self.wave = self._init_state()

        # V13.0 State Kernel: Plastic Structure Health
        self.health = 100.0 # S-Value (Persistent)

    def _init_state(self):
        if self.type == 'branch':
            # Axiom 1: Branch = Shell-Core Structure
            # Axiom 3: Branch = Mass (Potential Energy)
            
            # 1. Load Core Composition (Hidden Stems)
            core_stems = Kernel.HIDDEN_STEMS.get(self.char, {})
            
            # Map stems to elements for the wave distribution
            dist = {e: 0.0 for e in ["Wood", "Fire", "Earth", "Metal", "Water"]}
            if core_stems:
                for stem, ratio in core_stems.items():
                    props = Kernel.STEM_PROPERTIES.get(stem)
                    if props:
                        el = props['element']
                        dist[el] += ratio
            else:
                pass # Default empty 
                
            # 2. Determine Mass (Amplitude) based on Position (Axiom 3)
            # Find which pillar this is (year/month/day/hour)
            mass = 10.0 # Base
            for key, weight in Kernel.POSITION_WEIGHTS.items():
                if key in self.id:
                    mass = 100.0 * weight # Scale 100 base
                    break
            
            return WaveFunction(dist, amplitude=mass)
            
        elif self.type == 'stem':
            # Axiom 1: Stem = Wave/Ray
            # Axiom 3: Stem = Intensity (Kinetic Energy)
            
            # Starts as Virtual Image (Low Intensity) until Rooted
            props = Kernel.STEM_PROPERTIES.get(self.char, {})
            dist = {e: 0.0 for e in ["Wood", "Fire", "Earth", "Metal", "Water"]}
            if props:
                dist[props['element']] = 1.0
            
            return WaveFunction(dist, amplitude=5.0) # Low base intensity
            
        return WaveFunction()

class FluxEngine:
    """
    Antigravity V7.0 Physics Engine.
    Implements the Unified Axioms from the Kernel.
    """
    def __init__(self, chart):
        self.chart = chart
        self.particles = []
        self.log = []
        self.disabled_rules = set() # V18.0: Interaction Control
        self.detected_rules = set() # V18.0: For UI to discover what happened
        
        self.params = {
            "entropy_penalty": 0.5,
        }
        
        # Initialize particles immediately for tests/consumers expecting them
        self._build_particles()

    def _build_particles(self, state_map=None):
        self.particles = []
        pillars = ['year', 'month', 'day', 'hour']
        for p_name in pillars:
            p_data = self.chart.get(p_name)
            if not p_data: continue
            
            # Stem
            s_char = p_data.get('stem')
            if s_char:
                pid = f"{p_name}_stem"
                p = Particle(s_char, pid, "stem")
                if state_map and pid in state_map:
                    p.health = state_map[pid]
                self.particles.append(p)
            
            # Branch
            b_char = p_data.get('branch')
            if b_char:
                pid = f"{p_name}_branch"
                p = Particle(b_char, pid, "branch")
                if state_map and pid in state_map:
                    p.health = state_map[pid]
                self.particles.append(p)

    def set_environment(self, da_yun=None, liu_nian=None):
        if da_yun:
            s, b = da_yun.get('stem'), da_yun.get('branch')
            if s: self._inject_particle(s, "dy_stem", "stem", 40.0)
            if b: self._inject_particle(b, "dy_branch", "branch", 50.0) 

        if liu_nian:
            s, b = liu_nian.get('stem'), liu_nian.get('branch')
            if s: self._inject_particle(s, "ln_stem", "stem", 60.0) 
            if b: self._inject_particle(b, "ln_branch", "branch", 60.0) 

    def _inject_particle(self, char, pid, ptype, amp):
        p = Particle(char, pid, ptype)
        p.wave.amplitude = amp
        self.particles.append(p)

    def set_hyperparameters(self, params):
        """
        V18.0: Update physics engine parameters dynamically.
        Matches keys from Architect Console.
        """
        for k, v in params.items():
            # Map legacy or external keys to internal params if needed
            self.params[k] = v

    def V18_init_interaction_events(self):
         self.interaction_events = []

    def compute_energy_state(self):
        trace = {}
        self.detected_rules = set() # Reset
        self.interaction_events = [] # V18.1: Structured Trace
        
        # 1. Geometric Interactions (Shell-Shell Physics)
        self._solve_branch_geometry()
        
        # 2. Wave Propagation (Core-to-Stem Physics)
        self._solve_stem_intensity()

        # Capture L1 (Physical/Initial) Spectrum for Architect Console
        trace['l1_spectrum'] = self._get_current_spectrum()

        # 3. Global Flux Network (The Calculator V15.0)
        self._solve_global_flux(trace)
        
        # 4. Field Effects (Spacetime Dynamics V16.0)
        self._solve_spacetime_dynamics()
        
        # Snapshot Final (L2 / Heuristic)
        trace['spectrum'] = self._get_current_spectrum()
        trace['l2_spectrum'] = trace['spectrum'] # Alias for console compatibility
        trace['interactions'] = self.interaction_events # Export to Trace
        
        # --- Compatibility Layer ---
        ten_gods_data = self._generate_ten_gods_view(trace['spectrum'])
        
        result = {
            'spectrum': trace['spectrum'],
            'log': self.log,
            'particle_states': [
                {'id': p.id, 'char': p.char, 'type': p.type, 'amp': p.wave.amplitude, 'health': p.health, 'status': p.status} 
                for p in self.particles
            ],
            'trace': trace,
            'detected_rules': list(self.detected_rules) # Export for UI
        }
        result.update(ten_gods_data)
        
        new_state_map = {}
        for p in self.particles:
            if "dy_" in p.id or "ln_" in p.id: continue
            if p.wave.amplitude < 15.0 and ("StructureBroken" in p.status or "ShellRuptured" in p.status):
                dmg = 20.0
                p.health = max(0.0, p.health - dmg)
                self.log.append(f"💔 PERMANENT DAMAGE: {p.char} Health -{dmg} (Current: {p.health})")
            new_state_map[p.id] = p.health
            
        result['final_state_map'] = new_state_map
        return result

    def _solve_branch_geometry(self):
        branches = [p for p in self.particles if p.type == 'branch']
        processed_pairs = set()
        
        # V18.1: Structural Logic - SanHe Trio Detection (Priority 1)
        trios = [
            ({'申', '子', '辰'}, "Water"),
            ({'亥', '卯', '未'}, "Wood"),
            ({'寅', '午', '戌'}, "Fire"),
            ({'巳', '酉', '丑'}, "Metal")
        ]
        
        for chars, element in trios:
            # Find particles matching these chars
            matched_particles = []
            for c in chars:
                found = [p for p in branches if p.char == c]
                if found:
                    matched_particles.append(found[0]) # Take first instance for simplicity logic
            
            # Check if we have 3 distinct chars covered
            if len(set(p.char for p in matched_particles)) == 3:
                # SanHe Formed!
                p1, p2, p3 = matched_particles[0], matched_particles[1], matched_particles[2]
                
                rule_key = f"SanHe: {element} Bureau"
                self.detected_rules.add(rule_key)
                if rule_key in self.disabled_rules:
                    self.log.append(f"🚫 Rule Disabled: {rule_key}")
                else:
                    self.log.append(f"🌊 三合局成象: {p1.char}-{p2.char}-{p3.char} -> {element}局 (SanHe Bureau)")
                    
                    # Mark pairs as processed to avoid double counting BanHe
                    ids = sorted([p1.id, p2.id, p3.id])
                    processed_pairs.add(tuple(sorted((p1.id, p2.id))))
                    processed_pairs.add(tuple(sorted((p1.id, p3.id))))
                    processed_pairs.add(tuple(sorted((p2.id, p3.id))))
                    
                    # Apply Effect
                    # Delta tracking?
                    d_p1 = p1.wave.amplitude * 0.5
                    d_p2 = p2.wave.amplitude * 0.5
                    d_p3 = p3.wave.amplitude * 0.5
                    
                    p1.wave.amplitude += d_p1
                    p2.wave.amplitude += d_p2
                    p3.wave.amplitude += d_p3
                    
                    for p in [p1, p2, p3]:
                        p.status.append(f"PhaseLock_{element}")
                        p.wave.collapse_to(element, strength=0.9)
                        
                    # Structured Trace
                    self.interaction_events.append({
                        "type": "SanHe",
                        "name": f"三合{element}局",
                        "participants": [p.char for p in [p1, p2, p3]],
                        "theory": f"三合完整能量场 ({element} Frame)",
                        "delta": {
                            p1.char: f"+{d_p1:.1f}",
                            p2.char: f"+{d_p2:.1f}",
                            p3.char: f"+{d_p3:.1f}"
                        }
                    })

        # Pairwise Loop (Priority 2)
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                p1, p2 = branches[i], branches[j]
                
                pair_id = tuple(sorted([p1.id, p2.id]))
                if pair_id in processed_pairs: continue
                processed_pairs.add(pair_id)
                
                interaction = Kernel.get_interaction_type(p1.char, p2.char)
                
                if interaction:
                    # Rename SanHe to BanHe (Half) if occurring pairwise
                    if interaction == "SanHe":
                        interaction = "BanHe" 
                        
                    chars = sorted([p1.char, p2.char])
                    rule_key = f"{interaction}: {'-'.join(chars)}"
                    self.detected_rules.add(rule_key)
                    if rule_key in self.disabled_rules:
                        self.log.append(f"🚫 Rule Disabled: {rule_key}")
                        continue
                
                    if interaction == "BanHe": 
                        target = self._get_sanhe_target(p1.char, p2.char)
                        cn_target = {"Water":"水", "Fire":"火", "Wood":"木", "Metal":"金", "Earth":"土"}.get(target, target)
                        
                        d_p1, d_p2 = p1.wave.amplitude * 0.2, p2.wave.amplitude * 0.2
                        
                        self.log.append(f"🔄 半合拱气: {p1.char}-{p2.char} -> {target}气 (BanHe)")
                        p1.status.append(f"PhaseLock_{target}")
                        p2.status.append(f"PhaseLock_{target}")
                        
                        p1.wave.amplitude += d_p1
                        p2.wave.amplitude += d_p2
                        self._apply_sanhe_transformation(p1, p2, target)
                        
                        self.interaction_events.append({
                            "type": "BanHe",
                            "name": f"半合{cn_target}局",
                            "participants": [p1.char, p2.char],
                            "theory": f"半合拱局 (Semi-Harmony {target})",
                            "delta": {p1.char: f"+{d_p1:.1f}", p2.char: f"+{d_p2:.1f}"}
                        })
                        
                    elif interaction == "LiuChong":
                        self.log.append(f"💥 能量冲克: {p1.char}-{p2.char} (Collision)")
                        p1.status.append("ShellRuptured")
                        p2.status.append("ShellRuptured")
                        
                        # Logic: Energy Loss
                        loss_p1 = p1.wave.amplitude * 0.4
                        loss_p2 = p2.wave.amplitude * 0.4
                        
                        p1.wave.amplitude -= loss_p1
                        p2.wave.amplitude -= loss_p2
                        p1.wave.entropy += 20.0
                        p2.wave.entropy += 20.0
                        
                        self.interaction_events.append({
                            "type": "LiuChong",
                            "name": "六冲",
                            "participants": [p1.char, p2.char],
                            "theory": "对冲撞击 (180° Axial Clash)",
                            "delta": {p1.char: f"-{loss_p1:.1f}", p2.char: f"-{loss_p2:.1f}"}
                        })
                        
                    elif interaction == "XiangXing":
                        self.log.append(f"⚔️ 刑伤剪切: {p1.char}-{p2.char} (Shear Stress)")
                        p1.status.append("ShearStress")
                        p2.status.append("ShearStress")
                        
                        loss_p1 = p1.wave.amplitude * 0.2
                        loss_p2 = p2.wave.amplitude * 0.2
                        
                        p1.wave.amplitude -= loss_p1
                        p2.wave.amplitude -= loss_p2
                        
                        self.interaction_events.append({
                            "type": "XiangXing",
                            "name": "相刑",
                            "participants": [p1.char, p2.char],
                            "theory": "侧向刑伤 (90° Shear Stress)",
                            "delta": {p1.char: f"-{loss_p1:.1f}", p2.char: f"-{loss_p2:.1f}"}
                        })

    def _get_sanhe_target(self, c1, c2):
        water_set = {"申", "子", "辰"}
        metal_set = {"巳", "酉", "丑"}
        fire_set = {"寅", "午", "戌"}
        wood_set = {"亥", "卯", "未"}
        
        if c1 in water_set and c2 in water_set: return "Water"
        if c1 in metal_set and c2 in metal_set: return "Metal"
        if c1 in fire_set and c2 in fire_set: return "Fire"
        if c1 in wood_set and c2 in wood_set: return "Wood"
        return None

    def _apply_sanhe_transformation(self, p1, p2, target=None):
        if not target:
             target = self._get_sanhe_target(p1.char, p2.char)
        
        if target:
            p1.wave.collapse_to(target, strength=0.8)
            p2.wave.collapse_to(target, strength=0.8)

    def _solve_stem_intensity(self):
        stems = [p for p in self.particles if p.type == 'stem']
        branches = [p for p in self.particles if p.type == 'branch']
        
        for s in stems:
            s_elem = max(s.wave.dist, key=s.wave.dist.get)
            max_root_strength = 0.0
            total_root_energy = 0.0
            
            for b in branches:
                transmittance = b.wave.dist.get(s_elem, 0.0)
                if transmittance > 0:
                    flow = b.wave.amplitude * transmittance
                    total_root_energy += flow
                    max_root_strength = max(max_root_strength, transmittance)
                    
                    # Reverse Tagging: Branch is "Revealed" by this Stem
                    # Avoid duplicates if possible, or dedup later in UI
                    if "Revealed" not in b.status:
                        b.status.append("Revealed")
            
            # This is "internal" physics, usually not switchable, but let's allow blocking specific root? No.
            
            if max_root_strength < 0.1 and total_root_energy < 5.0:
                s.wave.amplitude = 2.0 
                s.status.append("VirtualImage")
            else:
                s.wave.amplitude = 5.0 + total_root_energy
                s.status.append("Rooted") # Explicit Positive Confirmation
                if total_root_energy > 30.0:
                    s.status.append("LaserBeam") 

    def _solve_global_flux(self, trace):
        node_map = {p.id: p for p in self.particles}
        pillars = ['year', 'month', 'day', 'hour']
        connections = [] 
        
        # Build Edges
        for i, p_name in enumerate(pillars):
            s_id = f"{p_name}_stem"
            b_id = f"{p_name}_branch"
            
            if s_id in node_map and b_id in node_map:
                self._add_flow_edge(node_map[s_id], node_map[b_id], connections)
                self._add_flow_edge(node_map[b_id], node_map[s_id], connections)
            
            if i < len(pillars) - 1:
                next_p = pillars[i+1]
                ns_id = f"{next_p}_stem"
                nb_id = f"{next_p}_branch"
                targets = [t for t in [ns_id, nb_id] if t in node_map]
                sources = [s for s in [s_id, b_id] if s in node_map]
                for src_id in sources:
                    for tgt_id in targets:
                        self._add_flow_edge(node_map[src_id], node_map[tgt_id], connections)

        # Simulate Flow
        transfer_rate = 0.3 
        net_flow_map = {pid: 0.0 for pid in node_map}
        
        for src, tgt in connections:
            # V18.0: Flow Control? Flow is implicit. 
            pass  
            
            amount = src.wave.amplitude * transfer_rate
            src.wave.amplitude -= amount
            tgt.wave.amplitude += amount
            net_flow_map[src.id] -= amount
            net_flow_map[tgt.id] += amount
            
            self.log.append(f"🌊 Flow: {src.char} -> {tgt.char} ({amount:.1f}E)")
            
        # Synergy (Lian Zhu)
        for e1 in connections:
            src1, mid1 = e1
            for e2 in connections:
                mid2, end2 = e2
                if mid1 == mid2 and src1 != end2:
                    
                    # Rule Check
                    rule_key = f"Synergy: {src1.char}->{mid1.char}->{end2.char}"
                    self.detected_rules.add(rule_key)
                    if rule_key in self.disabled_rules:
                        continue
                        
                    end2.wave.amplitude *= 1.25
                    end2.status.append("SynergyBoost")
                    self.log.append(f"✨ Lian Zhu Synergy: {src1.char}->{mid1.char}->{end2.char} (+25%)")

        if net_flow_map:
            sink_id = max(net_flow_map, key=net_flow_map.get)
            sink_val = net_flow_map[sink_id]
            if sink_val > 5.0: 
                sink_node = node_map[sink_id]
                sink_node.status.append("SystemFocus")
                trace['system_focus'] = {
                    'id': sink_id, 
                    'char': sink_node.char, 
                    'net_flow': sink_val,
                    'final_energy': sink_node.wave.amplitude
                }
                self.log.append(f"🎯 System Focus (Sink): {sink_node.char} (Net +{sink_val:.1f})")

    def _add_flow_edge(self, p1, p2, edge_list):
        e1 = self._get_main_element(p1)
        e2 = self._get_main_element(p2)
        if Kernel.ELEMENT_GENERATION.get(e1) == e2:
            edge_list.append((p1, p2))

    def _get_main_element(self, p):
        return max(p.wave.dist, key=p.wave.dist.get)

    def _solve_spacetime_dynamics(self):
        dy_stem = next((p for p in self.particles if p.id == "dy_stem"), None)
        dy_branch = next((p for p in self.particles if p.id == "dy_branch"), None)
        
        dy_elements = set()
        if dy_stem: dy_elements.add(self._get_main_element(dy_stem))
        if dy_branch: dy_elements.add(self._get_main_element(dy_branch))
        
        natal_elements = set()
        for p in self.particles:
            if "dy_" not in p.id and "ln_" not in p.id:
                natal_elements.add(self._get_main_element(p))
                
        for dy_elem in dy_elements:
            e_prev = None
            e_next = Kernel.ELEMENT_GENERATION.get(dy_elem)
            for k, v in Kernel.ELEMENT_GENERATION.items():
                if v == dy_elem:
                    e_prev = k
                    break
            
            if e_prev in natal_elements and e_next in natal_elements:
                rule_key = f"TongGuan: {dy_elem} bridges {e_prev}->{e_next}"
                self.detected_rules.add(rule_key)
                if rule_key in self.disabled_rules: continue
                
                self.log.append(f"🌉 Structural Repair (Tong Guan): Da Yun {dy_elem} bridges {e_prev}->{e_next}")
                for p in self.particles:
                    p.wave.amplitude *= 1.1 
        
        ln_stem = next((p for p in self.particles if p.id == "ln_stem"), None)
        ln_branch = next((p for p in self.particles if p.id == "ln_branch"), None)
        
        if ln_stem or ln_branch:
             self._solve_liunian_trigger(ln_stem, ln_branch)
             
    def _solve_liunian_trigger(self, ln_stem, ln_branch):
        natal_branches = [p for p in self.particles if p.type == 'branch' and "ln_" not in p.id and "dy_" not in p.id]
        
        if ln_stem:
            ln_elem = self._get_main_element(ln_stem)
            for nb in natal_branches:
                core = Kernel.HIDDEN_STEMS.get(nb.char, {})
                for h_stem in core:
                    h_elem = Kernel.STEM_PROPERTIES[h_stem]['element']
                    if h_elem == ln_elem:
                         rule_key = f"Activation: LN {ln_stem.char}->{nb.char}({h_stem})"
                         self.detected_rules.add(rule_key)
                         if rule_key in self.disabled_rules: continue
                         
                         self.log.append(f"⚡ Activation: Liu Nian {ln_stem.char} activates {h_stem} in {nb.char}")
                         nb.wave.amplitude += 10.0 
                         nb.status.append("Activated")

        if ln_branch:
            for nb in natal_branches:
                interaction = Kernel.get_interaction_type(ln_branch.char, nb.char)
                if interaction == "LiuChong":
                    rule_key = f"LiuChong: {ln_branch.char}-{nb.char}"
                    self.detected_rules.add(rule_key)
                    if rule_key in self.disabled_rules: continue
                    
                    self.log.append(f"⚔️ CRITICAL: Liu Nian {ln_branch.char} CLASHES {nb.char}")
                    nb.status.append("StructureBroken")
                    nb.wave.amplitude *= 0.25 
                    nb.wave.entropy += 50.0 
                    
    def _get_current_spectrum(self):
        spec = {e: 0.0 for e in ["Wood", "Fire", "Earth", "Metal", "Water"]}
        for p in self.particles:
            for e in spec:
                spec[e] += p.wave.get_energy(e)
        return spec

    def _get_stem_spectrum(self):
        spec = {s: 0.0 for s in Kernel.STEM_PROPERTIES.keys()}
        for p in self.particles:
            if p.type == 'stem' and p.char in spec:
                spec[p.char] += p.wave.amplitude
        for p in self.particles:
            if p.type == 'branch':
                core = Kernel.HIDDEN_STEMS.get(p.char, {})
                for stem, ratio in core.items():
                    spec[stem] += p.wave.amplitude * ratio
        return spec

    def calculate_flux(self, dy_stem=None, dy_branch=None, ln_stem=None, ln_branch=None, state_map=None, disabled_rules=None):
        """
        Calculates flux with optional disabled rules (V18.0)
        """
        self.disabled_rules = disabled_rules or set()
        self._build_particles(state_map)
        
        for p in self.particles:
            if p.health < 100.0:
               p.wave.amplitude *= (p.health / 100.0)

        da_yun = None
        if dy_stem or dy_branch: 
            da_yun = {'stem': dy_stem, 'branch': dy_branch}
        
        liu_nian = None
        if ln_stem or ln_branch: 
            liu_nian = {'stem': ln_stem, 'branch': ln_branch}
        
        self.set_environment(da_yun, liu_nian)
        return self.compute_energy_state()

    # Legacy Wrapper for Ten Gods Engine UI mapping
    def _generate_ten_gods_view(self, spectrum):
        dm_stem = self.chart.get('day', {}).get('stem')
        if not dm_stem: return {}
        
        stem_spec = self._get_stem_spectrum()
        
        stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        gods_map = {
            "甲": {"甲":"BiJian", "乙":"JieCai", "丙":"ShiShen", "丁":"ShangGuan", "戊":"PianCai", "己":"ZhengCai", "庚":"QiSha", "辛":"ZhengGuan", "壬":"PianYin", "癸":"ZhengYin"},
            "乙": {"乙":"BiJian", "甲":"JieCai", "丁":"ShiShen", "丙":"ShangGuan", "己":"PianCai", "戊":"ZhengCai", "辛":"QiSha", "庚":"ZhengGuan", "癸":"PianYin", "壬":"ZhengYin"},
            "丙": {"丙":"BiJian", "丁":"JieCai", "戊":"ShiShen", "己":"ShangGuan", "庚":"PianCai", "辛":"ZhengCai", "壬":"QiSha", "癸":"ZhengGuan", "甲":"PianYin", "乙":"ZhengYin"},
            "丁": {"丁":"BiJian", "丙":"JieCai", "己":"ShiShen", "戊":"ShangGuan", "辛":"PianCai", "庚":"ZhengCai", "癸":"QiSha", "壬":"ZhengGuan", "乙":"PianYin", "甲":"ZhengYin"},
            "戊": {"戊":"BiJian", "己":"JieCai", "庚":"ShiShen", "辛":"ShangGuan", "壬":"PianCai", "癸":"ZhengCai", "甲":"QiSha", "乙":"ZhengGuan", "丙":"PianYin", "丁":"ZhengYin"},
            "己": {"己":"BiJian", "戊":"JieCai", "辛":"ShiShen", "庚":"ShangGuan", "癸":"PianCai", "壬":"ZhengCai", "乙":"QiSha", "甲":"ZhengGuan", "丁":"PianYin", "丙":"ZhengYin"},
            "庚": {"庚":"BiJian", "辛":"JieCai", "壬":"ShiShen", "癸":"ShangGuan", "甲":"PianCai", "乙":"ZhengCai", "丙":"QiSha", "丁":"ZhengGuan", "戊":"PianYin", "己":"ZhengYin"},
            "辛": {"辛":"BiJian", "庚":"JieCai", "癸":"ShiShen", "壬":"ShangGuan", "乙":"PianCai", "甲":"ZhengCai", "丁":"QiSha", "丙":"ZhengGuan", "己":"PianYin", "戊":"ZhengYin"},
            "壬": {"壬":"BiJian", "癸":"JieCai", "甲":"ShiShen", "乙":"ShangGuan", "丙":"PianCai", "丁":"ZhengCai", "戊":"QiSha", "己":"ZhengGuan", "庚":"PianYin", "辛":"ZhengYin"},
            "癸": {"癸":"BiJian", "壬":"JieCai", "乙":"ShiShen", "甲":"ShangGuan", "丁":"PianCai", "丙":"ZhengCai", "己":"QiSha", "戊":"ZhengGuan", "辛":"PianYin", "庚":"ZhengYin"}
        }
        
        current_map = gods_map.get(dm_stem, {})
        tg_data = {}
        
        labels = {
            "BiJian": "比肩 (Friend)", "JieCai": "劫财 (Rob Wealth)",
            "ShiShen": "食神 (Artist)", "ShangGuan": "伤官 (Rebel)",
            "PianCai": "偏财 (Windfall)", "ZhengCai": "正财 (Salary)",
            "QiSha": "七杀 (Warrior)", "ZhengGuan": "正官 (Leader)",
            "PianYin": "偏印 (Mystic)", "ZhengYin": "正印 (Sage)"
        }
        
        for s, energy in stem_spec.items():
            god_name = current_map.get(s, "Unknown")
            if god_name == "Unknown": continue
            
            # Fix: Add raw key for API/Dashboard access
            tg_data[god_name] = energy
            
            label = labels.get(god_name, god_name)
            tg_data[label] = {
                "score": round(energy, 1),
                "entropy": 0.5,
                "state": "Stable" if energy < 80 else "High Energy"
            }
            
        cat_map = {
            "比劫 (Friends/Self)": ["BiJian", "JieCai"],
            "食伤 (Talent/Output)": ["ShiShen", "ShangGuan"],
            "财星 (Wealth/Wife)": ["PianCai", "ZhengCai"],
            "官杀 (Power/Husband)": ["QiSha", "ZhengGuan"],
            "印枭 (Resource/Knowledge)": ["PianYin", "ZhengYin"]
        }
        for cat_label, god_codes in cat_map.items():
            total_score = 0
            for code in god_codes:
                label = labels[code]
                if label in tg_data:
                    total_score += tg_data[label]['score']
            tg_data[cat_label] = {"score": round(total_score, 1), "entropy": 0.5, "state": "Stable"}

        return tg_data
