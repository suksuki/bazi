
# Liang Xiangrun "Great LiuNian" Rules - Digitization Spec
# Module: core.rules.liang_liunian

import logging

class LiangLiuNianEngine:
    """
    Implements specific heuristic rules from Liang Xiangrun's "Great LiuNian Cases".
    Focuses on:
    1. San Xing (Three Punishments) - Analyzing the 'Punishment of Momentum'.
    2. Liu Nian Access Path - Priority of interaction.
    """
    
    def __init__(self, particles, log_list):
        self.particles = particles
        self.log = log_list
        self.triggered_rules = []

    def apply_all(self):
        """Run all Liang rules."""
        self._check_san_xing()
        self._check_earth_punishment()
        # self._check_fan_yin() # Future
        return self.triggered_rules

    def _check_san_xing(self):
        """
        Rule: Yin-Si-Shen San Xing (寅巳申三刑)
        Source: 梁湘润《大流年》
        Logic:
           - Yin (Wood/Fire), Si (Fire/Metal), Shen (Metal/Water).
           - Interaction: Fire Smelts Metal (Si-Shen), Metal Chops Wood (Shen-Yin).
           - Result: 'Punishment of Power'. High Energy, High Friction.
           - Outcome: Dependent on 'Useful God'. If Fire/Metal is favorable, can be explosive success. If not, disaster.
        Quantum Effect:
           - Entropy += 0.4 (Chaos)
           - Fire Energy += Boost (Hidden Release)
           - Metal Energy += Boost (Active Clash)
        """
        chars = [p.char for p in self.particles if p.type in ['branch', 'dayun_branch', 'liunian_branch']]
        
        has_yin = "寅" in chars
        has_si = "巳" in chars
        has_shen = "申" in chars
        
        if has_yin and has_si and has_shen:
            self.log.append("⚡ DETECTED: Yin-Si-Shen Three Punishments (寅巳申三刑)")
            self.log.append("   -> Source: Liang Xiangrun 'Punishment of Momentum'")
            self.log.append("   -> Effect: High Kinetic Friction. Fire & Metal unstable increase.")
            
            self.triggered_rules.append("SanXing_YinSiShen")
            
            # Apply Quantum Effects
            # 1. Entropy Spike (Chaos)
            # In FluxEngine, usually handled by checking flags, or we modify particles directly here?
            # Direct modification is cleaner for this plugin style.
            
            for p in self.particles:
                # Dampen general stability (Entropy penalty)
                p.wave.amplitude *= 0.8 
                
                # Boost specific elements (The "Release")
                # Yin (Fire/Wood), Si (Fire/Metal), Shen (Water/Metal)
                # Interaction releases Fire (from Yin/Si) and Metal (Si/Shen)
                if "Fire" in p.wave.dist:
                    p.wave.dist["Fire"] *= 1.5 # Flare up
                if "Metal" in p.wave.dist:
                    p.wave.dist["Metal"] *= 1.3 # Sharpen
                    
                p.status.append("Punished")

    def _check_earth_punishment(self):
        """
        Rule: Chou-Wei-Xu San Xing (丑未戌三刑)
        Source: Liang Xiangrun 'Punishment of Ungratefulness' (无恩之刑)
        Logic:
           - Chou (Earth/Water/Metal), Wei (Earth/Fire/Wood), Xu (Earth/Fire/Metal).
           - Interaction: Earth Clashing with Earth -> Massive Earth debris.
           - Result: 'Earth Overload'. 
           - Outcome: Buries Water (Wealth/Wisdom) and obscures Fire. Legal issues, internal heat/sickness.
        Quantum Effect:
           - Earth Energy *= 2.0 (Massive Boost)
           - Water Energy *= 0.1 (Buried/Trapped)
           - Status: "Earth_Trap"
        """
        chars = [p.char for p in self.particles if p.type in ['branch', 'dayun_branch', 'liunian_branch']]
        
        has_chou = "丑" in chars
        has_wei = "未" in chars
        has_xu = "戌" in chars
        
        if has_chou and has_wei and has_xu:
            self.log.append("⚡ DETECTED: Chou-Wei-Xu Earth Punishment (丑未戌三刑)")
            self.log.append("   -> Source: Liang Xiangrun 'Punishment of Ungratefulness'")
            self.log.append("   -> Effect: Earth Overload. Water Buried. Hidden trouble.")
            
            self.triggered_rules.append("SanXing_ChouWeiXu")
            
            for p in self.particles:
                # 1. Earth Boost
                if "Earth" in p.wave.dist:
                    p.wave.dist["Earth"] *= 2.0 
                    
                # 2. Water Burial (The danger zone)
                if "Water" in p.wave.dist:
                    if p.wave.dist["Water"] > 0:
                        p.wave.dist["Water"] *= 0.1
                        p.status.append("Buried_by_Earth")
                        
                p.status.append("Ungrateful_Punishment")
        Source: 梁湘润《大流年》
        Logic:
           - Yin (Wood/Fire), Si (Fire/Metal), Shen (Metal/Water).
           - Interaction: Fire Smelts Metal (Si-Shen), Metal Chops Wood (Shen-Yin).
           - Result: 'Punishment of Power'. High Energy, High Friction.
           - Outcome: Dependent on 'Useful God'. If Fire/Metal is favorable, can be explosive success. If not, disaster.
        Quantum Effect:
           - Entropy += 0.4 (Chaos)
           - Fire Energy += Boost (Hidden Release)
           - Metal Energy += Boost (Active Clash)
        """
        chars = [p.char for p in self.particles if p.type in ['branch', 'dayun_branch', 'liunian_branch']]
        
        has_yin = "寅" in chars
        has_si = "巳" in chars
        has_shen = "申" in chars
        
        if has_yin and has_si and has_shen:
            self.log.append("⚡ DETECTED: Yin-Si-Shen Three Punishments (寅巳申三刑)")
            self.log.append("   -> Source: Liang Xiangrun 'Punishment of Momentum'")
            self.log.append("   -> Effect: High Kinetic Friction. Fire & Metal unstable increase.")
            
            self.triggered_rules.append("SanXing_YinSiShen")
            
            # Apply Quantum Effects
            # 1. Entropy Spike (Chaos)
            # In FluxEngine, usually handled by checking flags, or we modify particles directly here?
            # Direct modification is cleaner for this plugin style.
            
            for p in self.particles:
                # Dampen general stability (Entropy penalty)
                p.wave.amplitude *= 0.8 
                
                # Boost specific elements (The "Release")
                # Yin (Fire/Wood), Si (Fire/Metal), Shen (Water/Metal)
                # Interaction releases Fire (from Yin/Si) and Metal (Si/Shen)
                if "Fire" in p.wave.dist:
                    p.wave.dist["Fire"] *= 1.5 # Flare up
                if "Metal" in p.wave.dist:
                    p.wave.dist["Metal"] *= 1.3 # Sharpen
                    
                p.status.append("Punished")

        # Future: Chou-Wei-Xu (Earth Punishment)
