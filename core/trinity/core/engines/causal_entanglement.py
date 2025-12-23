"""
Phase C: Causal Entanglement Engine
===================================
Analyzes higher-order interaction structures via Information Entropy & Singularity Detection.

Physical Model: Causal Entanglement
- Bazi branches are information nodes.
- Interactions (Clash, Join, Penalty, etc.) are entanglement links.
- High-order overlaps create life singularities.

Mathematical Model: Causal Entropy
- S = -sum(p_i * ln(p_i)) where p_i is the relative energy of interaction i.
- Singularity Index (Σ) = Count of distinct high-priority interactions at a single node.
"""

import math
from typing import List, Dict, Any, Set, Tuple

class CausalEntanglementEngine:
    """
    The 'Singularity Detector' that identifies high-complexity causal structures.
    """

    def __init__(self):
        pass

    def analyze_emergence(self, interactions: List[Dict[str, Any]], branches: List[str]) -> Dict[str, Any]:
        """
        Main entry point for Phase C analysis.
        
        Args:
            interactions: List of active interactions from LogicArbitrator.
            branches: List of 4 (or 6) branches in the chart.
            
        Returns:
            Dict containing Causal Entropy, Singularity Index, and Causal Graph.
        """
        if not interactions:
            return {
                "causal_entropy": 0.0,
                "singularity_index": 0.0,
                "singularities": [],
                "network_graph": {"nodes": [], "links": []}
            }

        # 1. Calculate Causal Entropy (S)
        entropy = self._calculate_entropy(interactions)
        
        # 2. Detect Singularities (Σ)
        singularities, singularity_index = self._detect_singularities(interactions, branches)
        
        # 3. Generate Network Graph
        graph = self._generate_causal_graph(interactions, branches)
        
        # 4. Identify Negentropy Suggestion
        negentropy = self._identify_negentropy_suggestion(interactions, singularities, singularity_index, entropy)
        
        return {
            "causal_entropy": round(entropy, 4),
            "singularity_index": round(singularity_index, 2),
            "singularities": singularities,
            "network_graph": graph,
            "negentropy_protocol": negentropy
        }

    def _calculate_entropy(self, interactions: List[Dict[str, Any]]) -> float:
        """
        S = -sum(p_i * log(p_i))
        Where p_i is the importance (q-value) of an interaction relative to the total.
        """
        total_q = sum(abs(i.get('q', 0.5)) for i in interactions)
        if total_q == 0:
            return 0.0
            
        entropy = 0.0
        for i in interactions:
            p_i = abs(i.get('q', 0.5)) / total_q
            if p_i > 0:
                entropy -= p_i * math.log(p_i)
                
        return entropy

    def _detect_singularities(self, interactions: List[Dict[str, Any]], branches: List[str]) -> Tuple[List[Dict[str, Any]], float]:
        """
        Identifies branches that are 'Overloaded' with conflicting or reinforcing signals.
        """
        node_overlaps = {b: [] for b in set(branches)}
        
        # Priority mapping for singularity weight
        # Lower priority value in definitions usually means higher importance
        for i in interactions:
            involved_branches = i.get('branches', set())
            for b in involved_branches:
                if b in node_overlaps:
                    node_overlaps[b].append(i)
        
        singularities = []
        max_overlap_count = 0
        
        for branch, active_inters in node_overlaps.items():
            overlap_count = len(active_inters)
            if overlap_count >= 2:
                # Calculate singularity weight based on diversity and intensity
                unique_types = len(set(i.get('type') for i in active_inters))
                avg_q = sum(abs(i.get('q', 0.5)) for i in active_inters) / overlap_count
                
                # Formula: Intensity * Complexity
                s_weight = avg_q * (1.0 + 0.5 * (unique_types - 1))
                
                singularities.append({
                    "branch": branch,
                    "overlap_count": overlap_count,
                    "unique_types": unique_types,
                    "weight": round(s_weight, 2),
                    "interactions": [i.get('name') for i in active_inters]
                })
                
                if s_weight > max_overlap_count:
                    max_overlap_count = s_weight
                    
        return singularities, max_overlap_count

    def _identify_negentropy_suggestion(self, interactions: List[Dict[str, Any]], 
                                       singularities: List[Dict[str, Any]], 
                                       s_index: float, entropy: float) -> Dict[str, str]:
        """
        Calculates the best 'bridge' or 'drain' element to reduce system entropy.
        """
        if entropy < 0.6:
            return {"status": "STABLE", "suggestion": "系统处于低熵稳态，无需干预。", "primary_remedy": "N/A"}
        
        # Element mapping (Simplified for logic)
        BRANCH_ELEMENTS = {
            '寅': 'Wood', '卯': 'Wood', '亥': 'Water', '子': 'Water',
            '巳': 'Fire', '午': 'Fire', '申': 'Metal', '酉': 'Metal',
            '辰': 'Earth', '戌': 'Earth', '丑': 'Earth', '未': 'Earth'
        }
        
        conflicts = [i for i in interactions if i.get('phi', 0) > 2.0] # High phase shift = conflict
        
        suggestion = "检测到高熵纠缠，建议执行架构对冲。"
        remedy = "未知 (Unknown)"
        
        # 1. Check for specific element wars
        clashing_elements = set()
        for i in conflicts:
            involved = i.get('branches', set())
            elems = {BRANCH_ELEMENTS.get(b) for b in involved if b in BRANCH_ELEMENTS}
            if len(elems) == 2:
                clashing_elements.update(elems)
                
        # Logic: Mediation
        if "Metal" in clashing_elements and "Wood" in clashing_elements:
            suggestion = "检测到【金木交战】死锁，建议通过‘水粒子’进行降噪调停。"
            remedy = "💧 壬/癸 (Water)"
        elif "Water" in clashing_elements and "Fire" in clashing_elements:
            suggestion = "检测到【水火既济】失稳，建议通过‘木粒子’进行通关对冲。"
            remedy = "🌿 甲/乙 (Wood)"
        elif "Fire" in clashing_elements and "Metal" in clashing_elements:
            suggestion = "检测到【火金剧变】，建议通过‘土粒子’进行能量缓冲。"
            remedy = "🏔️ 戊/己 (Earth)"
        elif "Wood" in clashing_elements and "Earth" in clashing_elements:
            suggestion = "检测到【木土受压】，建议通过‘火粒子’引导能量消解。"
            remedy = "🔥 丙/丁 (Fire)"
        elif "Earth" in clashing_elements and "Water" in clashing_elements:
            suggestion = "检测到【土水障壁】，建议通过‘金粒子’进行通道疏通。"
            remedy = "⚔️ 庚/辛 (Metal)"
            
        # 2. Check for Overload (Entropy high but maybe no specific clash)
        if remedy == "未知 (Unknown)" and (s_index > 1.0 or entropy > 1.0):
             # Find dominant element from the most complex/intense nodes
             active_nodes = [BRANCH_ELEMENTS.get(s.get('branch')) for s in singularities if s.get('branch') in BRANCH_ELEMENTS]
             if active_nodes:
                 dominant = max(set(active_nodes), key=active_nodes.count)
                 if dominant == "Fire":
                     suggestion = "检测到【火系能量】极端溢出，建议执行‘泄洪’协议 (通过湿土粒子降温)。"
                     remedy = "🟤 辰/丑 (Wet Earth)"
                 elif dominant == "Wood":
                     suggestion = "检测到【木系能量】溢出，建议通过‘火粒子’向外导能。"
                     remedy = "🔥 丙/丁 (Fire)"
                 elif dominant == "Water":
                     suggestion = "检测到【水系能量】凝滞，建议通过‘木粒子’进行疏导。"
                     remedy = "🌿 甲/乙 (Wood)"
                 elif dominant == "Metal":
                     suggestion = "检测到【金系能量】过刚，建议通过‘水粒子’进行挫锐降噪。"
                     remedy = "💧 壬/癸 (Water)"
                 elif dominant == "Earth":
                     suggestion = "检测到【土系能量】厚重，建议通过‘金粒子’进行化泄。"
                     remedy = "⚔️ 庚/辛 (Metal)"

        return {
            "status": "CRITICAL" if entropy > 1.2 else "WARNING",
            "suggestion": suggestion,
            "primary_remedy": remedy
        }

    def _generate_causal_graph(self, interactions: List[Dict[str, Any]], branches: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generates a node-link structure for visualization.
        """
        nodes = []
        node_set = set(branches)
        
        # Pillar mapping
        pillar_labels = ["Year", "Month", "Day", "Hour", "Luck", "Annual"]
        
        for idx, b in enumerate(branches):
            nodes.append({
                "id": f"{b}_{idx}",
                "name": b,
                "pillar": pillar_labels[idx] if idx < len(pillar_labels) else "External"
            })
            
        links = []
        for i in interactions:
            involved = list(i.get('branches', set()))
            if len(involved) == 2:
                # Binary link
                # Find all occurrences of these branches in pillars
                source_indices = [idx for idx, val in enumerate(branches) if val == involved[0]]
                target_indices = [idx for idx, val in enumerate(branches) if val == involved[1]]
                
                for si in source_indices:
                    for ti in target_indices:
                        if si != ti:
                            links.append({
                                "source": f"{involved[0]}_{si}",
                                "target": f"{involved[1]}_{ti}",
                                "type": i.get('type'),
                                "name": i.get('name'),
                                "q": i.get('q', 0.5)
                            })
            elif len(involved) > 2:
                # Multi-body link (Trio)
                # Connect sequentially or to center? Sequentially for simplicity
                for k in range(len(involved)):
                    b_curr = involved[k]
                    b_next = involved[(k + 1) % len(involved)]
                    
                    source_indices = [idx for idx, val in enumerate(branches) if val == b_curr]
                    target_indices = [idx for idx, val in enumerate(branches) if val == b_next]
                    
                    for si in source_indices:
                        for ti in target_indices:
                            if si != ti:
                                links.append({
                                    "source": f"{b_curr}_{si}",
                                    "target": f"{b_next}_{ti}",
                                    "type": i.get('type'),
                                    "name": i.get('name'),
                                    "q": i.get('q', 0.5)
                                })
                                
        return {"nodes": nodes, "links": links}
