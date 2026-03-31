
import logging
from typing import List, Generator, Tuple, Dict, Any
import random

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
JIA_ZI = [STEMS[i % 10] + BRANCHES[i % 12] for i in range(60)]

class SyntheticBaziEngine:
    """
    🚀 SyntheticBaziEngine (Antigravity Synthetic Evolution - ASE)
    
    Generates the full spectrum of 518,400 Bazi combinations.
    Supports random assignment of Luck/Annual pillars and GEO/ERA factors.
    """
    
    STEMS = STEMS
    BRANCHES = BRANCHES
    JIA_ZI = JIA_ZI
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @classmethod
    def get_month_pillar(cls, year_stem: str, month_index: int) -> str:
        """
        Calculate month pillar based on year stem.
        month_index: 1 (Tiger/寅) to 12 (Ox/丑)
        """
        stem_map = {"甲": 2, "己": 2, "乙": 4, "庚": 4, "丙": 6, "辛": 6, "丁": 8, "壬": 8, "戊": 0, "癸": 0}
        start_stem_idx = stem_map.get(year_stem, 0)
        
        month_stem_idx = (start_stem_idx + (month_index - 1)) % 10
        month_branch_idx = (2 + (month_index - 1)) % 12
        
        return cls.STEMS[month_stem_idx] + cls.BRANCHES[month_branch_idx]

    @classmethod
    def get_hour_pillar(cls, day_stem: str, hour_index: int) -> str:
        """
        Calculate hour pillar based on day stem.
        hour_index: 0 (Rat/子) to 11 (Pig/亥)
        """
        stem_map = {"甲": 0, "己": 0, "乙": 2, "庚": 2, "丙": 4, "辛": 4, "丁": 6, "壬": 6, "戊": 8, "癸": 8}
        start_stem_idx = stem_map.get(day_stem, 0)
        
        hour_stem_idx = (start_stem_idx + hour_index) % 10
        hour_branch_idx = hour_index % 12
        
        return cls.STEMS[hour_stem_idx] + cls.BRANCHES[hour_branch_idx]

    def generate_all_bazi(self) -> Generator[List[str], None, None]:
        """
        Generates all 518,400 Bazi combinations.
        Order: Year -> Month -> Day -> Hour
        """
        for year_pillar in self.JIA_ZI:
            y_stem = year_pillar[0]
            for m_idx in range(1, 13):
                month_pillar = self.get_month_pillar(y_stem, m_idx)
                for day_pillar in self.JIA_ZI:
                    d_stem = day_pillar[0]
                    for h_idx in range(12):
                        hour_pillar = self.get_hour_pillar(d_stem, h_idx)
                        yield [year_pillar, month_pillar, day_pillar, hour_pillar]

    def generate_sample_variants(self, count: int = 1000) -> List[Dict[str, Any]]:
        """
        Generates a sample of Bazi charts with random environmental injections.
        """
        generator = self.generate_all_bazi()
        samples = []
        for _ in range(count):
            try:
                bazi = next(generator)
                luck = random.choice(self.JIA_ZI)
                annual = random.choice(self.JIA_ZI)
                geo_factor = random.uniform(0.7, 1.3)
                geo_element = random.choice(["Wood", "Fire", "Earth", "Metal", "Water", "Neutral"])
                
                samples.append({
                    "chart": bazi,
                    "context": {
                        "luck_pillar": luck,
                        "annual_pillar": annual,
                        "geo_factor": geo_factor,
                        "data": {
                            "geo_factor": geo_factor,
                            "geo_element": geo_element
                        }
                    }
                })
            except StopIteration:
                break
        return samples

class ExpectedValueCollector:
    """
    📊 ExpectedValueCollector
    
    Aggregates physical metrics from ASE batch runs to define the Statistical Baseline.
    """
    
    def __init__(self):
        self.metrics = {
            "SAI": [],
            "IC": [],
            "Entropy": [],
            "Reynolds": [],
            "Binding_Energy": [],
            "Vibration_Impedance": []
        }
        self.singularities = []

    def collect(self, report: Dict[str, Any]):
        phy = report.get("physics", {})
        stress = phy.get("stress", {})
        wealth = phy.get("wealth", {})
        rel = phy.get("relationship", {})
        vib = phy.get("vibration", {})
        
        self.metrics["SAI"].append(stress.get("SAI", 0))
        self.metrics["IC"].append(stress.get("IC", 0))
        self.metrics["Entropy"].append(phy.get("entropy", 0))
        self.metrics["Reynolds"].append(wealth.get("Reynolds", 0))
        self.metrics["Binding_Energy"].append(rel.get("Binding_Energy", 0))
        self.metrics["Vibration_Impedance"].append(vib.get("impedance_magnitude", 0))
        
        if stress.get("SAI", 0) > 2.0 or wealth.get("Reynolds", 0) > 4000:
            self.singularities.append({
                "chart": report.get("meta", {}).get("chart"),
                "SAI": stress.get("SAI"),
                "Reynolds": wealth.get("Reynolds")
            })

    def get_summary(self) -> Dict[str, Any]:
        summary = {}
        for key, vals in self.metrics.items():
            if not vals: continue
            summary[key] = {
                "mean": sum(vals) / len(vals),
                "max": max(vals),
                "min": min(vals),
                "stdev": (sum((x - (sum(vals)/len(vals)))**2 for x in vals) / len(vals))**0.5
            }
        summary["singularity_count"] = len(self.singularities)
        return summary
