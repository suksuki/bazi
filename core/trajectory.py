import random
import datetime
from lunar_python import Solar
from core.flux import FluxEngine
from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

class AdvancedTrajectoryEngine:
    def __init__(self, chart, luck_cycles, start_year):
        self.chart = chart
        self.luck_cycles = luck_cycles
        self.start_year = start_year
        self.flux_engine = FluxEngine(chart)
        self.quantum = QuantumEngine() # Init V2.0 Engine

    def generate_v2_curve(self, start_year, end_year, favorable_elements=None, unfavorable_elements=None):
        """
        V2.0 Deterministic Life Curve using 'Cover Head/Cut Feet' Structural Logic.
        """
        # 1. Auto-detect favorable if not provided
        if not favorable_elements or not unfavorable_elements:
             # Basic Wang/Shuai check
             # Note: self.chart expected format from BaziCalculator, need conversion or simple mapping
             # For robustness, we'll try to deduce from QuantumEngine helper if we had birth data, 
             # but here we might rely on the caller passing it, or do a rough estimate.
             # Fallback: Assume Balanced/Strong for now or require inputs.
             pass 

        timeline = []
        for year in range(start_year, end_year + 1):
             # 2. Get Pillar (e.g. "辛卯")
             # Use QuantumEngine helper
             elems = self.quantum.get_elements_for_year(year) # ["Metal", "Wood"] - this gives elements, not chars
             # We need actual chars for structural check. 
             # Let's use lunar_python directly as we are inside the engine context
             from lunar_python import Solar
             solar = Solar.fromYmd(year, 6, 15)
             lunar = solar.getLunar()
             year_pz = lunar.getYearInGanZhi() # "辛卯"
             
             # 3. Call V2.0 Score
             result = self.quantum.calculate_year_score(
                 year_pillar=year_pz,
                 favorable_elements=favorable_elements or [],
                 unfavorable_elements=unfavorable_elements or [],
                 birth_chart=self.chart
             )
             raw_score = result['score']
             details = result['details']
             
             # 4. Normalize (-15 ~ +15) -> (-10 ~ +10)
             # Smoothing high volatility
             normalized_score = max(-10, min(10, raw_score))
             
             # Analyze Reason (Simple Reverse Engineering for UI)
             comment = ""
             if raw_score <= -5.0:
                 comment = "⚠️ 结构截脚/盖头"
             elif raw_score >= 5.0:
                 comment = "🌟 干支同气/生扶"

             # Append V3.0 Details
             # V3.0 Sprint 4: Treasury Detection for UI
             is_treasury_open = False
             is_wealth_treasury = False
             treasury_element = None
             
             if details:
                 # Check for Treasury Openings
                 treasury_msg = [d for d in details if "库" in d]
                 if treasury_msg:
                     comment = f"{comment} | {' '.join(treasury_msg)}"
                     is_treasury_open = True
                     
                     # Detect if it's a Wealth Treasury (财库)
                     if any("💰" in d or "财库" in d for d in details):
                         is_wealth_treasury = True
                     
                     # Extract treasury element (e.g., 戌, 辰)
                     for d in details:
                         if "库[" in d:
                             # Extract character between [ and ]
                             start = d.find("[") + 1
                             end = d.find("]")
                             if start > 0 and end > start:
                                 treasury_element = d[start:end]
                                 break

             timeline.append({
                 "year": year,
                 "pillar": year_pz,
                 "score": normalized_score,
                 "comment": comment.strip(" |"),
                 "raw_score": raw_score,
                 # V3.0 Metadata
                 "is_treasury_open": is_treasury_open,
                 "is_wealth_treasury": is_wealth_treasury,
                 "treasury_element": treasury_element,
                 "details": details  # Full details list
             })
             
        return timeline
        
    def run_monte_carlo(self, end_age=90, granularity="year", n_simulations=50):
        """
        Optimized Monte Carlo:
        1. Calculate deterministic backbone (Pillars, Flux, Quantum Mean) ONCE.
        2. Run N cheap stochastic sampling passes.
        """
        # Optimize N for granularities
        if granularity == 'day': n_simulations = min(n_simulations, 5)
        elif granularity == 'month': n_simulations = min(n_simulations, 20)

        # 1. Pre-calculate Backbone (The Heavy Lifting)
        backbone = self._calculate_backbone(end_age, granularity)
        
        # 2. Init Sampler
        from core.wuxing_engine import WuXingEngine
        from core.quantum import TenGodsWaveFunction
        
        wx = WuXingEngine(self.chart)
        strength_data = wx.calculate_strength()
        wave_function = TenGodsWaveFunction(chart_structure={}, wuxing_report=strength_data)
        
        all_paths = []
        
        for _ in range(n_simulations):
            path = []
            for step in backbone:
                # Stochastic Step
                dom_god = step['dom_god']
                aspects_data = step['aspects_data'] # {Career: {Expected: 50...}}
                
                vector_t = {}
                for aspect, data in aspects_data.items():
                    mu = data['Expected_Value']
                    # Collapse Wave Function (Random Gauss)
                    val = wave_function.collapse_wave_function(dom_god, base_energy=mu)
                    vector_t[aspect] = val
                
                # Metadata
                vector_t['Total'] = sum(vector_t.values()) / max(1, len(vector_t))
                vector_t['age'] = step['age']
                vector_t['year'] = step['year']
                
                path.append(vector_t)
            all_paths.append(path)
            
        return self._aggregate_paths_multi_dim(all_paths)

    def _calculate_backbone(self, end_age, granularity):
        """
        Generates the deterministic trajectory backbone.
        """
        # Note: QuantumSimulator not needed here, only TenGodsWaveFunction is used
        from lunar_python import Solar
        
        timeline = []
        start_date = datetime.date(self.start_year, 1, 1)
        curr_date = start_date
        age = 0
        
        # optimization: cache dynyun lookup
        dy_cache = {}
        
        while age <= end_age:
            # 1. Calendar
            solar = Solar.fromYmd(curr_date.year, curr_date.month, curr_date.day)
            lunar = solar.getLunar()
            
            y_gz = lunar.getYearInGanZhi()
            m_gz = lunar.getMonthInGanZhi()
            d_gz = lunar.getDayInGanZhi()
            
            # 2. Da Yun
            curr_dy_gan, curr_dy_zhi = "", ""
            year = curr_date.year
            if year in dy_cache:
                curr_dy_gan, curr_dy_zhi = dy_cache[year]
            else:
                for cycle in self.luck_cycles:
                    if cycle['start_year'] <= year <= cycle['end_year']:
                        gz = cycle['gan_zhi']
                        if len(gz) >= 2: 
                             curr_dy_gan, curr_dy_zhi = gz[0], gz[1]
                        break
                dy_cache[year] = (curr_dy_gan, curr_dy_zhi)
            
            # 3. External Trigger
            if granularity == 'day':
                ext_stem, ext_branch = d_gz[0], d_gz[1]
            elif granularity == 'month':
                ext_stem, ext_branch = m_gz[0], m_gz[1]
            else: 
                ext_stem, ext_branch = y_gz[0], y_gz[1]
                
            # 4. Flux & Quantum
            flux_data = self.flux_engine.calculate_flux(curr_dy_gan, curr_dy_zhi, ext_stem, ext_branch)
            total_entropy = 0.0
            if flux_data:
                for d in flux_data.values():
                     if isinstance(d, dict) and 'entropy' in d:
                         total_entropy += d.get('entropy', 0.0)
            
            if total_entropy > 6: dom_god = "QiSha"
            elif total_entropy > 4: dom_god = "ShangGuan"
            elif total_entropy > 2: dom_god = "PianCai"
            else: dom_god = "ZhengGuan"
            
            q_engine = QuantumEngine(chart_gods={dom_god: 50}, reactions=[], flux_data=flux_data)
            aspects_result = q_engine.simulate() # Returns {Expected, Sigma...} for each aspect
            
            timeline.append({
                'age': age,
                'year': year,
                'dom_god': dom_god,
                'aspects_data': aspects_result
            })
            
            # 5. Advance
            if granularity == 'year':
                curr_date = datetime.date(curr_date.year + 1, 1, 1)
            elif granularity == 'month':
                # logic for next month
                nxt_m = curr_date.month + 1
                nxt_y = curr_date.year
                if nxt_m > 12: nxt_m, nxt_y = 1, nxt_y + 1
                try: curr_date = datetime.date(nxt_y, nxt_m, 1)
                except: curr_date = datetime.date(nxt_y, nxt_m, 28) # fallback
            elif granularity == 'day':
                curr_date += datetime.timedelta(days=1)
                
            age = curr_date.year - self.start_year
            
        return timeline

    def _aggregate_paths_multi_dim(self, input_paths):
        """
        Aggregates N paths -> Stats for EACH dimension (Total, Career, Wealth...)
        """
        if not input_paths: return []
        
        steps = len(input_paths[0])
        keys = [k for k in input_paths[0][0].keys() if k not in ['age', 'year']] # e.g. Total, Career...
        
        stats_timeline = []
        import statistics

        for i in range(steps):
            age = input_paths[0][i]['age']
            year = input_paths[0][i]['year']
            
            row = {"age": age, "year": year}
            
            for k in keys:
                scores = [p[i][k] for p in input_paths]
                row[f"{k}_mean"] = statistics.mean(scores)
                # Standard Deviation for Total only? Or all? 
                # Let's keep data light. Just Mean for aspects, Sigma for Total.
                if k == "Total":
                    sd = statistics.stdev(scores) if len(scores)>1 else 0
                    row["Total_upper"] = row[f"{k}_mean"] + sd
                    row["Total_lower"] = row[f"{k}_mean"] - sd
            
            stats_timeline.append(row)
            
        return stats_timeline
