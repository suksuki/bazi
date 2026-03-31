
from core.kernel import Kernel
from learning.db import LearningDB
import json
import logging

logger = logging.getLogger(__name__)

class RuleInjector:
    """
    Layer 2: Dynamic Rule Injector
    Fetches rules from BrainDB and applies them to the current Flux State.
    """
    def __init__(self, flux_result):
        """
        flux_result: The output from FluxEngine (particle_states, log, etc.)
        """
        self.flux = flux_result
        self.db = LearningDB()
        self.active_rules = [] # List of triggered rule objects
        
    def run(self):
        """
        Main execution method.
        1. Fetch all enabled rules from DB.
        2. Evaluate condition against Flux State.
        3. If true, append to active_rules.
        """
        # Fetch all rules (Naive for now, in production we'd cache or filter)
        # Assuming db.get_all_rules() returns dicts with actual DB format
        all_rules_data = self.db.get_all_rules() 
        
        # Convert flux_result to a flattened context for easier evaluation
        context = self._build_context()
        
        for rule in all_rules_data:
            try:
                # Extract fields from actual DB format
                rule_name = rule.get('rule_name', 'Unnamed Rule')
                trigger_conditions = rule.get('trigger_conditions', [])
                description = rule.get('description', 'No description')
                energy_adj = rule.get('energy_adjustment', {})
                source = rule.get('source_book', 'Unknown')
                
                # Check if any trigger condition matches
                matched = False
                matched_condition = ""
                
                for cond in trigger_conditions:
                    if self._evaluate_natural_language(cond, context):
                        matched = True
                        matched_condition = cond
                        break
                
                if matched:
                    # Triggered!
                    self.active_rules.append({
                        "name": rule_name,
                        "source": source,
                        "desc": description,
                        "logic_trace": f"条件匹配: {matched_condition}",
                        "effect": energy_adj if energy_adj else "规则已激活"
                    })
            except Exception as e:
                # logger.warning(f"Rule eval failed: {e}")
                continue
                
        return self.active_rules

    def _build_context(self):
        """
        Unpack Flux Result into safe variables for eval().
        """
        ctx = {}
        particles = self.flux.get('particle_states', [])
        
        # 1. Elements Energy Sum
        # Re-calculate from particle amps roughly if not provided, or better, 
        # FluxEngine should provide 'spectrum'. 
        # Let's check if 'spectrum' is in flux result.
        spectrum = self.flux.get('spectrum', {}) # {"Wood": 100.0, ...}
        
        ctx['Wood'] = spectrum.get('Wood', 0)
        ctx['Fire'] = spectrum.get('Fire', 0)
        ctx['Earth'] = spectrum.get('Earth', 0)
        ctx['Metal'] = spectrum.get('Metal', 0)
        ctx['Water'] = spectrum.get('Water', 0)
        
        # 2. Characters
        ctx['chars'] = [p['char'] for p in particles]
        
        # 3. Particle Objects (access via ID)
        # ctx['year_branch'] = ...
        for p in particles:
             ctx[p['id']] = p
             
        return ctx

    def _evaluate(self, condition_str, context):
        """
        Safe-ish evaluation of condition string.
        """
        if not condition_str: return False
        
        try:
            # Use eval with restricted scope
            # Available vars: Wood, Fire, chars, year_branch...
            return eval(condition_str, {"__builtins__": {}}, context)
        except Exception as e:
            # logger.warning(f"Eval error [{condition_str}]: {e}")
            return False

    def _evaluate_natural_language(self, condition_str, context):
        """
        Evaluate natural language trigger conditions (支持中英文).
        Examples:
        - "Branches contains Si and You" / "地支 包含 巳 和 酉"
        - "Fire > 50"
        - "Day Master is Wood" / "日主 是 木"
        - "Stems contains Jia" / "天干 包含 甲"
        """
        if not condition_str: return False
        
        condition_lower = condition_str.lower()
        
        # Enhanced character mapping
        branch_map = {
            'zi': '子', 'chou': '丑', 'yin': '寅', 'mao': '卯',
            'chen': '辰', 'si': '巳', 'wu': '午', 'wei': '未',
            'shen': '申', 'you': '酉', 'xu': '戌', 'hai': '亥'
        }
        
        stem_map = {
            'jia': '甲', 'yi': '乙', 'bing': '丙', 'ding': '丁',
            'wu': '戊', 'ji': '己', 'geng': '庚', 'xin': '辛',
            'ren': '壬', 'gui': '癸'
        }
        
        # All Chinese characters (stems and branches)
        all_chinese_chars = set(branch_map.values()) | set(stem_map.values())
        
        # Pattern 0: Chinese "地支 包含 X" or "天干 包含 X"
        if "地支" in condition_str and "包含" in condition_str:
            # Extract Chinese characters from condition
            chars_to_find = [c for c in condition_str if c in all_chinese_chars]
            
            if chars_to_find:
                if " 和 " in condition_str or "和" in condition_str:
                    # All must be present
                    return all(c in context['chars'] for c in chars_to_find)
                elif " 或 " in condition_str or "或" in condition_str:
                    # Any can be present
                    return any(c in context['chars'] for c in chars_to_find)
                else:
                    # Single char or implicit OR
                    return any(c in context['chars'] for c in chars_to_find)
        
        if "天干" in condition_str and "包含" in condition_str:
            chars_to_find = [c for c in condition_str if c in all_chinese_chars]
            
            if chars_to_find:
                if " 和 " in condition_str or "和" in condition_str:
                    return all(c in context['chars'] for c in chars_to_find)
                elif " 或 " in condition_str or "或" in condition_str:
                    return any(c in context['chars'] for c in chars_to_find)
                else:
                    return any(c in context['chars'] for c in chars_to_find)
        
        # Pattern 1: English "Branches contains X" or "Branch contains X"
        if "branch" in condition_lower and "contain" in condition_lower:
            chars_to_find = []
            for pinyin, cn_char in branch_map.items():
                if pinyin in condition_lower:
                    chars_to_find.append(cn_char)
            
            if chars_to_find:
                if " and " in condition_lower:
                    # All must be present
                    return all(c in context['chars'] for c in chars_to_find)
                elif " or " in condition_lower:
                    # Any can be present
                    return any(c in context['chars'] for c in chars_to_find)
                else:
                    # Single char or implicit OR
                    return any(c in context['chars'] for c in chars_to_find)
        
        # Pattern 2: English "Stems contains X" or "Stem contains X"
        if "stem" in condition_lower and "contain" in condition_lower:
            chars_to_find = []
            for pinyin, cn_char in stem_map.items():
                if pinyin in condition_lower:
                    chars_to_find.append(cn_char)
            
            if chars_to_find:
                if " and " in condition_lower:
                    return all(c in context['chars'] for c in chars_to_find)
                elif " or " in condition_lower:
                    return any(c in context['chars'] for c in chars_to_find)
                else:
                    return any(c in context['chars'] for c in chars_to_find)
        
        # Pattern 3: Quality checks (MUST come before generic element checks!)
        if "strong" in condition_lower or "powerful" in condition_lower or "强" in condition_str:
            # Check if any mentioned element is > 80
            for elem in ['Wood', 'Fire', 'Earth', 'Metal', 'Water', '木', '火', '土', '金', '水']:
                if elem.lower() in condition_lower or elem in condition_str:
                    elem_key = {'木': 'Wood', '火': 'Fire', '土': 'Earth', '金': 'Metal', '水': 'Water'}.get(elem, elem)
                    return context.get(elem_key, 0) > 80
        
        if "weak" in condition_lower or "弱" in condition_str:
            for elem in ['Wood', 'Fire', 'Earth', 'Metal', 'Water', '木', '火', '土', '金', '水']:
                if elem.lower() in condition_lower or elem in condition_str:
                    elem_key = {'木': 'Wood', '火': 'Fire', '土': 'Earth', '金': 'Metal', '水': 'Water'}.get(elem, elem)
                    return context.get(elem_key, 0) < 30
        
        # Pattern 4: "good" or "excellent" - heuristic positive condition
        if "good" in condition_lower or "excellent" in condition_lower or "好" in condition_str or "优秀" in condition_str:
            # If it mentions life/condition, check overall energy
            total_energy = sum(context.get(e, 0) for e in ['Wood', 'Fire', 'Earth', 'Metal', 'Water'])
            return total_energy > 200  # Heuristic
        
        # Pattern 5: "Element > value" or "Element < value"
        for elem in ['Wood', 'Fire', 'Earth', 'Metal', 'Water']:
            if elem.lower() in condition_lower:
                try:
                    if '>' in condition_str:
                        parts = condition_str.split('>')
                        threshold = float(parts[1].strip())
                        return context.get(elem, 0) > threshold
                    elif '<' in condition_str:
                        parts = condition_str.split('<')
                        threshold = float(parts[1].strip())
                        return context.get(elem, 0) < threshold
                    elif '=' in condition_str or 'is' in condition_lower:
                        # "Fire is high" or similar
                        return context.get(elem, 0) > 50  # Heuristic threshold
                except:
                    pass
        
        # Pattern 6: "Day Master is X" / "日主 是 X"
        if "day master" in condition_lower or "daymaster" in condition_lower or "日主" in condition_str:
            # Check if any element is mentioned
            for elem in ['Wood', 'Fire', 'Earth', 'Metal', 'Water']:
                if elem.lower() in condition_lower:
                    # Check day_stem particle
                    day_stem = context.get('day_stem')
                    if day_stem:
                        # Get element from stem
                        from core.kernel import Kernel
                        stem_char = day_stem.get('char')
                        if stem_char in Kernel.STEM_PROPERTIES:
                            dm_elem = Kernel.STEM_PROPERTIES[stem_char]['element']
                            return dm_elem == elem
            
            # Check for specific stems
            for pinyin, cn_char in stem_map.items():
                if pinyin in condition_lower:
                    day_stem = context.get('day_stem')
                    if day_stem and day_stem.get('char') == cn_char:
                        return True
        
        # Fallback: Try direct eval
        try:
            return self._evaluate(condition_str, context)
        except:
            return False

    def _calculate_effect(self, rule, context):
        """
        Return structured impact.
        """
        return rule.get('impact', "No quantitative impact defined.")

    def _explain_match(self, condition, context):
        return "Logic Match"
