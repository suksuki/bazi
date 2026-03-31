
import re
import json
import logging

class China95Parser:
    """
    Miner Strategy: China95 (元亨利贞)
    Protocol V6.1 - Tier 0 Target
    """
    
    def __init__(self):
        self.logger = logging.getLogger("China95Miner")
        self.feedback_keywords = ["反馈", "准", "对了", "确实", "神准", "应期", "结婚", "离了", "破财", "生子", "去世"]
    
    def parse_thread(self, thread_html_or_text):
        """
        Parses a simulate thread structure.
        Input is expected to be a raw text dump or simplified HTML/Text object representation.
        For this demo, we assume the input is a list of posts: [{'user': 'OP', 'content': '...'}, ...]
        """
        if not isinstance(thread_html_or_text, list):
            # If string, try to split by simple logic (Mocking a scraper result)
            self.logger.warning("Input is string, assuming single post mock.")
            posts = [{'user': 'LouZhu', 'content': thread_html_or_text}]
        else:
            posts = thread_html_or_text

        if not posts:
            return None
            
        op_user = posts[0]['user']
        op_content = posts[0]['content']
        
        # 1. Strategy B: Extract Bazi (China95 Format)
        bazi_json = self._extract_bazi_china95(op_content)
        if not bazi_json:
            return {"error": "No Bazi Found", "quality": 0}

        # 2. Strategy A: Feedback Anchor
        feedback_timeline = []
        op_replies = [p for p in posts[1:] if p['user'] == op_user]
        
        if not op_replies and len(posts) > 1:
            # OP never replied
            return {"error": "Zombie Thread (No OP Reply)", "quality": 0}
            
        # Scan replies
        for post in op_replies:
             content = post['content']
             # Check keywords
             if any(Kw in content for Kw in self.feedback_keywords):
                 feedback_timeline.append({
                     "raw_content": content[:100] + "...",
                     "sentiment": 1.0, # Simplified positive assumption for presence of "准/反馈"
                     "type": "General Feedback"
                 })
                 
        # 3. Quality Score
        quality = 0.5 # Base
        if bazi_json: quality += 0.2
        if feedback_timeline: quality += 0.25
        if len(feedback_timeline) > 2: quality = 0.99
        
        return {
            "source": "China95",
            "data_quality_score": round(quality, 2),
            "bazi_input": bazi_json,
            "ground_truth_events": feedback_timeline
        }

    def _extract_bazi_china95(self, text):
        """
        Parses common China95排盘 output.
        Handles vertical layout where Branches are on the line below Stems.
        """
        lines = text.split('\n')
        
        gender = "Unknown"
        stems = []
        branches = []
        year_val = "Unknown"
        
        # 1. Scan for Gender & Stems Line
        stem_line_idx = -1
        
        for i, line in enumerate(lines):
            # Check Date
            date_match = re.search(r"公历[：: ]*(\d{4})年", line)
            if date_match:
                year_val = date_match.group(1)
            
            # Check Stems Marker
            if "乾造" in line or "坤造" in line:
                gender = "Male" if "乾造" in line else "Female"
                stem_line_idx = i
                
                # Extract Stems from this line
                # Pattern: Marker + S1 + S2 + S3 + S4
                # Allow for messy spaces
                matches = re.findall(r"([甲乙丙丁戊己庚辛壬癸])", line)
                # Usually matches include the marker chars if we aren't careful, 
                # but "乾造" don't contain stems. Wait, what if someone writes '甲' in text?
                # Better stricter regex for the chart line logic.
                
                # Strict structure: (乾造|坤造) ... S ... S ... S ... S
                # But sometimes "乾造：甲子..." (Horizontal)
                # Let's check for Horizontal first (Standard regex)
                horiz_res = self._try_horizontal_parse(line)
                if horiz_res:
                    return {
                        "gender": gender,
                        "year_val": year_val,
                        "pillars": horiz_res
                    }
                
                # If not horizontal (count of pairs < 4), assume Vertical Stems
                # Extract just the 4 stems
                # Remove '乾/坤/造' to avoid confusion if they contained stem chars (they don't)
                clean_line = line.replace("乾造", "").replace("坤造", "")
                found_stems = re.findall(r"([甲乙丙丁戊己庚辛壬癸])", clean_line)
                if len(found_stems) >= 4:
                    stems = found_stems[:4]
                break

        # 2. If Stems found, look for Branches in next lines
        if stems and stem_line_idx != -1:
            # Look at next 1-3 lines for branches
            for j in range(1, 4):
                if stem_line_idx + j >= len(lines):
                    break
                
                next_line = lines[stem_line_idx + j]
                # Look for 4 Branches
                found_branches = re.findall(r"([子丑寅卯辰巳午未申酉戌亥])", next_line)
                
                if len(found_branches) >= 4:
                    branches = found_branches[:4]
                    break
        
        # 3. Construct Result
        if stems and branches:
            return {
                "gender": gender,
                "year_val": year_val,
                "bazi_structure": {
                    "year": {"stem": stems[0], "branch": branches[0]},
                    "month": {"stem": stems[1], "branch": branches[1]},
                    "day": {"stem": stems[2], "branch": branches[2]},
                    "hour": {"stem": stems[3], "branch": branches[3]}
                }
            }
        
        # Fallback: regex search on full text if line-parsing failed
        return self._fallback_regex(text, gender, year_val)

    def _try_horizontal_parse(self, line):
        # Matches: 甲子 乙丑 ...
        pairs = re.findall(r"([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])", line)
        if len(pairs) >= 4:
            return pairs[:4]
        return None

    def _fallback_regex(self, text, gender, year_val):
        simple_match = re.search(r"([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])", text)
        if simple_match:
             return {
                 "gender": gender,
                 "year_val": year_val,
                 "pillars": list(simple_match.groups()),
                 "note": "Fallback horizontal regex"
             }
        return None
