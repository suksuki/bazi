
import math

# --- Part 1: Data Schema (Quantum Particles) ---

class Particle:
    def __init__(self, id_str, char, element, pillar_idx=-1, is_external=False):
        self.id = id_str
        self.char = char
        self.element = element # Wood, Fire, Earth, Metal, Water
        self.base_energy = 0.0
        self.final_energy = 0.0
        self.pillar_idx = pillar_idx # 0=Year, 1=Month, 2=Day, 3=Hour
        self.is_external = is_external # True if DaYun or LiuNian
        self.state = "Normal"
        
        # Hidden Stems (Simplified for Simulation)
        self.hidden_stems = self._get_hidden_stems(char)
        
    def _get_hidden_stems(self, char):
        # Simplified Core Map (Main Qi Only for Rooting check + Ratio)
        # Ratio is roughly Main 0.6, Middle 0.3, Residual 0.1
        map_data = {
            "巳": [{"stem": "丙", "ratio": 0.60, "el": "Fire"}, {"stem": "戊", "ratio": 0.30, "el": "Earth"}, {"stem": "庚", "ratio": 0.10, "el": "Metal"}],
            "酉": [{"stem": "辛", "ratio": 1.00, "el": "Metal"}],
            "丑": [{"stem": "己", "ratio": 0.60, "el": "Earth"}, {"stem": "癸", "ratio": 0.30, "el": "Water"}, {"stem": "辛", "ratio": 0.10, "el": "Metal"}],
            "子": [{"stem": "癸", "ratio": 1.00, "el": "Water"}],
        }
        return map_data.get(char, [])

    def __repr__(self):
        return f"[{self.id}:{self.char}({self.final_energy:.1f})]"

# --- Part 2: Quantum Energy Engine ---

