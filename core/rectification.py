
import datetime
from core.trajectory import AdvancedTrajectoryEngine
from lunar_python import Solar

class RectificationEngine:
    """
    Reverse engineers the Bazi chart (specifically the Hour Pillar) 
    based on known life events.
    """
    
    def __init__(self, chart_loader_func):
        # We need a function that can create a chart object given a date/time
        # This prevents circular imports or duplicated logic
        self.chart_loader = chart_loader_func
        
    def find_best_hour(self, year, month, day, events):
        """
        Iterates through 12 double-hours to find the best fit for the events.
        events: List of {year, aspect, score}
        """
        results = []
        hours = [0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23] # Representative hours
        
        for h in hours:
            # 1. Create Chart for this hour
            # We assume a standard function signature for chart creation
            try:
                # Construct a Solar object or similar input for the chart loader
                solar = Solar.fromYmdHms(year, month, day, h, 0, 0)
                chart = self.chart_loader(solar)
                
                # 2. Run Simulation
                # We need Luck Cycles to run sim. Chart object usually has it or we compute it.
                # Assuming chart object encompasses all needed data
                # Or we need to re-instantiate TrajectoryEngine logic
                
                # Let's assume chart is the dictionary the system uses
                # We need to construct the 'luck_cycles' separately if not in chart
                # Ideally, reuse main.py's `compute_chart` logic.
                
                # ...Wait, AdvancedTrajectoryEngine needs `chart` (dict) and `luck_cycles`.
                # I will need to call the external computation logic.
                # For now, I will just return the fitness score logic here and let the caller loop.
                pass 
            except Exception as e:
                print(f"Rectification Error at hour {h}: {e}")
                continue
                
        return results

    def score_simulation(self, sim_stats, events):
        """
        Calculates fitness score.
        sim_stats: [{'year': 2000, 'Total_mean': 60, ...}]
        events: [{'year': 2000, 'aspect': 'Career', 'score': 90}]
        """
        total_error = 0
        count = 0
        
        sim_map = {r['year']: r for r in sim_stats}
        
        for e in events:
            yr = e.get('year')
            if yr not in sim_map: continue
            
            # Target
            actual = e.get('score', 50)
            
            # Prediction
            # If aspect is specific (Career), look for Career_mean.
            # Fallback to Total_mean.
            aspect_key = e.get('aspect', 'Total')
            # Map aspect to column
            col_map = {
                "Career": "事业 (Career)_mean", 
                "Wealth": "财富 (Wealth)_mean",
                "Total": "Total_mean"
            }
            # Simple fuzzy matching
            target_col = "Total_mean" 
            for k, v in col_map.items():
                if k in aspect_key: target_col = v; break
            
            # Check if column exists, else use Total
            if target_col not in sim_map[yr]: target_col = "Total_mean"
            
            predicted = sim_map[yr].get(target_col, 50)
            
            # Error = Squared Diff
            error = (predicted - actual) ** 2
            total_error += error
            count += 1
            
        if count == 0: return 0
        rmse = (total_error / count) ** 0.5
        
        # Fitness = 100 - RMSE (Simplified)
        fitness = max(0, 100 - rmse)
        return fitness
