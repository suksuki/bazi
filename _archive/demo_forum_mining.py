
import re
import json

# ==========================================
# 1. MOCK DATA: 10 Styles of Forum Threads
# ==========================================
MOCK_THREADS = [
    # Style 1: Standard Horizontal
    """
    [求测] 大师看看我的财运，乾造：甲子 乙亥 丙午 丁酉。
    目前在公司上班，感觉没前途。
    反馈：2021年确实像大师说的，破财了，炒股亏了5万。
    """,
    
    # Style 2: Vertical / Spaced
    """
    女命，想问婚姻。
    坤造
    壬  癸  辛  己
    申  卯  巳  亥
    大运：甲辰 乙巳...
    楼主反馈：辛丑年结婚了，对象是同学，很准。
    """,
    
    # Style 3: Clean Labeled
    """
    出生日期：1990年5月5日
    八字：
    年柱：庚午
    月柱：辛巳
    日柱：壬申
    时柱：癸卯
    请教事业。
    Feedback: 庚子年换工作了，工资涨了30%。
    """,
    
    # Style 4: Hidden in text
    """
    新人发帖。男，出生于戊辰年，甲寅月，乙未日，丙子时。
    小时候家里穷，现在做IT。
    反馈：壬寅年（2022）生了儿子，正如所测。
    """,
    
    # Style 5: No separators (Rare but happens)
    """
    乾造 癸酉乙卯丁巳庚戌
    求测学业。
    反馈：考研上岸了，丁酉年考上的。
    """,
     
    # Style 6: With messy interfering text
    """
    排盘系统：元亨利贞网
    姓名：某人  性别：男
    公历：1988年...
    乾造：戊  甲  丁  庚 (日空 申酉)
          辰  寅  卯  戌
    大运：乙卯 丙辰...
    真实反馈：2018年戊戌年，父亲去世，非常痛苦，准得可怕。
    """,

    # Style 7: Short form
    """
    甲子 丙寅 戊午 庚申
    看看今年怎么样？
    feedback: 还可以，平平淡淡。
    """,
    
    # Style 8: Traditional text
    """
    此造：壬戌 壬子 戊申 乙卯。
    断：身弱财旺。
    反馈：确实身体不好，一直吃药。
    """,
    
    # Style 9: Chat style
    """
    楼主：请帮我看下。
    乾：乙丑，己丑，癸酉，癸亥。
    二楼：财多身弱。
    楼主回复二楼：不对，我家里挺有钱的，父亲是高管。
    """,
    
    # Style 10: Full Report Dump
    """
    易学排盘
    ----------------
    乾造：
    年：丙寅
    月：庚寅
    日：辛酉
    时：戊子
    ----------------
    反馈：大运走的好，辛丑年发了一笔横财。
    """
]

# ==========================================
# 2. REGEX ENGINE (The Core Task)
# ==========================================

class BaziRegexExtractor:
    def __init__(self):
        self.stems = "甲乙丙丁戊己庚辛壬癸"
        self.branches = "子丑寅卯辰巳午未申酉戌亥"
        
        # Pattern A: 4 Pairs (e.g. "甲子 乙丑 丙寅 丁卯")
        # Matches 4 groups of [Stem][Branch], separated by optional spaces/chars
        self.patt_4pairs = re.compile(
            rf"([{self.stems}][{self.branches}])"  # Pillar 1
            rf"[\s\u3000\t,，\-|]*"                # Separator
            rf"([{self.stems}][{self.branches}])"  # Pillar 2
            rf"[\s\u3000\t,，\-|]*"
            rf"([{self.stems}][{self.branches}])"  # Pillar 3
            rf"[\s\u3000\t,，\-|]*"
            rf"([{self.stems}][{self.branches}])"  # Pillar 4
        )
        
        # Pattern B: Vertical/Split (e.g. "甲 乙 丙 丁" then "子 丑 寅 卯")
        # Finds 4 Stems followed clearly by 4 Branches later
        self.patt_stems = re.compile(rf"[{self.stems}]\s+[{self.stems}]\s+[{self.stems}]\s+[{self.stems}]")
        self.patt_branches = re.compile(rf"[{self.branches}]\s+[{self.branches}]\s+[{self.branches}]\s+[{self.branches}]")

    def extract(self, text):
        # Clean text
        text_clean = text.replace("\n", " ")
        
        # Strategy A: Try to find 4 contiguous pillars (Horizontal)
        match = self.patt_4pairs.search(text_clean)
        if match:
            return list(match.groups())
            
        # Strategy B: Try to find 4 Stems line and 4 Branches line (Vertical)
        # This is harder in flat text, requires relative position check.
        # Simplification for Demo: Just look for horizontal format or manual labels
        
        # Strategy C: Labeled (Year: X...)
        # Naive extraction of all stem-branch pairs found
        all_pairs = re.findall(rf"[{self.stems}][{self.branches}]", text_clean)
        if len(all_pairs) >= 4:
            # Heuristic: Take the first 4 distinct ones found close together?
            # Or just take top 4.
            return all_pairs[:4]
            
        return None

# ==========================================
# 3. FEEDBACK EXTRACTOR (Simple Rule-Based)
# ==========================================
def extract_feedback(text):
    # Determine Sentiment
    sentiment = 0.0
    
    pos_keywords = ["准", "对", "确实", "没错", "是的", "应验", "结婚", "升职", "发财", "生了"]
    neg_keywords = ["不对", "反了", "错了", "胡说", "没有", "还可以", "平平"]
    
    feedback_text = ""
    
    # Locate Feedback Section
    pattern = re.compile(r"(反馈|feedback|回复|真实反馈)[：:](.*)", re.IGNORECASE)
    match = pattern.search(text)
    if match:
        feedback_text = match.group(2)[:50] + "..." # Snippet
        full_fb = match.group(2)
        
        # Scoring
        if any(k in full_fb for k in neg_keywords):
            sentiment = -0.5 # Correction
            if "不对" in full_fb: sentiment = -1.0
        elif any(k in full_fb for k in pos_keywords):
            sentiment = 1.0
        else:
            sentiment = 0.1 # Neutral/Ambiguous
            
    return feedback_text, sentiment

# ==========================================
# 4. RUN DEMO
# ==========================================
if __name__ == "__main__":
    extractor = BaziRegexExtractor()
    
    print(f"{'ID':<4} | {'八字 (Bazi Structure)':<30} | {'反馈 (Feedback Snippet)':<30} | {'Score'}")
    print("-" * 85)
    
    for i, thread in enumerate(MOCK_THREADS):
        # 1. Extract Bazi
        bazi = extractor.extract(thread)
        bazi_str = " ".join(bazi) if bazi else "❌ Extraction Failed"
        
        # 2. Extract Feedback
        fb_txt, score = extract_feedback(thread)
        if not fb_txt: fb_txt = "(No specific feedback found)"
        
        print(f"#{i+1:<3} | {bazi_str:<30} | {fb_txt:<30} | {score}")