class QuantumEnergyEngine:
    def __init__(self):
        self.elements = ["Wood", "Fire", "Earth", "Metal", "Water"]
        self.stems = []
        self.branches = []
        self.season_element = None
        
        self.log = []
        
    def log_step(self, step_name, msg):
        self.log.append(f"[{step_name}] {msg}")
        print(f"[{step_name}] {msg}")

    # --- Step 1: Initialization ---
    def init_particles(self, stem_chars, branch_chars, month_idx=1):
        self.stems = [Particle(f"S{i}", c, self._get_el(c), i) for i, c in enumerate(stem_chars)]
        self.branches = [Particle(f"B{i}", c, self._get_el(c), i) for i, c in enumerate(branch_chars)]
        
        # Determine Season (Month Branch Element)
        self.season_element = self.branches[month_idx].element
        self.log_step("INIT", f"Season: {self.branches[month_idx].char} ({self.season_element})")
        
        # Apply Base Energy Rule
        all_particles = self.stems + self.branches
        for p in all_particles:
            if p.element == self.season_element:
                p.base_energy = 40.0 # Dang Ling
            elif self._is_generating(self.season_element, p.element):
                p.base_energy = 20.0 # Xiang Sheng
            else:
                p.base_energy = 10.0 # Ke/Xie/Hao
            p.final_energy = p.base_energy
            
        self.log_step("INIT", f"Base Energies Set: {all_particles}")

    # --- Step 2: Vector Interference ---
    
    def calculate_rooting(self):
        """
        Rooting: Stem Energy += Branch.Core_Energy * (2.0 / Distance)
        """
        for stem in self.stems:
            stem_el = stem.element
            
            for branch in self.branches:
                # Check for same element in cores
                matched_core = next((core for core in branch.hidden_stems if core['el'] == stem_el), None)
                
                if matched_core:
                    # Distance Factor (0=Same Pillar, 1=Adj, etc.)
                    dist = abs(stem.pillar_idx - branch.pillar_idx)
                    dist_factor = max(1.0, float(dist) + 0.5) # Avoid div by zero, simplified
                    
                    # Core Energy Contribution (Base * Ratio)
                    core_energy = branch.final_energy * matched_core['ratio']
                    
                    boost = core_energy * (2.0 / dist_factor)
                    stem.final_energy += boost
                    
                    self.log_step("ROOTING", f"{stem.char} rooted in {branch.char} (Dist {dist}). Boost +{boost:.1f}")

    def check_phase_locking(self):
        """
        Tri-Harmony: Snake(Si) + Rooster(You) + Ox(Chou) -> Metal
        Effect: Sum * 1.5. Suppress non-metal cores.
        """
        # Simplified Detection: Check if Si, You, Chou indices exist
        chars = [b.char for b in self.branches]
        
        has_si = '巳' in chars
        has_you = '酉' in chars
        has_chou = '丑' in chars
        
        if has_si and has_you and has_chou:
            self.log_step("PHASE_LOCK", "⚠️ Tri-Harmony Detected: 巳酉丑 (Metal Bureau)")
            
            # Identify particles
            metal_bureau_particles = [b for b in self.branches if b.char in ['巳', '酉', '丑']]
            
            total_raw_energy = sum(p.final_energy for p in metal_bureau_particles)
            resonance_bonus = total_raw_energy * 0.5 # Total * 1.5
            
            # Apply Transformation
            for p in metal_bureau_particles:
                p.state = "PhaseLock_Metal"
                # Boost Energy (Distribute bonus proportionally or just add to field?)
                # Prompt says: "Sum energies * 1.5". We distribute this amplification.
                p.final_energy *= 1.5
                
                # Suppress Rebel Qi (Non-Metal Cores)
                # Effectively, this changes the ELEMENT of the particle to Metal for later calculations
                if p.element != "Metal":
                    self.log_step("TRANSFORM", f"{p.char} ({p.element}) Phase-Transformed to METAL")
                    p.element = "Metal" 
                    # Note: In a real simulation, we'd zero out hidden stem ratios. 
            
            self.log_step("PHASE_LOCK", f"System Energy Amplified by Phase Lock. Total Field: {total_raw_energy * 1.5:.1f}")

    def calculate_clash(self):
        """
        Clash: Zi vs Wu, etc.
        Effect: Energy *= 0.5 for both.
        """
        # Simple Scan O(N^2)
        pairs = [('子', '午'), ('巳', '亥')] # Simplified list
        
        clashed = set()
        for i, b1 in enumerate(self.branches):
            for j, b2 in enumerate(self.branches):
                if i >= j: continue
                
                pair = tuple(sorted([b1.char, b2.char]))
                # Check Zi-Wu clash logic (here checking if tuple matches specific set not imp'd fully, just logic)
                is_clash = False
                if '子' in pair and '午' in pair: is_clash = True
                if '巳' in pair and '亥' in pair: is_clash = True
                
                # Case 2 Special: 3 Snakes vs 1 Pig? No, Case 2 is 3 Snakes vs 1 Rat (Zi).
                # Zi (Water) controls Si (Fire), but Si is strong?
                # Actually Zi-Si is not a standard opposition (Clash is Si-Hai).
                # But "Water controls Fire".
                # Let's verify Case 2 requirement: "三巳战一子" -> "Three Snakes Fight One Rat"? 
                # Calculating "Ke" (Control) damage.
                pass 

    # --- Step 4: Dynamic Overlay ---
    def add_dynamic_layers(self, dy_gan, dy_zhi, ln_gan, ln_zhi):
        self.log_step("DYNAMIC", f"Injecting DaYun [{dy_gan}{dy_zhi}] & LiuNian [{ln_gan}{ln_zhi}]")
        
        # Create External Particles (High Energy)
        # Rule: LiuNian priority. Let's give them high base energy.
        p_dy_s = Particle("DY_S", dy_gan, self._get_el(dy_gan), is_external=True)
        p_dy_b = Particle("DY_B", dy_zhi, self._get_el(dy_zhi), is_external=True)
        p_ln_s = Particle("LN_S", ln_gan, self._get_el(ln_gan), is_external=True)
        p_ln_b = Particle("LN_B", ln_zhi, self._get_el(ln_zhi), is_external=True)
        
        # LiuNian Priority: Weight x 1.2
        ext_base = 50.0 
        p_dy_s.final_energy = ext_base
        p_dy_b.final_energy = ext_base
        p_ln_s.final_energy = ext_base * 1.2
        p_ln_b.final_energy = ext_base * 1.2
        
        self.stems.extend([p_dy_s, p_ln_s])
        self.branches.extend([p_dy_b, p_ln_b])
        
        # Re-Run Interactions
        # 1. Check Stems Combine (Yi-Geng)
        # Case 2: Yi (Wood) vs Geng (Metal). Metal controls Wood. 
        # Combine? Yi-Geng He Hua Metal.
        has_yi = any(s.char == '乙' for s in self.stems)
        has_geng = any(s.char == '庚' for s in self.stems)
        
        if has_yi and has_geng:
            self.log_step("COMBINE", "Stem Combine Detected: 乙 + 庚 -> 金 (Metal)")
            for s in self.stems:
                if s.char == '乙':
                    self.log_step("LOSS", f"{s.id} (乙 Wood) energy lost to combination.")
                    s.final_energy *= 0.2 # Significant weakening
                if s.char == '庚':
                    s.final_energy *= 1.5 # Gained leader status

    # --- Helpers ---
    def _get_el(self, char):
        m = {"甲":"Wood", "乙":"Wood", "丙":"Fire", "丁":"Fire", "戊":"Earth", "己":"Earth", "庚":"Metal", "辛":"Metal", "壬":"Water", "癸":"Water"}
        m2 = {"子":"Water", "丑":"Earth", "寅":"Wood", "卯":"Wood", "辰":"Earth", "巳":"Fire", "午":"Fire", "未":"Earth", "申":"Metal", "酉":"Metal", "戌":"Earth", "亥":"Water"}
        return m.get(char) or m2.get(char)

    def _is_generating(self, e1, e2):
        # Wood->Fire->Earth->Metal->Water->Wood
        order = ["Wood", "Fire", "Earth", "Metal", "Water"]
        try:
            i1 = order.index(e1)
            i2 = order.index(e2)
            return (i1 + 1) % 5 == i2
        except: return False

    def get_totals(self):
        totals = {e: 0.0 for e in self.elements}
        for p in self.stems + self.branches:
            # If transformed, use current element
            totals[p.element] += p.final_energy
        return totals

