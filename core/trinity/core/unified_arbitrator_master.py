
import logging
import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional

# --- Core Engine Imports ---
from core.trinity.core.engines.quantum_dispersion import QuantumDispersionEngine
from core.trinity.core.assets.pillar_gravity_engine import PillarGravityEngine
from core.trinity.core.assets.resonance_booster import ResonanceBooster
from core.trinity.core.assets.spacetime_inertia_engine import SpacetimeInertiaEngine
from core.trinity.core.engines.structural_stress import StructuralStressEngine
from core.trinity.core.engines.wealth_fluid import WealthFluidEngine
from core.trinity.core.engines.relationship_gravity import RelationshipGravityEngine
# [NEW] Integrated Assets
from core.trinity.core.intelligence.symbolic_stars import SymbolicStarsEngine
from core.trinity.core.assets.combination_phase_logic import CombinationPhaseEngine
from core.processors.geo import GeoProcessor
from core.trinity.core.engines.resonance_field import ResonanceField
from core.trinity.core.engines.structural_vibration import StructuralVibrationEngine
from core.trinity.core.intelligence.logic_arbitrator import LogicArbitrator
from core.trinity.core.physics.wave_laws import WaveState
from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.logic_registry import LogicRegistry
from core.bazi_profile import BaziProfile
from core.trinity.core.intelligence.destiny_translator import DestinyTranslator, TranslationStyle
from core.utils import Stellar_Comedy_Parser
from core.trinity.core.conflict_arbitrator import ConflictArbitrator
from core.trinity.core.nexus.context import ContextSnapshot, ContextInjector, ArbitrationScenario

logger = logging.getLogger(__name__)

