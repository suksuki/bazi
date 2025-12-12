
import pytest
import sys
import os

# Adjust path to find core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.flux import FluxEngine
from core.kernel import Kernel

class TestConstitutionV1:
    """
    Validation Suite for ALGORITHM_CONSTITUTION_v1.0.md
    Ensures that the FluxEngine adheres to the Core Axioms.
    """

    # --- Test 1: Particle Structure (Shell-Core) ---
    def test_axiom_05_shell_core_structure(self):
        """
        Verifies Axiom 5: Branches are Shell-Core composites.
        Checks that hidden stems are correctly loaded.
        """
        # Create a chart with specific branches
        chart = {
            'year': {'branch': '寅'}, # Tiger: Jia(60), Bing(30), Wu(10)
            'month': {'branch': '子'}, # Rat: Gui(100)
        }
        
        flux = FluxEngine(chart)
        
        # 1. Check Tiger (Yin)
        tiger = next(p for p in flux.particles if p.char == '寅')
        dist = tiger.wave.dist
        
        # Verify Energy Distribution roughly matches Ratios
        # Note: WaveFunction normalizes, so sum is 1.0.
        # Elements: Wood(Jia), Fire(Bing), Earth(Wu)
        assert dist['Wood'] == pytest.approx(0.6, abs=0.05)
        assert dist['Fire'] == pytest.approx(0.3, abs=0.05)
        assert dist['Earth'] == pytest.approx(0.1, abs=0.05)
        
        # 2. Check Rat (Zi)
        rat = next(p for p in flux.particles if p.char == '子')
        dist_rat = rat.wave.dist
        assert dist_rat['Water'] == pytest.approx(1.0, abs=0.01)

    # --- Test 2: Geometric Interactions (SanHe) ---
    def test_axiom_06_interaction_sanhe(self):
        """
        Verifies Axiom 6: Geometric Interaction (Trine/Phase Lock).
        Chart: Shen (Monkey) + Zi (Rat) + Chen (Dragon) -> Water Bureau
        """
        chart = {
            'year': {'branch': '申'},
            'month': {'branch': '子'},
            'day': {'branch': '辰'},
        }
        
        flux = FluxEngine(chart)
        res = flux.compute_energy_state()
        
        # Check Rules
        rules = res['detected_rules']
        assert "SanHe: Water Bureau" in rules, f"Expected SanHe Water Bureau, got {rules}"
        
        # Check Phase Lock Status on Particles
        particles = res['particle_states']
        for p in particles:
            if p['type'] == 'branch':
                assert "PhaseLock_Water" in p['status'], f"Particle {p['char']} missing PhaseLock_Water"
                
    # --- Test 3: Geometric Interactions (LiuChong) ---
    def test_axiom_06_interaction_liuchong(self):
        """
        Verifies Axiom 6: Geometric Interaction (Opposition/Clash).
        Chart: Zi (Rat) + Wu (Horse) -> Clash (180deg)
        """
        chart = {
            'year': {'branch': '子'},
            'month': {'branch': '午'},
        }
        
        flux = FluxEngine(chart)
        res = flux.compute_energy_state()
        
        # Check Rules
        rules = res['detected_rules']
        assert "LiuChong: 午-子" in rules or "LiuChong: 子-午" in rules
        
        # Check Shell Rupture
        particles = res['particle_states']
        for p in particles:
             if p['type'] == 'branch':
                assert "ShellRuptured" in p['status'], f"Particle {p['char']} should be Ruptured"
                
    # --- Test 4: Spacetime Duality (Da Yun vs Liu Nian) ---
    def test_axiom_09_spacetime_duality(self):
        """
        Verifies Axiom 9: Spacetime Duality.
        Da Yun (Background) vs Liu Nian (Trigger).
        """
        # Chart: Metal (Generator) ... [Gap] ... Wood (Receiver)
        # Missing Water to bridge the gap.
        chart = {
            'year': {'stem': '庚', 'branch': '申'}, # Strong Metal
            'hour': {'stem': '甲', 'branch': '寅'}, # Strong Wood
        }
        
        flux = FluxEngine(chart)
        
        # Scenario A: Da Yun = Water (Ren) -> Should Bridge (Tong Guan)
        # Metal -> Water -> Wood
        res_dy = flux.calculate_flux(dy_stem='壬')
        
        assert any("TongGuan" in rule for rule in res_dy['detected_rules']), "Da Yun Water should bridge Metal-Wood"
        
        # Scenario B: Liu Nian = Fire (Bing) -> Should Trigger/Clash not Bridge
        # We need a setup where LN triggers something specific.
        # Let's use LN Branch clashing with Year Branch.
        # Chart Year: Shen (Monkey). LN: Yin (Tiger).
        res_ln = flux.calculate_flux(ln_branch='寅')
        
        assert any("LiuChong" in rule for rule in res_ln['detected_rules']), "Liu Nian Tiger should clash with Monkey"
        # Check for Critical Log
        critical_logs = [l for l in res_ln['log'] if "CRITICAL" in l]
        assert len(critical_logs) > 0, "Liu Nian Clash should be CRITICAL"

if __name__ == "__main__":
    t = TestConstitutionV1()
    t.test_axiom_05_shell_core_structure()
    t.test_axiom_06_interaction_sanhe()
    t.test_axiom_06_interaction_liuchong()
    t.test_axiom_09_spacetime_duality()
    print("All Constitution V1 Tests Passed.")
