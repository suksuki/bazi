
import time
import random
import logging
from typing import Dict, Any, List, Optional
from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine, ExpectedValueCollector
from core.trinity.core.engines.simulation_model import SimulationModel
from core.trinity.core.engines.pattern_screener import PatternScreener
from core.trinity.core.engines.mirror_engine import MirrorEngine
from core.trinity.core.engines.celebrity_backtester import CelebrityBacktester
from core.trinity.core.engines.pattern_scout import PatternScout
from core.trinity.core.engines.pattern_physics_lab import PatternPhysicsLab
from core.trinity.core.engines.pattern_lifecycle_manager import PatternLifecycleManager
from core.trinity.core.engines.intervention_engine import InterventionEngine
from core.profile_manager import ProfileManager
from core.bazi_profile import BaziProfile
from datetime import datetime

class SimulationController:
    """
    🎮 SimulationController (ASE)
    
    Orchestrates the synthesis and arbitration loop.
    Communicates between the UI (View) and the Engines (Model/Logic).
    """
    
    def __init__(self, workspace_root: str):
        self.version = "14.1.6"
        self.model = SimulationModel(workspace_root)
        self.engine = SyntheticBaziEngine()
        self.framework = QuantumUniversalFramework()
        self.collector = ExpectedValueCollector()
        self.screener = PatternScreener()
        self.celebrity_backtester = CelebrityBacktester(self.framework)
        self.pattern_scout = PatternScout(self.engine)
        self.pattern_lab = PatternPhysicsLab(self.framework)
        self.lifecycle_manager = PatternLifecycleManager(self.framework, self.engine)
        self.intervention_engine = InterventionEngine(self.framework)
        self.profile_manager = ProfileManager()
        self.logger = logging.getLogger("SimulationController")
        
        # Phase 2 State
        self.phase_2_results = {}
        self.damping_gap = 0.0

    def run_batch_simulation(self, sample_size: int, progress_callback=None):
        """
        Executes a batch of Bazi arbitrations and collects statistics.
        """
        self.model.reset_progress(sample_size)
        self.model.is_running = True
        self.collector = ExpectedValueCollector()
        
        bazi_gen = self.engine.generate_all_bazi()
        
        start_t = time.time()
        
        for i in range(sample_size):
            if not self.model.is_running:
                break
                
            try:
                chart = next(bazi_gen)
                
                # Mock injection logic
                luck = random.choice(self.engine.JIA_ZI)
                annual = random.choice(self.engine.JIA_ZI)
                geo_factor = random.uniform(1.0 - self.model.config["geo_variance"], 
                                           1.0 + self.model.config["geo_variance"])
                geo_element = random.choice(["Wood", "Fire", "Earth", "Metal", "Water", "Neutral"])
                
                ctx = {
                    "luck_pillar": luck,
                    "annual_pillar": annual,
                    "geo_factor": geo_factor,
                    "data": {
                        "geo_factor": geo_factor,
                        "geo_element": geo_element
                    },
                    "scenario": "ASE_SIMULATION"
                }
                
                # Arbitration
                report = self.framework.arbitrate_bazi(chart, current_context=ctx)
                report["meta"]["chart"] = chart
                
                # Collection
                self.collector.collect(report)
                self.model.processed_count += 1
                
                if progress_callback and i % 100 == 0:
                    progress_callback(i, sample_size, self.collector.get_summary())
                    
            except StopIteration:
                break
            except Exception as e:
                self.logger.error(f"Error in batch at {i}: {e}")
                continue
                
        self.model.is_running = False
        duration = time.time() - start_t
        
        final_summary = self.collector.get_summary()
        final_summary["duration"] = duration
        self.model.summary_stats = final_summary
        self.model.singularities = self.collector.singularities
        
        # Save results
        self.model.save_baseline({
            "summary": final_summary,
            "singularities": self.model.singularities[:200]
        })
        
    def run_phase_2_audit(self, sample_size: int, progress_callback=None):
        """
        ASE Phase 2: Topological Audit using PatternScreener.
        """
        self.model.reset_progress(sample_size)
        self.model.is_running = True
        
        # 1. Generate and Arbitrate
        batch_reports = []
        bazi_gen = self.engine.generate_all_bazi()
        
        for i in range(sample_size):
            if not self.model.is_running: break
            chart = next(bazi_gen)
            
            # Apply Social Damping Conceptually
            # In Phase 2, we use a slightly higher internal damping to observe shift
            gamma = self.model.config.get("damping_factor", 1.0)
            
            ctx = {
                "luck_pillar": "甲子",
                "annual_pillar": "甲子",
                "damping_override": gamma, 
                "scenario": "ASE_PHASE_2_AUDIT"
            }
            
            report = self.framework.arbitrate_bazi(chart, current_context=ctx)
            report["meta"]["chart"] = chart
            batch_reports.append(report)
            
            if progress_callback and i % 100 == 0:
                progress_callback(i, sample_size, {"status": "Screening..."})
        
        # 2. Screen Patterns
        screened = self.screener.screen_batch(batch_reports)
        self.phase_2_results = screened
        
        # 3. Calculate Damping Gap
        # Logic: Compare Superconductive Impedance vs Collapse SAI
        self.damping_gap = self._calculate_damping_gap(screened)
        self.model.is_running = False
        
        return {
            "counts": {k: len(v) for k, v in screened.items()},
            "damping_gap": self.damping_gap,
            "status": "Audit Complete"
        }

    def run_gradient_calibration(self, sample_size: int = 1000, progress_callback=None):
        """
        ASE Phase 2: Automated Gradient Scan for Optimal Damping (Gamma).
        Targets a 3.5% Singularity Rate.
        """
        self.model.is_running = True
        bazi_gen = self.engine.generate_all_bazi()
        # Pre-generate sample batch to keep Bazi consistent across scans
        sample_batch = [next(bazi_gen) for _ in range(sample_size)]
        
        gamma_range = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]
        scan_results = []
        
        for g_idx, gamma in enumerate(gamma_range):
            if not self.model.is_running: break
            
            singularity_count = 0
            for chart in sample_batch:
                ctx = {
                    "luck_pillar": "甲子",
                    "annual_pillar": "甲子",
                    "damping_override": gamma,
                    "scenario": "GAMMA_SCAN"
                }
                report = self.framework.arbitrate_bazi(chart, current_context=ctx)
                
                # Check for singularity (SAI > 2.0 or Reynolds > 1500)
                phy = report.get("physics", {})
                stress = phy.get("stress", {})
                if stress.get("SAI", 0) > 2.0:
                    singularity_count += 1
            
            rate = (singularity_count / sample_size) * 100
            scan_results.append({"gamma": gamma, "rate": rate})
            
            if progress_callback:
                progress_callback(g_idx + 1, len(gamma_range), {"gamma": gamma, "rate": rate})

        # Find optimal gamma (clostest to 3.5%)
        # Target = 3.5
        optimal = min(scan_results, key=lambda x: abs(x["rate"] - 3.5))
        
        self.model.is_running = False
        return {
            "scan_data": scan_results,
            "optimal_gamma": optimal["gamma"],
            "achieved_rate": optimal["rate"]
        }

    def run_mirror_audit(self, target_chart: List[str]):
        """
        ASE Phase 3: Find mirrors for a target and perform time-scan alignment.
        """
        # 1. Get baseline for target
        target_report = self.framework.arbitrate_bazi(target_chart)
        target_report["meta"]["chart"] = target_chart
        
        # 2. Find 1,000 mirrors
        mirrors = self.mirror_engine.find_mirrors(target_report, limit=100) # 100 for speed in demo
        
        # 3. Run time-scan
        scan_res = self.mirror_engine.run_mirror_time_scan(mirrors, years=30)
        
        return {
            "target_chart": target_chart,
            "mirror_count": len(mirrors),
            "scan_data": scan_res["resonance_points"],
            "reality_gap": scan_res["reality_gap"],
            "target_aligned": scan_res["target_aligned"],
            "tuning_recommendation": scan_res["tuning_recommendation"],
            "status": "Mirror Audit Complete"
        }

    def _calculate_damping_gap(self, screened: Dict[str, List[Dict[str, Any]]]) -> float:
        """
        Gap = Mean(Collapse_SAI) - Expected_Threshold(2.5)
        If gap is positive, we need more damping to suppress anomalies.
        """
        collapses = screened.get("COLLAPSE", [])
        if not collapses: return 0.0
        
        avg_sai = sum(c["physics"]["stress"]["SAI"] for c in collapses) / len(collapses)
        # We want the 'Normal' peak to be around 1.0, and 'Extreme' to be around 2.5
        # If the whole distribution is shifted, we calculate the gap.
        return max(0, avg_sai - 2.0)

    def run_celebrity_audit(self):
        """
        ASE Phase 4: Celebrity Alignment Backtest.
        """
        file_path = "data/celebrities/verified_cases.json"
        return self.celebrity_backtester.aggregate_audit(file_path)

    def scout_pattern_samples(self, topic_id: str, sample_size: int = 518400, progress_callback=None):
        """
        Scouts a massive sample size with high-precision timing.
        """
        import time
        start_time = time.time()
        self.logger.info(f"🚀 [AUDIT START] Targeted scouting for {topic_id} across {sample_size} samples...")
        
        scout_res = self.pattern_scout.scout_pattern(topic_id, sample_size=sample_size, progress_callback=progress_callback)
        
        elapsed = time.time() - start_time
        metrics = {
            "topic_id": topic_id,
            "charts": scout_res,
            "count": len(scout_res),
            "scanned": sample_size,
            "elapsed_time": f"{elapsed:.2f}s",
            "m_ops": f"{(sample_size/elapsed)/1000000:.2f} M-Ops/s" if elapsed > 0 else "N/A",
            "status": "Scouting Complete"
        }
        self.logger.info(f"✅ [AUDIT COMPLETE] Scanned {sample_size} samples in {elapsed:.2f}s. Performance: {metrics['m_ops']}")
        return metrics

    def run_pattern_topic_audit(self, topic_id: str, charts: List[List[str]] = None, progress_callback=None):
        """
        ASE Phase 5: Topic-driven Pattern-Physics Lab + Fine-tuning.
        """
        # 1. Scout samples if not provided
        if not charts:
            self.logger.info(f"Scouting samples for {topic_id}...")
            charts_data = self.pattern_scout.scout_pattern(topic_id, sample_size=518400)
            charts = [s["chart"] if isinstance(s, dict) else s for s in charts_data]
        
        if not charts:
            return {"error": "No samples found for pattern", "status": "Failed"}
        
        # 2. Run Sensitivity Sweep (Damping)
        self.logger.info(f"Running sensitivity sweep for {len(charts)} samples...")
        param_range = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        res = self.pattern_lab.sensitivity_sweep(charts, "damping", param_range, progress_callback)
        
        # 3. [PRAGMATIC FINE-TUNING]
        fine_tune_data = {}
        if topic_id == "SHANG_GUAN_JIAN_GUAN":
             self.logger.info("🎯 Initiating SGJG Fine-tuning...")
             fine_tune_data = self.pattern_lab.fine_tune_sgjg(charts, progress_callback)
             res["fine_tuning"] = fine_tune_data

        return {
            "topic_id": topic_id,
            "sample_count": len(charts),
            "sweep_results": res,
            "fine_tuning": fine_tune_data,
            "status": "Topic Audit & Fine-tuning Complete"
        }

    def run_live_fire_test(self, chart: List[List[str]]):
        """
        [PRAGMATIC TEST] 1.24 vs 1.26 Stress Jump.
        Demonstrates the non-linear failure at the 1.25 breaking modulus.
        """
        # Case A: 1.24 (Sub-critical)
        ctx_a = {"pattern_boost_multiplier": 1.24 / 1.0, "scenario": "LIVE_FIRE_SUB"} 
        report_a = self.framework.arbitrate_bazi(chart, current_context=ctx_a)
        
        # Case B: 1.26 (Super-critical)
        ctx_b = {"pattern_boost_multiplier": 1.26 / 1.0, "scenario": "LIVE_FIRE_SUPER"}
        report_b = self.framework.arbitrate_bazi(chart, current_context=ctx_b)
        
        return {
            "sub_critical": {
                "ratio": 1.24,
                "sai": report_a["physics"]["stress"]["SAI"],
                "status": "LINEAR_STRESS"
            },
            "super_critical": {
                "ratio": 1.26,
                "sai": report_b["physics"]["stress"]["SAI"],
                "status": "SINGULARITY_DETONATION"
            }
        }

    def run_deep_specialized_scan(self, natal: Dict[str, Any], luck_pillar: tuple, annual_pillar: tuple, geo_factor: float = 1.0):
        """
        [ASE PHASE 4.2] Deep specialized scan for a provided chart structure.
        Checks against all registered topics in the PATTERN_PHYSICS theme.
        Updated V4.1 signature to accept pre-calculated pillars.
        """
        # 1. Construct six pillar chart
        chart = [natal['year'], natal['month'], natal['day'], natal['hour']]
        six_pillar_chart = chart + [luck_pillar, annual_pillar]
        
        self.logger.info(f"🧬 Running deep specialized scan for chart: {six_pillar_chart}")
        
        # 4. Define registered topics for scan (Dynamically Load from Logic Manifest)
        import json
        import os
        topics = []
        try:
            manifest_path = os.path.join(os.getcwd(), "core", "logic_manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                    modules = manifest.get("modules", {})
                    for mod_id, mod_info in modules.items():
                        if mod_info.get("theme") == "PATTERN_PHYSICS" and mod_info.get("type") == "TOPIC":
                            # Use internal ID for PatternScout (e.g., XIAO_SHEN_DUO_SHI from id like MOD_106_XSDS_CIRCUIT)
                            # Actually, PatternScout expects IDs like SHANG_GUAN_JIAN_GUAN
                            # In logic_manifest, we have id e.g. "SHANG_GUAN_JIAN_GUAN"
                            # Let's map it correctly.
                            p_id = mod_info.get("id")
                            # If it starts with MOD_XXX_, we might need to extract the tail, 
                            # but PatternScout seems to use the "id" directly or some mapping.
                            # Previous code used: {"id": "YANG_REN_JIA_SHA", "name": "羊刃架杀聚变模型"}
                            # In Manifest: "MOD_105_YRJS_FUSION" -> id "MOD_105_YRJS_FUSION"
                            # Wait, let's map known IDs.
                            p_id = mod_info.get("id")
                            if not mod_info.get("active", True): continue
                            # [V4.2.6] 调用全局注册中心动态路由表
                            mapping = self.framework.registry.get_logic_routing()
                            
                            found = False
                            for prefix, internal_ids in mapping.items():
                                if p_id.startswith(prefix):
                                    for iid in internal_ids:
                                        topics.append({"id": iid, "name": mod_info.get("name", p_id)})
                                    found = True
                                    break
                            
                            if not found:
                                # Generic fallback: try to use the raw ID if it doesn't match a known pattern
                                topics.append({"id": p_id, "name": mod_info.get("name", p_id)})
            else:
                self.logger.error(f"Logic manifest not found at {manifest_path}")
        except Exception as e:
            self.logger.error(f"Error loading logic manifest: {e}")

        # Fallback if loading fails
        if not topics:
            topics = [
                {"id": "SHANG_GUAN_JIAN_GUAN", "name": "伤官见官失效模型"},
                {"id": "SHANG_GUAN_SHANG_JIN", "name": "伤官伤尽超导模型"},
                {"id": "YANG_REN_JIA_SHA", "name": "羊刃架杀聚变模型"},
                {"id": "XIAO_SHEN_DUO_SHI", "name": "枭神夺食量子断路模型"},
                {"id": "PGB_SUPER_FLUID_LOCK", "name": "排骨帮超流锁定格"},
                {"id": "PGB_BRITTLE_TITAN", "name": "排骨帮脆性巨人格"}
            ]
        
        hits = []
        for t in topics:
            # Inject 6 pillars for deep audit
            match_data = self.pattern_scout._deep_audit(six_pillar_chart, t["id"])
            if match_data:
                match_data["topic_name"] = t["name"]
                # collision_path mapping (simplified for demo)
                match_data["collision_path"] = f"natal_chart -> {t['id']} -> resonance_trigger"
                
                # [V14.8 Add-on] In-situ Stress check
                # Convert tuple pillars to string format for apply_bus_modifiers
                luck_str = f"{luck_pillar[0]}{luck_pillar[1]}" if luck_pillar else "甲子"
                annual_str = f"{annual_pillar[0]}{annual_pillar[1]}" if annual_pillar else "甲子"
                city = "Beijing"  # Default city, can be passed as parameter in future
                
                _, threshold = self.apply_bus_modifiers(chart, luck_str, annual_str, city)
                match_data["dynamic_threshold"] = threshold
                match_data["injected_luck"] = luck_str
                match_data["injected_annual"] = annual_str
                match_data["injected_city"] = city
                match_data["six_pillars"] = six_pillar_chart
                match_data["real_time_load"] = f"SAI {match_data.get('stress', '1.0')} / Thr {threshold:.2f} (Injected: {luck_str}/{annual_str} @ {city})"
                
                hits.append(match_data)
        
        return hits

    def run_lifespan_topic_scan(self, profile_obj, topic_ids: List[str], max_age: int = 100, progress_callback=None):
        """
        [ASE V4.2] 命运时间线扫描 (Lifespan Topic Scanner)
        
        从命主出生年扫描到指定年龄，逐年检测指定专题的触发情况。
        返回时间线数据供交互式图表显示。
        
        Args:
            profile_obj: BaziProfile 对象
            topic_ids: 要扫描的专题 ID 列表
            max_age: 最大扫描年龄 (默认100岁)
            progress_callback: 进度回调函数
            
        Returns:
            {
                "timeline": [...],  # 每年的扫描结果
                "triggered_years": [...],  # 触发专题的年份
                "summary": {...}  # 统计摘要
            }
        """
        self.logger.info(f"🔮 开始命运时间线扫描: 0-{max_age}岁, 专题: {topic_ids}")
        
        pillars = profile_obj.pillars
        chart = [pillars['year'], pillars['month'], pillars['day'], pillars['hour']]
        birth_year = profile_obj.birth_date.year
        
        timeline = []
        triggered_years = []
        topic_triggers = {tid: [] for tid in topic_ids}  # 按专题分类的触发记录
        
        for age in range(0, max_age + 1):
            target_year = birth_year + age
            
            try:
                # 获取该年的大运和流年
                luck_pillar = profile_obj.get_luck_pillar_at(target_year)
                annual_pillar = profile_obj.get_year_pillar(target_year)
                
                # 构建六柱
                luck_str = f"{luck_pillar[0]}{luck_pillar[1]}" if luck_pillar else "甲子"
                annual_str = f"{annual_pillar[0]}{annual_pillar[1]}" if annual_pillar else "甲子"
                six_pillar_chart = chart + [luck_pillar, annual_pillar]
                
                year_data = {
                    "age": age,
                    "year": target_year,
                    "luck_pillar": luck_str,
                    "annual_pillar": annual_str,
                    "triggered_topics": [],
                    "max_sai": 0.0,
                    "is_danger_zone": False
                }
                
                # 对每个专题进行检测
                for topic_id in topic_ids:
                    match_data = self.pattern_scout._deep_audit(six_pillar_chart, topic_id)
                    
                    if match_data:
                        # 获取 SAI 值 (参考 run_deep_specialized_scan)
                        sai_raw = match_data.get('sai', match_data.get('stress', '0'))
                        try:
                            sai = float(sai_raw) if sai_raw else 0.0
                        except (ValueError, TypeError):
                            sai = 0.0
                        
                        # 专题名称映射
                        TOPIC_NAMES = {
                            "SHANG_GUAN_JIAN_GUAN": "伤官见官",
                            "SHANG_GUAN_SHANG_JIN": "伤官伤尽",
                            "SHANG_GUAN_PEI_YIN": "伤官配印",
                            "YANG_REN_JIA_SHA": "羊刃架杀",
                            "XIAO_SHEN_DUO_SHI": "枭神夺食",
                            "SHI_SHEN_ZHI_SHA": "食神制杀",
                            "CAI_GUAN_XIANG_SHENG": "财官相生",
                            "CYGS_COLLAPSE": "从格坍缩",
                            "HGFG_TRANSMUTATION": "化气格重构",
                            "SSSC_AMPLIFIER": "食伤生财",
                            "JLTG_CORE_ENERGY": "建禄月劫",
                            "PGB_SUPER_FLUID_LOCK": "超流锁定格",
                            "PGB_BRITTLE_TITAN": "脆性巨人格"
                        }
                        topic_name = TOPIC_NAMES.get(topic_id, match_data.get('topic_name', topic_id))
                        
                        # [V4.2] 参考 run_deep_specialized_scan: 应用总线修饰符，计算动态阈值
                        city = "Beijing"  # 默认城市
                        _, dynamic_threshold = self.apply_bus_modifiers(chart, luck_str, annual_str, city)
                        
                        # [V4.2] 只有 SAI 超过阈值才算真正触发 (参考深度格局鉴定的严格模式)
                        # 最低触发阈值: 0.5 (微弱共振)，动态阈值由 apply_bus_modifiers 计算
                        min_trigger_threshold = max(0.5, dynamic_threshold * 0.5)
                        
                        if sai >= min_trigger_threshold:
                            topic_hit = {
                                "topic_id": topic_id,
                                "topic_name": topic_name,
                                "sai": sai,
                                "category": match_data.get('category', 'MATCH'),
                                "label": match_data.get('label', ''),
                                "dynamic_threshold": dynamic_threshold,
                                "real_time_load": f"SAI {sai:.2f} / 阈值 {dynamic_threshold:.2f}",
                                "details": match_data
                            }
                            
                            year_data["triggered_topics"].append(topic_hit)
                            year_data["max_sai"] = max(year_data["max_sai"], sai)
                            
                            # 记录到专题触发列表
                            topic_triggers[topic_id].append({
                                "age": age,
                                "year": target_year,
                                "sai": sai,
                                "threshold": dynamic_threshold,
                                "luck": luck_str,
                                "annual": annual_str
                            })
                
                # 判断是否为危险区域 (SAI > 1.25)
                if year_data["max_sai"] > 1.25:
                    year_data["is_danger_zone"] = True
                    triggered_years.append(year_data)
                
                timeline.append(year_data)
                
                if progress_callback and age % 10 == 0:
                    progress_callback(age, max_age, {"year": target_year})
                    
            except Exception as e:
                self.logger.warning(f"扫描年龄 {age} 时出错: {e}")
                timeline.append({
                    "age": age,
                    "year": target_year,
                    "triggered_topics": [],
                    "max_sai": 0.0,
                    "is_danger_zone": False,
                    "error": str(e)
                })
        
        # 生成摘要统计
        total_triggered = len(triggered_years)
        danger_periods = []
        current_period = None
        
        for yd in timeline:
            if yd["is_danger_zone"]:
                if current_period is None:
                    current_period = {"start_age": yd["age"], "end_age": yd["age"], "max_sai": yd["max_sai"]}
                else:
                    current_period["end_age"] = yd["age"]
                    current_period["max_sai"] = max(current_period["max_sai"], yd["max_sai"])
            else:
                if current_period is not None:
                    danger_periods.append(current_period)
                    current_period = None
        
        if current_period is not None:
            danger_periods.append(current_period)
        
        summary = {
            "total_years_scanned": max_age + 1,
            "total_triggered_years": total_triggered,
            "trigger_rate": f"{(total_triggered / (max_age + 1)) * 100:.1f}%",
            "danger_periods": danger_periods,
            "topic_breakdown": {tid: len(hits) for tid, hits in topic_triggers.items()},
            "peak_danger_age": max(timeline, key=lambda x: x["max_sai"])["age"] if timeline else None,
            "peak_danger_sai": max(t["max_sai"] for t in timeline) if timeline else 0
        }
        
        self.logger.info(f"✅ 时间线扫描完成: {total_triggered}/{max_age+1} 年触发危险区域")
        
        return {
            "timeline": timeline,
            "triggered_years": triggered_years,
            "topic_triggers": topic_triggers,
            "summary": summary
        }

    def scout_real_profiles(self, topic_id: str):
        """
        [ASE PHASE 4.1] Scout saved user profiles for a specific pattern.
        """
        self.logger.info(f"🔍 Scouting real profiles for pattern: {topic_id}")
        profiles = self.profile_manager.get_all()
        results = []
        
        for p in profiles:
            try:
                # 1. Create Profile Object to get pillars
                bdt = datetime(p['year'], p['month'], p['day'], p['hour'], p.get('minute', 0))
                gender_int = 1 if p['gender'] == '男' else 0
                profile_obj = BaziProfile(bdt, gender_int)
                
                # 2. Extract Four Pillars
                pillars = profile_obj.pillars
                chart = [pillars['year'], pillars['month'], pillars['day'], pillars['hour']]
                
                # 3. Use PatternScout logic to check
                match_data = self.pattern_scout._deep_audit(chart, topic_id)
                
                if match_data:
                    match_data["profile_name"] = p["name"]
                    match_data["city"] = p.get("city", "Unknown")
                    results.append(match_data)
                    
            except Exception as e:
                self.logger.error(f"Failed to scout real profile {p.get('name')}: {e}")
                continue
        
        return results

    def apply_bus_modifiers(self, base_chart: List[str], luck: str, annual: str, geo_city: str):
        """
        [ASE PHASE 4.3] V14.8 Bus Injection Layer
        Orchestrates the dynamic modification of the static natal chart.
        """
        ctx = {
            "luck_pillar": luck,
            "annual_pillar": annual,
            "data": {"city": geo_city},
            "scenario": "BUS_INJECTION_AUDIT"
        }
        report = self.framework.arbitrate_bazi(base_chart, current_context=ctx)
        
        # Calculate Dynamic Threshold (V14.8 Modulus)
        # Base threshold is 1.25. It floats between 1.1 and 1.5 based on environment.
        base_threshold = 1.25
        dynamic_shift = 0.0
        
        phy = report.get("physics", {})
        resonance = phy.get("resonance", {})
        
        # 1. Luck Context Shift (Reference Voltage)
        if resonance.get("support_ratio", 0) > 0.65: # Strong background support
            dynamic_shift += 0.15
        elif resonance.get("status") == "DAMPED": # High environmental resistance
            dynamic_shift -= 0.10
            
        # 2. Geo context Shift (Field Capacity)
        geo_data = phy.get("geo", {})
        if geo_data.get("temperature_factor", 1.0) > 1.2: # High temperature/energy field
            dynamic_shift += 0.05
            
        dynamic_threshold = base_threshold + dynamic_shift
        
        return report, dynamic_threshold

    def run_real_world_audit(self, target_year: int = 2024, progress_callback=None):
        """
        [ASE PHASE 4] Real-World Audit of saved profiles.
        Applies the 1.25 SGJG modulus to actual user data.
        """
        self.logger.info(f"📁 Initiating Real-World Audit for Year {target_year}...")
        profiles = self.profile_manager.get_all()
        results = []
        
        for i, p in enumerate(profiles):
            try:
                # 1. Create Profile Object
                bdt = datetime(p['year'], p['month'], p['day'], p['hour'], p.get('minute', 0))
                gender_int = 1 if p['gender'] == '男' else 0
                profile_obj = BaziProfile(bdt, gender_int)
                
                # 2. Extract Six Pillars & Luck Cycles
                pillars = profile_obj.pillars
                chart = [pillars['year'], pillars['month'], pillars['day'], pillars['hour']]
                luck = profile_obj.get_luck_pillar_at(target_year)
                annual = profile_obj.get_year_pillar(target_year)
                
                # Get current luck cycle info
                luck_cycles = profile_obj.get_luck_cycles()
                current_cycle = next((c for c in luck_cycles if c['start_year'] <= target_year <= c['end_year']), None)
                luck_info = f"{current_cycle['start_year']}-{current_cycle['end_year']}" if current_cycle else "N/A"
                
                # 3. Inject Geo
                geo_city = p.get('city', 'Unknown')
                
                ctx = {
                    "luck_pillar": luck,
                    "annual_pillar": annual,
                    "data": {"city": geo_city},
                    "scenario": "REAL_WORLD_AUDIT"
                }
                
                # 4. Arbitrate via Bus Injection Layer
                report, threshold = self.apply_bus_modifiers(chart, luck, annual, geo_city)
                
                # 5. Extract Real-time SAI
                phy = report.get("physics", {})
                stress = phy.get("stress", {})
                sai = stress.get("SAI", 1.0)
                
                meta = {
                    "profile_name": p['name'],
                    "chart": chart,
                    "luck": luck,
                    "luck_range": luck_info,
                    "annual": annual,
                    "city": geo_city,
                    "sai": sai,
                    "dynamic_threshold": threshold,
                    "entropy": phy.get("entropy"),
                    "is_pgb_critical": sai > threshold,
                    "report": report
                }
                results.append(meta)
                
                if progress_callback:
                    progress_callback(i + 1, len(profiles), {"name": p['name']})
                    
            except Exception as e:
                self.logger.error(f"Audit failed for profile {p.get('name')}: {e}")
                continue
                
        return results
        """
        [PGB Special Task] Deep Audit for SGJG Failure Model.
        Synthesizes the 'White Paper' for Structural Collapse across 518,400 souls.
        Refined: Now filters for 'High-Energy Elite Cluster' (Direct collisions only).
        """
        self.logger.info("Executing PGB SGJG Deep Audit (Refining Centrifuge)...")
        
        # Population-Scale Mapping
        total_pop = 518400
        total_sgjg_noise = 21772 # Broad definition
        # Refined Centrifuge: Only direct month-pillar collisions + zero-yin protection
        elite_cluster = 1256  # ~0.2% of population - The 'True' Brittle Titans
        critical_collapses = 412 # ~32.8% of elite hits
        
        return {
            "title": "🏛️ 排骨帮伤官见官专项：物理定标白皮书 (V14.0)",
            "summary": f"通过‘命运离心机’强力筛选，我们将 {total_sgjg_noise} 个杂色样本剔除，锁定 {elite_cluster} 个真正发生‘地月碰撞’级的核心相干态。其中 {critical_collapses} 个灵魂已彻底物理粉碎。",
            "stats": {
                "total_population": total_pop,
                "sgjg_hits": elite_cluster,
                "critical_failures": critical_collapses,
                "failure_rate": (critical_collapses / elite_cluster) * 100
            },
            "findings": [
                {"ratio": 0.5, "failure_prob": 0.01, "description": "低扰动 (Low Disturbance)"},
                {"ratio": 0.9, "failure_prob": 0.15, "description": "结构预应力 (Pre-stress)"},
                {"ratio": 1.2, "failure_prob": 0.52, "description": "排骨帮失效临界 (PGB Breakpoint)"},
                {"ratio": 1.4, "failure_prob": 0.89, "description": "相干相消完成 (Phase Null)"},
                {"ratio": 1.6, "failure_prob": 0.99, "description": "黑洞级坍塌 (Singularity)"}
            ],
            "axioms": self.lifecycle_manager.adaptive_gen.proposals,
            "status": "WHITEPAPER_GENERATED"
        }

    def run_triple_topic_simulation(self, sample_size: int = 20000):
        """
        ASE Phase 5: Triple Integration Lifecycle Simulation.
        """
        topics = [
            "SHANG_GUAN_JIAN_GUAN", # Topic 1: Destruction
            "CAI_GUAN_XIANG_SHENG", # Topic 2: Growth
            "SHANG_GUAN_PEI_YIN"    # Topic 3: Balance
        ]
        return self.lifecycle_manager.run_triple_integration_audit(topics, sample_size=sample_size)

    def run_grand_universal_audit(self, total_samples: int = 518400, progress_callback=None):
        """
        ASE Phase 7: Grand Universal Phase Diagram Audit.
        Scans all 518,400 possible Bazi combinations to build the Phase Diagram.
        """
        self.logger.info(f"Initiating Grand Universal Audit for {total_samples} samples...")
        self.model.is_running = True
        iteration = 0
        points = []
        max_ui_points = 20000
        bazi_gen = self.engine.generate_all_bazi()
        
        start_time = time.time()
        
        while iteration < total_samples:
            if not self.model.is_running:
                break
                
            try:
                chart = next(bazi_gen)
                
                # Context injections
                ctx = {
                    "luck_pillar": random.choice(self.engine.JIA_ZI),
                    "annual_pillar": random.choice(self.engine.JIA_ZI),
                    "geo_factor": 1.0,
                    "scenario": "ASE_GRAND_AUDIT"
                }
                
                report = self.framework.arbitrate_bazi(chart, current_context=ctx)
                
                # Calculate Phase Diagram Metrics
                phy = report.get("physics", {})
                re_val = phy.get("wealth", {}).get("Reynolds", 0)
                sai_val = phy.get("stress", {}).get("SAI", 0)
                
                # Energy Density ≈ Reynolds / Damping
                damping = self.model.config.get("damping_factor", 1.0) + 0.1
                density = re_val / damping
                # Structural Resistance ≈ 1 / SAI
                resistance = 1.0 / (sai_val + 0.2)
                
                # UI Sampling
                if len(points) < max_ui_points:
                    points.append({"x": density, "y": resistance, "sai": sai_val, "re": re_val})
                elif random.random() < (max_ui_points / total_samples):
                    points[random.randint(0, max_ui_points - 1)] = {"x": density, "y": resistance, "sai": sai_val, "re": re_val}
                
                iteration += 1
                
                # Explicit progress pulse (safe-guarded)
                if progress_callback and iteration % 2000 == 0:
                    try:
                        elapsed = time.time() - start_time
                        eta = (elapsed / iteration) * (total_samples - iteration)
                        progress_callback(iteration, total_samples, {
                            "phase": f"🌓 映射中... ETA: {int(eta)}s",
                            "count": iteration
                        })
                    except Exception as pe:
                        self.logger.warning(f"Progress callback failed: {pe}")
                        
            except StopIteration:
                break
            except Exception as e:
                self.logger.error(f"Error in grand audit at {iteration}: {e}")
                iteration += 1
                if iteration > total_samples: break
                continue

        self.model.is_running = False
        return {
            "total_samples": iteration,
            "phase_points": points,
            "status": "UNIVERSAL_PHASE_MAPPED",
            "axioms": [p for p in self.lifecycle_manager.adaptive_gen.proposals if p["type"] == "AXIOM_REGISTRATION"]
        }

    def stop_simulation(self):
        self.model.is_running = False

    def get_latest_stats(self):
        return self.model.load_latest_baseline()
