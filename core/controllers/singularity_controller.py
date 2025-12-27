
"""
[SSEP] Singularity Hunter Controller
Orchestrates the interaction between UI and Physics Engine.
"""
import pandas as pd
from core.trinity.core.engines.singularity_engine import SingularityEngine

class SingularityController:
    """
    Controller Layer for Singularity Hunter.
    Handles data formatting, batch processing calls, and view-model mapping.
    """
    
    def __init__(self):
        self.engine = SingularityEngine()
        self.db = self._load_real_profiles()

    def _load_real_profiles(self):
        """
        Loads real Bazi profiles from the system and converts them to SSEP format.
        """
        from core.profile_manager import ProfileManager
        from core.bazi_profile import BaziProfile
        from datetime import datetime
        
        pm = ProfileManager()
        raw_profiles = pm.get_all()
        
        if not raw_profiles:
            # Fallback to Mock if no real data
            return self._init_mock_db()
            
        converted_db = []
        for p in raw_profiles:
            try:
                # 1. Parse Date
                dt = datetime(p['year'], p['month'], p['day'], p['hour'], p.get('minute', 0))
                
                # 2. Parse Gender
                g_val = 1 if p.get('gender') == "男" else 0
                
                # 3. Generate Chart
                bp = BaziProfile(dt, g_val)
                pillars = bp.pillars
                
                # 4. Format to [(S, B), ...]
                chart_tuples = []
                for key in ['year', 'month', 'day', 'hour']:
                    pil = pillars.get(key, '')
                    if len(pil) >= 2:
                        chart_tuples.append((pil[0], pil[1]))
                    else:
                        chart_tuples.append(('?', '?'))
                
                converted_db.append({
                    "id": p['id'],
                    "name": p['name'],
                    "chart": chart_tuples
                })
            except Exception as e:
                print(f"Error loading profile {p.get('name')}: {e}")
                
        return converted_db

    def _init_mock_db(self):
        # ... (Keep existing mock logic as fallback or reference)
        # Generate some mock samples for the Hunter Demo
        db = []
        # 1. True Singularity
        db.append({
            "id": "S_0001_EMP",
            "name": "Emperor A (Mock)",
            "chart": [('戊', '辰'), ('戊', '辰'), ('戊', '辰'), ('戊', '辰')]
        })
        # 2. Accretion Disk (Fake)
        db.append({
            "id": "S_0002_TRB",
            "name": "General B (Mock)",
            "chart": [('戊', '辰'), ('戊', '辰'), ('戊', '辰'), ('甲', '寅')]
        })
        # 3. Superconducting Transmutation
        db.append({
            "id": "S_0003_TMS",
            "name": "Sage C (Mock)",
            "chart": [('甲', '辰'), ('己', '丑'), ('戊', '辰'), ('丙', '辰')] 
        })
        # 4. Hidden Conductor (Missing Trigger)
        # Ji-Earth heavy chart, missing Jia. Waiting for Jia Luck.
        db.append({
            "id": "H_0004_LAT",
            "name": "Hidden Dragon D (Mock)",
            "chart": [('己', '丑'), ('己', '丑'), ('戊', '辰'), ('丙', '辰')]
        })
        return db

    def execute_global_scan(self):
        """
        Triggers the Holographic Scan on the database.
        Returns a DataFrame for the UI grid.
        """
    def execute_global_scan(self):
        """
        Triggers the Holographic Scan on the database.
        Returns a DataFrame for the UI grid.
        """
        candidates = self.engine.holographic_scan(self.db)
        
        # Status Translation Map
        STATUS_MAP = {
            "SUPERCONDUCTING (Zero Resistance)": "🔵 超导态 (零电阻)",
            "SINGULARITY (True Black Hole)": "⚫ 奇点 (真黑洞)",
            "ACCRETION_DISK (Fake/Turbulent)": "🔴 吸积盘 (湍流)",
            "NORMAL_SPACE": "⚪ 常态时空"
        }

        # Format for UI
        data = []
        for c in candidates:
            # Translated Status
            raw_status = c['status']
            cn_status = STATUS_MAP.get(raw_status, raw_status)
            
            # Mechanism Translation
            mech = c.get('mechanism', 'Unknown')
            mech = mech.replace("Quantum Phase:", "量子相变:").replace("Mass Dominance:", "质量霸权:").replace("Turbulence:", "湍流扰动:")
            
            data.append({
                "ID": c['id'],
                "姓名 (Name)": c.get('name', c['id']),
                "物理状态 (Status)": cn_status,
                "成格机制 (Mechanism)": mech,
                "质量占比 (Mass)": f"{float(c['mass_ratio']):.2f}",
                "纯度 (Purity)": f"{c['purity_proxy']:.2f}",
                "特征标签 (Tags)": ", ".join(c['tags'])
            })
        return pd.DataFrame(data)

    def run_dynamic_injection(self, chart_id):
        """
        Runs the dynamic injection simulation for a specific chart.
        """
        # Find chart
        sample = next((x for x in self.db if x['id'] == chart_id), None)
        if not sample: return None
        
        # Define Future 10 Years (Mock years for now, can be real future)
        years = [f"202{i}" for i in range(6, 16)]
        
        timeline = self.engine.penetrate_horizon(sample['chart'], years)
        return pd.DataFrame(timeline)

    def execute_potential_scan(self):
        """
        [Mission 002] Scans for Hidden Conductors.
        """
        from core.profile_manager import ProfileManager
        from core.bazi_profile import BaziProfile
        from datetime import datetime
        
        # Load Profiles for Time Mapping
        pm = ProfileManager()
        all_profiles = pm.get_all()
        
        gems = self.engine.scan_potential_conductors(self.db)
        data = []
        for g in gems:
            triggers_cn = g['potential_triggers']
            
            # [Time Mapping] Resolve Luck Pillar to Calendar Years
            mapped_triggers = []
            
            # Find Profile
            p_data = next((p for p in all_profiles if p['id'] == g['id']), None)
            
            luck_map = {}
            if p_data:
                try:
                    dt = datetime(p_data['year'], p_data['month'], p_data['day'], p_data['hour'], p_data.get('minute', 0))
                    g_val = 1 if p_data.get('gender') == "男" else 0
                    bp = BaziProfile(dt, g_val)
                    cycles = bp.get_luck_cycles() # [{"gan_zhi": "甲辰", "start_year": 2024, "end_year": 2033}, ...]
                    for cyc in cycles:
                        luck_map[cyc['gan_zhi']] = f"{cyc['start_year']}-{cyc['end_year']}"
                except:
                    pass
            
            for t in triggers_cn:
                # t format: "大运[甲辰] 激活..."
                # Extract "甲辰"
                import re
                match = re.search(r"大运\[(..)\].*激活", t)
                if match:
                    luck_ganzhi = match.group(1)
                    if luck_ganzhi in luck_map:
                        time_range = luck_map[luck_ganzhi]
                        t = t.replace(f"大运[{luck_ganzhi}]", f"大运[{luck_ganzhi} @ {time_range}]")
                mapped_triggers.append(t)
            
            data.append({
                "ID": g['id'],
                "姓名 (Name)": g['name'],
                "基础纯度 (Base Purity)": g['base_purity'],
                "激活密钥 (Triggers)": " | ".join(mapped_triggers),
                "潜伏状态 (Status)": "🟡 隐形超导 (Awakening)"
            })
        return pd.DataFrame(data)
