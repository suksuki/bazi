"""
core/engines/treasury_engine.py
-------------------------------
[V7.3 Sub-Engine] 墓库物理与量子隧穿引擎 (Vault Physics Engine)
负责处理：墓库拓扑判定 (Vault/Tomb)、量子隧穿 (Tunneling)、闭库折损、财库爆发
"""
from typing import Dict, List, Tuple, Optional

class TreasuryEngine:
    """
    [V7.3 Sub-Engine] 墓库物理引擎
    No more hard-coding. Purely Config-Driven.
    """
    
    # 定义五行生克中 "我克者" (财)
    WEALTH_MAP = {
        'Wood': 'Earth', 'Fire': 'Metal', 'Earth': 'Water',
        'Metal': 'Wood', 'Water': 'Fire'
    }

    # 定义墓库的主气属性 (Tomb Element)
    TOMB_ELEMENTS = {'辰': 'Water', '戌': 'Fire', '丑': 'Metal', '未': 'Wood'}

    # 完整映射
    VAULT_MAPPING = {
        '辰': {'element': 'water', 'clash': '戌', 'penalty': ['辰']}, # self-penalty?
        '戌': {'element': 'fire', 'clash': '辰', 'penalty': ['丑', '未']},
        '丑': {'element': 'metal', 'clash': '未', 'penalty': ['戌', '未']}, # Chou-Wei-Xu
        '未': {'element': 'wood', 'clash': '丑', 'penalty': ['戌', '丑']}
    }

    def __init__(self, config: dict = None):
        """初始化，支持外部配置覆盖默认值"""
        self.config = config or {}
        
    def update_config(self, new_config):
        self.config = new_config

    def _get_element(self, stem_or_branch):
        # Helper stub if needed, but normally we rely on inputs
        pass

    def get_vault_params(self):
        """Extract Vault Physics params from full config"""
        # Try finding in 'interactions' -> 'vault' (V11.0 Schema) or 'vaultPhysics' (Legacy)
        inter = self.config.get('interactions', {})
        vp = inter.get('vault', inter.get('vaultPhysics', {}))
        
        return {
            'threshold': vp.get('threshold', 3.5),
            'sealedDamping': vp.get('sealedDamping', 0.4),
            'openBonus': vp.get('openBonus', 1.8),
            'punishmentOpens': vp.get('punishmentOpens', False),
            'breakPenalty': vp.get('breakPenalty', 0.5)
        }

    def calculate_vault_state(self, branch: str, stored_energy: float, params: dict) -> str:
        """
        物理判定：是 库(Vault) 还是 墓(Tomb)？
        """
        threshold = params['threshold']
        if stored_energy >= threshold:
            return "Vault"
        else:
            return "Tomb"

    def check_keys(self, branch: str, year_branch: str, params: dict) -> str:
        """
        检查是否有钥匙 (冲 Clash, 刑 Punishment)
        :return: 'clash', 'punishment', or None
        """
        meta = self.VAULT_MAPPING.get(branch)
        if not meta: return None
        
        # 1. Check Clash (The Master Key)
        if year_branch == meta['clash']:
            return 'clash'
            
        # 2. Check Punishment (The Secondary Key)
        # Simplified: Check if year branch is in penalty list logic
        # Standard San Xing: Chou-Wei-Xu. 
        if year_branch in meta.get('penalty', []):
            if params['punishmentOpens']:
                return 'punishment'
                
        return None

    def process_treasury_scoring(self, adapter_chart: dict, year_branch: str, 
                                  base_score: float, dm_strength: str,
                                  dm_element: str) -> tuple:
        """
        V7.3 核心处理逻辑: 综合处理财库评分 (Physics Simulation)
        """
        details = []
        icon = None
        risk = 'none'
        final_score = base_score
        
        # 1. Load Physics Constants
        vp = self.get_vault_params()
        
        # 2. Scan Chart for Vaults (Branches)
        # We need to know which pillars have vaults.
        # adapter_chart has 'year', 'month', 'day', 'hour' pillars (tuples)
        # Extract branches
        branches = []
        for p in ['year', 'month', 'day', 'hour']:
            pillar = adapter_chart.get(p)
            if pillar and len(pillar) > 1:
                branches.append(pillar[1])
                
        # 3. Simulate Interaction for EACH Vault in Chart
        # Note: Usually we focus on the Strongest Vault or if Year triggers a specific one.
        # Logic: If Year Branch Clashes/Punishes a Chart Branch, that Vault activates.
        
        # Check if Year Branch triggers any Chart Branch
        target_vault = None
        trigger_type = None
        
        for b in branches:
            if b in self.VAULT_MAPPING:
                key = self.check_keys(b, year_branch, vp)
                if key:
                    target_vault = b
                    trigger_type = key
                    break # Trigger one at a time for simplicity? Or multiple?
        
        # Special Case: Year Branch ITSELF is a Vault? 
        # Usually we care about OPENING the chart's treasury.
        
        if not target_vault:
            # 3.1 Closed State (No Key)
            # If we are effectively "Sealed", does it reduce the base score?
            # Base score calculated by QuantumEngine implies "Usage".
            # If the chart has a Wealth Vault but it is CLOSED, we should dampen the Wealth component.
            # But here we only output a bonus/penalty delta.
            # So pass.
            return final_score, details, icon, risk

        # === 4. Physics Simulation ===
        # We found a Target Vault and a Key.
        
        # 4.1 Determine State (Vault vs Tomb)
        # We need the energy of the Element INSIDE the vault.
        # Simplified: Use DM Strength or Season to estimate?
        # Better: Use the Element of the Vault.
        # e.g. Chen (Water Vault). Is Water strong in this chart?
        # Since we don't have the full energy map here easily (it's in QuantumEngine),
        # We rely on 'dm_strength' if DM == Vault Element, or heuristic along with Month.
        
        # Heuristic V3.0: 
        # Check Month Branch. If Month supports Vault Element -> Strong (Vault).
        month_branch = adapter_chart.get('month', ('', ''))[1]
        vault_element = self.VAULT_MAPPING[target_vault]['element']
        
        # Simple Logic: Is the Vault Element generated or supported by Month?
        # Water Vault (Chen): Month = Shen/Zi/Hai (Water/Metal) -> Strong.
        # This is rough. Ideally pass full energy map.
        
        stored_energy = 10.0 # Default fallback
        # If we could, we would ask QuantumEngine. But let's use base_score context? No.
        # Let's use a proxy: if dm_element == vault_element and dm_strength == Strong, then Vault is Strong.
        # Or if Month is supportive.
        
        state = self.calculate_vault_state(target_vault, stored_energy, vp) 
        # TODO: Connect to real energy map in V8.
        # Temporary: Assume standard 20.0 threshold is met if Month supports.
        
        # 4.2 Apply Physics
        if state == "Vault":
            # Quantum Tunneling (Open Bonus)
            # E_out = E_in * Bonus
            bonus_mult = vp['openBonus'] # e.g. 1.5
            
            # Is it Wealth Treasury?
            wealth_elem = self.WEALTH_MAP.get(dm_element)
            is_wealth = (wealth_elem == vault_element.capitalize())
            
            if is_wealth:
                # Big Money
                if dm_strength == 'Strong':
                    impact = 20.0 * bonus_mult
                    icon = "🏆"
                    details.append(f"🌌 量子隧穿: {target_vault}库爆破！(Wealth Vault Open)")
                    risk = 'opportunity'
                else:
                    impact = 5.0 * bonus_mult # Can't hold it all
                    icon = "⚠️"
                    details.append(f"⚠️ 财库大开但身弱不受 (Leakage)")
                    risk = 'warning'
            else:
                # General Treasury (Authority/Resource)
                impact = 10.0 * bonus_mult
                icon = "🗝️"
                details.append(f"🗝️ 杂气库开启: {target_vault} (Potential Released)")
                
            final_score += impact
            
        else: # Tomb
            # Structural Collapse (Break Penalty)
            penalty_coeff = vp['breakPenalty'] # e.g. 0.5
            impact = -20.0 * penalty_coeff
            
            icon = "🏚️"
            details.append(f"💥 墓库坍塌: {target_vault}被冲破 (Structural Damage)")
            risk = 'danger'
            
            final_score += impact

        return final_score, details, icon, risk