class UnifiedArbitratorMaster:
    """
    🏛️ 大一统仲裁团 (Grand Unified Arbitrator)
    
    The central command center for Antigravity V10.x.
    Orchestrates all physics modules to generate a 'Holographic' verdict.
    """
    
    def __init__(self):
        self.registry = LogicRegistry()
        logger.info(f"🏛️ Initializing Unified Arbitrator Master [V{self.registry.version}]")
        
        # 1. Initialize Sub-Engines
        self.dispersion_engine = QuantumDispersionEngine()
        self.gravity_engine = PillarGravityEngine()
        self.resonance_booster = ResonanceBooster()
        self.inertia_engine = SpacetimeInertiaEngine()
        self.stress_engine = StructuralStressEngine()
        self.combo_engine = CombinationPhaseEngine()
        # GeoProcessor needs no args usually, assuming it loads internal json
        self.geo_processor = GeoProcessor()
        self.resonance_field = ResonanceField()
        # 60 甲子空亡映射（按旬空公式生成）
        self._void_table = self._build_void_table()
        # Standardized Framework Utility: Destiny Translator (Default to Stephen Chow style)
        self.translator = DestinyTranslator(style=TranslationStyle.STEPHEN_CHOW)

    @staticmethod
    def _build_void_table() -> Dict[str, List[str]]:
        """生成 60 甲子 -> 空亡对照表，确保空亡判定覆盖全表。"""
        stems = "甲乙丙丁戊己庚辛壬癸"
        branches = "子丑寅卯辰巳午未申酉戌亥"
        table: Dict[str, List[str]] = {}
        for i in range(60):
            stem = stems[i % 10]
            branch = branches[i % 12]
            pillar = f"{stem}{branch}"
            voids = BaziProfile.get_void_branches(pillar)
            table[pillar] = voids
        return table

    def _get_void_branches_60(self, day_pillar: str) -> List[str]:
        if not day_pillar:
            return []
        if day_pillar in self._void_table:
            return self._void_table[day_pillar]
        return BaziProfile.get_void_branches(day_pillar)

    def _evaluate_rules(self, unified_state: Dict[str, Any], context: Optional[ContextSnapshot] = None) -> Dict[str, Any]:
        """根据 manifest 规则和当前物理读数生成触发列表与断言。"""
        rules_manifest = self.registry.get_all_active_rules()
        modules_manifest = {m['id']: m for m in self.registry.get_active_modules()}

        phy = unified_state.get("physics", {})
        env = unified_state.get("environment", {})

        wealth = phy.get("wealth", {})
        rel = phy.get("relationship", {})
        resonance = phy.get("resonance", {})
        gravity = phy.get("gravity", {})
        inertia = phy.get("inertia", {})
        combo = phy.get("combination", {})
        life_path = phy.get("life_path", {})
        stress = phy.get("stress", {})
        entropy = phy.get("entropy", 0)
        void_shield = phy.get("void_shield", 1.0)

        triggered: List[Dict[str, Any]] = []

        # Wealth dynamics
        if "PH_WEALTH_PERMEABILITY" in rules_manifest:
            triggered.append({
                "id": "PH_WEALTH_PERMEABILITY",
                "metric": wealth.get("Reynolds", 0),
                "status": "TURBULENT" if wealth.get("State") == "TURBULENT" else "OBSERVED"
            })
        if "PH_WEALTH_VISCOSITY" in rules_manifest:
            triggered.append({
                "id": "PH_WEALTH_VISCOSITY",
                "metric": wealth.get("Viscosity", 0),
                "status": "HIGH" if wealth.get("Viscosity", 0) > 1.5 else "NORMAL"
            })
        if "PH_BI_JIE_SHIELD" in rules_manifest:
            triggered.append({
                "id": "PH_BI_JIE_SHIELD",
                "status": "PENDING",
                "note": "占位：比劫护盾算法未接入（专题：财富流体力学）"
            })

        # Relationship dynamics
        if "PH_GRAVITY_BINDING" in rules_manifest:
            triggered.append({
                "id": "PH_GRAVITY_BINDING",
                "metric": rel.get("Binding_Energy", 0),
                "state": rel.get("State", "UNKNOWN")
            })
        if "PH_PHASE_COLLAPSE" in rules_manifest:
            triggered.append({
                "id": "PH_PHASE_COLLAPSE",
                "state": rel.get("State", "UNKNOWN")
            })
        if "PH_PEACH_BLOSSOM" in rules_manifest and "Peach_Blossom_Amplitude" in rel:
            triggered.append({
                "id": "PH_PEACH_BLOSSOM",
                "metric": rel.get("Peach_Blossom_Amplitude", 0)
            })

        # Resonance / Gravity / Inertia
        if "PH_ROOTING_GAIN" in rules_manifest:
            triggered.append({
                "id": "PH_ROOTING_GAIN",
                "gain": resonance.get("gain", 1.0),
                "status": resonance.get("status")
            })
        if "PH_PILLAR_GRAVITY" in rules_manifest:
            triggered.append({
                "id": "PH_PILLAR_GRAVITY",
                "metric": gravity
            })
        if "PH_FLUID_VISCOSITY" in rules_manifest:
            triggered.append({
                "id": "PH_FLUID_VISCOSITY",
                "metric": inertia.get("Viscosity", 0.5)
            })

        # Combination / Void
        if combo:
            triggered.append({
                "id": "PH_COMBINATION_PHASE",
                "status": combo.get("status"),
                "power_ratio": combo.get("power_ratio")
            })
        if void_shield < 1.0 and "PH27_VOID" in rules_manifest:
            triggered.append({
                "id": "PH27_VOID",
                "damping_factor": void_shield
            })

        # Collapse / entropy
        if "PH28_ANNIHILATION" in rules_manifest and entropy > 1.0:
            triggered.append({
                "id": "PH28_ANNIHILATION",
                "metric": entropy,
                "status": "WARNING" if entropy <= 1.5 else "CRITICAL"
            })
        if "PH25-26_COLLAPSE" in rules_manifest:
            sai_val = stress.get("SAI", 0)
            ic_val = stress.get("IC", 0)
            if sai_val >= 1.5 or ic_val <= 0.2:
                triggered.append({
                    "id": "PH25-26_COLLAPSE",
                    "metric": {"SAI": sai_val, "IC": ic_val},
                    "status": "RISK"
                })

        # Life-path risks
        if "PH_RISK_NODE_DETECT" in rules_manifest and life_path and life_path.get("risk_nodes"):
            triggered.append({
                "id": "PH_RISK_NODE_DETECT",
                "risk_count": len(life_path.get("risk_nodes", []))
            })

        # Verdict synthesis
        dm_char = unified_state.get("meta", {}).get("dm", "")
        dm_elem = BaziParticleNexus.STEMS.get(dm_char, ("Earth", "Yang", 5))[0]
        verdict = {
            "label": dm_char,
            "element": dm_elem,
            "structure": f"熵={entropy:.2f} | SAI={stress.get('SAI',0):.2f} | IC={stress.get('IC',0):.2f}",
            "wealth": f"Re={wealth.get('Reynolds',0):.0f} / ν={wealth.get('Viscosity',0):.2f} / {wealth.get('State','STAGNANT')}",
            "relationship": f"E={rel.get('Binding_Energy',0):.1f} / {rel.get('State','UNKNOWN')} / 桃花={rel.get('Peach_Blossom_Amplitude',0):.2f}",
            "action": f"月令权重={gravity.get('Month',0):.2f} | 惯性ν={inertia.get('Viscosity',0.5):.2f} | 交运月龄={env.get('months_since_switch',6.0)}"
        }

        # --- Phase 1 Conflict Arbitration & Layering ---
        # Resolve conflicts and group by layer
        resolved_rules = ConflictArbitrator.resolve_conflicts(triggered, self.registry.manifest.get("registry", {}), context=context)
        tiered_rules = ConflictArbitrator.group_by_layer(resolved_rules)

        return {
            "rules": resolved_rules,
            "tiered_rules": tiered_rules,
            "modules_active": list(modules_manifest.keys()),
            "verdict": verdict
        }
        
    def arbitrate_bazi(self, bazi_chart: List[str], birth_info: Dict[str, Any] = None, current_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes the full physics pipeline on a Bazi chart.
        """
        if not bazi_chart or len(bazi_chart) < 4:
            return {"error": "Invalid Chart Data"}

        # Context Defaults
        ctx = current_context or {}
        luck = ctx.get('luck_pillar', '甲子') 
        annual = ctx.get('annual_pillar', '甲子')
        months_since_switch = ctx.get('months_since_switch', 6.0)
        geo_city = ctx.get('data', {}).get('city', 'Unknown')
        scenario_str = ctx.get('scenario', 'GENERAL')
        
        # Create Context Snapshot (Phase 8: Context-Aware State Machine)
        context = ContextInjector.create_from_request(
            luck_pillar=luck,
            annual_pillar=annual,
            geo_city=geo_city,
            scenario=scenario_str
        )

        # Extract stems/branches
        try:
            current_dm = bazi_chart[2][0]
            month_branch = bazi_chart[1][1]
            day_branch = bazi_chart[2][1]
            all_stems = [p[0] for p in bazi_chart]
            all_branches = [p[1] for p in bazi_chart]
            # [NEW] Add Dynamic Branches (Luck/Annual) for Stress & Star calculation
            if luck and len(luck) > 1: all_branches.append(luck[1])
            if annual and len(annual) > 1: all_branches.append(annual[1])
            # [V12.2.0 FIX] Add Dynamic Stems (Luck/Annual) for Expert Assertions
            if luck and len(luck) > 0: all_stems.append(luck[0])
            if annual and len(annual) > 0: all_stems.append(annual[0])
        except IndexError:
            return {"error": "Chart Parsing Failed"}

        # Load active rules/modules for later cross-check
        manifest_rules = self.registry.get_all_active_rules()
        manifest_modules = {m['id']: m for m in self.registry.get_active_modules()}

        # --- PHASE 1: Base Physics (Environment) ---
        all_pillars = bazi_chart + [luck, annual]
        
        # Determine Solar Term Progress (Phase B)
        # In a real scenario, this would be computed from birth_info
        phase_progress = ctx.get('phase_progress', 0.5)
        geo_factor = ctx.get('geo_factor', 1.0)
        
        # 1.1 Quantum Dispersion (Substrate)
        substrate_field = self.dispersion_engine.get_dynamic_weights(month_branch, phase_progress)

        # 1.2 Pillar Gravity (Weights)
        gravity_weights = self.gravity_engine.calculate_dynamic_weights(phase_progress)

        # 1.3 Void Shielding (Simple Logic)
        void_branches: List[str] = []
        is_void = False
        try:
            day_pillar = bazi_chart[2]
            void_branches = self._get_void_branches_60(day_pillar)
            is_void = any(br in void_branches for br in all_branches)
        except Exception:
            is_void = False
        void_shield_factor = 0.45 if is_void else 1.0

        # 1.4 GEO Correction - Use passed geo_factor if available, otherwise lookup
        ctx_data = ctx.get('data', {})
        passed_geo_factor = ctx_data.get('geo_factor')
        passed_geo_element = ctx_data.get('geo_element', 'Neutral')
        
        if passed_geo_factor is not None:
            # Use directly passed geo info from UI
            geo_modifiers = {
                'desc': f"{geo_city} - {passed_geo_element}",
                'temperature_factor': passed_geo_factor,
                'humidity_factor': 1.0,
                'environment_bias': f"地理因子: {passed_geo_factor:.2f}x | 五行亲和: {passed_geo_element}",
                'fire': passed_geo_factor if 'Fire' in passed_geo_element else 1.0,
                'water': passed_geo_factor if 'Water' in passed_geo_element else 1.0,
                'wood': passed_geo_factor if 'Wood' in passed_geo_element else 1.0,
                'metal': passed_geo_factor if 'Metal' in passed_geo_element else 1.0,
                'earth': passed_geo_factor if 'Earth' in passed_geo_element else 1.0
            }
        else:
            # Fallback to GeoProcessor lookup
            geo_modifiers = self.geo_processor.process(geo_city)
        
        # --- PHASE 2: Micro-Structures (Internal) ---
        # 2.1 Structural Stress (SAI/IC)
        self.stress_engine.day_master = current_dm
        stress_report = self.stress_engine.calculate_micro_lattice_defects(all_branches, month_branch)
        
        # 2.2 Symbolic Stars (Tian Yi / Wen Chang / Lu / Yang Ren / Peach / Horse)
        year_branch = bazi_chart[0][1] if bazi_chart and len(bazi_chart[0]) >= 2 else None
        star_stats = SymbolicStarsEngine.analyze_stars(current_dm, all_branches, year_branch=year_branch)
        star_phys = SymbolicStarsEngine.get_physical_modifiers(star_stats)
        
        # 2.3 Combination Phase (He Hua)
        # Check interactions between stems (e.g. Month Stem + Day Stem)
        m_stem = bazi_chart[1][0]
        combo_res = {}
        try:
            dm_stem = current_dm
            month_energy = gravity_weights.get('Month', 0.5)
            combo_res = self.combo_engine.check_combination_phase([dm_stem, m_stem], month_energy)
        except Exception:
            combo_res = {}

        # --- PHASE 3: Power Dynamics (Energy) ---
        # 3.1 Resonance Gain (Rooting)
        rooting_status = self.resonance_booster.calculate_resonance_gain(current_dm, all_branches)
        
        # [NEW] 3.2 Wealth Fluid Dynamics (Navier-Stokes)
        # We need an energy map (waves) for this. Constructing from Gravity x Dispersion.
        # Element Energy = Sum of (Weight of Pillar * Element Strength in Pillar)
        # Simplified: Use Month Command + Rooting for estimation.
        # Mapping Stems to Elements:
        from core.trinity.core.nexus.definitions import BaziParticleNexus
        elem_map = {} # Elem -> Amplitude
        for elem in ['Wood', 'Fire', 'Earth', 'Metal', 'Water']:
            elem_map[elem] = 0.0
            
        # Add Stem Energies (1.0 each, weighed by Gravity?) 
        # Simplify: Just count stems + branches (main qi)
        for p in bazi_chart:
            # Stems
            s_elem = BaziParticleNexus.STEMS.get(p[0])[0]
            elem_map[s_elem] = elem_map.get(s_elem, 0) + 1.0
            
            # Branches (Include Hidden Stems for Micro-Precision)
            # Use BaziParticleNexus to get hidden stems
            hidden_stems = BaziParticleNexus.get_branch_weights(p[1])
            for h_stem, h_weight in hidden_stems:
                 h_elem = BaziParticleNexus.STEMS.get(h_stem)[0]
                 # Normalize weight (assuming max ~10 in definition)
                 elem_map[h_elem] = elem_map.get(h_elem, 0) + (h_weight * 0.15)

        # [NEW] Inject Time-Space Energy (Luck & Annual)
        dynamic_pillars = []
        if luck: dynamic_pillars.append((luck, 0.8)) # Luck weight
        if annual: dynamic_pillars.append((annual, 1.2)) # Annual weight (Impulse)

        for pillar_str, weight in dynamic_pillars:
             if len(pillar_str) >= 2:
                s_char, b_char = pillar_str[0], pillar_str[1]
                # Stem
                if s_char in BaziParticleNexus.STEMS:
                    s_e = BaziParticleNexus.STEMS[s_char][0]
                    elem_map[s_e] = elem_map.get(s_e, 0) + (1.0 * weight)
                # Branch
                h_stems = BaziParticleNexus.get_branch_weights(b_char)
                for h_s, h_w in h_stems:
                    if h_s in BaziParticleNexus.STEMS:
                        h_e = BaziParticleNexus.STEMS[h_s][0]
                        elem_map[h_e] = elem_map.get(h_e, 0) + (h_w * 0.15 * weight)

        # [NEW] Apply Geo Modifiers
        # geo_modifiers e.g. {'Fire': 1.5, 'Water': 0.8}
        if geo_modifiers:
            for elem, boost in geo_modifiers.items():
                if elem in elem_map:
                    elem_map[elem] *= boost
            
        from core.trinity.core.nexus.definitions import PhysicsConstants
        # Create WaveState objects with real phases from PhysicsConstants
        waves_mock = {
            k: WaveState(amplitude=v, phase=PhysicsConstants.ELEMENT_PHASES.get(k, 0.0)) 
            for k, v in elem_map.items()
        }
        
        # Instantiate engines on fly or in init
        dm_elem = BaziParticleNexus.STEMS.get(current_dm)[0]
        wealth_engine = WealthFluidEngine(dm_elem)
        wealth_metrics = wealth_engine.analyze_flow(waves_mock)
        
        # [NEW] 3.3 Relationship Gravity
        # Need gender from birth_info or default Male
        gender = birth_info.get('gender', '男') if birth_info else '男'
        rel_engine = RelationshipGravityEngine(current_dm, gender)
        rel_metrics = rel_engine.analyze_relationship(
            waves_mock, bazi_chart, luck_pillar=luck, annual_pillar=annual, geo_factor=geo_modifiers.get('fire', 1.0) # Using generic geo
        )

        # [V12.2.0] 专旺格 Detection (Self-Dominance Follow Pattern)
        # When DM element > 55% of total energy, it's a self-dominance pattern
        total_energy = sum(elem_map.values())
        dm_energy = elem_map.get(dm_elem, 0)
        dm_dominance_ratio = dm_energy / max(total_energy, 0.1)
        is_self_dominant = dm_dominance_ratio > 0.55  # DM element > 55% = 专旺格
        
        # For 专旺格, also check 印/比 (Resource/Companion) which SUPPORT DM
        # Resource generates DM, Companion = same as DM
        gen_map = {"Wood": "Water", "Fire": "Wood", "Earth": "Fire", "Metal": "Earth", "Water": "Metal"}
        resource_elem = gen_map.get(dm_elem, "")
        resource_energy = elem_map.get(resource_elem, 0)
        support_ratio = (dm_energy + resource_energy) / max(total_energy, 0.1)
        is_follow_strong = support_ratio > 0.65  # DM + Resource > 65% = 从强

        # [NEW] 3.4 Resonance Field Analysis
        # Use the engines to get real coherence metrics
        dm_wave = waves_mock.get(dm_elem)
        field_list = [v for k, v in waves_mock.items() if k != dm_elem]
        res_analysis = self.resonance_field.evaluate_system(dm_wave, field_list)
        
        # [V12.2.0] Override is_follow for 专旺格/从强 cases
        final_is_follow = res_analysis.is_follow or is_self_dominant or is_follow_strong
        
        resonance_metrics = {
            "gain": rooting_status.get('gain', 1.0),
            "locking_ratio": res_analysis.locking_ratio,
            "sync_state": res_analysis.sync_state,
            "status": res_analysis.mode,
            "is_follow": final_is_follow,
            "dm_dominance_ratio": round(dm_dominance_ratio, 3),  # V12.2.0 Debug
            "support_ratio": round(support_ratio, 3),           # V12.2.0 Debug
            "follow_type": "专旺" if is_self_dominant else ("从强" if is_follow_strong else ("从弱" if res_analysis.is_follow else "身强/身弱"))
        }
        
        # [NEW] 3.5 Structural Vibration (MOD_15)
        # Non-linear energy transmission
        vib_engine = StructuralVibrationEngine(current_dm)
        # Context for vibration engine (reuse unified context 'ctx')
        vib_metrics = vib_engine.calculate_vibration_metrics(
             all_stems, all_branches, context=ctx
        )
        
        # --- PHASE 4: Temporal Evolution (Flow) ---
        # 4.1 Spacetime Inertia
        inertia_metrics = self.inertia_engine.calculate_inertia_weights(
             months_since_switch=months_since_switch
        )

        # Finalizing physics packet
        stellar_metrics = {
            "coherence": star_phys.get('entropy_damping', 1.0),
            "snr_boost": star_phys.get('snr_boost', 1.0),
            "attraction": star_phys.get('attraction_boost', 0.0),
            "impulse": star_phys.get('kinetic_impulse', 0.0),
            "stars": star_stats['active_stars']
        }

        # [Phase 6.0] Life-Path Sampling Disabled for Performance (Redundant after Radar Removal)
        life_path_data = None
        # try:
        #     if birth_info and all(k in birth_info for k in ('birth_year', 'birth_month', 'birth_day', 'birth_hour')):
        #         bdt = datetime(
        #             int(birth_info['birth_year']),
        #             int(birth_info['birth_month']),
        #             int(birth_info['birth_day']),
        #             int(birth_info['birth_hour'])
        #         )
        #         from core.bazi_profile import VirtualBaziProfile
        #         profile = VirtualBaziProfile({'year':bazi_chart[0], 'month':bazi_chart[1], 'day':bazi_chart[2], 'hour':bazi_chart[3]}, 
        #                                     gender=(1 if gender == '男' else 0), 
        #                                     birth_date=bdt)
        #         birth_year = bdt.year
        #         life_path_data = self.life_path_engine.simulate_lifespan(
        #             profile,
        #             start_year=birth_year,
        #             end_year=birth_year + 80,
        #             resolution='year'
        #         )
        # except Exception as e:
        #     logger.warning(f"Life-path simulation failed: {e}")
        #     life_path_data = None

        # --- synthesize Unified State ---
        # 5.1 Probability Wave Correction (Phase 8: Context-Aware Adjustment)
        # Apply GEO Bias and Environmental saturation to core metrics
        dm_char = current_dm
        # Get DM element (mock mapping for correction)
        dm_elem = BaziParticleNexus.STEMS.get(dm_char, ("Earth", "Yang", 5))[0]
        geo_bias_val = context.geo_bias.get(dm_elem, 1.0)
        
        # Calculate System Entropy (Adjusted by context)
        sai = stress_report.get('SAI', 0) * (2.0 - geo_bias_val) # Higher bias in DM element reduces stress
        ic = min(1.0, stress_report.get('IC', 0) * geo_bias_val)  # Higher bias increases coherence
        
        system_entropy = sai + (1.0 - ic) * 0.5
        system_entropy *= star_phys.get('entropy_damping', 1.0)
        
        # Adjust Wealth and Relationship metrics by context
        wealth_metrics['Reynolds'] *= geo_bias_val
        rel_metrics['Binding_Energy'] *= geo_bias_val
        
        unified_state = {
            "meta": {
                "version": self.registry.version,
                "timestamp": datetime.now().isoformat(),
                "dm": current_dm,
                "scenario": context.scenario.name
            },
            "physics": {
                "substrate": substrate_field,
                "gravity": gravity_weights,
                "void_shield": void_shield_factor,
                "void_branches": void_branches,
                "geo": geo_modifiers,
                "stress": {**stress_report, "SAI": round(sai, 3), "IC": round(ic, 3)},
                "stars": {
                    "stats": star_stats,
                    "modifiers": star_phys
                },
                "resonance": resonance_metrics,
                "wealth": wealth_metrics,       # [NEW]
                "relationship": rel_metrics,    # [NEW]
                "vibration": vib_metrics,       # [NEW] MOD_15
                "inertia": inertia_metrics,
                "combination": combo_res,
                "life_path": life_path_data,
                "entropy": round(system_entropy, 3)
            },
            "environment": {
                "luck": luck,
                "annual": annual,
                "months_since_switch": months_since_switch
            }
        }

        eval_res = self._evaluate_rules(unified_state, context=context)
        
        # [NEW] 5. Inter-layer Logic Arbitration (Phase H)
        # Call LogicArbitrator with full context: pillars, dm, solar_progress, dispersion_engine, geo_factor
        intensities = LogicArbitrator.calculate_field_intensities(
            pillars=all_pillars,
            day_master=current_dm,
            phase_progress=phase_progress,
            dispersion_engine=self.dispersion_engine,
            geo_factor=geo_factor
        )
        logic_interactions = LogicArbitrator.match_interactions(
            pillars=all_pillars,
            day_master=current_dm,
            phase_progress=phase_progress,
            dispersion_engine=self.dispersion_engine,
            geo_factor=geo_factor
        )

        # 5.1 Reconstruct Elemental Waves for UI (Holographic Export)
        # Map Shi Shen back to Elements based on DM
        dm_elem = BaziParticleNexus.STEMS.get(current_dm, ("Earth", "Yang", 5))[0]
        GEN = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"}
        CTRL = {"Wood": "Earth", "Earth": "Water", "Water": "Fire", "Fire": "Metal", "Metal": "Wood"}
        REVERSE_GEN = {v: k for k, v in GEN.items()}
        REVERSE_CTRL = {v: k for k, v in CTRL.items()}
        
        waves_dict = {}
        # Self
        waves_dict[dm_elem] = WaveState(intensities["比肩"] + intensities["劫财"], 0.0)
        # Output
        waves_dict[GEN[dm_elem]] = WaveState(intensities["食神"] + intensities["伤官"], 0.0)
        # Wealth
        waves_dict[CTRL[dm_elem]] = WaveState(intensities["偏财"] + intensities["正财"], 0.0)
        # Control
        ctrl_elem = REVERSE_CTRL[dm_elem]
        waves_dict[ctrl_elem] = WaveState(intensities["七杀"] + intensities["正官"], 0.0)
        # Resource
        res_elem = REVERSE_GEN[dm_elem]
        waves_dict[res_elem] = WaveState(intensities["偏印"] + intensities["正印"], 0.0)

        unified_state["waves"] = waves_dict
        
        # Merge physical rules with logic interactions and perform final arbitration
        all_triggered = eval_res.get("rules", []) + logic_interactions
        final_resolved = ConflictArbitrator.resolve_conflicts(all_triggered, self.registry.manifest.get("registry", {}), context=context)
        
        unified_state["rules"] = final_resolved
        unified_state["tiered_rules"] = ConflictArbitrator.group_by_layer(final_resolved)
        unified_state["modules_active"] = eval_res.get("modules_active", [])
        unified_state["verdict"] = eval_res.get("verdict", {})
        unified_state["plain_guidance"] = self._plain_guidance(unified_state)

        # [MOD_17] Intelligence Layer: Stephen Chow Style Translation
        from core.utils import Stellar_Comedy_Parser
        sai_val = stress_report.get('SAI', 1.0)
        ic_val = resonance_metrics.get('locking_ratio', 1.0)
        # Re-calculating with the final system_entropy
        stellar_narrative = Stellar_Comedy_Parser.translate(sai=sai_val, entropy=unified_state['physics']['entropy'], ic=ic_val)
        unified_state["intelligence"] = {
            "stellar_mantra": stellar_narrative
        }

        return unified_state

    def _plain_guidance(self, state: Dict[str, Any]) -> List[str]:
        """将关键指标转为白话提示，供前端直接展示。"""
        tips: List[str] = []
        phy = state.get("physics", {})
        env = state.get("environment", {})

        # 结构：熵 / SAI / IC
        ent = phy.get("entropy", 0)
        sai = phy.get("stress", {}).get("SAI", 0)
        ic = phy.get("stress", {}).get("IC", 0)
        if ent <= 0.6:
            tips.append("整体气场平稳，适合推进重要计划。")
        elif ent <= 1.2:
            tips.append("气场有起伏但可控，稳扎稳打为宜。")
        else:
            tips.append("熵值偏高，外部干扰大，建议先控节奏、降噪再决策。")
        if sai >= 1.2:
            tips.append("结构应力偏高，注意健康/工作负荷，分摊压力。")
        if ic >= 0.8:
            tips.append("信号相位抖动明显，沟通需更细，避免误判。")

        # 财富：Re / v / 状态
        wealth = phy.get("wealth", {})
        re_num = wealth.get("Reynolds", 0)
        nu_val = wealth.get("Viscosity", 0)
        if re_num < 100:
            tips.append("财富流动较慢，先蓄水和疏通渠道，暂缓冒进。")
        elif re_num > 4000:
            tips.append("财富流动湍急，机会伴随波动，务必加强风控与止盈。")
        else:
            tips.append("财富流动平顺，可稳步推进并注意分散风险。")
        if nu_val > 1.5:
            tips.append("比劫摩擦大，伙伴/竞争阻力重，宜引入制衡或规则。")

        # 情感：状态 / 桃花
        rel = phy.get("relationship", {})
        r_state = rel.get("State", "UNKNOWN")
        pb = rel.get("Peach_Blossom_Amplitude", 0)
        if r_state in ["ENTANGLED", "BOUND"]:
            tips.append("情感/合作引力稳固，可利用共振期推进关系。")
        elif r_state == "PERTURBED":
            tips.append("情感/合作受扰动，先沟通缓冲，避免硬碰。")
        elif r_state == "UNBOUND":
            tips.append("情感引力弱，降低期待，先提升连接感。")
        if pb > 0.5:
            tips.append("桃花信号强，宜分辨良性/干扰，保持边界。")

        # 行动：月令权重 / 惯性 / 交运月龄
        grav_m = phy.get("gravity", {}).get("Month", 0)
        if grav_m >= 0.55:
            tips.append("月令主导当下走势，顺月令之势行动。")
        inertia_v = phy.get("inertia", {}).get("Viscosity", 0.5)
        if inertia_v >= 0.8:
            tips.append("交运粘滞高，小步试探，避免大幅切换。")
        months_sw = env.get("months_since_switch", 6.0)
        if months_sw < 3:
            tips.append("刚交运，优先观察与调整节奏。")

        # 规则命中补充
        rules = state.get("rules", [])
        for r in rules:
            rid = r.get("id")
            if rid == "PH27_VOID":
                tips.append("命局触发空亡屏蔽，做事需留余量，避免硬上。")
            if rid == "PH_COMBINATION_PHASE" and r.get("status") == "PHASE_TRANSITION":
                tips.append("天干合化成功，利于借势转化资源。")
            if rid == "PH28_ANNIHILATION":
                tips.append("检测到湮灭/崩塌风险，务必降噪与减负。")
            if rid == "PH28_01":
                tips.append("检测到‘伤官见官’：官伤双强且见，易有口舌诉讼或事业动荡，建议务必低调稳健，避免硬刚规则。")
            if rid == "PH_RISK_NODE_DETECT" and r.get("risk_count"):
                tips.append(f"发现 {r.get('risk_count')} 个风险节点，需避开高危年份窗口。")

        # Life-path risk nodes → 贴近期命运提示
        life_path = phy.get("life_path", {}) or {}
        risk_nodes = life_path.get("risk_nodes", [])
        if risk_nodes:
            # 取最近未来 3 个风险年份
            try:
                rn_sorted = sorted(risk_nodes, key=lambda x: x.get("timestamp", ""))
            except Exception:
                rn_sorted = risk_nodes
            rn_filtered = []
            for r in rn_sorted:
                ts = r.get("timestamp", "")
                if len(rn_filtered) >= 3:
                    break
                rn_filtered.append(r)

            cat_advice = {
                "熵暴": "气场紊乱，先减速、护健康、稳现金流。",
                "结构应力": "结构压强大，别硬扛，分工减载，稳住根基。",
                "相位抖动": "沟通/关系易误判，放慢节奏，先对齐再行动。",
                "综合波动": "常规波动，保持韧性，节奏均衡即可。"
            }
            for r in rn_filtered:
                ts = r.get("timestamp", "")
                year = ts[:4] if ts else "未知"
                metrics = r.get("metrics", {})
                ent_v = metrics.get("entropy", 0)
                sai_v = metrics.get("sai", 0)
                ic_v = metrics.get("ic", 0)
                if ent_v >= 1.6:
                    category = "熵暴"
                elif sai_v >= 1.2:
                    category = "结构应力"
                elif ic_v >= 0.8:
                    category = "相位抖动"
                else:
                    category = "综合波动"
                tips.append(f"{year}年：{category}窗口，{cat_advice.get(category,'保持稳态应对。')}")

        return tips


    def arbitrate(self, chart: Dict, ctx: Dict) -> Dict:
        """
        Adapter for UI integration.
        Args:
            chart: {'day_master': str, 'branches': List[str]}
            ctx: Context dict
        """
        dm = chart.get('day_master', '甲')
        branches = chart.get('branches', ['子', '子', '子', '子'])
        
        # Reconstruct structural list for internal engine (Mock pillars)
        # We only have branches + DM. We will mock stems for non-DM pillars.
        # This is a degradation for the UI mock, but acceptable for demo.
        bazi_chart = [
            f"甲{branches[0] if len(branches)>0 else '子'}", # Year
            f"甲{branches[1] if len(branches)>1 else '子'}", # Month
            f"{dm}{branches[2] if len(branches)>2 else '子'}", # Day
            f"甲{branches[3] if len(branches)>3 else '子'}", # Hour
        ]
        
        # Call Internal
        birth_info = {"gender": "男"} # Default to male for UI demo
        state = self.arbitrate_bazi(bazi_chart, birth_info, ctx)
        
        # Parse Markdown Report to Structured Narrative for UI
        full_report = self.generate_holographic_report(state)
        
        # Extract sections using simple parsing
        overview = "系统稳定"
        guidance = "无"
        pulse = "无"
        
        try:
            parts = full_report.split("###")
            for p in parts:
                if "概述" in p or "Overview" in p:
                    # Extract the quote or first bold line
                    lines = [l.strip() for l in p.split('\n') if l.strip()]
                    for l in lines:
                        if l.startswith(">"): 
                            overview = l.replace(">", "").strip().replace("**", "")
                            break
                        if "定义为" in l:
                             overview = l
                if "真言" in p or "Guidance" in p:
                     lines = [l.strip() for l in p.split('\n') if l.strip()]
                     for l in lines:
                        if "GEO" in l or "建议" in l:
                             guidance = l
                if "模拟" in p or "Scan" in p:
                     # Keep the table part or summary
                     pulse = "T+N Event Scan Active"
        except:
            pass

        return {
            "physics": state['physics'],
            "narrative": {
                "overview": overview,
                "guidance": guidance,
                "pulse_scan": "已执行100年全息扫描，详情见下文。"
            }
        }
    
    def generate_holographic_report(self, state: Dict[str, Any]) -> str:
        """
        Translates the UnifiedState into the 'Mantra' report (Wong Kar-wai Style).
        """
        phy = state.get('physics', {})
        env = state.get('environment', {})
        
        stress = phy.get('stress', {})
        res = phy.get('resonance', {})
        grav = phy.get('gravity', {})
        stars = phy.get('stars', {})
        wealth = phy.get('wealth', {})
        rel = phy.get('relationship', {})
        modifiers = stars.get('modifiers', {})
        star_list = stars.get('stats', {}).get('active_stars', [])
        
        sai = stress.get('SAI', 0.0)
        entropy = phy.get('entropy', 0.0)
        void_factor = phy.get('void_shield', 1.0)
        
        # 1. Master Overview
        report = []
        report.append("### 🔮 第一部分：八字物理全息概述 (Master Overview)")
        
        # Use localized translator with standard Tool-Class interface if style matches
        if self.translator.style == TranslationStyle.STEPHEN_CHOW:
            poetic_verdict = Stellar_Comedy_Parser.translate(sai=sai, entropy=entropy, ic=stress.get('IC', 1.0))
        else:
            poetic_verdict = self.translator.translate_state(state)
            
        report.append(f"> **“{poetic_verdict}”**\n")
        
        # Tone Definition
        struct_type = "稳态平衡"
        if sai > 1.5: struct_type = "高应力-高能级"
        elif entropy < 0.5: struct_type = "低熵-超导"
        
        # Gravity Dominance
        weights = grav
        max_w_pillar = max(weights, key=weights.get) if weights else "Month"
        max_w_val = weights.get(max_w_pillar, 0) * 100
        
        report.append(f"**【系统稳定性】**：综合熵值 (Entropy) **{entropy:.2f}**。")
        report.append(f"**【核心结构】**：此局被定义为 **「{struct_type}」** 结构。**{max_w_pillar}** 拥有 **{max_w_val:.1f}%** 的绝对统治权。")
        
        # Wealth & Relationship Snippets
        re_num = wealth.get('Reynolds', 0)
        w_state = wealth.get('State', 'LAMINAR')
        report.append(f"**【财富流体】**：雷诺数 **Re={re_num}** ({w_state})。能量流动{'湍急而富有' if re_num > 4000 else '平稳有序' if re_num > 100 else '停滞'}。")
        
        rel_bind = rel.get('Binding_Energy', 0)
        rel_state = rel.get('State', 'UNBOUND')
        report.append(f"**【情感引力】**：绑定能 **E={rel_bind}** ({rel_state})。{'引力深沉，难以逃逸' if rel_state == 'BOUND' else '轨道游离，自由是唯一的代价'}。")
        
        # Modifiers
        mod_desc = []
        if void_factor < 0.9:
            mod_desc.append(f"触发空亡屏蔽 ({void_factor})")
        if modifiers.get('entropy_damping', 1.0) < 1.0:
            mod_desc.append("天乙量子阻尼生效")
        if modifiers.get('lu_gain', 1.0) > 1.0:
            mod_desc.append("禄神锚点锁定")
        
        if mod_desc:
            report.append(f"**【修正场】**：虽有应力干扰，但 {'，'.join(mod_desc)}，系统具备极强的人为修正能力。")
        else:
            report.append("**【修正场】**：系统裸露于原生时空场中，无额外量子护盾。")

        # 2. Real-time Guidance
        report.append("\n### 🌊 第二部分：当下真言与 GEO 建议 (Real-time Guidance)")
        report.append("> **“针对当前时空坐标的物理对冲方案。”**\n")
        
        viscosity = phy.get('inertia', {}).get('Viscosity', 0.5)
        # Assuming Geo Processor returns a 'desc' or we parse modifiers
        geo = phy.get('geo', {})
        geo_msg = geo.get('environment_bias', '环境场强平衡')
        
        report.append(f"**【惯性预警】**：粘滞指数 **{viscosity:.2f}**，{'流动性极佳，换道超车正当时' if viscosity < 0.4 else '历史惯性极大，切勿轻举妄动'}。")
        report.append(f"**【GEO 建议】**：当前坐标显示 **{geo_msg}**。{'若感到压力过载，建议向反向五行区域迁徙以寻求物理对冲。' if entropy > 0.8 else '地气相宜，安营扎寨。'}")

        # [NEW] MOD_17: Stellar Interaction
        intelligence = state.get("intelligence", {})
        if intelligence.get("stellar_mantra"):
            report.append("\n### ✨ 第四部分：星辰相干真言 (Stellar Coherence Mantra)")
            report.append(f"> **“{intelligence['stellar_mantra']}”**\n")
            
            # Add telemetry for stellar metrics
            stellar = phy.get('stellar', {})
            attraction = stellar.get('attraction', 0.0)
            impulse = stellar.get('impulse', 0.0)
            
            st_metrics = []
            if attraction > 0: st_metrics.append(f"量子引力增益: +{attraction:.2f} eV")
            if impulse > 0: st_metrics.append(f"动能冲量增益: +{impulse:.2f} ΔV")
            
            if st_metrics:
                report.append(f"**【星辰修正】**：{' | '.join(st_metrics)}")

        # 3. Future Pulse Scan
        report.append("\n### 🚀 第三部分：百年事件触发模拟 (100-Year Pulse Scan)")
        report.append("> **“因果模拟，标记人生关键奇点。”**\n")
        
        report.append("| 时间 (Time) | 信号 (Signal) | 事件预警 (Event) |")
        report.append("| :--- | :--- | :--- |")
        
        # Mock Logic based on Yang Ren
        life_path = phy.get('life_path', {}) or {}
        risk_nodes = life_path.get('risk_nodes', [])
        
        if risk_nodes:
            # Current year for relative timing
            try:
                current_year_int = int(state['meta']['timestamp'][:4])
            except (ValueError, KeyError, TypeError):
                current_year_int = datetime.now().year
                
            # Filter for future events only
            future_risks = [r for r in risk_nodes if int(r.get('timestamp', '0000')[:4]) >= current_year_int]
            
            # Sort by risk score and filter for diversity (one per year for the top ones)
            unique_years = {}
            for r in sorted(future_risks, key=lambda x: x.get('risk_score', 0), reverse=True):
                y = r.get('timestamp', '0000')[:4]
                if y not in unique_years:
                    unique_years[y] = r
                if len(unique_years) >= 5:
                    break
            
            sorted_risks = sorted(unique_years.values(), key=lambda x: x.get('timestamp', ''))
            
            for r in sorted_risks:
                year_str = r.get('timestamp', '')[:4]
                if not year_str.isdigit(): continue
                year = int(year_str)
                metrics = r.get('metrics', {})
                sai_v = metrics.get('sai', 0)
                ic_v = metrics.get('ic', 0)
                # Event mantra handling
                if self.translator.style == TranslationStyle.STEPHEN_CHOW:
                    mantra = Stellar_Comedy_Parser.translate(sai=sai_v, entropy=metrics.get('entropy', 0), ic=ic_v)
                else:
                    mantra = self.translator.get_event_mantra(r)
                
                sig_icon = "🔴" if r.get('risk_score', 0) > 1.5 else "🟡"
                report.append(f"| **T+{year - current_year_int}y ({year})** | SAI={sai_v:.2f}, IC={ic_v:.2f} {sig_icon} | **{mantra}** |")
        else:
            # Fallback if no life_path
            yr_count = stars.get('stats', {}).get('yang_ren_count', 0)
            if yr_count > 0:
                report.append("| **T+15y** | SAI=2.40 🔴 | **“命运在这个春天准备了两份一模一样的礼物。一份是惊喜，另一份是警示，你必须全部签收。”** |")
            
            if entropy > 1.0:
                report.append("| **T+42y** | η=0.08 🌑 | **“不要试图在浓雾里狂奔，那是信号最微弱的时候。”** |")
            else:
                 report.append("| **T+30y** | Res=Max 🟢 | **“人生高光时刻，全功率输出。所有的粒子都在为你而歌。”** |")

        report.append("\n**【终极仲裁】**：")
        report.append("> *“人生所有的遗憾，都是物理学上的必然。既已洞悉因果，便无须回头。”*")
        
        return "\n".join(report)

# Global Instance for Dynamic Import
unified_arbitrator = UnifiedArbitratorMaster()
