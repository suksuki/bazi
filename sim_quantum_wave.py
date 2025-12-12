
import math

class WaveFunction:
    """
    Represents the quantum state of a Bazi particle.
    - distribution: Probability density over the 5 Elements (Must sum to 1.0)
    - amplitude: Total Energy Magnitude
    """
    def __init__(self, distribution=None, amplitude=0.0):
        self.elements = ["Wood", "Fire", "Earth", "Metal", "Water"]
        if distribution:
            self.dist = distribution
        else:
            self.dist = {e: 0.0 for e in self.elements}
        self.amplitude = amplitude

    def normalize(self):
        total = sum(self.dist.values())
        if total > 0:
            for k in self.dist:
                self.dist[k] /= total
        else:
            # Vacuous state? strictly shouldn't happen for active particles
            pass

    def collapse_to(self, target_element, strength=1.0):
        """
        Shifts the wavefunction towards a target element.
        strength: 0.0 to 1.0 (1.0 = full collapse to pure state)
        """
        for e in self.elements:
            if e == target_element:
                target_val = 1.0
            else:
                target_val = 0.0
            
            # Linear Interpolation (Lerp)
            self.dist[e] = self.dist[e] * (1 - strength) + target_val * strength
        
        self.normalize()

    def get_energy(self, element):
        return self.amplitude * self.dist.get(element, 0.0)

    def __repr__(self):
        # Show top 2 probabilities
        top = sorted(self.dist.items(), key=lambda x: x[1], reverse=True)[:2]
        s = ", ".join([f"{k}:{v:.2f}" for k, v in top])
        return f"[Amp:{self.amplitude:.1f} | {s}]"


class Particle:
    def __init__(self, char, id_str):
        self.char = char
        self.id = id_str
        # Initialize Wave Function based on Hidden Stems
        self.wave = self._init_wave(char)
        
    def _init_wave(self, char):
        # Hidden Stems Map (Rough Ratios)
        # Si (Snake): Bing (Fire) 60, Wu (Earth) 30, Geng (Metal) 10
        map_data = {
            "巳": {"Fire": 0.6, "Earth": 0.3, "Metal": 0.1},
            "酉": {"Metal": 1.0},
            "丑": {"Earth": 0.6, "Water": 0.3, "Metal": 0.1},
            "子": {"Water": 1.0},
            "丁": {"Fire": 1.0},
            "乙": {"Wood": 1.0},
            "庚": {"Metal": 1.0}
        }
        dist = map_data.get(char, {}).copy()
        
        # Fill missing with 0
        all_els = ["Wood", "Fire", "Earth", "Metal", "Water"]
        for e in all_els:
            if e not in dist: dist[e] = 0.0
            
        # Normalize just in case
        total = sum(dist.values())
        if total > 0:
            for k in dist: dist[k] /= total
            
        # Initial Amplitude (Base)
        # We'll set this dynamically later, but default to 10.0
        return WaveFunction(dist, amplitude=10.0)


class QuantumWaveEngine:
    def __init__(self):
        self.particles = []
        self.log = []

    def log_step(self, step, msg):
        self.log.append(f"[{step}] {msg}")
        print(f"[{step}] {msg}")

    def load_case(self, stem_chars, branch_chars, month_char):
        self.particles = []
        # Create Particles
        for i, c in enumerate(stem_chars):
            self.particles.append(Particle(c, f"STEM_{i}"))
        for i, c in enumerate(branch_chars):
            self.particles.append(Particle(c, f"BRANCH_{i}"))
            
        # Set Amplitudes based on Season (Month Branch)
        # Simplified Season Logic
        season_map = {
            "巳": "Fire", "酉": "Metal", "丑": "Earth", # etc
            "子": "Water"
        }
        season_el = season_map.get(month_char, "Earth")
        self.log_step("INIT", f"Month: {month_char} ({season_el})")
        
        for p in self.particles:
            # Check p's main qi (highest prob)
            main_el = max(p.wave.dist, key=p.wave.dist.get)
            
            if main_el == season_el:
                p.wave.amplitude = 50.0 # Dang Ling
            elif self._is_generating(season_el, main_el):
                p.wave.amplitude = 30.0 # Xiang Sheng
            else:
                p.wave.amplitude = 20.0 # Qiu/Si
                
            # Log initial states
            # print(f"  > {p.char}: {p.wave}")

    def run_phase_locking(self):
        """
        V5.1 Logic: Vector Rotation
        """
        chars = [p.char for p in self.particles if "BRANCH" in p.id]
        has_si = '巳' in chars
        has_you = '酉' in chars
        has_chou = '丑' in chars
        
        if has_si and has_you and has_chou:
            self.log_step("WAVE_MECH", "🌀 Tri-Harmony Field Detected (Si-You-Chou)")
            
            target_el = "Metal"
            branches = [p for p in self.particles if "BRANCH" in p.id]
            
            for p in branches:
                if p.char in ['巳', '酉', '丑']:
                    old_wave = str(p.wave)
                    
                    # 1. Amplitude Boost (Resonance)
                    p.wave.amplitude *= 1.5
                    
                    # 2. Vector Rotation (Collapse towards Metal)
                    # Not 100% collapse, but significant (e.g. 80%)
                    # This preserves some "Rebel Qi" (e.g. trace Fire in Snake)
                    p.wave.collapse_to("Metal", strength=0.8)
                    
                    self.log_step("COLLAPSE", f"{p.char}: {old_wave} -> {p.wave}")

    def run_rooting(self):
        """
        V5.1 Rooting: Stem absorbs energy from Branch based on Vector Overlap (Dot Product)
        """
        stems = [p for p in self.particles if "STEM" in p.id]
        branches = [p for p in self.particles if "BRANCH" in p.id]
        
        for s in stems:
            # Identify main element of stem
            s_main = max(s.wave.dist, key=s.wave.dist.get)
            
            for b_idx, b in enumerate(branches):
                # Calculate Overlap: Stem's Main Element density in Branch
                overlap = b.wave.dist.get(s_main, 0.0)
                
                if overlap > 0.05: # Threshold
                    # Absorb energy
                    # Amount = Branch_Amp * Overlap * DistanceFactor
                    # Simplified dist factor
                    dist_factor = 1.0 # Placeholder
                    
                    gain = b.wave.amplitude * overlap * 0.5 * dist_factor
                    s.wave.amplitude += gain
                    self.log_step("ROOTING", f"{s.char} absorbs {gain:.1f} from {b.char} (Overlap: {overlap:.2f})")

    def _is_generating(self, e1, e2):
        order = ["Wood", "Fire", "Earth", "Metal", "Water"]
        try:
            return (order.index(e1) + 1) % 5 == order.index(e2)
        except: return False

    def get_spectrum(self):
        spectrum = {e: 0.0 for e in ["Wood", "Fire", "Earth", "Metal", "Water"]}
        for p in self.particles:
            for e, prob in p.wave.dist.items():
                spectrum[e] += p.wave.amplitude * prob
        return spectrum

# --- EXECUTION ---

print("=== 🌊 QUANTUM WAVE FUNCTION SIMULATION (V5.1) ===")
engine = QuantumWaveEngine()

# Case 1: Si-You-Chou
engine.load_case(["丁", "乙", "乙", "乙"], ["巳", "巳", "丑", "酉"], "巳")

print("\n--- Phase 1: Entanglement (Tri-Harmony) ---")
engine.run_phase_locking()

print("\n--- Phase 2: Rooting (Vector Overlap) ---")
engine.run_rooting()

spec = engine.get_spectrum()
print(f"\n📊 FINAL ENERGY SPECTRUM:\n{spec}")