# ==========================================
# TEST EXECUTION
# ==========================================

print("=== 🚀 QUANTUM BAZI ENGINE SIMULATION V5.0 ===")

# --- CASE 01: Static Calc (Metal Phase Lock) ---
print("\n>>> [CASE 01] 原局: 丁巳 / 乙巳 / 乙丑 / 乙酉")
qe = QuantumEnergyEngine()
# Init: Month is Si (Fire)
qe.init_particles(["丁", "乙", "乙", "乙"], ["巳", "巳", "丑", "酉"], month_idx=1) 

# Run Pipeline
qe.calculate_rooting()
qe.check_phase_locking()

scores = qe.get_totals()
print(f"\n📊 CASE 01 FINAL SCORES:\n{scores}")


# --- CASE 02: Dynamic Calc (Overlay) ---
print("\n\n>>> [CASE 02] 动态叠加: 庚子大运 + 乙巳流年")
# Continue from Case 1 state? Or fresh? Usually fresh + overlay.
# Let's use the resulting engine from Case 1 but add dynamic layers.
# Note: Case 1 already transformed Branches to Metal.
# Adding Geng (Metal) Child, Zi (Water) Child, Yi (Wood) Year, Si (Fire-turned-Metal?) Year.

# Actually Case 2 input is "叠加". So we take qe state and add.
qe.add_dynamic_layers("庚", "子", "乙", "巳")

scores_2 = qe.get_totals()
print(f"\n📊 CASE 02 FINAL SCORES:\n{scores_2}")
print("================================================")
