import random
import datetime
from lunar_python import Solar
from core.flux import FluxEngine

class AdvancedTrajectoryEngine:
    def __init__(self, chart, luck_cycles, start_year):
        self.chart = chart
        self.luck_cycles = luck_cycles
        self.start_year = start_year
        self.flux_engine = FluxEngine(chart)
        
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
        from core.quantum import QuantumEngine
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
